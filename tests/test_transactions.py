# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Transaction Class
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

import unittest
import json
from bitcoinlib.transactions import *
from bitcoinlib.keys import HDKey


class TestTransactionInputs(unittest.TestCase):

    def test_transaction_input_add_str(self):
        ph = "81b4c832d70cb56ff957589752eb4125a4cab78a25a8fc52d6a09e5bd4404d48"
        ti = Input(prev_hash=ph, output_index=0)
        self.assertEqual(ph, to_hexstring(ti.prev_hash))

    def test_transaction_input_add_bytes(self):
        ph = "81b4c832d70cb56ff957589752eb4125a4cab78a25a8fc52d6a09e5bd4404d48"
        ti = Input(prev_hash=to_bytes(ph), output_index=0)
        self.assertEqual(ph, to_hexstring(ti.prev_hash))

    def test_transaction_input_add_bytearray(self):
        ph = "81b4c832d70cb56ff957589752eb4125a4cab78a25a8fc52d6a09e5bd4404d48"
        ti = Input(prev_hash=to_bytearray(ph), output_index=0)
        self.assertEqual(ph, to_hexstring(ti.prev_hash))

    def test_transaction_input_add_scriptsig(self):
        ph = b"\xe3>\xbd\x17\x93\x8b\xc0\x13\xc6(\x95\x89*\xacT\xdf?[\xce\x96\xe4K\x89I\x94\x92ut\x1b\x14'\xe5"
        ii = b'\x00\x00\x00\x00'
        ss = b"G0D\x02 l\xa2\x8f{\xaf\xdde\xbd\xfc\x0f\xbd\x88\xf5\xa5\xb0\x03i\x91'\xca\xf0\xff\xf6\xe6U5" \
             b"\xd7\xf11\x15,\x03\x02 \x16\x170?c\x8e\x08\x94\x7f\x18i~\xdc\xb3\xa7\xa5:\xe6m\xf9O&)\xdb\x98" \
             b"\xdc\x0c\xc5\x07k4\xb7\x01!\x020\x9a\x19i\x19\xcf\xf1\xd1\x87T'\x1b\xe7\xeeT\xd1\xb3\x7fAL" \
             b"\xbb)+U\xd7\xed\x1f\r\xc8 \x9d\x13"
        ti = Input(ph, ii, unlocking_script=ss)
        r = {
            'public_key': '02309a196919cff1d18754271be7ee54d1b37f414cbb292b55d7ed1f0dc8209d13',
            'output_index': '00000000',
            'unlocking_script': '47304402206ca28f7bafdd65bdfc0fbd88f5a5b003699127caf0fff6e65535d7f131152c0302201617'
                                '303f638e08947f18697edcb3a7a53ae66df94f2629db98dc0cc5076b34b7012102309a196919cff1d1'
                                '8754271be7ee54d1b37f414cbb292b55d7ed1f0dc8209d13',
            'sequence': 'ffffffff',
            'prev_hash': 'e33ebd17938bc013c62895892aac54df3f5bce96e44b8949949275741b1427e5',
            'tid': 0,
            'address': '1L1Gohs21Xg54MvHuBMbmxhZSNCa1d3Cc2',
            'redeemscript': '',
            'script_type': 'p2pkh'
        }
        self.assertDictEqual(r, ti.json())

    def test_transaction_input_add_coinbase(self):
        ti = Input(b'\0'*32, 0)
        self.assertEqual('coinbase', ti.script_type)

    def test_transaction_input_add_public_key(self):
        ph = 'f2b3eb2deb76566e7324307cd47c35eeb88413f971d88519859b1834307ecfec'
        k = Key(0x18E14A7B6A307F426A94F8114701E7C8E774E7F9A47E2C2035DB29A206321725, compressed=False)
        ti = Input(prev_hash=ph, output_index=1, keys=k.public())
        self.assertEqual('16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM', ti.keys[0].address())


class TestTransactionOutputs(unittest.TestCase):

    def test_transaction_output_add_address(self):
        to = Output(1000, '12ooWd8Xag7hsgP9PBPnmyGe36VeUrpMSH')
        self.assertEqual(b'v\xa9\x14\x13\xd2\x15\xd2\x12\xcdQ\x88\xae\x02\xc5c_\xaa\xbd\xc4\xd7\xd4\xec\x91\x88\xac',
                         to.lock_script)

    def test_transaction_output_add_public_key(self):
        to = Output(1000000000, public_key='0450863AD64A87AE8A2FE83C1AF1A8403CB53F53E486D8511DAD8A04887E5B23522CD470'
                                           '243453A299FA9E77237716103ABC11A1DF38855ED6F2EE187E9C582BA6')
        self.assertEqual(b"v\xa9\x14\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee\x88\xac",
                         to.lock_script)

    def test_transaction_output_add_public_key_hash(self):
        to = Output(1000, public_key_hash='010966776006953d5567439e5e39f86a0d273bee')
        self.assertEqual(b"v\xa9\x14\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee\x88\xac",
                         to.lock_script)

    def test_transaction_output_add_script(self):
        to = Output(1000, lock_script='76a91423e102597c4a99516f851406f935a6e634dbccec88ac')
        self.assertEqual('14GiCdJHj3bznWpcocjcu9ByCmDPEhEoP8', to.address)


class TestTransactions(unittest.TestCase):

    def setUp(self):
        workdir = os.path.dirname(__file__)
        with open('%s/%s' % (workdir, 'transactions_raw.json'), 'r') as f:
            d = json.load(f)
        self.rawtxs = d['transactions']

    def test_transactions_deserialize_raw(self):
        for r in self.rawtxs:
            print("Deserialize %s" % r[0])
            t = Transaction.import_raw(r[1], r[4])
            self.assertEqual(len(t.inputs), r[2], msg="Incorrect numbers of inputs for tx '%s'" % r[0])
            self.assertEqual(len(t.outputs), r[3], msg="Incorrect numbers of outputs for tx '%s'" % r[0])

    def test_transactions_deserialize_raw_unicode(self):
        rawtx = u'01000000012ba87637d74080d041795915f843484523f7693ac1f1b359771b751acd2fef79010000006a4730440220722' \
                u'7634b962914c3310c6f71fb37c25ad64f239aead11a1a1e2de8b6d95d4de6022072d3841de897be38bd9ae0067e059bd7' \
                u'ad6947ae3731d97823801c09e00a70be0121033ef5447f54712d6a1aba7e77ad9f09ab77c21c84d1811a1b82a96fa08d9' \
                u'733deffffffff02be9d9600000000001976a914b66e314587c282d5ce290918228e390c0279884688ace280590b0b0000' \
                u'001976a914f2ea76adc2345f3591ce997def9043fbe68ecc1a88ac00000000'
        self.assertEqual('1P9RQEr2XeE3PEb44ZE35sfZRRW1JHU8qx',
                         Transaction.import_raw(rawtx).get()['outputs'][1]['address'])

    def test_transactions_deserialize_raw_bytearray(self):
        rawtx = bytearray(b'0100000001685c7c35aabe690cc99f947a8172ad075d4401448a212b9f26607d6ec5530915010000006a4730'
                          b'440220337117278ee2fc7ae222ec1547b3a40fa39a05f91c1e19db60060541c4b3d6e4022020188e1d5d843c'
                          b'045ddac78c42ed9ff6a1078414d15a9f065495628fde9d1e55012102d04293c65effbea9d61727374612820d'
                          b'192cd6d04f106a62c6a6768719de41dcffffffff026804ab01000000001976a914cf75d22e78c86e2e3d29f7'
                          b'a772f8ffd62391190388ac442d0304000000001976a9145b92b92ddd598d2d4977b3c4e5f552332aed743188'
                          b'ac00000000')
        print(rawtx)
        self.assertEqual('19MCFyVmyEhFjYNS8aKJT454jm4YZQjbqm',
                         Transaction.import_raw(rawtx).get()['outputs'][1]['address'])

    def test_transactions_verify_signature(self):
        for r in self.rawtxs:
            print("Verify %s" % r[0])
            t = Transaction.import_raw(r[1], r[4])
            if len(t.inputs) < 5:
                self.assertTrue(t.verify(), msg="Can not verify transaction '%s'" % r[0])

    def test_transactions_serialize_raw(self):
        for r in self.rawtxs:
            print("Serialize %s" % r[0])
            t = Transaction.import_raw(r[1], r[4])
            self.assertEqual(binascii.hexlify(t.raw()).decode(), r[1])

    def test_transactions_sign_1(self):
        pk = Key('cR6pgV8bCweLX1JVN3Q1iqxXvaw4ow9rrp8RenvJcckCMEbZKNtz', network='testnet')  # Private key for import
        inp = Input(prev_hash='d3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955', output_index=1,
                    keys=pk.public(), network='testnet')
        # key for address mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2
        pubkey = Key('0391634874ffca219ff5633f814f7f013f7385c66c65c8c7d81e7076a5926f1a75', network='testnet')
        out = Output(880000, public_key_hash=pubkey.hash160(), network='testnet')
        t = Transaction([inp], [out], network='testnet')
        t.sign(pk.private_byte)
        self.assertTrue(t.verify(), msg="Can not verify transaction '%s'")
        self.assertEqual(t.get()['inputs'][0]['address'], 'n3UKaXBRDhTVpkvgRH7eARZFsYE989bHjw')
        self.assertEqual(t.get()['outputs'][0]['address'], 'mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2')

    def test_transactions_sign_2(self):
        pk = Key('KwbbBb6iz1hGq6dNF9UsHc7cWaXJZfoQGFWeozexqnWA4M7aSwh4')  # Private key for import
        inp = Input(prev_hash='fdaa42051b1fc9226797b2ef9700a7148ee8be9466fc8408379814cb0b1d88e3',
                    output_index=1, keys=pk.public())
        out = Output(95000, address='1K5j3KpsSt2FyumzLmoVjmFWVcpFhXHvNF')
        t = Transaction([inp], [out])
        t.sign(pk.private_byte)
        self.assertTrue(t.verify(), msg="Can not verify transaction '%s'")

    def test_transactions_multiple_outputs(self):
        t = Transaction()
        t.add_output(2710000, '12ooWd8Xag7hsgP9PBPnmyGe36VeUrpMSH')
        t.add_output(2720000, '1D1gLEHsvjunpJxqjkWcPZqU4QzzRrHDdL')
        t.add_output(2730000, '15pV2dYQAWeahtTVGAzDeX1K1ndqgRU2go')
        t.add_input('82b48b128232256d1d5ce0c6ae7f7897f2b464d44456c25d7cf2be51626530d9', 0)
        self.assertEqual(3, len(t.outputs))

    def test_transactions_sign_multiple_inputs(self):
        # Two private keys with 1 UTXO on the blockchain each
        wif1 = 'xprvA3PZhxgsb5cogy52pm8eJf21gW2epoetxdCZxpmBWddViHmB7wgR4apQVxRHmyngapZ14pBzWSCP6sztWn8EaMmnwZaj' \
               'fs7oS6rZDYdnrwh'
        wif2 = 'xprvA3PZhxgsb5cojKHWdGGFBNut51QbAe5arWb7s7cJ9cT6zThQJFvYKKZDcmFirWJVVHgRYzqLc9XnuDMrP3Qwy8sK8Zu5' \
               'MisgvXVtGdwDhrH'

        # Create inputs with a UTXO with 2 unspent outputs which corresponds to this private keys
        utxo_hash = '0177ac29fa8b2960051321c730c6f15017503aa5b9c1dd2d61e7286e366fbaba'
        pk1 = HDKey(wif1)
        pk2 = HDKey(wif2)
        input1 = Input(prev_hash=utxo_hash, output_index=0, keys=pk1.public_byte, tid=0)
        input2 = Input(prev_hash=utxo_hash, output_index=1, keys=pk2.public_byte, tid=1)

        # Create a transaction with 2 inputs, and add 2 outputs below
        osm_address = '1J3pt9koWJZTo2jarg98RL89iJqff9Kobp'
        change_address = '1Ht9iDJ3FjwweQNuj451QVL6RAP5qxadFb'
        output1 = Output(amount=900000, address=osm_address)
        output2 = Output(amount=150000, address=change_address)
        t = Transaction(inputs=[input1, input2], outputs=[output1, output2])

        # Sign the inputs and verify
        # See txid 1ec28c925df0079ead9976d38165909ccb3580a428ce069ee13e63879df0c2fc
        t.sign(pk1.private_byte, 0)
        t.sign(pk2.private_byte, 1)
        self.assertTrue(t.verify())


class TestTransactionsScriptType(unittest.TestCase):

    def test_transaction_script_type_p2pkh(self):
        s = binascii.unhexlify('76a914af8e14a2cecd715c363b3a72b55b59a31e2acac988ac')
        self.assertEqual('p2pkh', script_deserialize(s)[0])

    def test_transaction_script_type_p2pkh_2(self):
        s = binascii.unhexlify('76a914a13fdfc301c89094f5dc1089e61888794130e38188ac')
        self.assertEqual('p2pkh', script_deserialize(s)[0])

    def test_transaction_script_type_p2sh(self):
        s = binascii.unhexlify('a914e3bdbeab033c7e03fd4cbf3a03ff14533260f3f487')
        self.assertEqual('p2sh', script_deserialize(s)[0])

    def test_transaction_script_type_nulldata(self):
        s = binascii.unhexlify('6a20985f23805edd2938e5bd9f744d36ccb8be643de00b369b901ae0b3fea911a1dd')
        res = script_deserialize(s)
        self.assertEqual('nulldata', res[0])
        self.assertEqual(b'20985f23805edd2938e5bd9f744d36ccb8be643de00b369b901ae0b3fea911a1dd',
                         binascii.hexlify(res[1][0]))

    def test_transaction_script_type_nulldata_2(self):
        s = binascii.unhexlify('6a')
        res = script_deserialize(s)
        self.assertEqual('nulldata', res[0])
        self.assertEqual(b'', binascii.hexlify(res[1][0]))

    def test_transaction_script_type_multisig(self):
        s = '514104fcf07bb1222f7925f2b7cc15183a40443c578e62ea17100aa3b44ba66905c95d4980aec4cd2f6eb426d1b1ec45d76724f' \
            '26901099416b9265b76ba67c8b0b73d210202be80a0ca69c0e000b97d507f45b98c49f58fec6650b64ff70e6ffccc3e6d0052ae'
        res = script_deserialize(s)
        self.assertEqual('multisig', res[0])
        self.assertEqual(2, res[3])

    def test_transaction_script_type_multisig_2(self):
        s = binascii.unhexlify('5121032487c2a32f7c8d57d2a93906a6457afd00697925b0e6e145d89af6d3bca330162102308673d169'
                               '87eaa010e540901cc6fe3695e758c19f46ce604e174dac315e685a52ae')
        res = script_deserialize(s)
        self.assertEqual('multisig', res[0])
        self.assertEqual(1, res[2])

    def test_transaction_script_type_multisig_error_count(self):
        s = binascii.unhexlify('51'
                               '4104fcf07bb1222f7925f2b7cc15183a40443c578e62ea17100aa3b44ba66905c95d4980aec4cd2f6eb426'
                               'd1b1ec45d76724f26901099416b9265b76ba67c8b0b73d'
                               '210202be80a0ca69c0e000b97d507f45b98c49f58fec6650b64ff70e6ffccc3e6d00'
                               '210202be80a0ca69c0e000b97d507f45b98c49f58fec6650b64ff70e6ffccc3e6d0052ae')
        self.assertRaisesRegexp(TransactionError, '3 signatures found, but 2 sigs expected',
                                script_deserialize, s)

    def test_transaction_script_type_multisig_error(self):
        s = binascii.unhexlify('5123032487c2a32f7c8d57d2a93906a6457afd00697925b0e6e145d89af6d3bca330162102308673d169')
        self.assertRaisesRegexp(TransactionError, 'is not an op_n code', script_deserialize, s)

    def test_transaction_script_type_empty_unknown(self):
        res = script_deserialize(b'')[0]
        self.assertEqual('empty', res)

    def test_transaction_script_type_string(self):
        s = binascii.unhexlify('5121032487c2a32f7c8d57d2a93906a6457afd00697925b0e6e145d89af6d3bca330162102308673d169'
                               '87eaa010e540901cc6fe3695e758c19f46ce604e174dac315e685a52ae')
        os = "OP_1 032487c2a32f7c8d57d2a93906a6457afd00697925b0e6e145d89af6d3bca33016 " \
             "02308673d16987eaa010e540901cc6fe3695e758c19f46ce604e174dac315e685a OP_2 OP_CHECKMULTISIG"
        self.assertEqual(os, str(script_to_string(s)))

    def test_transaction_script_deserialize_sig_pk(self):
        spk = '493046022100cf4d7571dd47a4d47f5cb767d54d6702530a3555726b27b6ac56117f5e7808fe0221008cbb42233bb04d7f28a' \
              '715cf7c938e238afde90207e9d103dd9018e12cb7180e0141042daa93315eebbe2cb9b5c3505df4c6fb6caca8b75678609856' \
              '7550d4820c09db988fe9997d049d687292f815ccd6e7fb5c1b1a91137999818d17c73d0f80aef9'
        ds = script_deserialize(spk)
        self.assertEqual(ds[0], 'sig_pubkey')
        self.assertEqual(ds[1][0], bytearray(b"0F\x02!\x00\xcfMuq\xddG\xa4\xd4\x7f\\\xb7g\xd5Mg\x02S\n5Urk\'\xb6\xacV"
                                             b"\x11\x7f^x\x08\xfe\x02!\x00\x8c\xbbB#;\xb0M\x7f(\xa7\x15\xcf|\x93\x8e#"
                                             b"\x8a\xfd\xe9\x02\x07\xe9\xd1\x03\xdd\x90\x18\xe1,\xb7\x18\x0e\x01"))
        self.assertEqual(ds[1][1], bytearray(b'\x04-\xaa\x931^\xeb\xbe,\xb9\xb5\xc3P]\xf4\xc6\xfbl\xac\xa8\xb7Vx`\x98'
                                             b'VuP\xd4\x82\x0c\t\xdb\x98\x8f\xe9\x99}\x04\x9dhr\x92\xf8\x15\xcc\xd6'
                                             b'\xe7\xfb\\\x1b\x1a\x91\x13y\x99\x81\x8d\x17\xc7=\x0f\x80\xae\xf9'))

    def test_transaction_script_deserialize_sig_pk2(self):
        spk = '473044022034519a85fb5299e180865dda936c5d53edabaaf6d15cd1740aac9878b76238e002207345fcb5a62deeb8d9d80e5' \
              'b412bd24d09151c2008b7fef10eb5f13e484d1e0d01210207c9ece04a9b5ef3ff441f3aad6bb63e323c05047a820ab45ebbe6' \
              '1385aa7446'
        ds = script_deserialize(spk)
        self.assertEqual(ds[0], 'sig_pubkey')
        self.assertEqual(
            to_hexstring(ds[1][0]), '3044022034519a85fb5299e180865dda936c5d53edabaaf6d15cd1740aac9878b76238e'
                                    '002207345fcb5a62deeb8d9d80e5b412bd24d09151c2008b7fef10eb5f13e484d1e0d01')
        self.assertEqual(
            to_hexstring(ds[1][1]), '0207c9ece04a9b5ef3ff441f3aad6bb63e323c05047a820ab45ebbe61385aa7446')
