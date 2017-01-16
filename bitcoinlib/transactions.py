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
from bitcoinlib.encoding import *
from bitcoinlib.keys import Key, get_key_format
from bitcoinlib.config.opcodes import opcodes, opcodenames
from bitcoinlib.main import *
from bitcoinlib.services.bitcoind import BitcoindClient

_logger = logging.getLogger(__name__)


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
        inputs.append({'id': i, 'prev_hash': inp_hash, 'output_index': inp_index,
                       'script_sig': scriptsig, 'sequence_number': sequence_number, })
        # inputs.append({'prev_hash': binascii.hexlify(inp_hash), 'output_index': change_base(inp_index, 256, 10),
        #                'script_sig': binascii.hexlify(scriptsig), 'sequence_number': sequence_number, })
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
        outputs.append({'amount': amount, 'script': script, })
    if not outputs:
        raise TransactionError("Error no outputs found in this transaction")
    locktime = change_base(rawtx[cursor:cursor + 4][::-1], 256, 10)

    return inputs, outputs, locktime, version


def parse_script_sig(s):
    l = s[0]
    sig = convert_der_sig(s[1:l])
    l2 = s[l+1]
    public_key = s[l+2:l+l2+2]
    return sig, public_key


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

    def input_addresses(self, id=None, return_type='hash160'):
        r = []
        for i in self.inputs:
            s = i['script_sig']
            l = s[0]
            sig_der = s[1:l]
            l2 = s[l+1]
            public_key = binascii.hexlify(s[l+2:l+l2+2]).decode('utf-8')
            k = Key(public_key, compressed=False)
            if return_type == 'hash160':
                r.append(k.hash160())
            elif return_type == 'hex':
                r.append(k.public_uncompressed())
            elif return_type == 'byte':
                print(k.public_hex())
                r.append(binascii.unhexlify(k.public_uncompressed()))
        if id is None:
            return r
        else:
            return r[id]

    def get(self):
        return {
            'inputs': self.inputs,
            'outputs': self.outputs,
            'locktime': self.locktime,
        }

    def raw(self, signable=False):
        r = self.version[::-1]
        r += int_to_varbyteint(len(self.inputs))
        for i in self.inputs:
            r += i['prev_hash'][::-1] + i['output_index'][::-1]
            if not signable:
                r += struct.pack('B', len(i['script_sig'])) + i['script_sig']
            else:
                r += b'\x19\x76\xa9\x14' + binascii.unhexlify(self.input_addresses(id=i['id'])) + \
                     b'\x88\xac'
            r += i['sequence_number']

        r += int_to_varbyteint(len(self.outputs))
        for o in self.outputs:
            r += struct.pack('<Q', o['amount'])
            r += struct.pack('B', len(o['script'])) + o['script']
        r += struct.pack('<L', self.locktime)
        if signable:
            r += b'\1\0\0\0'
        return r


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

    # rt = (
    # "0100000001a97830933769fe33c6155286ffae34db44c6b8783a2d8ca52ebee6414d399ec300000000" + "8a47" + "304402202c2e1a746c556546f2c959e92f2d0bd2678274823cc55e11628284e4a13016f80220797e716835f9dbcddb752cd0115a970a022ea6f2d8edafff6e087f928e41baac01" + "41" + "04392b964e911955ed50e4e368a9476bc3f9dcc134280e15636430eb91145dab739f0d68b82cf33003379d885a0b212ac95e9cddfd2d391807934d25995468bc55" + "ffffffff02015f0000000000001976a914c8e90996c7c6080ee06284600c684ed904d14c5c88ac204e000000000000" + "1976a914348514b329fda7bd33c7b2336cf7cd1fc9544c0588ac00000000")

    rt = '01000000013420a0a70bf81cdb4afe531b00fa8fa87ad4c11715df44c624c12816d61e5305010000006b483045022100911c1fe6ff2fe7d6df5070e56b5ada1cb5d8b90200087352fd2b76616e75a06602203b915066d24c0d8393c166d58f7e4b642ecff8e966a52bd6cc14c6f231ccd45c012103f467003ac3c4230d4119d82cc73f329fc6405c65655322c2e27b4f3dd0481616feffffff02ba910000000000001600140c80795fe9dc1f7e902407168962b560c9f7c2f583d88c28000000001976a91488feddfdfb256fa7c077cbc09332d2253d76c83088ac00000000'

    myTxn_forSig = (
    "0100000001a97830933769fe33c6155286ffae34db44c6b8783a2d8ca52ebee6414d399ec300000000" + "1976a914" + "167c74f7491fe552ce9e1912810a984355b8ee07" + "88ac" + "ffffffff02015f0000000000001976a914c8e90996c7c6080ee06284600c684ed904d14c5c88ac204e000000000000" + "1976a914348514b329fda7bd33c7b2336cf7cd1fc9544c0588ac00000000" + "01000000")

    print("raw %s" % rt)
    t = Transaction.import_raw(rt)
    # pprint(t.get())
    t_to_sign = t.raw(signable=True)

    import hashlib
    pub_key = t.input_addresses(return_type='byte')[0]
    hashToSign = hashlib.sha256(hashlib.sha256(t_to_sign).digest()).digest()

    # signature = convert_der_sig(t.inputs[0]['script_sig'][1:])
    signature, pk = parse_script_sig(t.inputs[0]['script_sig'])
    print("Public Key (in sig) %s" % binascii.hexlify(pk))
    print("Public Key %s" % binascii.hexlify(pub_key))
    print("Hash to Sign %s" % binascii.hexlify(hashToSign))
    print("Signature %s" % signature)
    vk = ecdsa.VerifyingKey.from_string(pub_key[1:], curve=ecdsa.SECP256k1)
    vk.verify_digest(binascii.unhexlify(signature), hashToSign)

    # for i in t.inputs:
    #     s = binascii.unhexlify(i['script_sig'])
    #     l = s[0]
    #     sig_der = s[1:l]
    #     l2 = s[l+1]
    #     public_key = binascii.hexlify(s[l+2:l+l2+2]).decode('utf-8')
    #     sig = convert_der_sig(sig_der)
    #
    #     print("Public Key %s" % public_key)
    #     first = '01000000'  # Version bytes in Little-Endian (reversed) format
    #     first += '01'        # Number of UTXO's inputs
    #     first += 'a3919372c9807d92507289d71bdd38f10682a49c47e50dc0136996b43d8aa54e'
    #     first += '01000000'  # Index number of previous transaction
    #     signable_transaction = first + "1976a914" + sig + "88ac" + "01000000"
    #     print(signable_transaction)
    #     import ecdsa
    #     import hashlib
    #     hashToSign = hashlib.sha256(hashlib.sha256(binascii.unhexlify(signable_transaction)).digest()).digest()
    #     # assert (parsed[1][-2:] == '01')  # hashtype
    #     # sig = keyUtils.derSigToHexSig(parsed[1][:-2])
    #     # public_key = parsed[2]
    #     vk = ecdsa.VerifyingKey.from_string(binascii.unhexlify(sig), curve=ecdsa.SECP256k1)
    #     assert (vk.verify_digest(public_key[2:], hashToSign))
    #
    #     pk = Key(import_key=public_key, network='testnet')
    #     pk.info()

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
