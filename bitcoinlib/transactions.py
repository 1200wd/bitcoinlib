# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    TRANSACTION class to create, verify and sign Transactions
#    © 2018 February - 1200 Web Development <http://1200wd.com/>
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

from bitcoinlib.encoding import *
from bitcoinlib.config.opcodes import *
from bitcoinlib.keys import HDKey, Key, deserialize_address
from bitcoinlib.networks import Network, DEFAULT_NETWORK


_logger = logging.getLogger(__name__)

SCRIPT_TYPES = {
    'p2pkh': ['OP_DUP', 'OP_HASH160', 'signature', 'OP_EQUALVERIFY', 'OP_CHECKSIG'],
    'sig_pubkey': ['signature', 'SIGHASH_ALL', 'public_key'],
    'p2sh': ['OP_HASH160', 'signature', 'OP_EQUAL'],
    'p2sh_multisig': ['OP_0', 'multisig', 'redeemscript'],
    'multisig': ['op_m', 'multisig', 'op_n', 'OP_CHECKMULTISIG'],
    'pubkey': ['signature', 'OP_CHECKSIG'],
    'nulldata': ['OP_RETURN', 'return_data']
}

SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
SIGHASH_ANYONECANPAY = 80


class TransactionError(Exception):
    """
    Handle Transaction class Exceptions

    """

    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def _transaction_deserialize(rawtx, network=DEFAULT_NETWORK):
    """
    Deserialize a raw transaction
    
    Returns a dictionary with list of input and output objects, locktime and version.
    
    Will raise an error if wrong number of inputs are found or if there are no output found.
    
    :param rawtx: Raw transaction as String, Byte or Bytearray
    :type rawtx: str, bytes, bytearray
    :param network: Network code, i.e. 'bitcoin', 'testnet', 'litecoin', etc. Leave emtpy for default network
    :type network: str

    :return Transaction:
    """
    rawtx = to_bytes(rawtx)
    version = rawtx[0:4][::-1]
    coinbase = False
    flag = None
    cursor = 4
    if rawtx[4:5] == b'\0':
        cursor += 1
        flag = rawtx[cursor:cursor+1]
        cursor += 1
    n_inputs, size = varbyteint_to_int(rawtx[cursor:cursor+9])
    cursor += size
    inputs = []

    for n in range(0, n_inputs):
        inp_hash = rawtx[cursor:cursor + 32][::-1]
        if not len(inp_hash):
            raise TransactionError("Input transaction hash not found. Probably malformed raw transaction")
        if inp_hash == 32 * b'\0':
            coinbase = True
        output_n = rawtx[cursor + 32:cursor + 36][::-1]
        cursor += 36

        unlocking_script_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        unlocking_script = rawtx[cursor:cursor + unlocking_script_size]
        cursor += unlocking_script_size
        sequence_number = rawtx[cursor:cursor + 4]
        cursor += 4
        inputs.append(Input(prev_hash=inp_hash, output_n=output_n, unlocking_script=unlocking_script,
                            sequence=sequence_number, index_n=n, network=network))
    if len(inputs) != n_inputs:
        raise TransactionError("Error parsing inputs. Number of tx specified %d but %d found" % (n_inputs, len(inputs)))

    outputs = []
    n_outputs, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
    cursor += size
    output_total = 0
    for n in range(0, n_outputs):
        value = change_base(rawtx[cursor:cursor + 8][::-1], 256, 10)
        cursor += 8
        lock_script_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        lock_script = rawtx[cursor:cursor + lock_script_size]
        cursor += lock_script_size
        outputs.append(Output(value=value, lock_script=lock_script, network=network, output_n=n))
        output_total += value
    if not outputs:
        raise TransactionError("Error no outputs found in this transaction")
    if flag:
        n_witnesses, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        for n in range(0, n_witnesses):
            witness_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
            cursor += size
            # witness_hash = rawtx[cursor:cursor + witness_size][::-1]
            cursor += witness_size
    locktime = change_base(rawtx[cursor:cursor + 4][::-1], 256, 10)

    return Transaction(inputs, outputs, locktime, version, network, size=len(rawtx), output_total=output_total,
                       coinbase=coinbase, flag=flag, rawtx=to_hexstring(rawtx))


def script_deserialize(script, script_types=None):
    """
    Deserialize a script: determine type, number of signatures and script data.
    
    :param script: Raw script
    :type script: str, bytes, bytearray
    :param script_types: Limit script type determination to this list. Leave to default None to search in all script types.
    :type script_types: list

    :return list: With this items: [script_type, data, number_of_sigs_n, number_of_sigs_m] 
    """

    def _parse_signatures(scr, max_signatures=None, redeemscript_expected=False):
        scr = to_bytes(scr)
        sigs = []
        total_lenght = 0
        while len(scr) and (max_signatures is None or max_signatures > len(sigs)):
            l, sl = varbyteint_to_int(scr[0:9])
            # TODO: Rethink and rewrite this:
            if l not in [20, 33, 65, 70, 71, 72, 73]:
                break
            if len(scr) < l:
                break
            if redeemscript_expected and len(scr[l + 1:]) < 20:
                break
            sigs.append(scr[1:l + 1])
            total_lenght += l + sl
            scr = scr[l + 1:]
        return sigs, total_lenght

    data = {'script_type': '', 'keys': [], 'signatures': [], 'redeemscript': b''}
    script = to_bytes(script)
    if not script:
        data.update({'script_type': 'empty'})
        return data

    if script_types is None:
        script_types = SCRIPT_TYPES
    elif not isinstance(script_types, list):
        script_types = [script_types]

    for script_type in script_types:
        cur = 0
        ost = SCRIPT_TYPES[script_type]
        data['script_type'] = script_type
        data['number_of_sigs_n'] = 1
        data['number_of_sigs_m'] = 1
        found = True
        for ch in ost:
            if cur >= len(script):
                found = False
                break
            cur_char = script[cur]
            if sys.version < '3':
                cur_char = ord(script[cur])
            if ch == 'signature':
                s, total_length = _parse_signatures(script[cur:], 1)
                if not s:
                    found = False
                    break
                data['signatures'] += s
                cur += total_length
            elif ch == 'public_key':
                pk_size, size = varbyteint_to_int(script[cur:cur + 9])
                key = script[cur + size:cur + size + pk_size]
                if key[0] == '0x30':
                    data['keys'].append(binascii.unhexlify(convert_der_sig(key[:-1])))
                else:
                    data['keys'].append(key)
                cur += size + pk_size
            elif ch == 'OP_RETURN':
                if cur_char == opcodes['OP_RETURN'] and cur == 0:
                    data.update({'op_return': script[cur+1:]})
                    found = True
                    break
                else:
                    found = False
                    break
            elif ch == 'multisig':  # one or more signatures
                redeemscript_expected = False
                if 'redeemscript' in ost:
                    redeemscript_expected = True
                s, total_length = _parse_signatures(script[cur:], redeemscript_expected=redeemscript_expected)
                data['signatures'] += s
                cur += total_length
            elif ch == 'redeemscript':
                size_byte = 0
                if script[cur:cur+1] == b'\x4c':
                    size_byte = 1
                elif script[cur:cur + 1] == b'\x4d':
                    size_byte = 2
                elif script[cur:cur + 1] == b'\x4e':
                    size_byte = 3
                data['redeemscript'] = script[cur+1+size_byte:]
                data2 = script_deserialize(data['redeemscript'])
                if 'signatures' not in data2:
                    found = False
                    break
                data['keys'] = data2['signatures']
                data['number_of_sigs_m'] = data2['number_of_sigs_m']
                data['number_of_sigs_n'] = data2['number_of_sigs_n']
                cur = len(script)
            elif ch == 'op_m':
                if cur_char in OP_N_CODES:
                    data['number_of_sigs_m'] = cur_char - opcodes['OP_1'] + 1
                else:
                    found = False
                    break
                cur += 1
            elif ch == 'op_n':
                if cur_char in OP_N_CODES:
                    data['number_of_sigs_n'] = cur_char - opcodes['OP_1'] + 1
                else:
                    raise TransactionError("%s is not an op_n code" % cur_char)
                if data['number_of_sigs_m'] > data['number_of_sigs_n']:
                    raise TransactionError("Number of signatures to sign (%s) is higher then actual "
                                           "amount of signatures (%s)" %
                                           (data['number_of_sigs_m'], data['number_of_sigs_n']))
                if len(data['signatures']) > int(data['number_of_sigs_n']):
                    raise TransactionError("%d signatures found, but %s sigs expected" %
                                           (len(data['signatures']), data['number_of_sigs_n']))
                cur += 1
            elif ch == 'SIGHASH_ALL':
                pass
                # cur += 1
            else:
                try:
                    if cur_char == opcodes[ch]:
                        cur += 1
                    else:
                        found = False
                        break
                except IndexError:
                    raise TransactionError("Opcode %s not found [type %s]" % (ch, script_type))

        if found:
            return data
    _logger.warning("Could not parse script, unrecognized lock_script. Script: %s" % to_hexstring(script))
    return {'script_type': 'unknown'}


def script_deserialize_sigpk(script):
    """
    Deserialize a unlocking script (scriptSig) with a signature and public key. The DER encoded signature is
    decoded to a normal signature with point x and y in 64 bytes total.
    
    Returns signature and public key.
    
    :param script: A unlocking script
    :type script: bytes

    :return tuple: Tuple with a signature and public key in bytes
    """
    data = script_deserialize(script, ['sig_pubkey'])
    assert(len(data['signatures']) == 1)
    assert(len(data['keys']) == 1)
    return data['signatures'][0], data['keys'][0]


def script_to_string(script):
    """
    Convert script to human readable string format with OP-codes, signatures, keys, etc
    
    Example: "OP_DUP OP_HASH160 af8e14a2cecd715c363b3a72b55b59a31e2acac9 OP_EQUALVERIFY OP_CHECKSIG"
    
    :param script: A locking or unlocking script
    :type script: bytes, str

    :return str: 
    """
    script = to_bytes(script)
    data = script_deserialize(script)
    if not data or data['script_type'] == 'empty':
        return ""
    sigs = ' '.join([to_hexstring(i) for i in data['signatures']])

    scriptstr = SCRIPT_TYPES[data['script_type']]
    scriptstr = [sigs if x in ['signature', 'multisig', 'return_data'] else x for x in scriptstr]
    if 'redeemscript' in data and data['redeemscript']:
        redeemscript_str = script_to_string(data['redeemscript'])
        scriptstr = [redeemscript_str if x == 'redeemscript' else x for x in scriptstr]
    scriptstr = [opcodenames[80 + int(data['number_of_sigs_m'])] if x == 'op_m' else x for x in scriptstr]
    scriptstr = [opcodenames[80 + int(data['number_of_sigs_n'])] if x == 'op_n' else x for x in scriptstr]

    return ' '.join(scriptstr)


def _serialize_multisig_redeemscript(public_key_list, n_required=None):
    # Serialize m-to-n multisig script. Needs a list of public keys
    for key in public_key_list:
        if not isinstance(key, (str, bytes)):
            raise TransactionError("Item %s in public_key_list is not of type string or bytes")
    if n_required is None:
        n_required = len(public_key_list)

    script = int_to_varbyteint(opcodes['OP_1'] + n_required - 1)
    for key in public_key_list:
        script += int_to_varbyteint(len(key)) + key
    script += int_to_varbyteint(opcodes['OP_1'] + len(public_key_list) - 1)
    script += b'\xae'  # 'OP_CHECKMULTISIG'

    return script


def serialize_multisig_redeemscript(key_list, n_required=None, compressed=True):
    """
    Create a multisig redeemscript used in a p2sh.

    Contains the number of signatures, followed by the list of public keys and the OP-code for the number of signatures required.

    :param key_list: List of public keys
    :type key_list: Key, list
    :param n_required: Number of required signatures
    :type n_required: int
    :param compressed: Use compressed public keys?
    :type compressed: bool

    :return bytes: A multisig redeemscript
    """
    if not key_list:
        return b''
    if not isinstance(key_list, list):
        raise TransactionError("Argument public_key_list must be of type list")
    public_key_list = []
    for k in key_list:
        if isinstance(k, Key):
            if compressed:
                public_key_list.append(k.public_byte)
            else:
                public_key_list.append(k.public_uncompressed_byte)
        elif len(k) == 65 and k[0:1] == b'\x04' or len(k) == 33 and k[0:1] in [b'\x02', b'\x03']:
            public_key_list.append(k)
        else:
            try:
                kobj = Key(k)
                if compressed:
                    public_key_list.append(kobj.public_byte)
                else:
                    public_key_list.append(kobj.public_uncompressed_byte)
            except:
                raise TransactionError("Unknown key %s, please specify Key object, public or private key string")

    return _serialize_multisig_redeemscript(public_key_list, n_required)


def _p2sh_multisig_unlocking_script(sigs, redeemscript, hash_type=None):
    usu = b'\x00'
    if not isinstance(sigs, list):
        sigs = [sigs]
    for sig in sigs:
        s = to_bytes(sig)
        if hash_type:
            s += struct.pack('B', hash_type)
        usu += int_to_varbyteint(len(s)) + to_bytes(s)
    rs_size = int_to_varbyteint(len(redeemscript))
    if len(redeemscript) >= 76:
        if len(rs_size) == 1:
            size_byte = b'\x4c'
        elif len(rs_size) == 2:
            size_byte = b'\x4d'
        else:
            size_byte = b'\x4e'
        usu += size_byte
    usu += rs_size + redeemscript
    return usu


def verify_signature(transaction_to_sign, signature, public_key):
    """
    Verify if signatures signs provided transaction hash and corresponds with public key

    :param transaction_to_sign: Raw transaction to sign
    :type transaction_to_sign: bytes, str
    :param signature: A signature
    :type signature: bytes, str
    :param public_key: The public key
    :type public_key: bytes, str

    :return bool: Return True if verified

    """
    transaction_to_sign = to_bytes(transaction_to_sign)
    signature = to_bytes(signature)
    public_key = to_bytes(public_key)
    if len(transaction_to_sign) != 32:
        transaction_to_sign = hashlib.sha256(hashlib.sha256(transaction_to_sign).digest()).digest()
    if len(public_key) == 65:
        public_key = public_key[1:]
    ver_key = ecdsa.VerifyingKey.from_string(public_key, curve=ecdsa.SECP256k1)
    try:
        if signature.startswith(b'\x30'):
            try:
                signature = convert_der_sig(signature[:-1], as_hex=False)
            except Exception:
                pass
        ver_key.verify_digest(signature, transaction_to_sign)
    except ecdsa.keys.BadSignatureError:
        return False
    except ecdsa.keys.BadDigestError as e:
        _logger.info("Bad Digest %s (error %s)" %
                     (binascii.hexlify(signature), e))
        return False
    return True


class Input:
    """
    Transaction Input class, normally part of Transaction class
    
    An Input contains a reference to an UTXO or Unspent Transaction Output (prev_hash + output_n).
    To spent the UTXO an unlocking script can be included to prove ownership.
    
    Inputs are verified by the Transaction class.
    
    """

    def __init__(self, prev_hash, output_n, keys=None, signatures=None, unlocking_script=b'', script_type='p2pkh',
                 sequence=4294967295, compressed=True, sigs_required=None, sort=False, index_n=0,
                 value=0, double_spend=False, network=DEFAULT_NETWORK):
        """
        Create a new transaction input
        
        :param prev_hash: Transaction hash of the UTXO (previous output) which will be spent.
        :type prev_hash: bytes, hexstring
        :param output_n: Output number in previous transaction.
        :type output_n: bytes, int
        :param keys: A list of Key objects or public / private key string in various formats. If no list is provided but a bytes or string variable, a list with one item will be created. Optional
        :type keys: list (bytes, str)
        :param signatures: Specify optional signatures
        :type signatures: bytes, str
        :param unlocking_script: Unlocking script (scriptSig) to prove ownership. Optional
        :type unlocking_script: bytes, hexstring
        :param script_type: Type of unlocking script used, i.e. p2pkh or p2sh_multisig. Default is p2pkh
        :type script_type: str
        :param sequence: Sequence part of input, you normally do not have to touch this
        :type sequence: bytes, int
        :param compressed: Use compressed or uncompressed public keys. Default is compressed
        :type compressed: bool
        :param sigs_required: Number of signatures required for a p2sh_multisig unlocking script
        :type sigs_required: int
        :param sort: Sort public keys according to BIP0045 standard. Default is False to avoid unexpected change of key order.
        :type sort: boolean
        :param index_n: Index of input in transaction. Used by Transaction class.
        :type index_n: int
        :param value: Input value
        :type value: int
        :param network: Network, leave empty for default
        :type network: str
        """
        self.prev_hash = to_bytes(prev_hash)
        self.output_n = output_n
        if isinstance(output_n, numbers.Number):
            self.output_n_int = output_n
            self.output_n = struct.pack('>I', output_n)
        else:
            self.output_n_int = struct.unpack('>I', output_n)[0]
            self.output_n = output_n
        if isinstance(keys, (bytes, str)):
            keys = [keys]
        if unlocking_script is None:
            unlocking_script = b''
        self.unlocking_script = b'' if unlocking_script is None else to_bytes(unlocking_script)
        self.unlocking_script_unsigned = b''
        if self.prev_hash == 32 * b'\0':
            self.script_type = 'coinbase'
        else:
            self.script_type = script_type
        if isinstance(sequence, numbers.Number):
            self.sequence = sequence
        else:
            self.sequence = struct.unpack('<I', sequence)[0]
        self.compressed = compressed
        self.network = Network(network)
        self.index_n = index_n
        self.value = value
        if keys is None:
            keys = []
        self.keys = []
        if not isinstance(keys, list):
            keys = [keys]
        if not signatures:
            signatures = []
        if not isinstance(signatures, list):
            signatures = [signatures]
        # Sort according to BIP45 standard
        self.sort = sort
        if sort:
            self.keys.sort(key=lambda k: k.public_byte)
        self.address = ''
        self.signatures = []
        self.redeemscript = b''
        if not sigs_required:
            if script_type == 'p2sh_multisig':
                raise TransactionError("Please specify number of signatures required (sigs_required) parameter")
            else:
                sigs_required = 1
        self.sigs_required = sigs_required
        self.script_type = script_type
        self.double_spend = double_spend

        if prev_hash == b'\0' * 32:
            self.script_type = 'coinbase'

        # If unlocking script is specified extract keys, signatures, type from script
        if unlocking_script and self.script_type != 'coinbase' and not signatures:
            us_dict = script_deserialize(unlocking_script)
            if not us_dict:  # or us_dict['script_type'] in ['unknown', 'empty']
                raise TransactionError("Could not parse unlocking script (%s)" % binascii.hexlify(unlocking_script))
            self.script_type = us_dict['script_type']
            if us_dict['script_type'] not in ['unknown', 'empty']:
                self.sigs_required = us_dict['number_of_sigs_n']
                self.redeemscript = us_dict['redeemscript']
                signatures += us_dict['signatures']
                keys += us_dict['keys']

        for key in keys:
            if not isinstance(key, Key):
                kobj = Key(key, network=network)
            else:
                kobj = key
            if kobj not in self.keys:
                if kobj.compressed != self.compressed:
                    self.compressed = kobj.compressed
                    _logger.warning("Key compressed is %s but Input class compressed argument is %s " %
                                    (kobj.compressed, self.compressed))
                self.keys.append(kobj)

        for sig in signatures:
            if isinstance(sig, dict):
                if sig['sig_der'] not in [x['sig_der'] for x in self.signatures]:
                    self.signatures.append(sig)
            else:
                assert(isinstance(sig, bytes))
                sig_der = ''
                if sig.startswith(b'\x30'):
                    # If signature ends with Hashtype, remove hashtype and continue
                    # TODO: support for other hashtypes
                    if sig.endswith(b'\x01'):
                        _, junk = ecdsa.der.remove_sequence(sig)
                        if junk == b'\x01':
                            sig_der = sig[:-1]
                    else:
                        sig_der = sig
                    try:
                        sig = convert_der_sig(sig[:-1], as_hex=False)
                    except Exception:
                        pass
                self.signatures.append(
                    {
                        'sig_der': sig_der,
                        'signature': to_bytes(sig),
                        'priv_key': '',
                        'pub_key': ''
                    })

        if self.script_type == 'sig_pubkey':
            self.script_type = 'p2pkh'
        if self.script_type == 'p2pkh':
            if self.keys:
                self.unlocking_script_unsigned = b'\x76\xa9\x14' + to_bytes(self.keys[0].hash160()) + b'\x88\xac'
                self.address = self.keys[0].address()
        elif self.script_type == 'p2sh_multisig':
            if not self.keys:
                raise TransactionError("Please provide keys to append multisig transaction input")
            if not self.redeemscript:
                self.redeemscript = serialize_multisig_redeemscript(self.keys, n_required=self.sigs_required,
                                                                    compressed=self.compressed)

            self.address = pubkeyhash_to_addr(script_to_pubkeyhash(self.redeemscript),
                                              versionbyte=self.network.prefix_address_p2sh)
            self.unlocking_script_unsigned = self.redeemscript

    def dict(self):
        """
        Get transaction input information in json format
        
        :return dict: Json with output_n, prev_hash, output_n, type, address, public_key, public_key_hash, unlocking_script and sequence
        
        """
        pks = []
        for k in self.keys:
            pks.append(k.public_hex)
        if len(self.keys) == 1:
            pks = pks[0]
        return {
            'index_n': self.index_n,
            'prev_hash': to_hexstring(self.prev_hash),
            'output_n': self.output_n_int,
            'script_type': self.script_type,
            'address': self.address,
            'value': self.value,
            'public_key': pks,
            'double_spend': self.double_spend,
            'script': to_hexstring(self.unlocking_script),
            'redeemscript': to_hexstring(self.redeemscript),
            'sequence': self.sequence,
            'signatures': [to_hexstring(s['signature']) for s in self.signatures],
        }

    def __repr__(self):
        return "<Input(prev_hash=%s, output_n=%d, address=%s, index_n=%s, type=%s)>" % \
               (self.prev_hash, self.output_n_int, self.address, self.index_n, self.script_type)


class Output:
    """
    Transaction Output class, normally part of Transaction class.
    
    Contains the amount and destination of a transaction. 
    
    """
    def __init__(self, value, address='', public_key_hash=b'', public_key=b'', lock_script=b'', spent=False,
                 output_n=0, network=DEFAULT_NETWORK):
        """
        Create a new transaction output
        
        An transaction outputs locks the specified amount to a public key. Anyone with the private key can unlock
        this output.
        
        The transaction output class contains an amount and the destination which can be provided either as address, 
        public key, public key hash or a locking script. Only one needs to be provided as the they all can be derived 
        from each other, but you can provide as much attributes as you know to improve speed.
        
        :param value: Amount of output in smallest denominator of currency, for example satoshi's for bitcoins
        :type value: int
        :param address: Destination address of output. Leave empty to derive from other attributes you provide.
        :type address: str
        :param public_key_hash: Hash of public key
        :type public_key_hash: bytes, str
        :param public_key: Destination public key
        :type public_key: bytes, str
        :param lock_script: Locking script of output. If not provided a default unlocking script will be provided with a public key hash.
        :type lock_script: bytes, str
        :param network: Network, leave empty for default
        :type network: str
        """
        if not (address or public_key_hash or public_key or lock_script):
            raise TransactionError("Please specify address, lock_script, public key or public key hash when "
                                   "creating output")

        self.value = value
        self.lock_script = b'' if lock_script is None else to_bytes(lock_script)
        self.public_key_hash = to_bytes(public_key_hash)
        self.address = address
        self.public_key = to_bytes(public_key)
        self.network = Network(network)
        self.compressed = True
        self.k = None
        self.versionbyte = self.network.prefix_address
        self.script_type = 'p2pkh'
        self.spent = spent
        self.output_n = output_n

        if self.public_key:
            self.k = Key(binascii.hexlify(self.public_key).decode('utf-8'), network=network)
            self.address = self.k.address()
            self.compressed = self.k.compressed
        if self.public_key_hash and not self.address:
            self.address = pubkeyhash_to_addr(public_key_hash, versionbyte=self.versionbyte)
        if self.address:
            address_dict = deserialize_address(self.address)
            if address_dict['script_type']:
                self.script_type = address_dict['script_type']
            else:
                raise TransactionError("Could not determine script type of address %s" % self.address)
            self.public_key_hash = address_dict['public_key_hash_bytes']
            if address_dict['network'] and self.network.network_name != address_dict['network']:
                raise TransactionError("Address (%s) is from different network then defined %s" %
                                       (address_dict['network'], self.network.network_name))
        if not self.public_key_hash and self.k:
            self.public_key_hash = self.k.hash160()

        if self.lock_script and not self.public_key_hash:
            ss = script_deserialize(self.lock_script)
            self.script_type = ss['script_type']
            if self.script_type == 'p2sh':
                self.versionbyte = self.network.prefix_address_p2sh
            if self.script_type in ['p2pkh', 'p2sh']:
                self.public_key_hash = ss['signatures'][0]
                self.address = pubkeyhash_to_addr(self.public_key_hash, versionbyte=self.versionbyte)
            else:
                _logger.warning("Script type %s not supported" % self.script_type)

        if self.lock_script == b'':
            if self.script_type == 'p2pkh':
                self.lock_script = b'\x76\xa9\x14' + self.public_key_hash + b'\x88\xac'
            elif self.script_type == 'p2sh':
                self.lock_script = b'\xa9\x14' + self.public_key_hash + b'\x87'
            else:
                raise TransactionError("Unknown output script type %s, please provide own locking script" %
                                       self.script_type)

    def dict(self):
        """
        Get transaction output information in json format

        :return dict: Json with amount, locking script, public key, public key hash and address

        """
        return {
            'value': self.value,
            'script': to_hexstring(self.lock_script),
            'script_type': self.script_type,
            'public_key': to_hexstring(self.public_key),
            'public_key_hash': to_hexstring(self.public_key_hash),
            'address': self.address,
            'output_n': self.output_n,
            'spent': self.spent,
        }

    def __repr__(self):
        return "<Output(value=%d, address=%s, type=%s)>" % (self.value, self.address, self.script_type)


class Transaction:
    """
    Transaction Class
    
    Contains 1 or more Input class object with UTXO's to spent and 1 or more Output class objects with destinations.
    Besides the transaction class contains a locktime and version.
    
    Inputs and outputs can be included when creating the transaction, or can be add later with add_input and
    add_output respectively.
    
    A verify method is available to check if the transaction Inputs have valid unlocking scripts. 
    
    Each input in the transaction can be signed with the sign method provided a valid private key.
    
    """

    @staticmethod
    def import_raw(rawtx, network=DEFAULT_NETWORK):
        """
        Import a raw transaction and create a Transaction object
        
        Uses the _transaction_deserialize method to parse the raw transaction and then calls the init method of
        this transaction class to create the transaction object
        
        :param rawtx: Raw transaction string
        :type rawtx: bytes, str
        :param network: Network, leave empty for default
        :type network: str

        :return Transaction:
         
        """
        rawtx = to_bytes(rawtx)
        return _transaction_deserialize(rawtx, network=network)

    def __init__(self, inputs=None, outputs=None, locktime=0, version=1, network=DEFAULT_NETWORK,
                 fee=None, fee_per_kb=None, size=None, hash='', date=None, confirmations=None,
                 block_height=None, block_hash=None, input_total=0, output_total=0, rawtx='', status='new',
                 coinbase=False, verified=False, flag=None):
        """
        Create a new transaction class with provided inputs and outputs. 
        
        You can also create a empty transaction and add input and outputs later.
        
        To verify and sign transactions all inputs and outputs need to be included in transaction. Any modification 
        after signing makes the transaction invalid.
        
        :rtype:
        :param inputs: Array of Input objects. Leave empty to add later
        :type inputs: Input, list
        :param outputs: Array of Output object. Leave empty to add later
        :type outputs: Output, list
        :param locktime: Unix timestamp or blocknumber. Default is 0
        :type locktime: int
        :param version: Version rules. Defaults to 1 in bytes 
        :type version: bytes, int
        :param network: Network, leave empty for default network
        :type network: str
        :param fee: Fee in smallest denominator (ie Satoshi) for complete transaction
        :type fee: int
        :param fee_per_kb: Fee in smallest denominator per kilobyte. Specify when exact transaction size is not known.
        :type fee_per_kb: int
        :param size; Transaction size in bytes
        :type size: int
        :param date: Confirmation date of transaction
        :type date: datetime.datetime
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
        :param rawtx: Raw hexstring of complete transaction
        :type rawtx: str
        :param status: Transaction status, for example: 'new', 'incomplete', 'unconfirmed', 'confirmed'
        :type status: str
        :param coinbase: Coinbase transaction or not?
        :type coinbase: bool
        :param verified: Is transaction successfully verified? Updated when verified() method is called
        :type verified: bool
        :param flag: Transaction flag to indicate version, for example for SegWit
        :type flag: bytes, str
        """
        self.inputs = []
        if inputs is not None:
            for inp in inputs:
                self.inputs.append(inp)
            if not input_total:
                input_total = sum([i.value for i in inputs])
        id_list = [i.index_n for i in self.inputs]
        if list(set(id_list)) != id_list:
            _logger.warning("Identical transaction indexes (tid) found in inputs, please specify unique index. "
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
            if fee <= 0:
                raise TransactionError("Transaction inputs total value must be greater then total value of "
                                       "transaction outputs")

        if isinstance(version, int):
            self.version = struct.pack('>L', version)
        else:
            self.version = version
        self.locktime = locktime
        self.network = Network(network)
        self.coinbase = coinbase
        self.flag = flag
        self.fee = fee
        self.fee_per_kb = fee_per_kb
        self.size = size
        self.change = 0
        self.hash = hash
        self.date = date
        self.confirmations = confirmations
        self.block_height = block_height
        self.block_hash = block_hash
        self.input_total = input_total
        self.output_total = output_total
        self.rawtx = rawtx
        self.status = status
        self.verified = verified
        if not self.hash and rawtx:
            self.hash = to_hexstring(hashlib.sha256(hashlib.sha256(to_bytes(rawtx)).digest()).digest()[::-1])

    def __repr__(self):
        return "<Transaction(input_count=%d, output_count=%d, status=%s, network=%s)>" % \
               (len(self.inputs), len(self.outputs), self.status, self.network.network_name)

    def dict(self):
        """
        Return Json dictionary with transaction information: Inputs, outputs, version and locktime
        
        :return dict: 
        """
        inputs = []
        outputs = []
        for i in self.inputs:
            inputs.append(i.dict())
        for o in self.outputs:
            outputs.append(o.dict())
        return {
            'hash': self.hash,
            'date': self.date,
            'network': self.network.network_name,
            'coinbase': self.coinbase,
            'flag': self.flag,
            'confirmations': self.confirmations,
            'block_height': self.block_height,
            'block_hash': self.block_hash,
            'fee': self.fee,
            'fee_per_kb': self.fee_per_kb,
            'inputs': inputs,
            'outputs': outputs,
            'input_total': self.input_total,
            'output_total': self.output_total,
            'version': self.version,
            'locktime': self.locktime,
            'raw': self.raw_hex(),
            'size': self.size,
            'verified': self.verified,
            'status': self.status
        }

    def info(self):
        """
        Prints transaction information to standard output

        """
        print("Transaction %s" % self.hash)
        print("Date: %s" % self.date)
        print("Network: %s" % self.network.network_name)
        print("Status: %s" % self.status)
        print("Verified: %s" % self.verified)
        print("Inputs")
        for ti in self.inputs:
            print("-", ti.address, ti.value, to_hexstring(ti.prev_hash), ti.output_n_int)
            print("  Script type: %s, signatures: %d (%d of %d)" %
                  (ti.script_type, len(ti.signatures), ti.sigs_required, len(ti.keys)))
        print("Outputs")
        for to in self.outputs:
            if to.script_type == 'nulldata':
                print("- NULLDATA ", to.lock_script[2:])
            else:
                print("-", to.address, to.value)
        print("Fee: %s" % self.fee)
        print("Confirmations: %s" % self.confirmations)

    def raw(self, sign_id=None, hash_type=SIGHASH_ALL):
        """
        Get raw transaction 
        
        Return transaction with signed inputs if signatures are available
        
        :param sign_id: Create raw transaction which can be signed by transaction with this input ID
        :type sign_id: int
        :param hash_type: Specific hash type, default is SIGHASH_ALL
        :type hash_type: int

        :return bytes:
        
        """
        r = self.version[::-1]
        r += int_to_varbyteint(len(self.inputs))
        for i in self.inputs:
            r += i.prev_hash[::-1] + i.output_n[::-1]
            if sign_id is None:
                r += int_to_varbyteint(len(i.unlocking_script)) + i.unlocking_script
            elif sign_id == i.index_n:
                r += int_to_varbyteint(len(i.unlocking_script_unsigned)) + i.unlocking_script_unsigned
            else:
                r += b'\0'
            r += struct.pack('<L', i.sequence)

        r += int_to_varbyteint(len(self.outputs))
        for o in self.outputs:
            if o.value < 0:
                raise TransactionError("Output value < 0 not allowed")
            r += struct.pack('<Q', o.value)
            r += int_to_varbyteint(len(o.lock_script)) + o.lock_script
        r += struct.pack('<L', self.locktime)
        if sign_id is not None:
            r += struct.pack('<L', hash_type)
        else:
            self.size = len(r)
        return r

    def raw_hex(self, sign_id=None, hash_type=SIGHASH_ALL):
        """
        Wrapper for raw method. Return current raw transaction hex

        :param sign_id: Create raw transaction which can be signed by transaction with this input ID
        :type sign_id: int
        :param hash_type: Specific hash type, default is SIGHASH_ALL
        :type hash_type: int

        :return hexstring: 
        """
        return to_hexstring(self.raw(sign_id, hash_type=hash_type))

    def verify(self):
        """
        Verify all inputs of a transaction, check if signatures match public key.
        
        Does not check if UTXO is valid or has already been spent
        
        :return bool: True if enough signatures provided and if all signatures are valid
        """

        self.verified = False
        for i in self.inputs:
            if i.script_type == 'coinbase':
                return True
            if not i.signatures:
                _logger.info("No signatures found for transaction input %d" % i.index_n)
                return False
            if len(i.signatures) < i.sigs_required:
                _logger.info("Not enough signatures provided. Found %d signatures but %d needed" %
                             (len(i.signatures), i.sigs_required))
                return False
            t_to_sign = self.raw(i.index_n)
            transaction_hash_to_sign = hashlib.sha256(hashlib.sha256(t_to_sign).digest()).digest()
            sig_id = 0
            for key in i.keys:
                if sig_id > i.sigs_required-1:
                    break
                if sig_id >= len(i.signatures):
                    _logger.info("No valid signatures found")
                    return False
                if verify_signature(transaction_hash_to_sign,
                                 i.signatures[sig_id]['signature'], key.public_uncompressed_byte[1:]):
                    sig_id += 1
            if sig_id < i.sigs_required:
                _logger.info("Not enough valid signatures provided. Found %d signatures but %d needed" %
                             (sig_id, i.sigs_required))
                return False
        self.verified = True
        return True

    def sign(self, keys, tid=None, hash_type=SIGHASH_ALL):
        """
        Sign the transaction input with provided private key
        
        :param keys: A private key or list of private keys
        :type keys: HDKey, Key, bytes, list
        :param tid: Index of transaction input
        :type tid: int
        :param hash_type: Specific hash type, default is SIGHASH_ALL
        :type hash_type: int

        :return int: Return int with number of signatures added
        """

        if tid is None:
            tids = range(len(self.inputs))
        else:
            tids = [tid]

        n_signs = 0
        for tid in tids:
            if not isinstance(keys, list):
                keys = [keys]

            if self.inputs[tid].script_type == 'coinbase':
                raise TransactionError("Can not sign coinbase transactions")
            tsig = hashlib.sha256(hashlib.sha256(self.raw(tid)).digest()).digest()

            pub_key_list = [x.public_byte for x in self.inputs[tid].keys]
            pub_key_list_uncompressed = [x.public_uncompressed_byte for x in self.inputs[tid].keys]
            n_total_sigs = len(pub_key_list)
            sig_domain = [''] * n_total_sigs

            for key in keys:
                if isinstance(key, (HDKey, Key)):
                    priv_key = key.private_byte
                    pub_key = key.public_byte
                else:
                    ko = Key(key, compressed=self.inputs[tid].compressed)
                    priv_key = ko.private_byte
                    pub_key = ko.public_byte
                if not priv_key:
                    raise TransactionError("Please provide a valid private key to sign the transaction. "
                                           "%s is not a private key" % priv_key)
                sk = ecdsa.SigningKey.from_string(priv_key, curve=ecdsa.SECP256k1)
                while True:
                    sig_der = sk.sign_digest(tsig, sigencode=ecdsa.util.sigencode_der)
                    # Test if signature has low S value, to prevent 'Non-canonical signature: High S Value' errors
                    # TODO: Recalc 's' instead, see:
                    #       https://github.com/richardkiss/pycoin/pull/24/files#diff-12d8832e97767321d1f3c40909be8b23
                    signature = convert_der_sig(sig_der)
                    s = int(signature[64:], 16)
                    if s < ecdsa.SECP256k1.order / 2:
                        break
                newsig = {
                        'sig_der': to_bytes(sig_der),
                        'signature': to_bytes(signature),
                        'priv_key': priv_key,
                        'pub_key': pub_key,
                        'transaction_id': tid
                    }

                # Check if signature signs known key and is not already in list
                if pub_key not in pub_key_list:
                    raise TransactionError("This key does not sign any known key: %s" % pub_key)
                if pub_key in [x['pub_key'] for x in self.inputs[tid].signatures]:
                    _logger.warning("Key %s already signed" % pub_key)
                    break

                newsig_pos = pub_key_list.index(pub_key)
                sig_domain[newsig_pos] = newsig
                n_signs += 1

            # Add already known signatures on correct position
            n_sigs_to_insert = len(self.inputs[tid].signatures)
            for sig in self.inputs[tid].signatures:
                free_positions = [i for i, s in enumerate(sig_domain) if s == '']
                for pos in free_positions:
                    if verify_signature(tsig, sig['signature'], pub_key_list_uncompressed[pos]):
                        if not sig['pub_key']:
                            sig['pub_key'] = pub_key_list[pos]
                        if not sig['sig_der']:
                            raise TransactionError("Missing DER encoded signature in input %d" % tid)
                        sig_domain[pos] = sig
                        n_sigs_to_insert -= 1
                        break
            if n_sigs_to_insert:
                for sig in self.inputs[tid].signatures:
                    free_positions = [i for i, s in enumerate(sig_domain) if s == '']
                    for pos in free_positions:
                        sig_domain[pos] = sig
                        n_sigs_to_insert -= 1
                        break
            if n_sigs_to_insert:
                _logger.info("Some signatures are replaced with the signatures of the provided keys")
                n_signs -= n_sigs_to_insert
            self.inputs[tid].signatures = [s for s in sig_domain if s != '']

            if self.inputs[tid].script_type == 'p2pkh':
                if len(self.inputs[tid].signatures):
                    self.inputs[tid].unlocking_script = \
                        varstr(self.inputs[tid].signatures[0]['sig_der'] + struct.pack('B', hash_type)) + \
                        varstr(self.inputs[tid].keys[0].public_byte)
            elif self.inputs[tid].script_type == 'p2sh_multisig':
                n_tag = self.inputs[tid].redeemscript[0]
                if not isinstance(n_tag, int):
                    n_tag = struct.unpack('B', n_tag)[0]
                n_required = n_tag - 80
                signatures = [s['sig_der'] for s in self.inputs[tid].signatures[:n_required]]
                if b'' in signatures:
                    raise TransactionError("Empty signature found in signature list when signing. "
                                           "Is DER encoded version of signature defined?")
                self.inputs[tid].unlocking_script = \
                    _p2sh_multisig_unlocking_script(signatures, self.inputs[tid].redeemscript, hash_type)
            else:
                raise TransactionError("Script type %s not supported at the moment" % self.inputs[tid].script_type)
        return n_signs

    def add_input(self, prev_hash, output_n, keys=None, unlocking_script=b'', script_type='p2pkh',
                  sequence=4294967295, compressed=True, sigs_required=None, sort=False, index_n=None,
                  value=None, double_spend=False, signatures=None):
        """
        Add input to this transaction
        
        Wrapper for append method of Input class.

        :param prev_hash: Transaction hash of the UTXO (previous output) which will be spent.
        :type prev_hash: bytes, hexstring
        :param output_n: Output number in previous transaction.
        :type output_n: bytes, int
        :param keys: Public keys can be provided to construct an Unlocking script. Optional
        :type keys: bytes, str
        :param unlocking_script: Unlocking script (scriptSig) to prove ownership. Optional
        :type unlocking_script: bytes, hexstring
        :param script_type: Type of unlocking script used, i.e. p2pkh or p2sh_multisig. Default is p2pkh
        :type script_type: str
        :param sequence: Sequence part of input, you normally do not have to touch this
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
        :param signatures: Add signatures to input if already known
        :type signatures: bytes, str

        :return int: Transaction index number (index_n)
        """

        if index_n is None:
            index_n = len(self.inputs)
        self.inputs.append(
            Input(prev_hash=prev_hash, output_n=output_n, keys=keys, unlocking_script=unlocking_script,
                  script_type=script_type, network=self.network.network_name, sequence=sequence, compressed=compressed,
                  sigs_required=sigs_required, sort=sort, index_n=index_n, value=value, double_spend=double_spend,
                  signatures=signatures))
        return index_n

    def add_output(self, value, address='', public_key_hash=b'', public_key=b'', lock_script=b'', spent=False,
                   output_n=None):
        """
        Add an output to this transaction
        
        Wrapper for the append method of the Output class.
        
        :param value: Value of output in smallest denominator of currency, for example satoshi's for bitcoins
        :type value: int
        :param address: Destination address of output. Leave empty to derive from other attributes you provide.
        :type address: str
        :param public_key_hash: Hash of public key
        :type public_key_hash: bytes, str
        :param public_key: Destination public key
        :type public_key: bytes, str
        :param lock_script: Locking script of output. If not provided a default unlocking script will be provided with a public key hash.
        :type lock_script: bytes, str
        :param spent: Has output been spent in new transaction?
        :type spent: bool
        :param output_n: Index number of output in transaction
        :type output_n: int

        :return int: Transaction output number (output_n)

        """
        if address:
            to = address
        elif public_key:
            to = public_key
        else:
            to = public_key_hash
        if output_n is None:
            output_n = len(self.outputs)
        if not float(value).is_integer():
            raise TransactionError("Output to %s must be of type integer and contain no decimals" % to)
        if value < 0:
            raise TransactionError("Output to %s must be more then zero" % to)
        self.outputs.append(Output(value=int(value), address=address, public_key_hash=public_key_hash,
                                   public_key=public_key, lock_script=lock_script, spent=spent, output_n=output_n,
                                   network=self.network.network_name))
        return output_n

    def estimate_size(self, add_change_output=True):
        """
        Get estimated size in bytes for current transaction based on transaction type and number of inputs and outputs.

        :param add_change_output: Assume an extra change output will be created but has not been created yet.
        :type add_change_output: bool

        :return int: Estimated transaction size
        """
        est_size = 10
        if add_change_output:
            est_size += 34
        for inp in self.inputs:
            if inp.script_type in ['p2sh', 'p2pkh']:
                if inp.compressed:
                    est_size += 147
                else:
                    est_size += 180
            elif inp.script_type == 'p2sh_multisig':
                n_sigs = len(inp.keys)
                est_size += 9 + (n_sigs * 34) + (inp.sigs_required * 72)
            else:
                raise TransactionError("Unknown input script type %s cannot estimate transaction size" %
                                       inp.script_type)
        if not self.inputs:
            est_size += 147  # If nothing is known assume 1 p2sh/p2pkh input
        for outp in self.outputs:
            if outp.script_type in ['p2pkh', 'p2sh']:
                est_size += 34
            elif outp.script_type == 'nulldata':
                est_size += len(outp.lock_script) + 9
            else:
                raise TransactionError("Unknown output script type %s cannot estimate transaction size" %
                                       outp.script_type)
        return est_size

    def calculate_fee(self):
        """
        Get fee for this transaction in smallest denominator (i.e. Satoshi) based on its size and the
        transaction.fee_per_kb value

        :return int: Estimated transaction fee
        """

        if not self.fee_per_kb:
            raise TransactionError("Cannot calculate transaction fees: transaction.fee_per_kb is not set")
        return int(len(self.raw())/1024.0 * self.fee_per_kb)
