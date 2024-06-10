# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    TRANSACTION class to create, verify and sign Transactions
#    © 2017 - 2024 June - 1200 Web Development <http://1200wd.com/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from datetime import datetime
import json
import pickle
import random
from io import BytesIO
from bitcoinlib.encoding import *
# from bitcoinlib.config.opcodes import *
from bitcoinlib.keys import HDKey, Key, deserialize_address, Address, sign, verify, Signature
from bitcoinlib.networks import Network
from bitcoinlib.values import Value, value_to_satoshi
from bitcoinlib.scripts import Script

_logger = logging.getLogger(__name__)


class TransactionError(Exception):
    """
    Handle Transaction class Exceptions
    """

    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


# @deprecated  # Replaced by Script class in version 0.6
# def script_add_locktime_cltv(locktime_cltv, script):  # pragma: no cover
#     lockbytes = bytes([op.op_checklocktimeverify, op.op_drop])
#     if script and len(script) > 6:
#         if script[4:6] == lockbytes:
#             return script
#     return varstr(locktime_cltv.to_bytes(4, 'little')) + lockbytes + script
#
#
# @deprecated  # Replaced by Script class in version 0.6
# def script_add_locktime_csv(locktime_csv, script):  # pragma: no cover
#     lockbytes = bytes([op.op_checklocktimeverify, op.op_drop])
#     if script and len(script) > 6:
#         if script[4:6] == lockbytes:
#             return script
#     return varstr(locktime_csv.to_bytes(4, 'little')) + lockbytes + script


def get_unlocking_script_type(locking_script_type, witness_type='legacy', multisig=False):
    """
    Specify locking script type and get corresponding script type for unlocking script

    >>> get_unlocking_script_type('p2wsh')
    'p2sh_multisig'

    :param locking_script_type: Locking script type. I.e.: p2pkh, p2sh, p2wpkh, p2wsh
    :type locking_script_type: str
    :param witness_type: Type of witness: legacy or segwit. Default is legacy
    :type witness_type: str
    :param multisig: Is multisig script or not? Default is False
    :type multisig: bool

    :return str: Unlocking script type such as sig_pubkey or p2sh_multisig
    """

    if locking_script_type in ['p2pkh', 'p2wpkh']:
        return 'sig_pubkey'
    elif locking_script_type == 'p2wsh' or (witness_type == 'legacy' and multisig):
        return 'p2sh_multisig'
    elif locking_script_type == 'p2sh':
        if not multisig:
            return 'sig_pubkey'
        else:
            return 'p2sh_multisig'
    elif locking_script_type == 'p2pk':
        return 'signature'
    else:
        raise TransactionError("Unknown locking script type %s" % locking_script_type)


def transaction_update_spents(txs, address):
    """
    Update spent information for list of transactions for a specific address. This method assumes the list of
    transaction complete and up-to-date.

    This method loops through all the transaction and update all transaction outputs for given address, checks
    if the output is spent and add the spending transaction ID and index number to the outputs.

    The same list of transactions with updates outputs will be returned

    :param txs: Complete list of transactions for given address
    :type txs: list of Transaction
    :param address: Address string
    :type address: str

    :return list of Transaction:
    """
    spend_list = {}
    for t in txs:
        for inp in t.inputs:
            if inp.address == address:
                spend_list.update({(inp.prev_txid.hex(), inp.output_n_int): t})
    address_inputs = list(spend_list.keys())
    for t in txs:
        for to in t.outputs:
            if to.address != address:
                continue
            spent = True if (t.txid, to.output_n) in address_inputs else False
            txs[txs.index(t)].outputs[to.output_n].spent = spent
            if spent:
                spending_tx = spend_list[(t.txid, to.output_n)]
                spending_index_n = \
                    [inp for inp in txs[txs.index(spending_tx)].inputs
                     if inp.prev_txid.hex() == t.txid and inp.output_n_int == to.output_n][0].index_n
                txs[txs.index(t)].outputs[to.output_n].spending_txid = spending_tx.txid
                txs[txs.index(t)].outputs[to.output_n].spending_index_n = spending_index_n
    return txs


class Input(object):
    """
    Transaction Input class, used by Transaction class
    
    An Input contains a reference to an UTXO or Unspent Transaction Output (prev_txid + output_n).
    To spend the UTXO an unlocking script can be included to prove ownership.
    
    Inputs are verified by the Transaction class.
    """

    def __init__(self, prev_txid, output_n, keys=None, signatures=None, public_hash=b'', unlocking_script=b'',
                 locking_script=None, redeemscript=None, script_type=None, address='', sequence=0xffffffff,
                 compressed=None, sigs_required=None, sort=False, index_n=0, value=0, double_spend=False,
                 locktime_cltv=None, locktime_csv=None, key_path='', witness_type=None, witnesses=None, encoding=None,
                 strict=True, network=DEFAULT_NETWORK):
        """
        Create a new transaction input
        
        :param prev_txid: Transaction hash of the UTXO (previous output) which will be spent.
        :type prev_txid: bytes, str
        :param output_n: Output number in previous transaction.
        :type output_n: bytes, int
        :param keys: A list of Key objects or public / private key string in various formats. If no list is provided but a bytes or string variable, a list with one item will be created. Optional
        :type keys: list (bytes, str, Key, HDKey)
        :param signatures: Specify optional signatures
        :type signatures: list (bytes, str, Signature)
        :param public_hash: Public key hash or script hash. Specify if key is not available
        :type public_hash: bytes
        :param unlocking_script: Unlocking script (scriptSig) to prove ownership. Optional
        :type unlocking_script: bytes, hexstring
        :param locking_script: Unlocking script for signing transaction
        :type locking_script: bytes, hexstring
        :param redeemscript: Redeem script for p2sh transaction. Will be automatically created for standard scripts
        :type redeemscript: bytes, hexstring
        :param script_type: Type of unlocking script used, i.e. p2pkh or p2sh_multisig. Default is p2pkh
        :type script_type: str
        :param address: Address string or object for input
        :type address: str, Address
        :param sequence: Sequence part of input, used for locktime setting and replace by fee. No need to set directly normally.
        :type sequence: bytes, int
        :param compressed: Use compressed or uncompressed public keys. Default is compressed
        :type compressed: bool
        :param sigs_required: Number of signatures required for a p2sh_multisig unlocking script
        :type sigs_required: int
        :param sort: Sort public keys according to BIP0045 standard. Default is False to avoid unexpected change of key order.
        :type sort: boolean
        :param index_n: Index of input in transaction. Used by Transaction class.
        :type index_n: int
        :param value: Value of input in the smallest denominator integers (Satoshi's) or as Value object or string
        :type value: int, Value, str
        :param double_spend: Is this input also spend in another transaction
        :type double_spend: bool
        :param locktime_csv: Check Sequence Verify value
        :type locktime_csv: int
        :param key_path: Key path of input key as BIP32 string or list
        :type key_path: str, list
        :param witness_type: Specify witness/signature position: 'segwit' or 'legacy'. Determine from script, address or encoding if not specified.
        :type witness_type: str
        :param witnesses: List of witnesses for inputs, used for segwit transactions for instance. Argument can be list of bytes or string or a single bytes string with concatenated witnesses as found in a raw transaction.
        :type witnesses: list of bytes, list of str, bytes
        :param encoding: Address encoding used. For example bech32/base32 or base58. Leave empty for default
        :type encoding: str
        :param strict: Raise exception when input is malformed, incomplete or not understood
        :type strict: bool
        :param network: Network, leave empty for default
        :type network: str, Network
        """

        self.prev_txid = to_bytes(prev_txid)
        self.output_n = output_n
        if isinstance(output_n, int):
            self.output_n_int = output_n
            self.output_n = output_n.to_bytes(4, 'big')
        else:
            self.output_n_int = int.from_bytes(output_n, 'big')
            self.output_n = output_n
        self.unlocking_script = b'' if unlocking_script is None else to_bytes(unlocking_script)
        self.locking_script = b'' if locking_script is None else to_bytes(locking_script)
        self.script = None
        self.hash_type = SIGHASH_ALL
        if isinstance(sequence, numbers.Number):
            self.sequence = sequence
        else:
            self.sequence = int.from_bytes(sequence, 'little')
        self.compressed = compressed
        self.network = network
        if not isinstance(network, Network):
            self.network = Network(network)
        self.index_n = index_n
        self.value = value_to_satoshi(value, network=network)
        if not keys:
            keys = []
        self.keys = []
        if not isinstance(keys, list):
            keys = [keys]
        self.public_hash = public_hash
        if not signatures:
            signatures = []
        if not isinstance(signatures, list):
            signatures = [signatures]
        self.sort = sort

        self.address = ''
        self.address_obj = None
        if isinstance(address, Address):
            self.address_obj = address
            self.address = address.address
            self.encoding = address.encoding
            self.network = address.network
            self.witness_type = address.witness_type
        elif address:
            self.address = address
            self.address_obj = Address.parse(address)
        if self.address_obj:
            encoding = self.address_obj.encoding
            witness_type = self.address_obj.witness_type if self.address_obj.witness_type else witness_type
        self.signatures = []
        self.redeemscript = b'' if not redeemscript else redeemscript
        self.script_type = script_type
        if self.prev_txid == b'\0' * 32:
            self.script_type = 'coinbase'
        self.double_spend = double_spend
        self.locktime_cltv = locktime_cltv
        self.locktime_csv = locktime_csv
        self.witness_type = witness_type
        if encoding is None:
            self.encoding = 'bech32'
            if self.witness_type == 'legacy' or self.witness_type == 'p2sh-segwit':
                self.encoding = 'base58'
        else:
            self.encoding = encoding
        self.valid = None
        self.key_path = key_path

        self.witnesses = []
        if isinstance(witnesses, bytes):
            n_items, cursor = varbyteint_to_int(witnesses[0:9])
            for m in range(0, n_items):
                witness = b'\0'
                item_size, size = varbyteint_to_int(witnesses[cursor:cursor + 9])
                if item_size:
                    witness = witnesses[cursor + size:cursor + item_size + size]
                cursor += item_size + size
                self.witnesses.append(witness)
        elif witnesses:
            self.witnesses = [bytes.fromhex(w) if isinstance(w, str) else w for w in witnesses]

        # If unlocking script is specified extract keys, signatures, type from script
        if self.unlocking_script and self.script_type != 'coinbase' and not (signatures and keys):
            script = Script.parse_bytes(self.unlocking_script, is_locking=False, strict=strict)
            self.keys = script.keys
            self.signatures = script.signatures
            if len(self.signatures):
                self.hash_type = self.signatures[0].hash_type
            sigs_required = script.sigs_required
            if len(script.script_types) == 1 and not self.script_type:
                self.script_type = script.script_types[0]
        if self.locking_script and not self.signatures:
            ls = Script.parse_bytes(self.locking_script, is_locking=True, strict=strict)
            self.public_hash = self.public_hash if not ls.public_hash else ls.public_hash
            if ls.script_types[0] in ['p2wpkh', 'p2wsh']:
                self.witness_type = 'segwit'
        self.sigs_required = sigs_required if sigs_required else 1

        if self.script_type is None and self.witness_type is None and self.witnesses:
            self.witness_type = 'segwit'
        if self.witness_type is None or self.witness_type == 'legacy':
            if self.script_type in ['p2sh_p2wpkh', 'p2sh_p2wsh']:
                self.witness_type = 'p2sh-segwit'
                self.encoding = 'base58'
            elif not self.witness_type:
                if not self.witnesses:
                    self.witness_type = 'legacy'
                else:
                    self.witness_type = 'segwit'
        elif self.witness_type == 'segwit' and self.script_type == 'sig_pubkey' and encoding is None:
            self.encoding = 'bech32'
        if not self.script_type:
            self.script_type = 'sig_pubkey'

        for key in keys:
            if not isinstance(key, Key):
                kobj = Key(key, network=network, strict=strict)
            else:
                kobj = key
            if kobj not in self.keys:
                self.compressed = kobj.compressed
                self.keys.append(kobj)
        if self.compressed is None:
            self.compressed = True
        if self.sort:
            self.keys.sort(key=lambda k: k.public_byte)
        self.strict = strict

        for sig in signatures:
            if not isinstance(sig, Signature):
                try:
                    sig = Signature.parse(sig)
                except Exception as e:
                    _logger.error("Could not parse signature %s in Input. Error: %s" % (to_hexstring(sig), e))
                    continue
            if sig.as_der_encoded() not in [x.as_der_encoded() for x in self.signatures]:
                self.signatures.append(sig)
                if sig.hash_type:
                    self.hash_type = sig.hash_type

        if self.script_type in ['sig_pubkey', 'p2sh_p2wpkh'] and self.witnesses and not self.signatures and \
                len(self.witnesses) == 2 and b'\0' not in self.witnesses:
            self.signatures = [Signature.parse_bytes(self.witnesses[0])]
            self.hash_type = self.signatures[0].hash_type
            self.keys = [Key(self.witnesses[1], network=self.network, strict=self.strict)]

        self.update_scripts(hash_type=self.hash_type)

    @classmethod
    def parse(cls, raw, witness_type='segwit', index_n=0, strict=True, network=DEFAULT_NETWORK):
        """
        Parse raw BytesIO string and return Input object

        :param raw: Input
        :type raw: BytesIO
        :param witness_type: Specify witness/signature position: 'segwit' or 'legacy'. Derived from script if not specified.
        :type witness_type: str
        :param index_n: Index number of input
        :type index_n: int
        :param strict: Raise exception when input is malformed, incomplete or not understood
        :type strict: bool
        :param network: Network, leave empty for default
        :type network: str, Network

        :return Input:
        """
        prev_hash = raw.read(32)[::-1]
        if len(prev_hash) != 32:
            raise TransactionError("Input transaction hash not found. Probably malformed raw transaction")
        output_n = raw.read(4)[::-1]
        unlocking_script_size = read_varbyteint(raw)
        unlocking_script = raw.read(unlocking_script_size)
        script_type = None

        # TODO - handle non-standard input script b'\1\0',
        #  see tx 38cf5779d1c5ca32b79cd5052b54e824102e878f041607d3b962038f5a8cf1ed
        if unlocking_script_size == 1 and unlocking_script == b'\0':
            script_type = 'nonstandard_0001'

        inp_type = 'legacy'
        if witness_type == 'segwit' and not unlocking_script_size:
            inp_type = 'segwit'
        sequence_number = raw.read(4)

        return Input(prev_txid=prev_hash, output_n=output_n, unlocking_script=unlocking_script,
                     witness_type=inp_type, sequence=sequence_number, index_n=index_n, strict=strict, network=network,
                     script_type=script_type)

    def update_scripts(self, hash_type=SIGHASH_ALL):
        """
        Method to update Input scripts.

        Creates or updates unlocking script, witness script for segwit inputs, multisig redeemscripts and
        locktime scripts. This method is called when initializing an Input class or when signing an input.

        :param hash_type: Specific hash type, default is SIGHASH_ALL
        :type hash_type: int

        :return bool: Always returns True when method is completed
        """

        addr_data = b''
        unlock_script = b''
        if self.script_type in ['sig_pubkey', 'p2sh_p2wpkh']:
            if not self.public_hash and self.keys:
                self.public_hash = self.keys[0].hash160
            if not self.keys and not self.public_hash:
                return
            self.locking_script = b'\x76\xa9\x14' + self.public_hash + b'\x88\xac'
            addr_data = self.public_hash
            if self.signatures and self.keys:
                self.witnesses = [self.signatures[0].as_der_encoded() if hash_type else b'', self.keys[0].public_byte]
                unlock_script = b''.join([bytes(varstr(w)) for w in self.witnesses])
            if not self.unlocking_script or self.strict:
                if self.witness_type == 'p2sh-segwit':
                    self.unlocking_script = varstr(b'\0' + varstr(self.public_hash))
                elif self.witness_type == 'segwit':
                    self.unlocking_script = b''
                elif unlock_script != b'':
                    self.unlocking_script = unlock_script
        elif self.script_type in ['p2sh_multisig', 'p2sh_p2wsh']:
            if not self.redeemscript and self.keys:
                self.redeemscript = Script(script_types=['multisig'], keys=self.keys,
                                           sigs_required=self.sigs_required).serialize()
            if self.redeemscript and not self.public_hash:
                if self.witness_type == 'segwit' or self.witness_type == 'p2sh-segwit':
                    self.public_hash = hashlib.sha256(self.redeemscript).digest()
                else:
                    self.public_hash = hash160(self.redeemscript)
            addr_data = self.public_hash

            if self.redeemscript and self.keys:
                n_tag = self.redeemscript[0:1]
                if not isinstance(n_tag, int):
                    n_tag = int.from_bytes(n_tag, 'big')
                self.sigs_required = n_tag - 80
                signatures = [s.as_der_encoded() for s in self.signatures[:self.sigs_required]]
                if b'' in signatures:
                    raise TransactionError("Empty signature found in signature list when signing. "
                                           "Is DER encoded version of signature defined?")
                if len(signatures) and len(signatures) >= self.sigs_required:  # and not self.unlocking_script
                    unlock_script_obj = Script(script_types=['p2sh_multisig'], keys=[k.public_byte for k in self.keys],
                                               signatures=self.signatures[:self.sigs_required],
                                               sigs_required=self.sigs_required, redeemscript=self.redeemscript)
                    if self.witness_type in ['segwit', 'p2sh-segwit']:
                        unlock_script = unlock_script_obj.serialize_list()
                    else:
                        unlock_script = unlock_script_obj.serialize()
                if self.witness_type == 'segwit':
                    self.locking_script = b''
                    for k in self.keys:
                        self.locking_script += varstr(k.public_byte) + b'\xad\xab'
                    if len(self.locking_script) > 3:
                        self.locking_script = self.locking_script[:-2] + b'\xac'
                    if signatures:
                        self.witnesses = unlock_script
                elif self.witness_type == 'p2sh-segwit':
                    self.unlocking_script = varstr(b'\0' + varstr(self.public_hash))
                    if signatures:
                        self.witnesses = unlock_script
                elif unlock_script != b'': # and self.strict:
                    self.unlocking_script = unlock_script
        elif self.script_type == 'signature':
            if self.keys:
                self.locking_script = varstr(self.keys[0].public_byte) + b'\xac'
                addr_data = hash160(self.keys[0].public_byte)
            if self.signatures and not self.unlocking_script:
                self.unlocking_script = varstr(self.signatures[0].as_der_encoded())
        elif self.script_type == 'p2tr':  # segwit_v1
            self.redeemscript = self.witnesses[0]
            # FIXME: Address cannot be known without looking at previous transaction
        elif self.script_type[:11] not in ['coinbase', 'unknown', 'nonstandard'] and self.strict:
            raise TransactionError("Unknown unlocking script type %s for input %d" % (self.script_type, self.index_n))
        if addr_data and not self.address:
            self.address = Address(hashed_data=addr_data, encoding=self.encoding, network=self.network,
                                   script_type=self.script_type, witness_type=self.witness_type).address
        # FIXME: need to add locktime script to redeemscript
        # if self.locktime_cltv:
        #     self.locking_script = script_add_locktime_cltv(self.locktime_cltv, self.locking_script)
        #     # if self.unlocking_script:
        #     #     self.unlocking_script = script_add_locktime_cltv(self.locktime_cltv, self.unlocking_script)
        #     # if self.witness_type == 'segwit':
        #     #     self.witnesses.insert(0, script_add_locktime_cltv(self.locktime_cltv, b''))
        # if self.locktime_csv:
        #     self.locking_script = script_add_locktime_csv(self.locktime_csv, self.locking_script)
        #     self.unlocking_script = script_add_locktime_csv(self.locktime_csv, self.unlocking_script)
        return True

    def verify(self, transaction_hash):
        """
        Verify input with provided transaction hash, check if signatures matches public key.

        Does not check if UTXO is valid or has already been spent

        :param transaction_hash: Double SHA256 Hash of Transaction signature
        :type transaction_hash: bytes

        :return bool: True if enough signatures provided and if all signatures are valid
        """

        if self.script_type == 'coinbase':
            self.valid = True
            return True
        if not self.signatures:
            _logger.info("No signatures found for transaction input %d" % self.index_n)
            return False

        sig_n = 0
        key_n = 0
        sigs_verified = 0
        while sigs_verified < self.sigs_required:
            if key_n >= len(self.keys):
                _logger.info(
                    "Not enough valid signatures provided for input %d. Found %d signatures but %d needed" %
                    (self.index_n, sigs_verified, self.sigs_required))
                return False
            if sig_n >= len(self.signatures):
                _logger.info("No valid signatures found")
                return False
            key = self.keys[key_n]
            sig = self.signatures[sig_n]
            if verify(transaction_hash, sig, key):
                sigs_verified += 1
                sig_n += 1
            elif sig_n > 0:
                # try previous signature
                prev_sig = deepcopy(self.signatures[sig_n - 1])
                if verify(transaction_hash, prev_sig, key):
                    sigs_verified += 1
            key_n += 1
        self.valid = True
        return True

    def as_dict(self):
        """
        Get transaction input information in json format
        
        :return dict: Json with output_n, prev_txid, output_n, type, address, public_key, public_hash, unlocking_script and sequence
        """

        pks = []
        for k in self.keys:
            pks.append(k.public_hex)
        if len(self.keys) == 1:
            pks = pks[0]
        return {
            'index_n': self.index_n,
            'prev_txid': self.prev_txid.hex(),
            'output_n': self.output_n_int,
            'script_type': self.script_type,
            'address': self.address,
            'value': self.value,
            'public_keys': pks,
            'compressed': self.compressed,
            'encoding': self.encoding,
            'double_spend': self.double_spend,
            'script': self.unlocking_script.hex(),
            'redeemscript': self.redeemscript.hex(),
            'sequence': self.sequence,
            'signatures': [s.hex() for s in self.signatures],
            'sigs_required': self.sigs_required,
            # 'locktime_cltv': self.locktime_cltv,
            'locktime_csv': self.locktime_csv,
            'public_hash': self.public_hash.hex(),
            'unlocking_script': self.unlocking_script.hex(),
            'locking_script': self.locking_script.hex(),
            'witness_type': self.witness_type,
            'witness': b''.join(self.witnesses).hex(),
            'sort': self.sort,
            'valid': self.valid,
        }

    def __repr__(self):
        return "<Input(prev_txid='%s', output_n=%d, address='%s', index_n=%s, type='%s')>" % \
               (self.prev_txid.hex(), self.output_n_int, self.address, self.index_n, self.script_type)


class Output(object):
    """
    Transaction Output class, normally part of Transaction class.
    
    Contains the amount and destination of a transaction.
    """

    def __init__(self, value, address='', public_hash=b'', public_key=b'', lock_script=b'', spent=False,
                 output_n=0, script_type=None, witver=0, encoding=None, spending_txid='', spending_index_n=None,
                 strict=True, change=None, witness_type=None, network=DEFAULT_NETWORK):
        """
        Create a new transaction output
        
        A transaction outputs locks the specified amount to a public key. Anyone with the private key can unlock
        this output.
        
        The transaction output class contains an amount and the destination which can be provided either as address, 
        public key, public key hash or a locking script. Only one needs to be provided as they all can be derived
        from each other, but you can provide as many attributes as you know to improve speed.
        
        :param value: Amount of output in the smallest denominator integers (Satoshi's) or as Value object or string
        :type value: int, Value, str
        :param address: Destination address of output. Leave empty to derive from other attributes you provide. An instance of an Address or HDKey class is allowed as argument.
        :type address: str, Address, HDKey
        :param public_hash: Hash of public key or script
        :type public_hash: bytes, str
        :param public_key: Destination public key
        :type public_key: bytes, str
        :param lock_script: Locking script of output. If not provided a default unlocking script will be provided with a public key hash.
        :type lock_script: bytes, str
        :param spent: Is output already spent? Default is False
        :type spent: bool
        :param output_n: Output index number, default is 0. Index number has to be unique per transaction and 0 for first output, 1 for second, etc
        :type output_n: int
        :param script_type: Script type of output (p2pkh, p2sh, segwit p2wpkh, etc). Extracted from lock_script if provided.
        :type script_type: str
        :param witver: Witness version
        :type witver: int
        :param encoding: Address encoding used. For example bech32/base32 or base58. Leave empty to derive from address or default base58 encoding
        :type encoding: str
        :param spending_txid: Transaction hash of input spending this transaction output
        :type spending_txid: str
        :param spending_index_n: Index number of input spending this transaction output
        :type spending_index_n: int
        :param strict: Raise exception when output is malformed, incomplete or not understood
        :type strict: bool
        :param change: Is this a change output back to own wallet or not? Used for replace-by-fee.
        :type change: bool
        :param witness_type: Specify witness type: 'segwit' or 'legacy'. Determine from script, address or encoding if not specified.
        :type witness_type: str
        :param network: Network, leave empty for default
        :type network: str, Network
        """

        if strict and not (address or public_hash or public_key or lock_script):
            raise TransactionError("Please specify address, lock_script, public key or public key hash when "
                                   "creating output")

        self.change = change
        self.network = network
        if not isinstance(network, Network):
            self.network = Network(network)
        self.value = value_to_satoshi(value, network=network)
        self.lock_script = b'' if lock_script is None else to_bytes(lock_script)
        self.public_hash = to_bytes(public_hash)
        if isinstance(address, Address):
            self._address = address.address
            self._address_obj = address
        elif isinstance(address, HDKey):
            self._address = address.address()
            self._address_obj = address.address_obj
            public_key = address.public_byte
            if not script_type:
                script_type = script_type_default(address.witness_type, address.multisig, True)
            # self.public_hash = address.hash160
            # self.witness_type = address.witness_type
        else:
            self._address = address
            self._address_obj = None
        self.public_key = to_bytes(public_key)
        self.compressed = True
        self.versionbyte = self.network.prefix_address
        self.script_type = script_type
        self.encoding = encoding
        self.spent = spent
        self.output_n = output_n
        self.script = Script.parse_bytes(self.lock_script, strict=strict, is_locking=True)
        self.witver = witver
        self.witness_type = witness_type

        if self._address_obj:
            self.script_type = self._address_obj.script_type if script_type is None else script_type
            # if not script_type:
            #     script_type = script_type_default(address.witness_type, address.multisig, True)
            self.public_hash = self._address_obj.hash_bytes
            self.network = self._address_obj.network
            self.encoding = self._address_obj.encoding
            self.witness_type = self._address_obj.witness_type

        if self.script:
            self.script_type = self.script_type if not self.script.script_types else self.script.script_types[0]
            self.public_hash = self.script.public_hash
            if self.script.keys:
                self.public_key = self.script.keys[0].public_byte
            if self.script_type == 'p2tr':
                self.witver = self.script.commands[0] - 80

        if self.public_key and not self.public_hash:
            self.public_hash = hash160(self.public_key)
        elif self._address and (not self.public_hash or not self.script_type or not self.encoding):
            address_dict = deserialize_address(self._address, self.encoding, self.network.name)
            if address_dict['script_type'] and not script_type:
                self.script_type = address_dict['script_type']
            if not self.script_type:
                raise TransactionError("Could not determine script type of address %s" % self._address)
            self.encoding = address_dict['encoding']
            network_guesses = address_dict['networks']
            if address_dict['network'] and self.network.name != address_dict['network']:
                raise TransactionError("Address %s is from %s network and transaction from %s network" %
                                       (self._address, address_dict['network'], self.network.name))
            elif self.network.name not in network_guesses:
                raise TransactionError("Network for output address %s is different from transaction network. %s not "
                                       "in %s" % (self._address, self.network.name, network_guesses))
            self.public_hash = address_dict['public_key_hash_bytes']
            self.witness_type = address_dict['witness_type']
        if not self.encoding:
            self.encoding = 'bech32'
            if self.script_type in ['p2pkh', 'p2sh', 'p2pk'] or self.witness_type == 'legacy':
                self.encoding = 'base58'
            else:
                self.witness_type = 'segwit'

        if self.script_type is None:
            self.script_type = 'p2pkh'
            if self.encoding == 'bech32':
                self.script_type = 'p2wpkh'
        if not self.script and strict and (self.public_hash or self.public_key):
            self.script = Script(script_types=[self.script_type], public_hash=self.public_hash, keys=[self.public_key])
            self.lock_script = self.script.serialize()
            if not self.script:
                raise TransactionError("Unknown output script type %s, please provide locking script" %
                                       self.script_type)
        self.spending_txid = spending_txid
        self.spending_index_n = spending_index_n
        # if self.script_type != 'nulldata' and value < self.network.dust_amount:
        #     raise TransactionError("Output to %s must be more than dust amount %d" %
        #                            (self.address, self.network.dust_amount))

    @property
    def address_obj(self):
        """
        Get address object property. Create standard address object if not defined already.

        :return Address:
        """
        if not self._address_obj:
            if self.public_hash:
                self._address_obj = Address(hashed_data=self.public_hash, script_type=self.script_type,
                                            witver=self.witver, encoding=self.encoding, network=self.network)
                self._address = self._address_obj.address
                self.versionbyte = self._address_obj.prefix
        return self._address_obj

    @property
    def address(self):
        if not self._address:
            address_obj = self.address_obj
            if not address_obj:
                return ''
            self._address = address_obj.address
        return self._address

    @classmethod
    def parse(cls, raw, output_n=0, strict=True, network=DEFAULT_NETWORK):
        """
        Parse raw BytesIO string and return Output object

        :param raw: raw output stream
        :type raw: BytesIO
        :param output_n: Output number of Transaction output
        :type output_n: int
        :param strict: Raise exception when output is malformed, incomplete or not understood
        :type strict: bool
        :param network: Network, leave empty for default network
        :type network: str, Network

        :return Output:
        """
        value = int.from_bytes(raw.read(8)[::-1], 'big')
        lock_script_size = read_varbyteint(raw)
        lock_script = raw.read(lock_script_size)
        return Output(value=value, lock_script=lock_script, output_n=output_n, strict=strict, network=network)

    # TODO: Write and rewrite locktime methods
    # def set_locktime - CLTV (BIP65)
    # def set_locktime_blocks
    # def set_locktime_time

    def set_locktime_relative(self, locktime):
        """
        Relative timelocks with CHECKSEQUENCEVERIFY (CSV) as defined in BIP112
        :param locktime:
        :return:
        """
        pass

    def set_locktime_relative_blocks(self, blocks):
        """
        Set nSequence relative locktime for this transaction input. The transaction will only be valid if the specified number of blocks has been mined since the previous UTXO is confirmed.

        Maximum number of blocks is 65535 as defined in BIP-0068, which is around 455 days.

        When setting a relative timelock, the transaction version must be at least 2. The transaction will be updated so existing signatures for this input will be removed.

        :param blocks: The blocks value is the number of blocks since the previous transaction output has been confirmed.
        :type blocks: int

        :return None:
        """
        # if blocks == 0 or blocks == 0xffffffff:
        #     self.sequence = 0xffffffff
        #     return
        # if blocks > SEQUENCE_LOCKTIME_MASK:
        #     raise TransactionError("Number of nSequence timelock blocks exceeds %d" % SEQUENCE_LOCKTIME_MASK)
        # self.sequence = blocks
        # self.signatures = []

    def set_locktime_relative_time(self, seconds):
        """
        Set nSequence relative locktime for this transaction input. The transaction will only be valid if the specified amount of seconds have been passed since the previous UTXO is confirmed.

        Number of seconds will be rounded to the nearest 512 seconds. Any value below 512 will be interpreted as 512 seconds.

        Maximum number of seconds is 33553920 (512 * 65535), which equals 384 days. See BIP-0068 definition.

        When setting a relative timelock, the transaction version must be at least 2. The transaction will be updated so existing signatures for this input will be removed.

        :param seconds: Number of seconds since the related previous transaction output has been confirmed.
        :return:
        """
        # if seconds == 0 or seconds == 0xffffffff:
        #     self.sequence = 0xffffffff
        #     return
        # if seconds < 512:
        #     seconds = 512
        # if (seconds // 512) > SEQUENCE_LOCKTIME_MASK:
        #     raise TransactionError("Number of relative nSeqence timelock seconds exceeds %d" % SEQUENCE_LOCKTIME_MASK)
        # self.sequence = seconds // 512 + SEQUENCE_LOCKTIME_TYPE_FLAG
        # self.signatures = []

    def as_dict(self):
        """
        Get transaction output information in json format

        :return dict: Json with amount, locking script, public key, public key hash and address
        """

        return {
            'value': self.value,
            'script': self.lock_script.hex(),
            'script_type': self.script_type,
            'public_key': self.public_key.hex(),
            'public_hash': self.public_hash.hex(),
            'address': self.address,
            'output_n': self.output_n,
            'spent': self.spent,
            'spending_txid': self.spending_txid,
            'spending_index_n': self.spending_index_n,
        }

    def __repr__(self):
        return "<Output(value=%d, address=%s, type=%s)>" % (self.value, self.address, self.script_type)


class Transaction(object):
    """
    Transaction Class

    Contains 1 or more Input class object with UTXO's to spent and 1 or more Output class objects with destinations.
    Besides the transaction class contains a locktime and version.

    Inputs and outputs can be included when creating the transaction, or can be added later with add_input and
    add_output respectively.

    A verify method is available to check if the transaction Inputs have valid unlocking scripts.

    Each input in the transaction can be signed with the sign method provided a valid private key.
    """

    @classmethod
    def parse(cls, rawtx, strict=True, network=DEFAULT_NETWORK):
        """
        Parse a raw transaction and create a Transaction object

        :param rawtx: Raw transaction string
        :type rawtx: BytesIO, bytes, str
        :param strict: Raise exception when transaction is malformed, incomplete or not understood
        :type strict: bool
        :param network: Network, leave empty for default network
        :type network: str, Network

        :return Transaction:
        """
        raw_bytes = b''
        if isinstance(rawtx, bytes):
            raw_bytes = rawtx
            rawtx = BytesIO(rawtx)
        elif isinstance(rawtx, str):
            raw_bytes = bytes.fromhex(rawtx)
            rawtx = BytesIO(bytes.fromhex(rawtx))

        return cls.parse_bytesio(rawtx, strict, network, raw_bytes=raw_bytes)

    @classmethod
    def parse_bytesio(cls, rawtx, strict=True, network=DEFAULT_NETWORK, index=None, raw_bytes=b''):
        """
        Parse a raw transaction and create a Transaction object

        :param rawtx: Raw transaction bytes stream
        :type rawtx: BytesIO
        :param strict: Raise exception when transaction is malformed, incomplete or not understood
        :type strict: bool
        :param network: Network, leave empty for default network
        :type network: str, Network
        :param index: index position in block
        :type index: int
        :param raw_bytes: Raw transaction as bytes if available
        :param raw_bytes: bytes

        :return Transaction:
        """
        coinbase = False
        flag = None
        witness_type = 'legacy'
        network = network
        if not isinstance(network, Network):
            cls.network = Network(network)

        try:
            pos_start = rawtx.tell()
        except AttributeError:
            raise TransactionError("Provide raw transaction as BytesIO. Use parse, parse_bytes, parse_hex to parse "
                                   "other data types")

        version = rawtx.read(4)[::-1]
        if rawtx.read(1) == b'\0':
            flag = rawtx.read(1)
            if flag == b'\1':
                witness_type = 'segwit'
        else:
            rawtx.seek(-1, 1)

        n_inputs = read_varbyteint(rawtx)
        inputs = []
        for n in range(0, n_inputs):
            inp = Input.parse(rawtx, index_n=n, witness_type=witness_type, strict=strict, network=network)
            if inp.prev_txid == 32 * b'\0':
                coinbase = True
            inputs.append(inp)

        outputs = []
        output_total = 0
        n_outputs = read_varbyteint(rawtx)
        for n in range(0, n_outputs):
            o = Output.parse(rawtx, output_n=n, strict=strict, network=network)
            outputs.append(o)
            output_total += o.value
        if not outputs:
            raise TransactionError("Error no outputs found in this transaction")

        if witness_type == 'segwit':
            for n in range(0, len(inputs)):
                n_items = read_varbyteint(rawtx)
                if not n_items:
                    continue
                script = Script()
                is_taproot = False
                for m in range(0, n_items):
                    item_size = read_varbyteint(rawtx)
                    if item_size == 0:
                        witness = b'\0'
                    else:
                        witness = rawtx.read(item_size)
                    inputs[n].witnesses.append(witness)
                    if not is_taproot:
                        s = Script.parse_bytes(witness, strict=strict, is_locking=False)
                        if s.script_types == ['p2tr_unlock']:
                            # FIXME: Support Taproot unlocking scripts
                            _logger.warning("Taproot is not supported at the moment, rest of parsing input transaction "
                                            "skipped")
                            is_taproot = True
                        script += s

                inputs[n].script = script if not inputs[n].script else inputs[n].script + script
                inputs[n].keys = script.keys
                inputs[n].signatures = script.signatures
                if not script.script_types:
                    inputs[n].script_type = 'unknown'
                elif script.script_types[0][:13] == 'p2sh_multisig' or script.script_types[0] =='signature_multisig':
                    inputs[n].script_type = 'p2sh_multisig'
                    inputs[n].redeemscript = inputs[n].witnesses[-1]
                elif script.script_types[0] == 'p2tr_unlock':
                    inputs[n].script_type = 'p2tr'
                    inputs[n].witness_type = 'segwit'
                elif inputs[n].script_type == 'p2wpkh':
                    inputs[n].script_type = 'p2sh_p2wpkh'
                    inputs[n].witness_type = 'p2sh-segwit'
                elif inputs[n].script_type == 'p2wpkh' or inputs[n].script_type == 'p2wsh':
                    inputs[n].script_type = 'p2sh_p2wsh'
                    inputs[n].witness_type = 'p2sh-segwit'
                elif 'unknown' in script.script_types and not coinbase:
                    inputs[n].script_type = 'unknown'

                inputs[n].update_scripts()

        locktime_bytes = rawtx.read(4)[::-1]
        if len(locktime_bytes) != 4 and strict:
            raise TransactionError("Invalid transaction size, locktime bytes incomplete")

        locktime = int.from_bytes(locktime_bytes, 'big')
        raw_len = len(raw_bytes)
        if not raw_bytes:
            pos_end = rawtx.tell()
            raw_len = pos_end - pos_start
            rawtx.seek(pos_start)
            raw_bytes = rawtx.read(raw_len)

        return Transaction(inputs, outputs, locktime, version, network, size=raw_len, output_total=output_total,
                           coinbase=coinbase, flag=flag, witness_type=witness_type, rawtx=raw_bytes, index=index)

    @classmethod
    def parse_hex(cls, rawtx, strict=True, network=DEFAULT_NETWORK):
        """
        Parse a raw hexadecimal transaction and create a Transaction object. Wrapper for the :func:`parse_bytesio`
        method

        :param rawtx: Raw transaction hexadecimal string
        :type rawtx: str
        :param strict: Raise exception when transaction is malformed, incomplete or not understood
        :type strict: bool
        :param network: Network, leave empty for default network
        :type network: str, Network

        :return Transaction:
        """

        raw_bytes = bytes.fromhex(rawtx)
        return cls.parse_bytesio(BytesIO(raw_bytes), strict, network, raw_bytes=raw_bytes)

    @classmethod
    def parse_bytes(cls, rawtx, strict=True, network=DEFAULT_NETWORK):
        """
        Parse a raw bytes transaction and create a Transaction object.  Wrapper for the :func:`parse_bytesio`
        method

        :param rawtx: Raw transaction hexadecimal string
        :type rawtx: bytes
        :param strict: Raise exception when transaction is malformed, incomplete or not understood
        :type strict: bool
        :param network: Network, leave empty for default network
        :type network: str, Network

        :return Transaction:
        """

        return cls.parse_bytesio(BytesIO(rawtx), strict, network, raw_bytes=rawtx)

    @staticmethod
    def load(txid=None, filename=None):
        """
        Load transaction object from file which has been stored with the :func:`save` method.

        Specify transaction ID or filename.

        :param txid: Transaction ID. Transaction object will be read from .bitcoinlib datadir
        :type txid: str
        :param filename: Name of transaction object file
        :type filename: str

        :return Transaction:
        """
        if not filename and not txid:
            raise TransactionError("Please supply filename or txid")
        elif not filename and txid:
            p = Path(BCL_DATA_DIR, '%s.tx' % txid)
        else:
            p = Path(filename)
            if not p.parent or str(p.parent) == '.':
                p = Path(BCL_DATA_DIR, filename)
        f = p.open('rb')
        t = pickle.load(f)
        f.close()
        return t

    def __init__(self, inputs=None, outputs=None, locktime=0, version=None,
                 network=DEFAULT_NETWORK, fee=None, fee_per_kb=None, size=None, txid='', txhash='', date=None,
                 confirmations=None, block_height=None, block_hash=None, input_total=0, output_total=0, rawtx=b'',
                 status='new', coinbase=False, verified=False, witness_type='segwit', flag=None, replace_by_fee=False,
                 index=None):
        """
        Create a new transaction class with provided inputs and outputs.

        You can also create an empty transaction and add input and outputs later.

        To verify and sign transactions all inputs and outputs need to be included in transaction. Any modification
        after signing makes the transaction invalid.

        :param inputs: Array of Input objects. Leave empty to add later
        :type inputs: list (Input)
        :param outputs: Array of Output object. Leave empty to add later
        :type outputs: list (Output)
        :param locktime: Transaction level locktime. Locks the transaction until a specified block (value from 1 to 5 million) or until a certain time (Timestamp in seconds after 1-jan-1970). Default value is 0 for transactions without locktime
        :type locktime: int
        :param version: Version rules. Defaults to 1 in bytes
        :type version: bytes, int
        :param network: Network, leave empty for default network
        :type network: str, Network
        :param fee: Fee in the smallest denominator (ie Satoshi) for complete transaction
        :type fee: int
        :param fee_per_kb: Fee in the smallest denominator per kilobyte. Specify when exact transaction size is not known.
        :type fee_per_kb: int
        :param size: Transaction size in bytes
        :type size: int
        :param txid: The transaction id (same for legacy/segwit) based on [nVersion][txins][txouts][nLockTime as hexadecimal string
        :type txid: str
        :param txhash: The transaction hash (differs from txid for witness transactions), based on [nVersion][marker][flag][txins][txouts][witness][nLockTime] in Segwit (as hexadecimal string). Unused at the moment
        :type txhash: str
        :param date: Confirmation date of transaction
        :type date: datetime
        :param confirmations: Number of confirmations
        :type confirmations: int
        :param block_height: Block number which includes transaction
        :type block_height: int
        :param block_hash: Hash of block for this transaction
        :type block_hash: str
        :param input_total: Total value of inputs
        :type input_total: int
        :param output_total: Total value of outputs
        :type output_total: int
        :param rawtx: Bytes representation of complete transaction
        :type rawtx: bytes
        :param status: Transaction status, for example: 'new', 'unconfirmed', 'confirmed'
        :type status: str
        :param coinbase: Coinbase transaction or not?
        :type coinbase: bool
        :param verified: Is transaction successfully verified? Updated when verified() method is called
        :type verified: bool
        :param witness_type: Specify witness/signature position: 'segwit' or 'legacy'. Determine from script, address or encoding if not specified.
        :type witness_type: str
        :param flag: Transaction flag to indicate version, for example for SegWit
        :type flag: bytes, str
        :param index: Index of transaction in block. Used when parsing blocks
        :type index: int

        """

        self.coinbase = coinbase
        self.inputs = []
        if inputs is not None:
            for inp in inputs:
                self.inputs.append(inp)
            if not input_total:
                input_total = sum([i.value for i in inputs])
        id_list = [i.index_n for i in self.inputs]
        if list(dict.fromkeys(id_list)) != id_list:
            _logger.info("Identical transaction indexes (tid) found in inputs, please specify unique index. "
                         "Indexes will be automatically recreated")
            index_n = 0
            for inp in self.inputs:
                inp.index_n = index_n
                index_n += 1
        if outputs is None:
            self.outputs = []
        else:
            self.outputs = outputs
            if not output_total:
                output_total = sum([o.value for o in outputs])
        if fee is None and output_total and input_total:
            fee = input_total - output_total
            if fee < 0 or fee == 0 and not self.coinbase:
                raise TransactionError("Transaction inputs total value must be greater then total value of "
                                       "transaction outputs")
        if not version:
            version = b'\x00\x00\x00\x01'
        if isinstance(version, int):
            self.version = version.to_bytes(4, 'big')
            self.version_int = version
        else:
            self.version = version
            self.version_int = int.from_bytes(version, 'big')
        self.locktime = locktime
        self.network = network
        if not isinstance(network, Network):
            self.network = Network(network)
        self.flag = flag
        self.fee = fee
        self.fee_per_kb = fee_per_kb
        self.size = size
        self.vsize = size
        self.txid = txid
        self.txhash = txhash
        self.date = date
        self.confirmations = confirmations
        self.block_height = block_height
        self.block_hash = block_hash
        self.input_total = input_total
        self.output_total = output_total
        self.rawtx = rawtx
        self.status = status
        self.verified = verified
        self.witness_type = witness_type
        self.replace_by_fee = replace_by_fee
        self.change = 0
        self.index = index
        self.calc_weight_units()
        if self.witness_type not in ['legacy', 'segwit']:
            raise TransactionError("Please specify a valid witness type: legacy or segwit")
        if not self.txid:
            self.txid = self.signature_hash()[::-1].hex()

    def __repr__(self):
        return "<Transaction(id=%s, inputs=%d, outputs=%d, status=%s, network=%s)>" % \
               (self.txid, len(self.inputs), len(self.outputs), self.status, self.network.name)

    def __str__(self):
        return self.txid

    def __add__(self, other):
        """
        Merge this transaction with another transaction keeping the original transaction intact.

        :return Transaction:
        """
        t = deepcopy(self)
        t.merge_transaction(other)
        return t

    def __hash__(self):
        return self.txid

    def __eq__(self, other):
        """
        Compare two transaction, must have same transaction ID

        :param other: Other transaction object
        :type other: Transaction

        :return bool:
        """
        if not isinstance(other, Transaction):
            raise TransactionError("Can only compare with other Transaction object")
        return self.txid == other.txid

    def as_dict(self):
        """
        Return Json dictionary with transaction information: Inputs, outputs, version and locktime

        :return dict:
        """

        inputs = []
        outputs = []
        for i in self.inputs:
            inputs.append(i.as_dict())
        for o in self.outputs:
            outputs.append(o.as_dict())
        return {
            'txid': self.txid,
            'date': self.date,
            'network': self.network.name,
            'witness_type': self.witness_type,
            'coinbase': self.coinbase,
            'flag': None if not self.flag else ord(self.flag),
            'txhash': self.txhash,
            'confirmations': self.confirmations,
            'block_height': self.block_height,
            'block_hash': self.block_hash,
            'fee': self.fee,
            'fee_per_kb': self.fee_per_kb,
            'inputs': inputs,
            'outputs': outputs,
            'input_total': self.input_total,
            'output_total': self.output_total,
            'version': self.version_int,
            'locktime': self.locktime,
            'raw': self.raw_hex(),
            'size': self.size,
            'vsize': self.vsize,
            'verified': self.verified,
            'status': self.status
        }

    def as_json(self):
        """
        Get current transaction as json formatted string

        :return str:
        """
        adict = self.as_dict()
        return json.dumps(adict, indent=4, default=str)

    def as_bytes(self):
        """
        Return raw serialized transaction as bytes string

        :return bytes:
        """
        return self.raw()

    def as_hex(self):
        """
        Return raw hex string of transaction as hex string

        :return:
        """
        return self.raw_hex()

    def info(self):
        """
        Prints transaction information to standard output
        """

        print("Transaction %s" % self.txid)
        print("Date: %s" % self.date)
        print("Network: %s" % self.network.name)
        if self.locktime and self.locktime != 0xffffffff:
            if self.locktime < 500000000:
                print("Locktime: Until block %d" % self.locktime)
            else:
                print("Locktime: Until %s UTC" % datetime.fromtimestamp(self.locktime, timezone.utc))
        print("Version: %d" % self.version_int)
        print("Witness type: %s" % self.witness_type)
        print("Status: %s" % self.status)
        print("Verified: %s" % self.verified)
        print("Inputs")
        replace_by_fee = False
        for ti in self.inputs:
            print("-", ti.address, Value.from_satoshi(ti.value, network=self.network).str(1), ti.prev_txid.hex(),
                  ti.output_n_int)
            validstr = "not validated"
            if ti.valid:
                validstr = "valid"
            elif ti.valid is False:
                validstr = "invalid"
            print("  %s %s; sigs: %d (%d-of-%d) %s" %
                  (ti.witness_type, ti.script_type, len(ti.signatures), ti.sigs_required or 0, len(ti.keys), validstr))
            if ti.sequence <= SEQUENCE_REPLACE_BY_FEE:
                replace_by_fee = True
            if ti.sequence <= SEQUENCE_LOCKTIME_DISABLE_FLAG:
                if ti.sequence & SEQUENCE_LOCKTIME_TYPE_FLAG:
                    print("  Relative timelock for %d seconds" % (512 * (ti.sequence - SEQUENCE_LOCKTIME_TYPE_FLAG)))
                else:
                    print("  Relative timelock for %d blocks" % ti.sequence)
            # if ti.locktime_cltv:
            #     if ti.locktime_cltv & SEQUENCE_LOCKTIME_TYPE_FLAG:
            #         print("  Check Locktime Verify (CLTV) for %d seconds" %
            #               (512 * (ti.locktime_cltv - SEQUENCE_LOCKTIME_TYPE_FLAG)))
            #     else:
            #         print("  Check Locktime Verify (CLTV) for %d blocks" % ti.locktime_cltv)
            if ti.locktime_csv:
                if ti.locktime_csv & SEQUENCE_LOCKTIME_TYPE_FLAG:
                    print("  Check Sequence Verify Timelock (CSV) for %d seconds" %
                          (512 * (ti.locktime_csv - SEQUENCE_LOCKTIME_TYPE_FLAG)))
                else:
                    print("  Check Sequence Verify Timelock (CSV) for %d blocks" % ti.locktime_csv)

        print("Outputs")
        for to in self.outputs:
            if to.script_type == 'nulldata':
                print("- NULLDATA ", to.lock_script[2:])
            else:
                spent_str = ''
                if to.spent:
                    spent_str = 'S'
                elif to.spent is False:
                    spent_str = 'U'
                if to.change:
                    spent_str += 'C'
                print("-", to.address, Value.from_satoshi(to.value, network=self.network).str(1), to.script_type,
                      spent_str)
        if replace_by_fee:
            print("Replace by fee: Enabled")
        print("Size: %s" % self.size)
        print("Vsize: %s" % self.vsize)
        print("Fee: %s" % self.fee)
        print("Confirmations: %s" % self.confirmations)
        print("Block: %s" % self.block_height)

    def set_locktime_relative_blocks(self, blocks, input_index_n=0, locktime=0):
        """
        Set nSequence relative locktime for this transaction. The transaction will only be valid if the specified number of blocks has been mined since the previous UTXO is confirmed.

        Maximum number of blocks is 65535 as defined in BIP-0068, which is around 455 days.

        When setting a relative timelock, the transaction version must be at least 2. The transaction will be updated so existing signatures for this input will be removed.

        :param blocks: The blocks value is the number of blocks since the previous transaction output has been confirmed.
        :type blocks: int
        :param input_index_n: Index number of input for nSequence locktime
        :type input_index_n: int
        :param locktime: Overwrite default locktime, must be lower than current network blockcount. If anti-fee-sniping is used in a Wallet this value is already filled in.
        :type locktime: int

        :return:
        """
        if blocks == 0 or blocks == 0xffffffff:
            self.inputs[input_index_n].sequence = 0xffffffff
            self.sign(index_n=input_index_n, replace_signatures=True)
            return
        if blocks > SEQUENCE_LOCKTIME_MASK:
            raise TransactionError("Number of nSequence timelock blocks exceeds %d" % SEQUENCE_LOCKTIME_MASK)
        self.inputs[input_index_n].sequence = blocks
        self.version_int = 2 if self.version_int < 2 else self.version_int
        self.locktime = locktime if locktime else self.locktime
        self.sign_and_update(index_n=input_index_n)

    def set_locktime_relative_time(self, seconds, input_index_n=0, locktime=0):
        """
        Set nSequence relative locktime for this transaction. The transaction will only be valid if the specified amount of seconds have been passed since the previous UTXO is confirmed.

        Number of seconds will be rounded to the nearest 512 seconds. Any value below 512 will be interpreted as 512 seconds.

        Maximum number of seconds is 33553920 (512 * 65535), which equals 384 days. See BIP-0068 definition.

        When setting a relative timelock, the transaction version must be at least 2. The transaction will be updated so existing signatures for this input will be removed.

        :param seconds: Number of seconds since the related previous transaction output has been confirmed.
        :type seconds: int
        :param input_index_n: Index number of input for nSequence locktime
        :type input_index_n: int
        :param locktime: Overwrite default locktime, must be lower than current network blockcount. If anti-fee-sniping is used in a Wallet this value is already filled in.
        :type locktime: int

        :return:
        """
        if seconds == 0 or seconds == 0xffffffff:
            self.inputs[input_index_n].sequence = 0xffffffff
            self.sign(index_n=input_index_n, replace_signatures=True)
            return
        elif seconds < 512:
            seconds = 512
        elif (seconds // 512) > SEQUENCE_LOCKTIME_MASK:
            raise TransactionError("Number of relative nSeqence timelock seconds exceeds %d" % SEQUENCE_LOCKTIME_MASK)
        self.inputs[input_index_n].sequence = seconds // 512 + SEQUENCE_LOCKTIME_TYPE_FLAG
        self.version_int = 2 if self.version_int < 2 else self.version_int
        self.locktime = locktime if locktime else self.locktime
        self.sign_and_update(index_n=input_index_n)

    def set_locktime_blocks(self, blocks):
        """
        Set nLocktime, a transaction level absolute lock time in blocks using the transaction sequence field.

        So for example if you set this value to 600000 the transaction will only be valid after block 600000.

        You can also pass the locktime value directly to a Transaction object, or when sending from a wallet.

        :param blocks: Transaction is valid after supplied block number. Value must be between 0 and 500000000. Zero means no locktime.
        :type blocks: int

        :return:
        """
        if blocks == 0 or blocks == 0xffffffff:
            self.locktime = 0xffffffff
            self.sign(replace_signatures=True)
            self.verify()
            return
        elif blocks > 500000000:
            raise TransactionError("Number of locktime blocks must be below %d" % 500000000)
        self.locktime = blocks
        if blocks != 0 and blocks != 0xffffffff:
            for i in self.inputs:
                if i.sequence == 0xffffffff:
                    i.sequence = SEQUENCE_ENABLE_LOCKTIME
        self.sign_and_update()

    def set_locktime_time(self, timestamp):
        """
        Set nLocktime, a transaction level absolute lock time in timestamp using the transaction sequence field.

        You can also pass the locktime value directly to a Transaction object, or when sending from a wallet.

        :param timestamp: Transaction is valid after the given timestamp. Value must be between 500000000 and 0xfffffffe
        :return:
        """
        if timestamp == 0 or timestamp == 0xffffffff:
            self.locktime = 0xffffffff
            self.sign(replace_signatures=True)
            self.verify()
            return

        if timestamp <= 500000000:
            raise TransactionError("Timestamp must have a value higher then %d" % 500000000)
        if timestamp > 0xfffffffe:
            raise TransactionError("Timestamp must have a value lower then %d" % 0xfffffffe)
        self.locktime = timestamp

        # Input sequence value must be below 0xffffffff
        for i in self.inputs:
            if i.sequence == 0xffffffff:
                i.sequence = SEQUENCE_ENABLE_LOCKTIME
        self.sign_and_update()

    def signature_hash(self, sign_id=None, hash_type=SIGHASH_ALL, witness_type=None, as_hex=False):
        """
        Double SHA256 Hash of Transaction signature

        :param sign_id: Index of input to sign
        :type sign_id: int
        :param hash_type: Specific hash type, default is SIGHASH_ALL
        :type hash_type: int
        :param witness_type: Legacy or Segwit witness type? Leave empty to use Transaction witness type
        :type witness_type: str
        :param as_hex: Return value as hexadecimal string. Default is False
        :type as_hex: bool

        :return bytes: Transaction signature hash
        """
        return double_sha256(self.signature(sign_id, hash_type, witness_type), as_hex=as_hex)

    def signature(self, sign_id=None, hash_type=SIGHASH_ALL, witness_type=None):
        """
        Serializes transaction and calculates signature for Legacy or Segwit transactions

        :param sign_id: Index of input to sign
        :type sign_id: int
        :param hash_type: Specific hash type, default is SIGHASH_ALL
        :type hash_type: int
        :param witness_type: Legacy or Segwit witness type? Leave empty to use Transaction witness type
        :type witness_type: str

        :return bytes: Transaction signature
        """

        if witness_type is None:
            witness_type = self.witness_type
        if witness_type == 'legacy' or sign_id is None:
            return self.raw(sign_id, hash_type, 'legacy')
        elif witness_type in ['segwit', 'p2sh-segwit']:
            return self.signature_segwit(sign_id, hash_type)
        else:
            raise TransactionError("Witness_type %s not supported" % self.witness_type)

    def signature_segwit(self, sign_id, hash_type=SIGHASH_ALL):
        """
        Serialize transaction signature for segregated witness transaction

        :param sign_id: Index of input to sign
        :type sign_id: int
        :param hash_type: Specific hash type, default is SIGHASH_ALL
        :type hash_type: int

        :return bytes: Segwit transaction signature
        """
        assert (self.witness_type == 'segwit')
        prevouts_serialized = b''
        sequence_serialized = b''
        outputs_serialized = b''
        hash_prevouts = b'\0' * 32
        hash_sequence = b'\0' * 32
        hash_outputs = b'\0' * 32

        for i in self.inputs:
            prevouts_serialized += i.prev_txid[::-1] + i.output_n[::-1]
            sequence_serialized += i.sequence.to_bytes(4, 'little')
        if not hash_type & SIGHASH_ANYONECANPAY:
            hash_prevouts = double_sha256(prevouts_serialized)
            if (hash_type & 0x1f) != SIGHASH_SINGLE and (hash_type & 0x1f) != SIGHASH_NONE:
                hash_sequence = double_sha256(sequence_serialized)
        if (hash_type & 0x1f) != SIGHASH_SINGLE and (hash_type & 0x1f) != SIGHASH_NONE:
            for o in self.outputs:
                outputs_serialized += int(o.value).to_bytes(8, 'little')
                outputs_serialized += varstr(o.lock_script)
            hash_outputs = double_sha256(outputs_serialized)
        elif (hash_type & 0x1f) != SIGHASH_SINGLE and sign_id < len(self.outputs):
            outputs_serialized += int(self.outputs[sign_id].value).to_bytes(8, 'little')
            outputs_serialized += varstr(self.outputs[sign_id].lock_script)
            hash_outputs = double_sha256(outputs_serialized)

        is_coinbase = self.inputs[sign_id].script_type == 'coinbase'
        if not self.inputs[sign_id].value and not is_coinbase:
            raise TransactionError("Need value of input %d to create transaction signature, value can not be 0" %
                                   sign_id)

        if not self.inputs[sign_id].redeemscript:
            self.inputs[sign_id].redeemscript = self.inputs[sign_id].locking_script

        if (not self.inputs[sign_id].redeemscript or self.inputs[sign_id].redeemscript == b'\0') and \
                self.inputs[sign_id].redeemscript != 'unknown' and not is_coinbase:
            raise TransactionError("Redeem script missing")

        ser_tx = \
            self.version[::-1] + hash_prevouts + hash_sequence + self.inputs[sign_id].prev_txid[::-1] + \
            self.inputs[sign_id].output_n[::-1] + \
            varstr(self.inputs[sign_id].redeemscript) + int(self.inputs[sign_id].value).to_bytes(8, 'little') + \
            self.inputs[sign_id].sequence.to_bytes(4, 'little') + \
            hash_outputs + self.locktime.to_bytes(4, 'little') + hash_type.to_bytes(4, 'little')
        return ser_tx

    def raw(self, sign_id=None, hash_type=SIGHASH_ALL, witness_type=None):
        """
        Serialize raw transaction

        Return transaction with signed inputs if signatures are available

        :param sign_id: Create raw transaction which can be signed by transaction with this input ID
        :type sign_id: int, None
        :param hash_type: Specific hash type, default is SIGHASH_ALL
        :type hash_type: int
        :param witness_type: Serialize transaction with other witness type then default. Use to create legacy raw transaction for segwit transaction to create transaction signature ID's
        :type witness_type: str

        :return bytes:
        """

        if witness_type is None:
            witness_type = self.witness_type

        r = self.version[::-1]
        if sign_id is None and witness_type == 'segwit':
            r += b'\x00'  # marker (BIP 141)
            r += b'\x01'  # flag (BIP 141)

        r += int_to_varbyteint(len(self.inputs))
        r_witness = b''
        for i in self.inputs:
            r += i.prev_txid[::-1] + i.output_n[::-1]
            if i.witnesses and i.witness_type != 'legacy':
                r_witness += int_to_varbyteint(len(i.witnesses)) + b''.join([bytes(varstr(w)) for w in i.witnesses])
            else:
                r_witness += b'\0'
            if sign_id is None:
                if i.script_type == 'nonstandard_0001':
                    r += b'\1'
                r += varstr(i.unlocking_script)
            elif sign_id == i.index_n:
                if i.script_type == 'p2sh_multisig':
                    r += varstr(i.redeemscript)
                else:
                    r += varstr(i.locking_script)
            else:
                r += b'\0'
            r += i.sequence.to_bytes(4, 'little')

        r += int_to_varbyteint(len(self.outputs))
        for o in self.outputs:
            if o.value < 0:
                raise TransactionError("Output value < 0 not allowed")
            r += int(o.value).to_bytes(8, 'little')
            r += varstr(o.lock_script)

        if sign_id is None and witness_type == 'segwit':
            r += r_witness

        r += self.locktime.to_bytes(4, 'little')
        if sign_id is not None:
            r += hash_type.to_bytes(4, 'little')
        else:
            if not self.size and b'' not in [i.unlocking_script for i in self.inputs]:
                self.size = len(r)
                self.calc_weight_units()
        return r

    def raw_hex(self, sign_id=None, hash_type=SIGHASH_ALL, witness_type=None):
        """
        Wrapper for raw() method. Return current raw transaction hex

        :param sign_id: Create raw transaction which can be signed by transaction with this input ID
        :type sign_id: int
        :param hash_type: Specific hash type, default is SIGHASH_ALL
        :type hash_type: int
        :param witness_type: Serialize transaction with other witness type then default. Use to create legacy raw transaction for segwit transaction to create transaction signature ID's
        :type witness_type: str

        :return hexstring:
        """

        return self.raw(sign_id, hash_type=hash_type, witness_type=witness_type).hex()

    def witness_data(self):
        """
        Get witness data for all inputs of this transaction

        :return bytes:
        """
        witness_data = b''
        for i in self.inputs:
            witness_data += int_to_varbyteint(len(i.witnesses)) + b''.join([bytes(varstr(w)) for w in i.witnesses])
        return witness_data

    def verify(self):
        """
        Verify all inputs of a transaction, check if signatures match public key.

        Does not check if UTXO is valid or has already been spent

        :return bool: True if enough signatures provided and if all signatures are valid
        """

        self.verified = False
        for inp in self.inputs:
            try:
                transaction_hash = self.signature_hash(inp.index_n, inp.hash_type, inp.witness_type)
            except TransactionError as e:
                _logger.info("Could not create transaction hash. Error: %s" % e)
                return False
            if not transaction_hash:
                _logger.info("Need at least 1 key to create segwit transaction signature")
                return False
            self.verified = inp.verify(transaction_hash)
            if not self.verified:
                return False

        self.verified = True
        return True

    def sign(self, keys=None, index_n=None, multisig_key_n=None, hash_type=SIGHASH_ALL, fail_on_unknown_key=True,
             replace_signatures=False):
        """
        Sign the transaction input with provided private key

        :param keys: A private key or list of private keys
        :type keys: HDKey, Key, bytes, list
        :param index_n: Index of transaction input. Leave empty to sign all inputs
        :type index_n: int
        :param multisig_key_n: Index number of key for multisig input for segwit transactions. Leave empty if not known. If not specified all possibilities will be checked
        :type multisig_key_n: int
        :param hash_type: Specific hash type, default is SIGHASH_ALL
        :type hash_type: int
        :param fail_on_unknown_key: Method fails if public key from signature is not found in public key list
        :type fail_on_unknown_key: bool
        :param replace_signatures: Replace signature with new one if already signed.
        :type replace_signatures: bool

        :return None:
        """

        if hash_type != SIGHASH_ALL:
            raise TransactionError("Hash type othen than SIGHASH_ALL are not supported at the moment")

        if index_n is None:
            tids = range(len(self.inputs))
        else:
            tids = [index_n]

        if keys is None:
            keys = []
        elif not isinstance(keys, list):
            keys = [keys]

        for tid in tids:
            n_signs = 0
            tid_keys = [k if isinstance(k, (HDKey, Key)) else Key(k, compressed=self.inputs[tid].compressed)
                        for k in keys]
            for k in self.inputs[tid].keys:
                if k.is_private and k not in tid_keys:
                    tid_keys.append(k)
            # If input does not contain any keys, try using provided keys
            if not self.inputs[tid].keys:
                self.inputs[tid].keys = tid_keys
                self.inputs[tid].update_scripts(hash_type=hash_type)
            if self.inputs[tid].script_type == 'coinbase':
                raise TransactionError("Can not sign coinbase transactions")
            pub_key_list = [k.public_byte for k in self.inputs[tid].keys]
            n_total_sigs = len(self.inputs[tid].keys)
            sig_domain = [''] * n_total_sigs

            txid = self.signature_hash(tid, hash_type, self.inputs[tid].witness_type)
            for key in tid_keys:
                # Check if signature signs known key and is not already in list
                if key.public_byte not in pub_key_list:
                    if fail_on_unknown_key:
                        raise TransactionError("This key does not sign any known key: %s" % key.public_hex)
                    else:
                        _logger.info("This key does not sign any known key: %s" % key.public_hex)
                        continue
                if not replace_signatures and key in [x.public_key for x in self.inputs[tid].signatures]:
                    _logger.info("Key %s already signed" % key.public_hex)
                    break

                if not key.private_byte:
                    raise TransactionError("Please provide a valid private key to sign the transaction")
                sig = sign(txid, key, hash_type=hash_type)
                newsig_pos = pub_key_list.index(key.public_byte)
                sig_domain[newsig_pos] = sig
                n_signs += 1

            if not n_signs:
                break

            # Add already known signatures on correct position
            n_sigs_to_insert = len(self.inputs[tid].signatures)
            for sig in self.inputs[tid].signatures:
                if not sig.public_key:
                    break
                newsig_pos = pub_key_list.index(sig.public_key.public_byte)
                if sig_domain[newsig_pos] == '':
                    sig_domain[newsig_pos] = sig
                    n_sigs_to_insert -= 1
            if n_sigs_to_insert:
                for sig in self.inputs[tid].signatures:
                    free_positions = [i for i, s in enumerate(sig_domain) if s == '']
                    for pos in free_positions:
                        sig_domain[pos] = sig
                        n_sigs_to_insert -= 1
                        break
            if n_sigs_to_insert:
                _logger.info("Some signatures are replaced with the signatures of the provided keys")
            self.inputs[tid].signatures = [s for s in sig_domain if s != '']
            self.inputs[tid].update_scripts(hash_type)

    def sign_and_update(self, index_n=None):
        """
        Update transaction ID and resign. Use if some properties of the transaction changed

        :param index_n: Index of transaction input. Leave empty to sign all inputs
        :type index_n: int

        :return:
        """

        self.version = self.version_int.to_bytes(4, 'big')
        self.sign(index_n=index_n, replace_signatures=True)
        self.txid = self.signature_hash()[::-1].hex()
        self.size = len(self.raw())
        self.calc_weight_units()
        self.update_totals()
        if self.fee:
            self.fee_per_kb = int((self.fee / float(self.vsize)) * 1000)

    def add_input(self, prev_txid, output_n, keys=None, signatures=None, public_hash=b'', unlocking_script=b'',
                  locking_script=None, script_type=None, address='',
                  sequence=0xffffffff, compressed=True, sigs_required=None, sort=False, index_n=None,
                  value=None, double_spend=False,locktime_cltv=None, locktime_csv=None,
                  key_path='', witness_type=None, witnesses=None, encoding=None, strict=True):
        """
        Add input to this transaction

        Wrapper for append method of Input class.

        :param prev_txid: Transaction hash of the UTXO (previous output) which will be spent.
        :type prev_txid: bytes, hexstring
        :param output_n: Output number in previous transaction.
        :type output_n: bytes, int
        :param keys: Public keys can be provided to construct an Unlocking script. Optional
        :type keys: list (bytes, str, Key, HDKey)
        :param signatures: Add signatures to input if already known
        :type signatures: bytes, str
        :param public_hash: Specify public hash from key or redeemscript if key is not available
        :type public_hash: bytes
        :param unlocking_script: Unlocking script (scriptSig) to prove ownership. Optional
        :type unlocking_script: bytes, hexstring
        :param locking_script: Locking script (scriptPubKey) of previous output if known
        :type locking_script: bytes, hexstring
        :param script_type: Type of unlocking script used, i.e. p2pkh or p2sh_multisig. Default is p2pkh
        :type script_type: str
        :param address: Specify address of input if known, default is to derive from key or scripts
        :type address: str, Address
        :param sequence: Sequence part of input, used for timelocked transactions
        :type sequence: int, bytes
        :param compressed: Use compressed or uncompressed public keys. Default is compressed
        :type compressed: bool
        :param sigs_required: Number of signatures required for a p2sh_multisig unlocking script
        :param sigs_required: int
        :param sort: Sort public keys according to BIP0045 standard. Default is False to avoid unexpected change of key order.
        :type sort: boolean
        :param index_n: Index number of position in transaction, leave empty to add input to end of inputs list
        :type index_n: int
        :param value: Value of input
        :type value: int
        :param double_spend: True if double spend is detected, depends on which service provider is selected
        :type double_spend: bool
        :param locktime_cltv: Check Locktime Verify value.
        :type locktime_cltv: int
        :param locktime_csv: Check Sequency Verify value.
        :type locktime_csv: int
        :param key_path: Key path of input key as BIP32 string or list
        :type key_path: str, list
        :param witness_type: Specify witness/signature position: 'segwit' or 'legacy'. Determine from script, address or encoding if not specified.
        :type witness_type: str
        :param witnesses: List of witnesses for inputs, used for segwit transactions for instance.
        :type witnesses: list of bytes, list of str
        :param encoding: Address encoding used. For example bech32/base32 or base58. Leave empty to derive from script or script type
        :type encoding: str
        :param strict: Raise exception when input is malformed or incomplete
        :type strict: bool

        :return int: Transaction index number (index_n)
        """

        if index_n is None:
            index_n = len(self.inputs)
        if self.replace_by_fee and sequence == 0xffffffff:
            sequence = SEQUENCE_REPLACE_BY_FEE
        sequence_int = sequence
        if isinstance(sequence, bytes):
            sequence_int = int.from_bytes(sequence, 'little')
        if self.version == b'\x00\x00\x00\x01' and 0 < sequence_int < SEQUENCE_LOCKTIME_DISABLE_FLAG:
            self.version = b'\x00\x00\x00\x02'
            self.version_int = 2
        self.inputs.append(
            Input(prev_txid=prev_txid, output_n=output_n, keys=keys, signatures=signatures, public_hash=public_hash,
                  unlocking_script=unlocking_script, locking_script=locking_script,
                  script_type=script_type, address=address, sequence=sequence, compressed=compressed,
                  sigs_required=sigs_required, sort=sort, index_n=index_n, value=value, double_spend=double_spend,
                  locktime_cltv=locktime_cltv, locktime_csv=locktime_csv, key_path=key_path, witness_type=witness_type,
                  witnesses=witnesses, encoding=encoding, strict=strict, network=self.network.name))
        return index_n

    def add_output(self, value, address='', public_hash=b'', public_key=b'', lock_script=b'', spent=False,
                   output_n=None, encoding=None, spending_txid=None, spending_index_n=None, strict=True,
                   change=None):
        """
        Add an output to this transaction

        Wrapper for the append method of the Output class.

        :param value: Value of output in the smallest denominator of currency, for example satoshi's for bitcoins
        :type value: int
        :param address: Destination address of output. Leave empty to derive from other attributes you provide.
        :type address: str, Address
        :param public_hash: Hash of public key or script
        :type public_hash: bytes, str
        :param public_key: Destination public key
        :type public_key: bytes, str
        :param lock_script: Locking script of output. If not provided a default unlocking script will be provided with a public key hash.
        :type lock_script: bytes, str
        :param spent: Has output been spent in new transaction?
        :type spent: bool, None
        :param output_n: Index number of output in transaction
        :type output_n: int
        :param encoding: Address encoding used. For example bech32/base32 or base58. Leave empty for to derive from script or script type
        :type encoding: str
        :param spending_txid: Transaction hash of input spending this transaction output
        :type spending_txid: str
        :param spending_index_n: Index number of input spending this transaction output
        :type spending_index_n: int
        :param strict: Raise exception when output is malformed or incomplete
        :type strict: bool
        :param change: Is this a change output back to own wallet or not? Used for replace-by-fee.
        :type change: bool

        :return int: Transaction output number (output_n)
        """

        lock_script = to_bytes(lock_script)
        if output_n is None:
            output_n = len(self.outputs)
        if not float(value).is_integer():
            raise TransactionError("Output must be of type integer and contain no decimals")
        if lock_script.startswith(b'\x6a'):
            if value != 0:
                raise TransactionError("Output value for OP_RETURN script must be 0")
        self.outputs.append(Output(value=int(value), address=address, public_hash=public_hash,
                                   public_key=public_key, lock_script=lock_script, spent=spent, output_n=output_n,
                                   encoding=encoding, spending_txid=spending_txid, spending_index_n=spending_index_n,
                                   strict=strict, change=change, network=self.network.name))
        return output_n

    def merge_transaction(self, transaction):
        """
        Merge this transaction with provided Transaction object.

        Add all inputs and outputs of a transaction to this Transaction object. Because the transaction signature
        changes with this operation, the transaction inputs need to be signed again.

        Can be used to implement CoinJoin. Where two or more unrelated Transactions are merged into 1 transaction
        to safe fees and increase privacy.

        :param transaction: The transaction to be merged
        :type transaction: Transaction

        """
        self.inputs += transaction.inputs
        self.outputs += transaction.outputs
        self.shuffle()
        self.update_totals()
        self.sign_and_update()

    def estimate_size(self, number_of_change_outputs=0):
        """
        Get estimated vsize in for current transaction based on transaction type and number of inputs and outputs.

        For old-style legacy transaction the vsize is the length of the transaction. In segwit transaction the
        witness data has less weight. The formula used is: math.ceil(((est_size-witness_size) * 3 + est_size) / 4)

        :param number_of_change_outputs: Number of change outputs, default is 0
        :type number_of_change_outputs: int

        :return int: Estimated transaction size
        """

        # if self.input_total and self.output_total + self.fee == self.input_total:
        #     add_change_output = False
        est_size = 12
        witness_size = 2
        if self.witness_type != 'legacy':
            est_size += 2
        # If no inputs assume 1 input
        if not self.inputs:
            est_size += 125
            witness_size += 72
        for inp in self.inputs:
            est_size += 40
            scr_size = 0
            if inp.witness_type != 'legacy':
                est_size += 1
            if inp.unlocking_script and len(inp.signatures) >= inp.sigs_required:
                scr_size += len(varstr(inp.unlocking_script))
                if inp.witness_type == 'p2sh-segwit':
                    scr_size += sum([1 + len(w) for w in inp.witnesses])
            else:
                if inp.script_type == 'sig_pubkey':
                    scr_size += 107
                    if not inp.compressed:
                        scr_size += 33
                    if inp.witness_type == 'p2sh-segwit':
                        scr_size += 24
                # elif inp.script_type in ['p2sh_multisig', 'p2sh_p2wpkh', 'p2sh_p2wsh']:
                elif inp.script_type == 'p2sh_multisig':
                    scr_size += 9 + (len(inp.keys) * 34) + (inp.sigs_required * 72)
                    if inp.witness_type == 'p2sh-segwit':
                        scr_size += 17 * inp.sigs_required
                elif inp.script_type == 'signature':
                    scr_size += 9 + 72
                else:
                    raise TransactionError("Unknown input script type %s cannot estimate transaction size" %
                                           inp.script_type)
            est_size += scr_size
            witness_size += scr_size
        for outp in self.outputs:
            est_size += 8
            if outp.lock_script:
                est_size += len(varstr(outp.lock_script))
            else:
                raise TransactionError("Need locking script for output %d to estimate size" % outp.output_n)
        if number_of_change_outputs:
            is_multisig = True if self.inputs and self.inputs[0].script_type == 'p2sh_multisig' else False
            co_size = 8
            if not self.inputs or self.inputs[0].witness_type == 'legacy':
                co_size += 24 if is_multisig else 26
            elif self.inputs[0].witness_type == 'p2sh-segwit':
                co_size += 24
            else:
                co_size += 33 if is_multisig else 23
            est_size += (number_of_change_outputs * co_size)
        self.size = est_size
        self.vsize = est_size
        if self.witness_type == 'legacy':
            return est_size
        else:
            self.vsize = math.ceil((((est_size - witness_size) * 3 + est_size) / 4) - 1.5)
            return self.vsize

    def calc_weight_units(self):
        """
        Calculate weight units and vsize for this Transaction. Weight units are used to determine fee.

        :return int:
        """
        if not self.size:
            return None
        witness_data_size = len(self.witness_data())
        wu = self.size * 4
        if self.witness_type == 'segwit' and witness_data_size > 1:
            wu = wu - 6  # for segwit marker and flag
            wu = wu - witness_data_size * 3
        self.vsize = math.ceil(wu / 4)
        return wu

    @property
    def weight_units(self):
        return self.calc_weight_units()

    def calculate_fee(self):
        """
        Get fee for this transaction in the smallest denominator (i.e. Satoshi) based on its size and the
        transaction.fee_per_kb value

        :return int: Estimated transaction fee
        """

        if not self.fee_per_kb:
            raise TransactionError("Cannot calculate transaction fees: transaction.fee_per_kb is not set")
        if self.fee_per_kb < self.network.fee_min:
            self.fee_per_kb = self.network.fee_min
        elif self.fee_per_kb > self.network.fee_max:
            self.fee_per_kb = self.network.fee_max
        if not self.vsize:
            self.estimate_size()
        fee = int(self.vsize / 1000.0 * self.fee_per_kb)
        return fee

    def update_totals(self):
        """
        Update input_total, output_total and fee according to inputs and outputs of this transaction

        :return int:
        """

        self.input_total = sum([i.value for i in self.inputs if i.value])
        self.output_total = sum([o.value for o in self.outputs if o.value])
        if self.coinbase:
            self.input_total = self.output_total
        # self.fee = 0
        if self.input_total:
            self.fee = self.input_total - self.output_total
            if self.vsize:
                self.fee_per_kb = int((self.fee / float(self.vsize)) * 1000)

    def update_inputs(self, input_n=None):
        """
        Update input scripts to reflect changes you made to one of more inputs. All inputs will be updated unless
        you specificy a specific input.

        :param input_n: Input to update, leave empty to update all input scripts

        :return:
        """
        input_list = range(0, len(self.inputs)) if input_n is None else [input_n]
        for inp in input_list:
            self.inputs[inp].update_scripts()

    def save(self, filename=None):
        """
        Store transaction object as file, so it can be imported in bitcoinlib later with the :func:`load` method.

        :param filename: Location and name of file, leave empty to store transaction in bitcoinlib data directory: .bitcoinlib/<transaction_id.tx)
        :type filename: str

        :return:
        """
        if not filename:
            p = Path(BCL_DATA_DIR, '%s.tx' % self.txid)
        else:
            p = Path(filename)
            if not p.parent or str(p.parent) == '.':
                p = Path(BCL_DATA_DIR, filename)
        f = p.open('wb')
        pickle.dump(self, f)
        f.close()

    def shuffle_inputs(self):
        """
        Shuffle transaction inputs in random order.

        :return:
        """
        random.shuffle(self.inputs)
        for idx, o in enumerate(self.inputs):
            o.index_n = idx

    def shuffle_outputs(self):
        """
        Shuffle transaction outputs in random order.

        :return:
        """
        random.shuffle(self.outputs)
        for idx, o in enumerate(self.outputs):
            o.output_n = idx

    def shuffle(self):
        """
        Shuffle transaction inputs and outputs in random order.

        :return:
        """
        self.shuffle_inputs()
        self.shuffle_outputs()

    def bumpfee(self, fee=0, extra_fee=0):
        """
        Increase fee for this transaction. If replace-by-fee is signaled in this transaction the fee can be
        increased to speed up inclusion on the blockchain.

        If not fee or extra_fee is provided the extra fee will be increased by the formule you can find in the code
        below using the BUMPFEE_DEFAULT_MULTIPLIER from the config settings.

        The extra fee will be deducted from change output. This method fails if there are not enough change outputs
        to cover fees.

        :param fee: New fee for this transaction
        :type fee: int
        :param extra_fee: Extra fee to add to current transaction fee
        :type extra_fee: int

        :return None:
        """
        if not self.fee:
            raise TransactionError("Current transaction fee is zero, cannot increase fee")
        if not self.vsize:
            self.estimate_size()

        minimal_required_fee = self.vsize
        if fee:
            if fee < self.fee + minimal_required_fee:
                raise TransactionError("Fee cannot be less than minimal required fee")
            extra_fee = fee - self.fee
        elif extra_fee:
            if extra_fee < minimal_required_fee:
                raise TransactionError("Extra fee cannot be less than minimal required fee")
            fee = self.fee + extra_fee
        else:
            fee = int(self.fee * (1.03 ** BUMPFEE_DEFAULT_MULTIPLIER) +
                      (minimal_required_fee * BUMPFEE_DEFAULT_MULTIPLIER))
            extra_fee = fee - self.fee

        remaining_fee = extra_fee
        outputs_to_delete = []
        for outp in [o for o in self.outputs if o.change]:
            if not remaining_fee:
                break
            if outp.value > remaining_fee * 2:
                outp.value -= extra_fee
                remaining_fee = 0
            elif outp.value < remaining_fee:
                remaining_fee -= outp.value
                outputs_to_delete.append(outp)
            else:
                outputs_to_delete.append(outp)
                remaining_fee = 0

        if remaining_fee:
            raise TransactionError("Not enough unspent outputs to bump transaction fee")
        self.fee = fee
        for o in outputs_to_delete:
            self.outputs.remove(o)
        self.sign_and_update()
