# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    TRANSACTION class to create, verify and sign Transactions
#    © 2017 April - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.keys import Key
from bitcoinlib.networks import Network, DEFAULT_NETWORK


_logger = logging.getLogger(__name__)

SCRIPT_TYPES = {
    'p2pkh': ['OP_DUP', 'OP_HASH160', 'signature', 'OP_EQUALVERIFY', 'OP_CHECKSIG'],
    'sig_pubkey': ['signature', 'SIGHASH_ALL', 'public_key'],
    'p2sh': ['OP_HASH160', 'signature', 'OP_EQUAL'],
    'multisig2': ['OP_0', 'multisig'],
    'multisig': ['op_m', 'multisig', 'op_n', 'OP_CHECKMULTISIG'],
    'pubkey': ['signature', 'OP_CHECKSIG'],
    'nulldata': ['OP_RETURN', 'return_data']
}


class TransactionError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def transaction_deserialize(rawtx, network=DEFAULT_NETWORK):
    """
    Deserialize a raw transaction
    
    Returns a dictionary with list of input and output objects, locktime and version.
    
    Will raise an error if wrong number of inputs are found or if there are no output found.
    
    :param rawtx: Raw transaction as String, Byte or Bytearray
    :type rawtx: str, bytes, bytearray
    :param network: Network code, i.e. 'bitcoin', 'testnet', 'litecoin', etc. Leave emtpy for default network
    :type network: str
    :return dict: json list with inputs, outputs, locktime and version
    """
    rawtx = to_bytes(rawtx)
    version = rawtx[0:4][::-1]
    n_inputs, size = varbyteint_to_int(rawtx[4:13])
    cursor = 4 + size
    inputs = []
    for i in range(0, n_inputs):
        inp_hash = rawtx[cursor:cursor + 32][::-1]
        if not len(inp_hash):
            raise TransactionError("Input transaction hash not found. Probably malformed raw transaction")
        inp_index = rawtx[cursor + 32:cursor + 36][::-1]
        cursor += 36

        unlock_scr_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        unlock_scr = rawtx[cursor:cursor + unlock_scr_size]
        cursor += unlock_scr_size
        sequence_number = rawtx[cursor:cursor + 4]
        cursor += 4
        inputs.append(Input(prev_hash=inp_hash, output_index=inp_index, unlocking_script=unlock_scr,
                            sequence=sequence_number, tid=i, network=network))
    if len(inputs) != n_inputs:
        raise TransactionError("Error parsing inputs. Number of tx specified %d but %d found" % (n_inputs, len(inputs)))

    outputs = []
    n_outputs, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
    cursor += size
    for o in range(0, n_outputs):
        amount = change_base(rawtx[cursor:cursor + 8][::-1], 256, 10)
        cursor += 8
        lock_script_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        lock_script = rawtx[cursor:cursor + lock_script_size]
        cursor += lock_script_size
        outputs.append(Output(amount=amount, lock_script=lock_script, network=network))
    if not outputs:
        raise TransactionError("Error no outputs found in this transaction")
    locktime = change_base(rawtx[cursor:cursor + 4][::-1], 256, 10)

    return inputs, outputs, locktime, version


def script_deserialize(script, script_types=None):
    """
    Deserialize a script: determine type, number of signatures and script data.
    
    :param script: Raw script
    :type script: str, bytes, bytearray
    :param script_types: Limit script type determination to this list. Leave to default None to search in all script types.
    :type script_types: list
    :return list: With this items: [script_type, data, number_of_sigs_n, number_of_sigs_m] 
    """

    def _parse_signatures(scr, max_signatures=None):
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
            sigs.append(scr[1:l + 1])
            total_lenght += l + sl
            scr = scr[l + 1:]
        return sigs, total_lenght

    script = to_bytes(script)
    if not script:
        return ["empty", '', '', '']

    if script_types is None:
        script_types = SCRIPT_TYPES
    elif not isinstance(script_types, list):
        script_types = [script_types]

    for tp in script_types:
        cur = 0
        ost = SCRIPT_TYPES[tp]
        data = []
        number_of_sigs_n = 1
        number_of_sigs_m = 1
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
                data += s
                cur += total_length
            elif ch == 'public_key':
                pk_size, size = varbyteint_to_int(script[cur:cur + 9])
                data += [script[cur + size:cur + size + pk_size]]
                cur += size + pk_size
            elif ch == 'OP_RETURN':
                if cur_char == opcodes['OP_RETURN'] and cur == 0:
                    data.append(script[cur+1:])
                    found = True
                    break
                else:
                    found = False
                    break
            elif ch == 'multisig':  # one or more signature
                s, total_length = _parse_signatures(script[cur:])
                data += s
                cur += total_length
            elif ch == 'op_m':
                if cur_char in OP_N_CODES:
                    number_of_sigs_m = cur_char - opcodes['OP_1'] + 1
                else:
                    found = False
                    break
                cur += 1
            elif ch == 'op_n':
                if cur_char in OP_N_CODES:
                    number_of_sigs_n = cur_char - opcodes['OP_1'] + 1
                else:
                    raise TransactionError("%s is not an op_n code" % cur_char)
                if number_of_sigs_m > number_of_sigs_n:
                    raise TransactionError("Number of signatures to sign (%d) is higher then actual "
                                           "amount of signatures (%d)" % (number_of_sigs_m, number_of_sigs_n))
                if len(data) > number_of_sigs_n:
                    raise TransactionError("%d signatures found, but %d sigs expected" %
                                           (len(data), number_of_sigs_n))
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
                    raise TransactionError("Opcode %s not found [type %s]" % (ch, tp))

        if found:
            return [tp, data, number_of_sigs_m, number_of_sigs_n]
    _logger.warning("Could not parse script, unrecognized lock_script. Script: %s" % to_hexstring(script))
    return ["unknown", '', '', '']


def script_deserialize_sigpk(script):
    """
    Deserialize a unlocking script (scriptSig) with a signature and public key. The DER encoded signature is
    decoded to a normal signature with point x and y in 64 bytes total.
    
    Returns signature and public key.
    
    :param script: A unlocking script
    :type script: bytes
    :return tuple: Tuple with a signature and public key in bytes
    """
    _, data, _, _ = script_deserialize(script, 'sig_pubkey')
    return binascii.unhexlify(convert_der_sig(data[0][:-1])), data[1]


def script_to_string(script):
    """
    Convert script to human readable string format with OP-codes, signatures, keys, etc
    
    Example: "OP_DUP OP_HASH160 af8e14a2cecd715c363b3a72b55b59a31e2acac9 OP_EQUALVERIFY OP_CHECKSIG"
    
    :param script: A locking or unlocking script
    :type script: bytes, str
    :return str: 
    """
    script = to_bytes(script)
    tp, data, number_of_sigs_m, number_of_sigs_n = script_deserialize(script)
    if tp == "unknown":
        return tp
    sigs = ' '.join([to_hexstring(i) for i in data])

    scriptstr = SCRIPT_TYPES[tp]
    scriptstr = [sigs if x in ['signature', 'multisig', 'return_data'] else x for x in scriptstr]
    scriptstr = [opcodenames[80 + number_of_sigs_m] if x == 'op_m' else x for x in scriptstr]
    scriptstr = [opcodenames[80 + number_of_sigs_n] if x == 'op_n' else x for x in scriptstr]

    return ' '.join(scriptstr)


class Input:
    """
    Transaction Input class, normally part of Transaction class
    
    An Input contains a reference to an UTXO or Unspent Transaction Output (prev_hash + output_index).
    To spent the UTXO an unlocking script can be included to prove ownership.
    
    Inputs are verified by the Transaction class.
    
    """

    def __init__(self, prev_hash, output_index, unlocking_script=b'', public_key=b'', network=DEFAULT_NETWORK,
                 sequence=b'\xff\xff\xff\xff', tid=0):
        """
        Create a new transaction input
        
        :param prev_hash: Transaction hash of the UTXO (previous output) which will be spent.
        :type prev_hash: bytes, hexstring
        :param output_index: Output number in previous transaction.
        :type output_index: bytes, int
        :param unlocking_script: Unlocking script (scriptSig) to prove ownership. Optional
        :type unlocking_script: bytes, hexstring
        :param public_key: A public can be provided to construct an Unlocking script. Optional
        :type public_key: bytes, str
        :param network: Network, leave empty for default
        :type network: str
        :param sequence: Sequence part of input, you normally do not have to touch this
        :type sequence: bytes
        :param tid: Index of input in transaction. Used by Transaction class.
        :type tid: int
        """
        self.prev_hash = to_bytes(prev_hash)
        self.output_index = output_index
        if isinstance(output_index, numbers.Number):
            self.output_index = struct.pack('>I', output_index)
        self.unlocking_script = to_bytes(unlocking_script)
        self.sequence = to_bytes(sequence)
        self.tid = tid
        self.public_key = to_bytes(public_key)
        self.network = Network(network)

        self.signature = b''
        self.compressed = True
        self.public_key_uncompressed = ''
        self.k = None
        self.public_key_hash = b''
        self.address = ''
        self.type = ''
        self.public_key_hex = None

        if prev_hash == b'\0' * 32:
            self.type = 'coinbase'

        pk2 = b''
        if unlocking_script and self.type != 'coinbase':
            try:
                self.signature, pk2 = script_deserialize_sigpk(unlocking_script)
            except IndexError as err:
                raise TransactionError("Could not parse input script signature: %s" % err)
        if not public_key and pk2:
            self.public_key = pk2

        if self.public_key:
            self.public_key_hex = to_hexstring(self.public_key)
            self.k = Key(self.public_key_hex, network=network)
            self.public_key_uncompressed = self.k.public_uncompressed_byte
            self.public_key_hash = self.k.hash160()
            self.address = self.k.address()
            self.compressed = self.k.compressed

    def json(self):
        """
        Get transaction input information in json format
        
        :return dict: Json with tid, prev_hash, output_index, type, address, public_key, public_key_hash, unlocking_script and sequence
        
        """
        return {
            'tid': self.tid,
            'prev_hash': to_hexstring(self.prev_hash),
            'output_index': to_hexstring(self.output_index),
            'type': self.type,
            'address': self.address,
            'public_key': self.public_key_hex,
            'public_key_hash': to_hexstring(self.public_key_hash),
            'unlocking_script': to_hexstring(self.unlocking_script),
            'sequence': to_hexstring(self.sequence),
        }

    def __repr__(self):
        return "<Input (tid=%s, index=%s, address=%s)>" % (self.tid, to_hexstring(self.output_index), self.address)


class Output:
    """
    Transaction Output class, normally part of Transaction class.
    
    Contains the amount and destination of a transaction. 
    
    """
    def __init__(self, amount, address='', public_key_hash=b'', public_key=b'', lock_script=b'',
                 network=DEFAULT_NETWORK):
        """
        Create a new transaction output
        
        An transaction outputs locks the specified amount to a public key. Anyone with the private key can unlock
        this output.
        
        The transaction output class contains an amount and the destination which can be provided either as address, 
        public key, public key hash or a locking script. Only one needs to be provided as the they all can be derived 
        from each other, but you can provide as much attributes as you know to improve speed.
        
        :param amount: Amount of output in smallest denominator of currency, for example satoshi's for bitcoins
        :type amount: int
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

        self.amount = amount
        self.lock_script = to_bytes(lock_script)
        self.public_key_hash = to_bytes(public_key_hash)
        self.address = address
        self.public_key = to_bytes(public_key)
        self.network = Network(network)

        self.compressed = True
        self.k = None
        self.versionbyte = self.network.prefix_address

        if self.public_key:
            self.k = Key(binascii.hexlify(self.public_key).decode('utf-8'), network=network)
            self.address = self.k.address()
            self.compressed = self.k.compressed
        if self.public_key_hash and not self.address:
            self.address = pubkeyhash_to_addr(public_key_hash, versionbyte=self.versionbyte)
        if self.address and not self.public_key_hash:
            self.public_key_hash = addr_to_pubkeyhash(self.address)
        if not self.public_key_hash and self.k:
            self.public_key_hash = self.k.hash160()

        if self.lock_script and not self.public_key_hash:
            ps = script_deserialize(self.lock_script)
            if ps[0] == 'p2pkh':
                self.public_key_hash = ps[1][0]
                self.address = pubkeyhash_to_addr(ps[1][0], versionbyte=self.versionbyte)

        if self.lock_script == b'':
            self.lock_script = b'\x76\xa9\x14' + self.public_key_hash + b'\x88\xac'

    def json(self):
        """
        Get transaction output information in json format

        :return dict: Json with amount, locking script, public key, public key hash and address

        """
        return {
            'amount': self.amount,
            'lock_script': to_hexstring(self.lock_script),
            'public_key': to_hexstring(self.public_key),
            'public_key_hash': to_hexstring(self.public_key_hash),
            'address': self.address,
        }

    def __repr__(self):
        return "<Output (address=%s, amount=%d)>" % (self.address, self.amount)


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
        
        Uses the transaction_deserialize method to parse the raw transaction and then calls the init method of
        this transaction class to create the transaction object
        
        :param rawtx: Raw transaction string
        :type rawtx: bytes, str
        :param network: Network, leave empty for default
        :type network: str
        :return Transaction:
         
        """
        rawtx = to_bytes(rawtx)
        inputs, outputs, locktime, version = transaction_deserialize(rawtx, network=network)
        return Transaction(inputs, outputs, locktime, version, network)

    def __init__(self, inputs=None, outputs=None, locktime=0, version=b'\x00\x00\x00\x01',
                 network=DEFAULT_NETWORK):
        """
        Create a new transaction class with provided inputs and outputs. 
        
        You can also create a empty transaction and add input and outputs later.
        
        To verify and sign transactions all inputs and outputs need to be included in transaction. Any modification 
        after signing makes the transaction invalid.
        
        :param inputs: Array of Input objects. Leave empty to add later
        :type inputs: Input
        :param outputs: Array of Output object. Leave empty to add later
        :type outputs: Output
        :param locktime: Unix timestamp or blocknumber. Default is 0
        :type locktime: int
        :param version: Version rules. Defaults to 1 in bytes 
        :type version: bytes
        :param network: Network, leave empty for default network
        :type network: str
        """
        if inputs is None:
            self.inputs = []
        else:
            self.inputs = inputs
        if outputs is None:
            self.outputs = []
        else:
            self.outputs = outputs
        self.version = version
        self.locktime = locktime
        self.network = Network(network)

    def __repr__(self):
        return "<Transaction (inputcount=%d, outputcount=%d, network=%s)>" % \
               (len(self.inputs), len(self.outputs), self.network.network_name)

    def get(self):
        """
        Return Json dictionary with transaction information: Inputs, outputs, version and locktime
        
        :return dict: 
        """
        inputs = []
        outputs = []
        for i in self.inputs:
            inputs.append(i.json())
        for o in self.outputs:
            outputs.append(o.json())
        return {
            'inputs': inputs,
            'outputs': outputs,
            'version': self.version,
            'locktime': self.locktime,
        }

    def raw(self, sign_id=None):
        """
        Get raw transaction 
        
        Return transaction with signed inputs if signatures are available
        
        :param sign_id: Create raw transaction which can be signed by transaction with this input ID
        :type sign_id: int
        :return bytes:
        
        """
        r = self.version[::-1]
        r += int_to_varbyteint(len(self.inputs))
        for i in self.inputs:
            r += i.prev_hash[::-1] + i.output_index[::-1]
            if sign_id is None:
                r += struct.pack('B', len(i.unlocking_script)) + i.unlocking_script
            elif sign_id == i.tid:
                r += b'\x19\x76\xa9\x14' + to_bytes(i.public_key_hash) + \
                     b'\x88\xac'
            else:
                r += b'\0'
            r += i.sequence

        r += int_to_varbyteint(len(self.outputs))
        for o in self.outputs:
            if o.amount < 0:
                raise TransactionError("Output amount <0 not allowed")
            r += struct.pack('<Q', o.amount)
            r += struct.pack('B', len(o.lock_script)) + o.lock_script
        r += struct.pack('<L', self.locktime)
        if sign_id is not None:
            r += b'\1\0\0\0'
        return r

    def raw_hex(self):
        """
        Wrapper for raw method. Return current raw transaction hex
        
        :return hexstring: 
        """
        return to_hexstring(self.raw())

    def verify(self):
        """
        Verify all inputs of a transaction, check if signatures match public key.
        
        Does not check if UTXO is valid or has already been spent
        
        :return bool: True if signatures are valid 
        """
        for i in self.inputs:
            if i.type == 'coinbase':
                return True
            t_to_sign = self.raw(i.tid)
            hashtosign = hashlib.sha256(hashlib.sha256(t_to_sign).digest()).digest()
            pk = i.public_key_uncompressed[1:]
            try:
                signature, pk2 = script_deserialize_sigpk(i.unlocking_script)
            except Exception as e:
                # TODO: Add support for other script_types
                _logger.warning("Error %s. No support for script type %s" %
                                (e, script_deserialize(i.unlocking_script)[0]))
                return False

            vk = ecdsa.VerifyingKey.from_string(pk, curve=ecdsa.SECP256k1)
            try:
                vk.verify_digest(signature, hashtosign)
            except ecdsa.keys.BadDigestError as e:
                _logger.info("Bad Signature %s (error %s)" %
                             (binascii.hexlify(signature), e))
                return False
        return True

    def sign(self, priv_key, tid=0):
        """
        Sign the transaction input with provided private key
        
        :param priv_key: A private key
        :type priv_key: bytes
        :param tid: Index of transaction input
        :type tid: int
        :return: 
        """
        if self.inputs[tid].type == 'coinbase':
            raise TransactionError("Can not sign coinbase transactions")
        tsig = hashlib.sha256(hashlib.sha256(self.raw(tid)).digest()).digest()
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

        self.inputs[tid].unlocking_script = varstr(sig_der + b'\01') + varstr(self.inputs[tid].public_key)
        self.inputs[tid].signature = tsig

    def add_input(self, prev_hash, output_index, unlocking_script=b'', public_key=b'', sequence=b'\xff\xff\xff\xff'):
        """
        Add input to this transaction
        
        Wrapper for append method of Input class.

        :param prev_hash: Transaction hash of the UTXO (previous output) which will be spent.
        :type prev_hash: bytes, hexstring
        :param output_index: Output number in previous transaction.
        :type output_index: bytes, int
        :param unlocking_script: Unlocking script (scriptSig) to prove ownership. Optional
        :type unlocking_script: bytes, hexstring
        :param public_key: A public can be provided to construct an Unlocking script. Optional
        :type public_key: bytes, str
        :param sequence: Sequence part of input, you normally do not have to touch this
        :type sequence: bytes
        :return int: Transaction index 
        """
        new_id = len(self.inputs)
        self.inputs.append(Input(prev_hash, output_index, unlocking_script, public_key, self.network.network_name,
                                 sequence, new_id))
        return new_id

    def add_output(self, amount, address='', public_key_hash=b'', public_key=b'', lock_script=b''):
        """
        Add an output to this transaction
        
        Wrapper for the append method of the Output class.
        
        :param amount: Amount of output in smallest denominator of currency, for example satoshi's for bitcoins
        :type amount: int
        :param address: Destination address of output. Leave empty to derive from other attributes you provide.
        :type address: str
        :param public_key_hash: Hash of public key
        :type public_key_hash: bytes, str
        :param public_key: Destination public key
        :type public_key: bytes, str
        :param lock_script: Locking script of output. If not provided a default unlocking script will be provided with a public key hash.
        :type lock_script: bytes, str
        
        """
        self.outputs.append(Output(int(amount), address, public_key_hash, public_key, lock_script,
                                   self.network.network_name))


if __name__ == '__main__':
    from pprint import pprint

    print("\n===  Example of a basic raw transaction with 1 input and 2 outputs (destination and change address). ===")
    rt =  '01000000'  # Version bytes in Little-Endian (reversed) format
    # --- INPUTS ---
    rt += '01'        # Number of UTXO's inputs
    # Previous transaction hash (Little Endian format):
    rt += 'a3919372c9807d92507289d71bdd38f10682a49c47e50dc0136996b43d8aa54e'
    rt += '01000000'  # Index number of previous transaction
    # - INPUT: SCRIPTSIG -
    rt += '6a'        # Size of following unlocking script (ScripSig)
    rt += '47'        # PUSHDATA 47 - Push following 47 bytes signature to stack
    rt += '30'        # DER encoded Signature - Sequence
    rt += '44'        # DER encoded Signature - Length
    rt += '02'        # DER encoded Signature - Integer
    rt += '20'        # DER encoded Signature - Length of X:
    rt += '1f6e18f4532e14f328bc820cb78c53c57c91b1da9949fecb8cf42318b791fb38'
    rt += '02'        # DER encoded Signature - Integer
    rt += '20'        # DER encoded Signature - Lenght of Y:
    rt += '45e78c9e55df1cf3db74bfd52ff2add2b59ba63e068680f0023e6a80ac9f51f4'
    rt += '01'        # SIGHASH_ALL
    # - INPUT: PUBLIC KEY -
    rt += '21'        # PUSHDATA 21 - Push following 21 bytes public key to stack:
    rt += '0239a18d586c34e51238a7c9a27a342abfb35e3e4aa5ac6559889db1dab2816e9d'
    rt += 'feffffff'  # Sequence
    # --- OUTPUTS ---
    rt += '02'                  # Number of outputs
    rt += '3ef5980400000000'    # Output value in Little Endian format
    rt += '19'                  # Script length, of following scriptPubKey:
    rt += '76a914af8e14a2cecd715c363b3a72b55b59a31e2acac988ac'
    rt += '90940d0000000000'    # Output value #2 in Little Endian format
    rt += '19'                  # Script length, of following scriptPubKey:
    rt += '76a914f0d34949650af161e7cb3f0325a1a8833075165088ac'
    rt += 'b7740f00'   # Locktime

    print("\n- Import Raw Transaction -")
    t = Transaction.import_raw(rt)
    print("Raw: %s" % to_hexstring(t.raw()))
    pprint(t.get())
    output_script = t.outputs[0].lock_script
    print("\nOutput Script Type: %s " % script_deserialize(output_script)[0])
    print("Output Script String: %s" % script_to_string(output_script))
    print("\nt.verified() ==> %s" % t.verify())

    print("\n=== Determine Script Types ===")
    scripts = [
        '6a',
        '6a20985f23805edd2938e5bd9f744d36ccb8be643de00b369b901ae0b3fea911a1dd',

        '5121032487c2a32f7c8d57d2a93906a6457afd00697925b0e6e145d89af6d3bca330162102308673d16987eaa010e540901cc6'
        'fe3695e758c19f46ce604e174dac315e685a52ae',

        '5141'
        '04fcf07bb1222f7925f2b7cc15183a40443c578e62ea17100aa3b44ba66905c95d4980aec4cd2f6eb426d1b1ec45d76724f'
        '26901099416b9265b76ba67c8b0b73d'
        '210202be80a0ca69c0e000b97d507f45b98c49f58fec6650b64ff70e6ffccc3e6d0052ae',

        '76a914f0d34949650af161e7cb3f0325a1a8833075165088ac',

        '473044022034519a85fb5299e180865dda936c5d53edabaaf6d15cd1740aac9878b76238e002207345fcb5a62deeb8d9d80e5b4'
        '12bd24d09151c2008b7fef10eb5f13e484d1e0d01210207c9ece04a9b5ef3ff441f3aad6bb63e323c05047a820ab45ebbe61385'
        'aa7446',

        '493046022100cf4d7571dd47a4d47f5cb767d54d6702530a3555726b27b6ac56117f5e7808fe0221008cbb42233bb04d7f28a71'
        '5cf7c938e238afde90207e9d103dd9018e12cb7180e0141042daa93315eebbe2cb9b5c3505df4c6fb6caca8b756786098567550'
        'd4820c09db988fe9997d049d687292f815ccd6e7fb5c1b1a91137999818d17c73d0f80aef9',
    ]
    for s in scripts:
        print("\nScript: %s" % s)
        sp = script_deserialize(s)
        print("Type: %s" % sp[0])
        for d in sp[1]:
            print("Data: %s" % binascii.hexlify(d))
        print("Signatures n/m: %s/%s" % (sp[2], sp[3]))
        print("Script as String: %s" % script_to_string(s))

    print("\n=== Example based on explanation on "
          "http://bitcoin.stackexchange.com/questions/3374/how-to-redeem-a-basic-tx/24580 ===")
    t = Transaction()
    prev_tx = 'f2b3eb2deb76566e7324307cd47c35eeb88413f971d88519859b1834307ecfec'
    ki = Key(0x18E14A7B6A307F426A94F8114701E7C8E774E7F9A47E2C2035DB29A206321725, compressed=False)
    t.add_input(prev_hash=prev_tx, output_index=1, public_key=ki.public_hex)
    t.add_output(99900000, '1runeksijzfVxyrpiyCY2LCBvYsSiFsCm')
    t.sign(ki.private_byte)
    pprint(t.get())
    print(binascii.hexlify(t.raw()))
    print("Verified %s " % t.verify())

    print("\n=== Example based on"
          "http://www.righto.com/2014/02/bitcoins-hard-way-using-raw-bitcoin.html ===")
    ki = Key('5HusYj2b2x4nroApgfvaSfKYZhRbKFH41bVyPooymbC6KfgSXdD', compressed=False)
    txid = "81b4c832d70cb56ff957589752eb4125a4cab78a25a8fc52d6a09e5bd4404d48"
    utxo_input = Input(prev_hash=txid, output_index=0, public_key=ki.public_byte)
    pkh = "c8e90996c7c6080ee06284600c684ed904d14c5c"
    transaction_output = Output(amount=91234, public_key_hash=pkh)
    t = Transaction([utxo_input], [transaction_output])
    t.sign(ki.private_byte)
    print(binascii.hexlify(t.raw()))
    pprint(t.get())
    print("Verified %s " % t.verify())

    print("\n=== Create and sign Testnet Transaction using keys from Wallet class 'TestNetWallet' example "
          "See txid 71b0bc8669575cebf01110ed9bdb2b015f95ed830aac71720c81880f3935ece7 ===")
    ki = Key('cR6pgV8bCweLX1JVN3Q1iqxXvaw4ow9rrp8RenvJcckCMEbZKNtz', network='testnet')  # Private key for import
    input = Input(prev_hash='d3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955', output_index=1,
                  public_key=ki.public(), network='testnet')
    # key for address mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2
    ko = Key('0391634874ffca219ff5633f814f7f013f7385c66c65c8c7d81e7076a5926f1a75', network='testnet')
    output = Output(880000, public_key_hash=ko.hash160(), network='testnet')
    t = Transaction([input], [output], network='testnet')
    t.sign(ki.private_byte, 0)
    pprint(t.get())
    print("Raw Signed Transaction %s" % binascii.hexlify(t.raw()))
    print("Verified %s\n\n\n" % t.verify())

    print("\n=== Create and sign Testnet Transaction with Multiple OUTPUTS using keys from Wallet class "
          "'TestNetWallet' example"
          "\nSee txid f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618 ===")
    ki = Key('cRMjy1LLMPsVU4uaAt3br8Ft5vdJLx6prY4Sx7WjPARrpYAnVEkV', network='testnet')  # Private key for import
    ti = Input(prev_hash='adee8bdd011f60e52949b65b069ff9f19fc220815fdc1a6034613ed1f6b775f1', output_index=1,
               public_key=ki.public(), network='testnet')
    amount_per_address = 27172943
    output_addresses = ['mn6xJw1Cp2gLcSSQAYPnX4G2M6GARGyX5j', 'n3pdL33MgTA316odzeydhNrcKXdu6jy8ry',
                        'n1Bq89KaJrcaXEMUEsDSyhKHfTGi8mkfRJ', 'mrqYnxFPcf6u5xkEfmA3dxQzjB7ZcPgtTq',
                        'mwrETLWFdvEfDwRa44JvXngxCZp59MFcC6']
    outputs = []
    for oa in output_addresses:
        outputs.append(Output(amount_per_address, address=oa, network='testnet'))
    t = Transaction([ti], outputs, network='testnet')
    t.sign(ki.private_byte, 0)
    pprint(t.get())
    print("Raw Signed Transaction %s" % binascii.hexlify(t.raw()))
    print("Verified %s\n\n\n" % t.verify())

    print("\n=== Create and sign Testnet Transaction with Multiple INPUTS using keys from "
          "Wallet class 'TestNetWallet' example"
          "\nSee txid 82b48b128232256d1d5ce0c6ae7f7897f2b464d44456c25d7cf2be51626530d9 ===")
    # 5 inputs ('prev_hash', 'index', 'private_key')
    outputs = [Output(135000000, address='mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2', network='testnet')]
    t = Transaction(outputs=outputs, network='testnet')
    tis = [
        (u'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618', 0,
         'cQowpHh56TrwVk3YSYFuUo8X4ZLXkGJMtbkuo7NyauZZBGs9Tb7U'),
        (u'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618', 1,
         'cSVr1HyJ2V2S2C57HsSF5QwkJjEhfLDpPporv6iFgJG2kFQqE9yh'),
        (u'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618', 2,
         'cPMakfwNRW2dzBBcfcxiJu7ucpD5Xjb1Zev88Tz6mYNrwU4ymZCf'),
        (u'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618', 3,
         'cR1TSoqB8vS3azmBMZa4khssXw1V2agPxM76Xc4ciULie3cdKPDr'),
        (u'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618', 4,
         'cW19vMM1k8x2Luawr1FZogQibggg5745eNE8GLJcZXYQb7eYc3Cf')
    ]
    inputs = []
    for ti in tis:
        ki = Key(ti[2], network='testnet')
        t.add_input(prev_hash=ti[0], output_index=ti[1], public_key=ki.public(), sequence=b'\xff\xff\xff\xff')
    icount = 0
    for ti in tis:
        ki = Key(ti[2], network='testnet')
        t.sign(ki.private_byte, icount)
        icount += 1
    pprint(t.get())
    print("Raw Signed Transaction %s" % binascii.hexlify(t.raw()))
    print("Verified %s\n\n\n" % t.verify())

    print("\n=== Create bitcoin transaction with UTXO, amount, address and private key "
          "\nSee txid d99070c63e04a6bdb38b553733838d6196198908c8b8930bec0ba502bc483b72 ===")
    private_key = 'KwbbBb6iz1hGq6dNF9UsHc7cWaXJZfoQGFWeozexqnWA4M7aSwh4'
    utxo = 'fdaa42051b1fc9226797b2ef9700a7148ee8be9466fc8408379814cb0b1d88e3'
    amount = 95000
    send_to_address = '1K5j3KpsSt2FyumzLmoVjmFWVcpFhXHvNF'

    ki = Key(private_key)
    utxo_input = Input(prev_hash=utxo, output_index=1, public_key=ki.public())
    output_to = Output(amount, address=send_to_address)
    t = Transaction([utxo_input], [output_to])
    t.sign(ki.private_byte, 0)
    pprint(t.get())
    print("Raw Signed Transaction %s" % binascii.hexlify(t.raw()))
    print("Verified %s\n\n\n" % t.verify())

    from bitcoinlib.services.bitcoind import BitcoindClient
    bdc = BitcoindClient.from_config()
    try:
        res = bdc.proxy.sendrawtransaction(binascii.hexlify(t.raw()).decode('utf-8'))
        print("Send raw transaction, result %s" % res)
    except Exception as e:
        print("Error sending Transaction.", e)

    #
    # === TRANSACTIONS AND BITCOIND EXAMPLES
    #

    from bitcoinlib.services.bitcoind import BitcoindClient
    bdc = BitcoindClient.from_config()

    # Deserialize and verify a transaction
    txid = '73652b5f704b0a112b8bc68d063dac6238eb3e2861074a7a12ce24e2a332bd45'
    rt = bdc.getrawtransaction(txid)
    print("Raw: %s" % rt)
    t = Transaction.import_raw(rt)
    pprint(t.get())
    print("Verified: %s" % t.verify())

    # Deserialize transactions in latest block with bitcoind client
    MAX_TRANSACTIONS_VIEW = 100
    error_count = 0
    if MAX_TRANSACTIONS_VIEW:
        print("\n=== DESERIALIZE LAST BLOCKS TRANSACTIONS ===")
        blockhash = bdc.proxy.getbestblockhash()
        bestblock = bdc.proxy.getblock(blockhash)
        print('... %d transactions found' % len(bestblock['tx']))
        ci = 0
        ct = len(bestblock['tx'])
        for txid in bestblock['tx']:
            ci += 1
            print("\n[%d/%d] Deserialize txid %s" % (ci, ct, txid))
            rt = bdc.getrawtransaction(txid)
            print("Raw: %s" % rt)
            t = Transaction.import_raw(rt)
            pprint(t.get())
            print("Verified: %s" % t.verify())
            if ci > MAX_TRANSACTIONS_VIEW:
                break
        print("===   %d raw transactions deserialised   ===" %
              (ct if ct < MAX_TRANSACTIONS_VIEW else MAX_TRANSACTIONS_VIEW))
        print("===   errorcount %d" % error_count)
        print("===   D O N E   ===")

        # Deserialize transactions in the bitcoind mempool client
        print("\n=== DESERIALIZE MEMPOOL TRANSACTIONS ===")
        newtxs = bdc.proxy.getrawmempool()
        ci = 0
        ct = len(newtxs)
        print("Found %d transactions in mempool" % len(newtxs))
        for txid in newtxs:
            ci += 1
            print("[%d/%d] Deserialize txid %s" % (ci, ct, txid))
            try:
                rt = bdc.getrawtransaction(txid)
                print("- raw %s" % rt)
                t = Transaction.import_raw(rt)
                pprint(t.get())
            except Exception as e:
                print("Error when importing raw transaction %d, error %s", (txid, e))
                error_count += 1
            if ci > MAX_TRANSACTIONS_VIEW:
                break
        print("===   %d mempool transactions deserialised   ===" %
              (ct if ct < MAX_TRANSACTIONS_VIEW else MAX_TRANSACTIONS_VIEW))
        print("===   errorcount %d" % error_count)
        print("===   D O N E   ===")
