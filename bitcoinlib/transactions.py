# -*- coding: utf-8 -*-
#
#    bitcoinlib Transactions
#    © 2017 February - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.keys import Key, BKeyError
from bitcoinlib.main import *
from bitcoinlib.config.networks import *


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


def deserialize_transaction(rawtx, network=NETWORK_BITCOIN):
    """
    Deserialize a raw transaction

    :param rawtx: Raw transaction as String, Byte or Bytearray
    :param network: Network code, i.e. 'bitcoin', 'testnet', 'litecoin', etc
    :return: json list with inputs, outputs, locktime and version
    """
    rawtx = to_bytearray(rawtx)
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
        inputs.append(Input(prev_hash=inp_hash, output_index=inp_index, script_sig=scriptsig,
                            sequence=sequence_number, id=i, network=network))
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
        outputs.append(Output(amount=amount, script=script, network=network))
    if not outputs:
        raise TransactionError("Error no outputs found in this transaction")
    locktime = change_base(rawtx[cursor:cursor + 4][::-1], 256, 10)

    return inputs, outputs, locktime, version


def parse_script_sig(s):
    s = to_bytearray(s)
    if not s:
        _logger.warning("Parsing empty script sig in 'parse_script_sig(s)")
        return "", ""
    sig_size, size = varbyteint_to_int(s[0:9])
    sig = convert_der_sig(s[1:sig_size])
    cur = size+sig_size
    pk_size, size = varbyteint_to_int(s[cur:cur+9])
    public_key = s[cur+size:cur+size+pk_size]
    return sig, public_key


def _parse_signatures(script, max_signatures=None):
    if not isinstance(script, bytearray):
        raise TransactionError("Method '_parse_signatures' needs script in ByteArray format")
    script = to_bytearray(script)
    data = []
    total_lenght = 0
    count = 0
    while len(script) and (max_signatures is None or max_signatures > count):
        l, _ = varbyteint_to_int(script[0:9])
        if l not in [20, 33, 65]:
            break
        data.append(script[1:l+1])
        total_lenght += l + 1
        script = script[l+1:]
        count += 1
    return data, total_lenght


def output_script_parse(script):
    script = to_bytearray(script)
    if not script:
        return ["empty", '', '', '']

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
                s, total_length = _parse_signatures(script[cur:], 1)
                data += s
                cur += total_length
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
    _logger.warning("Could not parse script, unrecognized script")
    return ["unknown", '', '', '']


def output_script_type(script):
    return output_script_parse(script)[0]


def script_to_string(script):
    script = to_bytearray(script)
    tp, data, number_of_sigs_m, number_of_sigs_n = output_script_parse(script)
    sigs = ' '.join([binascii.hexlify(i).decode('utf-8') for i in data])

    scriptstr = OUTPUT_SCRIPT_TYPES[tp]
    scriptstr = [sigs if x in ['signature', 'multisig', 'return_data'] else x for x in scriptstr]
    scriptstr = [opcodenames[80 + number_of_sigs_m] if x == 'op_m' else x for x in scriptstr]
    scriptstr = [opcodenames[80 + number_of_sigs_n] if x == 'op_n' else x for x in scriptstr]

    return ' '.join(scriptstr)


class Input:

    @staticmethod
    def add(prev_hash, output_index=0, script_sig=b'', public_key='', network=NETWORK_BITCOIN):
        prev_hash = to_bytearray(prev_hash)
        if isinstance(output_index, numbers.Number):
            output_index = struct.pack('>I', output_index)
        return Input(prev_hash, output_index, script_sig=script_sig, public_key=public_key, network=network)

    def __init__(self, prev_hash, output_index, script_sig, sequence=b'\xff\xff\xff\xff', id=0, public_key='',
                 network=NETWORK_BITCOIN):
        self.prev_hash = prev_hash
        self.output_index = output_index
        self.script_sig = script_sig
        self.sequence = sequence
        self.id = id
        self.public_key = public_key

        self.signature = b''
        self._public_key = b''
        self.compressed = True
        self.public_key_uncompressed = ''
        self.k = None
        self.public_key_hash = ''
        self.address = ''
        self.type = ''

        if prev_hash == b'\0' * 32:
            self.type = 'coinbase'
        pk2 = b''
        if script_sig and self.type != 'coinbase':
            try:
                self.signature, pk2 = parse_script_sig(script_sig)
            except:
                _logger.warning("Could not parse input script signature")
                pass

        if not public_key and pk2:
            self._public_key = pk2
            self.public_key = binascii.hexlify(self._public_key).decode('utf-8')

        if self.public_key:
            self.k = Key(self.public_key, network=network)
            self.public_key_uncompressed = self.k.public_uncompressed()
            self.public_key_hash = self.k.hash160()
            self.address = self.k.address()
            self.compressed = self.k.compressed

    def json(self):
        return {
            'prev_hash': binascii.hexlify(self.prev_hash).decode('utf-8'),
            'type': self.type,
            'address': self.address,
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
    def add(amount, public_key_hash=b'', address='', network=NETWORK_BITCOIN):
        if not isinstance(public_key_hash, bytes):
            public_key_hash = binascii.unhexlify(public_key_hash)
        return Output(amount, public_key_hash=public_key_hash, address=address, network=network)

    def __init__(self, amount, script=b'', public_key_hash=b'', address='', public_key=b'', network=NETWORK_BITCOIN):
        self.amount = amount
        self.script = script
        self.public_key_hash = public_key_hash
        self.address = address
        self.public_key = public_key
        self.network = network

        self.compressed = True
        self.k = None
        versionbyte = NETWORKS[self.network]['address']

        if public_key:
            self.k = Key(binascii.hexlify(public_key).decode('utf-8'), network=network)
            self.address = self.k.address()
            self.compressed = self.k.compressed
        if public_key_hash:
            self.address = pubkeyhash_to_addr(public_key_hash, versionbyte=versionbyte)
        if address and not public_key_hash:
            self.public_key_hash = addr_to_pubkeyhash(address)
        if not public_key_hash and self.k:
            self.public_key_hash = self.k.hash160()

        if script and not self.public_key_hash:
            ps = output_script_parse(script)
            if ps[0] == 'p2pkh':
                self.public_key_hash = binascii.hexlify(ps[1][0])
                self.address = pubkeyhash_to_addr(ps[1][0], versionbyte=versionbyte)

        if self.script == b'':
            self.script = b'\x76\xa9\x14' + self.public_key_hash + b'\x88\xac'

    def json(self):
        return {
            'amount': self.amount,
            'script': binascii.hexlify(self.script).decode('utf-8'),
            'public_key': binascii.hexlify(self.public_key).decode('utf-8'),
            'public_key_hash': self.public_key_hash,
            'address': self.address,
        }

    def __repr__(self):
        return str(self.json())


class Transaction:

    @staticmethod
    def import_raw(rawtx, network=NETWORK_BITCOIN):
        rawtx = to_bytearray(rawtx)
        inputs, outputs, locktime, version = deserialize_transaction(rawtx, network=network)
        return Transaction(inputs, outputs, locktime, version, rawtx, network)

    def __init__(self, inputs, outputs, locktime=0, version=b'\x00\x00\x00\x01', rawtx=b'', network=NETWORK_BITCOIN):
        self.inputs = inputs
        self.outputs = outputs
        self.version = version
        self.locktime = locktime
        self.rawtx = rawtx
        self.network = network
        if not self.rawtx:
            self.rawtx = self.raw()

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
            # pk = binascii.unhexlify(i.public_key[2:])
            sighex, pk2 = parse_script_sig(i.script_sig)
            sig = binascii.unhexlify(sighex)
            # sig = binascii.unhexlify(i.signature)
            # pk3 = binascii.unhexlify(Key(pk2).public_uncompressed())[1:]
            vk = ecdsa.VerifyingKey.from_string(pk, curve=ecdsa.SECP256k1)
            try:
                vk.verify_digest(sig, hashtosign)
            except ecdsa.keys.BadDigestError as e:
                _logger.info("Bad Signature %s (error %s)" % (sig, e))
                return False
        return True

    def sign(self, priv_key, id=0):
        sig = hashlib.sha256(hashlib.sha256(self.raw(id)).digest()).digest()
        sk = ecdsa.SigningKey.from_string(priv_key, curve=ecdsa.SECP256k1)
        sig_der = sk.sign_digest(sig, sigencode=ecdsa.util.sigencode_der) + b'\01'  # 01 is hashtype
        k = Key(priv_key)
        # pub_key = binascii.unhexlify(k.public_uncompressed())
        pub_key = binascii.unhexlify(k.public())
        self.inputs[id].script_sig = varstr(sig_der) + varstr(pub_key)
        self.inputs[id].signature = binascii.hexlify(sig)
        # self.inputs[id].public_key = pub_key


if __name__ == '__main__':
    from pprint import pprint

    # Example of a basic raw transaction with 1 input and 2 outputs
    # (destination and change address).
    if True:
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

    if False:
        print("\n=== Determine Output Script Type ===")
        os = '6a20985f23805edd2938e5bd9f744d36ccb8be643de00b369b901ae0b3fea911a1dd'
        print("Output Script: %s" % os)
        print("Output Script String: %s" % script_to_string(os))
        os = '5121032487c2a32f7c8d57d2a93906a6457afd00697925b0e6e145d89af6d3bca330162102308673d16987eaa010e540901cc6' \
             'fe3695e758c19f46ce604e174dac315e685a52ae'
        print("\nOutput Script: %s" % os)
        print("Output Script String: %s" % script_to_string(os))
        s = binascii.unhexlify('514104fcf07bb1222f7925f2b7cc15183a40443c578e62ea17100aa3b44ba66905c95d4980aec4cd2f6e'
                               'b426d1b1ec45d76724f26901099416b9265b76ba67c8b0b73d210202be80a0ca69c0e000b97d507f45b9'
                               '8c49f58fec6650b64ff70e6ffccc3e6d0052ae')
        res = output_script_parse(s)

    # Example based on explanation on
    # http://bitcoin.stackexchange.com/questions/3374/how-to-redeem-a-basic-tx/24580
    if False:
        prev_tx = 'f2b3eb2deb76566e7324307cd47c35eeb88413f971d88519859b1834307ecfec'
        ki = Key(0x18E14A7B6A307F426A94F8114701E7C8E774E7F9A47E2C2035DB29A206321725, compressed=False)
        input = Input.add(prev_hash=binascii.unhexlify(prev_tx), output_index=1, public_key=ki.public_hex())
        output = Output.add(amount=99900000, address='1runeksijzfVxyrpiyCY2LCBvYsSiFsCm')
        t = Transaction([input], [output])
        print(binascii.hexlify(t.raw(0)))
        t.sign(ki.private_byte())
        pprint(t.get())
        print(binascii.hexlify(t.raw()))
        print("Verified %s " % t.verify())

    # Example based on
    # http://www.righto.com/2014/02/bitcoins-hard-way-using-raw-bitcoin.html
    if False:
        # Create a new transaction
        ki = Key('5HusYj2b2x4nroApgfvaSfKYZhRbKFH41bVyPooymbC6KfgSXdD', compressed=False)
        txid = "81b4c832d70cb56ff957589752eb4125a4cab78a25a8fc52d6a09e5bd4404d48"
        input = Input.add(prev_hash=binascii.unhexlify(txid), output_index=0, public_key=ki.public_hex())
        pkh = "c8e90996c7c6080ee06284600c684ed904d14c5c"
        output = Output.add(amount=91234, public_key_hash=binascii.unhexlify(pkh))
        t = Transaction([input], [output])
        t.sign(ki.private_byte())
        print(binascii.hexlify(t.raw()))
        pprint(t.get())
        print("Verified %s " % t.verify())

    # Create and sign Testnet Transaction using keys from Wallet class 'TestNetWallet' example
    # See txid 71b0bc8669575cebf01110ed9bdb2b015f95ed830aac71720c81880f3935ece7
    if False:
        ki = Key('cR6pgV8bCweLX1JVN3Q1iqxXvaw4ow9rrp8RenvJcckCMEbZKNtz')  # Private key for import
        input = Input.add(prev_hash='d3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955', output_index=1,
                          public_key=ki.public(), network='testnet')
        # key for address mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2
        ko = Key('0391634874ffca219ff5633f814f7f013f7385c66c65c8c7d81e7076a5926f1a75', network='testnet')
        output = Output.add(880000, public_key_hash=ko.hash160(), network='testnet')
        t = Transaction([input], [output], network='testnet')
        t.sign(ki.private_byte(), 0)
        pprint(t.get())
        print("Raw Signed Transaction %s" % binascii.hexlify(t.raw()))
        print("Verified %s\n\n\n" % t.verify())

    # Create bitcoin transaction with UTXO, amount, address and private key
    # See txid d99070c63e04a6bdb38b553733838d6196198908c8b8930bec0ba502bc483b72
    if False:
        private_key = 'KwbbBb6iz1hGq6dNF9UsHc7cWaXJZfoQGFWeozexqnWA4M7aSwh4'
        utxo = 'fdaa42051b1fc9226797b2ef9700a7148ee8be9466fc8408379814cb0b1d88e3'
        amount = 95000
        send_to_address = '1K5j3KpsSt2FyumzLmoVjmFWVcpFhXHvNF'

        key_input = Key(private_key)
        utxo_input = Input.add(prev_hash=utxo, output_index=1, public_key=key_input.public())
        output_to = Output.add(amount, address=send_to_address)
        t = Transaction([utxo_input], [output_to])
        t.sign(key_input.private_byte(), 0)
        pprint(t.get())
        print("Raw Signed Transaction %s" % binascii.hexlify(t.raw()))
        print("Verified %s\n\n\n" % t.verify())

        # from bitcoinlib.services.bitcoind import BitcoindClient
        # bdc = BitcoindClient.from_config()
        # try:
        #     res = bdc.proxy.sendrawtransaction(binascii.hexlify(t.raw()).decode('utf-8'))
        #     print("Send raw transaction, result %s" % res)
        # except Exception as e:
        #     print("Error sending Transaction.", e)

    #
    # === TRANSACTIONS AND BITCOIND EXAMPLES
    #

    from bitcoinlib.services.bitcoind import BitcoindClient
    bdc = BitcoindClient.from_config()

    if False:
        # Deserialize 1 transaction
        txid = '4d6b58b01522443acec344bab9e709d0ff428fce5cd491b18ce1d076353245ae'
        rt = bdc.getrawtransaction(txid)
        print("- raw %s" % rt)
        t = Transaction.import_raw(rt)
        pprint(t.get())

    # Deserialize transactions in latest block with bitcoind client
    MAX_TRANSACTIONS_VIEW = 1
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
            print("[%d/%d] Deserialize txid %s" % (ci, ct, txid))
            try:
                rt = bdc.getrawtransaction(txid)
            except Exception as e:
                print("Error fetching transaction", e)
                error_count += 1
                pass
            print("- raw %s" % rt)
            try:
                t = Transaction.import_raw(rt)
            except BKeyError as e:
                print("Error when importing raw transaction", e)
                error_count += 1
                continue

            pprint(t.get())
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
