# -*- coding: utf-8 -*-
#
#    bitcoinlib Transactions
#    © 2017 January - 1200 Web Development <http://1200wd.com/>
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

import binascii
import hashlib
from bitcoinlib.encoding import *
from bitcoinlib.config.opcodes import *
from bitcoinlib.keys import Key
from bitcoinlib.main import *
from bitcoinlib.services.bitcoind import BitcoindClient

_logger = logging.getLogger(__name__)

OUTPUT_SCRIPT_TYPES = {
    'p2pkh': ['OP_DUP', 'OP_HASH160', 'signature', 'OP_EQUALVERIFY', 'OP_CHECKSIG'],
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


def deserialize_transaction(rawtx):
    """
    Deserialize a raw transaction

    :param rawtx: Raw transaction in bytes
    :return: json list with inputs, outputs, locktime and version
    """
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

        scriptsig_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        scriptsig = rawtx[cursor:cursor + scriptsig_size]
        cursor += scriptsig_size
        sequence_number = rawtx[cursor:cursor + 4]
        cursor += 4
        inputs.append(Input(inp_hash, inp_index, scriptsig, sequence_number, i))
    if len(inputs) != n_inputs:
        raise TransactionError("Error parsing inputs. Number of tx specified %d but %d found" % (n_inputs, len(inputs)))

    outputs = []
    n_outputs, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
    cursor += size
    for o in range(0, n_outputs):
        amount = change_base(rawtx[cursor:cursor + 8][::-1], 256, 10)
        cursor += 8
        script_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        script = rawtx[cursor:cursor + script_size]
        cursor += script_size
        outputs.append(Output(amount, script))
    if not outputs:
        raise TransactionError("Error no outputs found in this transaction")
    locktime = change_base(rawtx[cursor:cursor + 4][::-1], 256, 10)

    return inputs, outputs, locktime, version


def parse_script_sig(s):
    if not s:
        return "", ""
    l = s[0]
    sig = convert_der_sig(s[1:l])
    l2 = s[l+1]
    public_key = s[l+2:l+l2+2]
    return sig, public_key


def _parse_signatures(script):
    data = []
    total_lenght = 0
    while len(script):
        l = script[0]
        if l not in [33, 65]:
            break
        data.append(script[1:l+1])
        total_lenght += l + 1
        script = script[l+1:]
    return data, total_lenght


def output_script_type(script):
    if isinstance(script, str):
        script = binascii.unhexlify(script)
    if not isinstance(script, bytes):
        raise TransactionError("Script must be in string or bytes format")

    if not script:
        return "unknown"

    for tp in OUTPUT_SCRIPT_TYPES:
        cur = 0
        ost = OUTPUT_SCRIPT_TYPES[tp]
        data = []
        number_of_sigs_n = 1
        number_of_sigs_m = 1
        found = True
        for ch in ost:
            if cur > len(script):
                found = False
                break
            if ch == 'signature':
                l = script[cur]
                data.append(script[cur+1:cur+1+l])
                cur += 1+l
            elif ch == 'return_data':
                data.append(script[cur+1:])
            elif ch == 'multisig':  # one or more signature
                s, total_length = _parse_signatures(script[cur:])
                data += s
                cur += total_length
            elif ch == 'op_m':
                if script[cur] in OP_N_CODES:
                    number_of_sigs_m = script[cur] - opcodes['OP_1'] + 1
                else:
                    found = False
                    break
                cur += 1
            elif ch == 'op_n':
                if script[cur] in OP_N_CODES:
                    number_of_sigs_n = script[cur] - opcodes['OP_1'] + 1
                else:
                    raise TransactionError("%s is not an op_n code" % script[cur])
                cur += 1
            else:
                try:
                    if opcodes[ch] == script[cur]:
                        cur += 1
                    else:
                        found = False
                        break
                except IndexError:
                    raise TransactionError("Opcode %s not found [type %s]" % (ch, tp))

        if found:
            return [tp, data, number_of_sigs_m, number_of_sigs_n]
    return "unknown"


def script_to_string(script):
    if isinstance(script, str):
        script = binascii.unhexlify(script)
    if not isinstance(script, bytes):
        raise TransactionError("Script must be in string or bytes format")

    tp, data, number_of_sigs_m, number_of_sigs_n = output_script_type(script)
    sigs = ' '.join([binascii.hexlify(i).decode('utf-8') for i in data])

    scriptstr = OUTPUT_SCRIPT_TYPES[tp]
    scriptstr = [sigs if x in ['signature', 'multisig', 'return_data'] else x for x in scriptstr]
    scriptstr = [opcodenames[80 + number_of_sigs_m] if x == 'op_m' else x for x in scriptstr]
    scriptstr = [opcodenames[80 + number_of_sigs_n] if x == 'op_n' else x for x in scriptstr]

    return ' '.join(scriptstr)


class Input:

    @staticmethod
    def add(prev_hash, output_index=0, public_key=b''):
        if not isinstance(prev_hash, bytes):
            prev_hash = binascii.unhexlify(prev_hash)
        if not isinstance(output_index, bytes):
            output_index = struct.pack('L', output_index)
        return Input(prev_hash, output_index, b'', public_key=public_key)

    def __init__(self, prev_hash, output_index, script_sig, sequence=b'\xff\xff\xff\xff', id=0, public_key=''):
        self.id = id
        self.prev_hash = prev_hash
        self.output_index = output_index
        self.script_sig = script_sig
        self.signature = b''
        self._public_key = b''
        self.public_key = public_key
        if public_key:
            self._public_key = binascii.unhexlify(public_key)
        pk2 = b''
        if script_sig:
            self.signature, pk2 = parse_script_sig(script_sig)
        if not public_key and pk2:
            self._public_key = pk2
            self.public_key = binascii.hexlify(self._public_key).decode('utf-8')
        self.k = None
        self.public_key_hash = ""
        self.address = ""
        self.address_uncompressed = ""
        if self.public_key:
            self.k = Key(self.public_key, network='testnet')
            self.public_key_uncompressed = self.k.public_uncompressed()
            self.public_key_hash = self.k.hash160()
            self.address = self.k.address(compressed=True)
            self.address_uncompressed = self.k.address_uncompressed()
        self.sequence = sequence

    def json(self):
        return {
            'prev_hash': binascii.hexlify(self.prev_hash).decode('utf-8'),
            'address': self.address,
            'address_uncompressed': self.address_uncompressed,
            'public_key': self.public_key,
            'public_key_hash': self.public_key_hash,
            'output_index': binascii.hexlify(self.output_index).decode('utf-8'),
            'script_sig': binascii.hexlify(self.script_sig).decode('utf-8'),
            'sequence': binascii.hexlify(self.sequence).decode('utf-8'),
        }

    def __repr__(self):
        return str(self.json())


class Output:

    @staticmethod
    def add(amount, public_key):
        if not isinstance(public_key, bytes):
            public_key = binascii.unhexlify(public_key)
        return Output(amount, public_key=public_key)

    def __init__(self, amount, script=b'', public_key=b''):
        self.amount = amount
        self.script = script
        self.public_key = public_key

    def json(self):
        return {
            'amount': self.amount,
            'script': binascii.hexlify(self.script).decode('utf-8'),
            'public_key': binascii.hexlify(self.public_key).decode('utf-8'),
        }

    def __repr__(self):
        return str(self.json())


class Transaction:

    @staticmethod
    def import_raw(rawtx):
        if isinstance(rawtx, str):
            rawtx = binascii.unhexlify(rawtx)
        elif not isinstance(rawtx, bytes):
            raise TransactionError("Raw Transaction must be of type bytes or str")

        inputs, outputs, locktime, version = deserialize_transaction(rawtx)

        return Transaction(inputs, outputs, locktime, version)

    def __init__(self, inputs, outputs, locktime=0, version=b'00000001'):
        self.inputs = inputs
        self.outputs = outputs
        self.version = version
        self.locktime = locktime

    def get(self):
        inputs = []
        outputs = []
        for i in self.inputs:
            inputs.append(i.json())
        for o in self.outputs:
            outputs.append(o.json())
        return {
            'inputs': inputs,
            'outputs': outputs,
            'locktime': self.locktime,
        }

    def raw(self, sign_id=None):
        r = self.version[::-1]
        r += int_to_varbyteint(len(self.inputs))
        for i in self.inputs:
            r += i.prev_hash[::-1] + i.output_index[::-1]
            if sign_id is None:
                r += struct.pack('B', len(i.script_sig)) + i.script_sig
            elif sign_id == i.id:
                r += b'\x19\x76\xa9\x14' + binascii.unhexlify(i.public_key_hash) + \
                     b'\x88\xac'
            else:
                r += b'\0'
            r += i.sequence

        r += int_to_varbyteint(len(self.outputs))
        for o in self.outputs:
            r += struct.pack('<Q', o.amount)
            r += struct.pack('B', len(o.script)) + o.script
        r += struct.pack('<L', self.locktime)
        if sign_id is not None:
            r += b'\1\0\0\0'
        return r

    def verify(self):
        for i in self.inputs:
            t_to_sign = self.raw(i.id)
            hashtosign = hashlib.sha256(hashlib.sha256(t_to_sign).digest()).digest()
            pk = binascii.unhexlify(i.public_key_uncompressed[2:])
            vk = ecdsa.VerifyingKey.from_string(pk, curve=ecdsa.SECP256k1)
            try:
                vk.verify_digest(binascii.unhexlify(i.signature), hashtosign)
            except ecdsa.keys.BadDigestError as e:
                _logger.info("Bad Signature %s (error %s)" % (i.signature, e))
                return False
            _logger.info("Signature Verified %s" % i.signature)
        return True


if __name__ == '__main__':
    from pprint import pprint

    # Example of a basic raw transaction with 1 input and 2 outputs
    # (destination and change address).
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

    print("\n=== Import Raw Transaction ===")
    t = Transaction.import_raw(rt)
    print("Raw: %s" % binascii.hexlify(t.raw()).decode('utf-8'))
    pprint(t.get())
    output_script = t.outputs[0].script
    print("\nOutput Script Type: %s " % output_script_type(output_script))
    print("Output Script String: %s" % script_to_string(output_script))
    print("\nt.verified() ==> %s" % t.verify())

    print("\n=== Determine Output Script Type ===")
    os = '6a20985f23805edd2938e5bd9f744d36ccb8be643de00b369b901ae0b3fea911a1dd'
    print("Output Script: %s" % os)
    pprint("Type: %s" % output_script_type(os))
    print("Output Script String: %s" % script_to_string(os))
    os = '5121032487c2a32f7c8d57d2a93906a6457afd00697925b0e6e145d89af6d3bca330162102308673d16987eaa010e540901cc6' \
         'fe3695e758c19f46ce604e174dac315e685a52ae'
    print("\nOutput Script: %s" % os)
    pprint("Type: %s" % output_script_type(os))
    print("Output Script String: %s" % script_to_string(os))

    # Create a new transaction
    # from bitcoinlib.keys import HDKey
    # ki = HDKey('tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKe'
    #            'PyA7irEvBoe4aAn52', network='testnet')
    # print(ki.public().address())
    # input = Input.add('d3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955', 1,
    #                   ki.public().public_uncompressed())
    # ko = HDKey('tprv8eb7i2C26Kngu1BW13Dc5VemHsVbp8g5CBiBwcQaL9odDDhcUUoE4QLC1G4yYHFDvhFaJmwtYw2snTWMEkz4ng9RTo'
    #            'eesHUtqeGCuRD6qiW')
    # output = Output.add(8900, ko.public().public_uncompressed())
    # t = Transaction([input], [output])

    if False:  # Set to True to enable example
        # Deserialize transactions in latest block with bitcoind client
        bdc = BitcoindClient.from_config()

        print("\n=== DESERIALIZE LAST BLOCKS TRANSACTIONS ===")
        blockhash = bdc.proxy.getbestblockhash()
        bestblock = bdc.proxy.getblock(blockhash)
        print('... %d transactions found' % len(bestblock['tx']))
        ci = 0
        ct = len(bestblock['tx'])
        for txid in bestblock['tx']:
            ci += 1
            print("[%d/%d] Deserialize txid %s" % (ci, ct, txid))
            try:
                rt = bdc.getrawtransaction(txid)
            except:
                pass
            print("- raw %s" % rt)
            t = Transaction.import_raw(rt)
            pprint(t.get())
        print("===   %d raw transactions deserialised   ===" % ct)
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
            except:
                print(txid)
        print("===   %d mempool transactions deserialised   ===" % ct)
        print("===   D O N E   ===")
