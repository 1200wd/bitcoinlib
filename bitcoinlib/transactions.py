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


def transaction_deserialize(rawtx, network=NETWORK_BITCOIN):
    """
    Deserialize a raw transaction

    :param rawtx: Raw transaction as String, Byte or Bytearray
    :param network: Network code, i.e. 'bitcoin', 'testnet', 'litecoin', etc
    :return: json list with inputs, outputs, locktime and version
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


def script_deserialize(script, script_types=None):

    def _parse_signatures(scr, max_signatures=None):
        scr = to_bytes(scr)
        sigs = []
        total_lenght = 0
        while len(scr) and (max_signatures is None or max_signatures > len(sigs)):
            l, sl = varbyteint_to_int(scr[0:9])
            # TODO: Rething and rewrite this:
            if l not in [20, 33, 65, 71, 72, 73]:
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
    _logger.warning("Could not parse script, unrecognized script")
    return ["unknown", '', '', '']


def script_deserialize_sigpk(script):
    _, data, _, _ = script_deserialize(script, 'sig_pubkey')
    # TODO convert_der_sig should return bytes not hexstr
    return convert_der_sig(data[0][:-1]), data[1]


def script_type(script):
    return script_deserialize(script)[0]


def script_to_string(script):
    script = to_bytes(script)
    tp, data, number_of_sigs_m, number_of_sigs_n = script_deserialize(script)
    if tp == "unknown":
        return tp
    sigs = ' '.join([to_string(i) for i in data])

    scriptstr = SCRIPT_TYPES[tp]
    scriptstr = [sigs if x in ['signature', 'multisig', 'return_data'] else x for x in scriptstr]
    scriptstr = [opcodenames[80 + number_of_sigs_m] if x == 'op_m' else x for x in scriptstr]
    scriptstr = [opcodenames[80 + number_of_sigs_n] if x == 'op_n' else x for x in scriptstr]

    return ' '.join(scriptstr)


class Input:

    def __init__(self, prev_hash, output_index, script_sig=b'', sequence=b'\xff\xff\xff\xff', id=0, public_key='',
                 network=NETWORK_BITCOIN):
        self.prev_hash = to_bytes(prev_hash)
        self.output_index = output_index
        if isinstance(output_index, numbers.Number):
            self.output_index = struct.pack('>I', output_index)
        self.script_sig = to_bytes(script_sig)
        self.sequence = to_bytes(sequence)
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
                self.signature, pk2 = script_deserialize_sigpk(script_sig)
            except:
                _logger.warning("Could not parse input script signature")
                pass

        if not public_key and pk2:
            self._public_key = pk2
            self.public_key = to_string(self._public_key)

        if self.public_key:
            self.k = Key(self.public_key, network=network)
            self.public_key_uncompressed = self.k.public_uncompressed()
            self.public_key_hash = self.k.hash160()
            self.address = self.k.address()
            self.compressed = self.k.compressed

    def json(self):
        return {
            'prev_hash': to_string(self.prev_hash),
            'type': self.type,
            'address': self.address,
            'public_key': self.public_key,
            'public_key_hash': self.public_key_hash,
            'output_index': to_string(self.output_index),
            'script_sig': to_string(self.script_sig),
            'sequence': to_string(self.sequence),
        }

    def __repr__(self):
        return str(self.json())


class Output:

    def __init__(self, amount, address='', public_key_hash=b'', public_key=b'', script=b'', network=NETWORK_BITCOIN):
        if not (address or public_key_hash or public_key or script):
            raise TransactionError("Please specify address, script, public key or public key hash when creating output")

        self.amount = amount
        self.script = to_bytes(script)
        self.public_key_hash = to_bytes(public_key_hash)
        self.address = address
        self.public_key = to_bytes(public_key)
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
            ps = script_deserialize(script)
            if ps[0] == 'p2pkh':
                self.public_key_hash = binascii.hexlify(ps[1][0])
                self.address = pubkeyhash_to_addr(ps[1][0], versionbyte=versionbyte)

        if self.script == b'':
            self.script = b'\x76\xa9\x14' + self.public_key_hash + b'\x88\xac'

    def json(self):
        return {
            'amount': self.amount,
            'script': to_string(self.script),
            'public_key': to_string(self.public_key),
            'public_key_hash': to_string(self.public_key_hash),
            'address': self.address,
        }

    def __repr__(self):
        return str(self.json())


class Transaction:

    @staticmethod
    def import_raw(rawtx, network=NETWORK_BITCOIN):
        rawtx = to_bytes(rawtx)
        inputs, outputs, locktime, version = transaction_deserialize(rawtx, network=network)
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
            sighex, pk2 = script_deserialize_sigpk(i.script_sig)
            sig = binascii.unhexlify(sighex)
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

    # ti = Input()

    to = Output(1000, '12ooWd8Xag7hsgP9PBPnmyGe36VeUrpMSH')
    pprint(to)

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
        print("Raw: %s" % to_string(t.raw()))
        pprint(t.get())
        output_script = t.outputs[0].script
        print("\nOutput Script Type: %s " % script_type(output_script))
        print("Output Script String: %s" % script_to_string(output_script))
        print("\nt.verified() ==> %s" % t.verify())

    if True:
        print("\n=== Determine Script Type ===")
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
            print("Deserialized:")
            pprint(script_deserialize(s))
            # print("Script as String: %s" % script_to_string(s))

    # Example based on explanation on
    # http://bitcoin.stackexchange.com/questions/3374/how-to-redeem-a-basic-tx/24580
    if True:
        prev_tx = 'f2b3eb2deb76566e7324307cd47c35eeb88413f971d88519859b1834307ecfec'
        ki = Key(0x18E14A7B6A307F426A94F8114701E7C8E774E7F9A47E2C2035DB29A206321725, compressed=False)
        input = Input(prev_hash=binascii.unhexlify(prev_tx), output_index=1, public_key=ki.public_hex())
        output = Output(amount=99900000, address='1runeksijzfVxyrpiyCY2LCBvYsSiFsCm')
        t = Transaction([input], [output])
        print(binascii.hexlify(t.raw(0)))
        t.sign(ki.private_byte())
        pprint(t.get())
        print(binascii.hexlify(t.raw()))
        print("Verified %s " % t.verify())

    # Example based on
    # http://www.righto.com/2014/02/bitcoins-hard-way-using-raw-bitcoin.html
    if True:
        # Create a new transaction
        ki = Key('5HusYj2b2x4nroApgfvaSfKYZhRbKFH41bVyPooymbC6KfgSXdD', compressed=False)
        txid = "81b4c832d70cb56ff957589752eb4125a4cab78a25a8fc52d6a09e5bd4404d48"
        input = Input(prev_hash=binascii.unhexlify(txid), output_index=0, public_key=ki.public_hex())
        pkh = "c8e90996c7c6080ee06284600c684ed904d14c5c"
        output = Output(amount=91234, public_key_hash=binascii.unhexlify(pkh))
        t = Transaction([input], [output])
        t.sign(ki.private_byte())
        print(binascii.hexlify(t.raw()))
        pprint(t.get())
        print("Verified %s " % t.verify())

    # Create and sign Testnet Transaction using keys from Wallet class 'TestNetWallet' example
    # See txid 71b0bc8669575cebf01110ed9bdb2b015f95ed830aac71720c81880f3935ece7
    if True:
        ki = Key('cR6pgV8bCweLX1JVN3Q1iqxXvaw4ow9rrp8RenvJcckCMEbZKNtz')  # Private key for import
        input = Input(prev_hash='d3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955', output_index=1,
                          public_key=ki.public(), network='testnet')
        # key for address mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2
        ko = Key('0391634874ffca219ff5633f814f7f013f7385c66c65c8c7d81e7076a5926f1a75', network='testnet')
        output = Output(880000, public_key_hash=ko.hash160(), network='testnet')
        t = Transaction([input], [output], network='testnet')
        t.sign(ki.private_byte(), 0)
        pprint(t.get())
        print("Raw Signed Transaction %s" % binascii.hexlify(t.raw()))
        print("Verified %s\n\n\n" % t.verify())

    # Create bitcoin transaction with UTXO, amount, address and private key
    # See txid d99070c63e04a6bdb38b553733838d6196198908c8b8930bec0ba502bc483b72
    if True:
        private_key = 'KwbbBb6iz1hGq6dNF9UsHc7cWaXJZfoQGFWeozexqnWA4M7aSwh4'
        utxo = 'fdaa42051b1fc9226797b2ef9700a7148ee8be9466fc8408379814cb0b1d88e3'
        amount = 95000
        send_to_address = '1K5j3KpsSt2FyumzLmoVjmFWVcpFhXHvNF'

        key_input = Key(private_key)
        utxo_input = Input(prev_hash=utxo, output_index=1, public_key=key_input.public())
        output_to = Output(amount, address=send_to_address)
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

    if True:
        from bitcoinlib.services.bitcoind import BitcoindClient
        bdc = BitcoindClient.from_config()

    if True:
        # Deserialize 1 transaction
        txid = '4d6b58b01522443acec344bab9e709d0ff428fce5cd491b18ce1d076353245ae'
        rt = bdc.getrawtransaction(txid)
        print("- raw %s" % rt)
        t = Transaction.import_raw(rt)
        pprint(t.get())

    # Deserialize transactions in latest block with bitcoind client
    MAX_TRANSACTIONS_VIEW = 0
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
