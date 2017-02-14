# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Unit Tests for Transaction Class
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

import unittest
import json

from bitcoinlib.transactions import *


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
        pk = Key('cR6pgV8bCweLX1JVN3Q1iqxXvaw4ow9rrp8RenvJcckCMEbZKNtz')  # Private key for import
        inp = Input.add(prev_hash='d3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955', output_index=1,
                        public_key=pk.public(), network='testnet')
        # key for address mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2
        pubkey = Key('0391634874ffca219ff5633f814f7f013f7385c66c65c8c7d81e7076a5926f1a75', network='testnet')
        out = Output.add(880000, public_key_hash=pubkey.hash160(), network='testnet')
        t = Transaction([inp], [out], network='testnet')
        t.sign(pk.private_byte(), 0)
        self.assertTrue(t.verify(), msg="Can not verify transaction '%s'")
        self.assertEqual(t.get()['inputs'][0]['address'], 'n3UKaXBRDhTVpkvgRH7eARZFsYE989bHjw')
        self.assertEqual(t.get()['outputs'][0]['address'], 'mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2')

    def test_transactions_sign_2(self):
        pk = Key('KwbbBb6iz1hGq6dNF9UsHc7cWaXJZfoQGFWeozexqnWA4M7aSwh4')  # Private key for import
        inp = Input.add(prev_hash='fdaa42051b1fc9226797b2ef9700a7148ee8be9466fc8408379814cb0b1d88e3',
                        output_index=1, public_key=pk.public())
        out = Output.add(95000, address='1K5j3KpsSt2FyumzLmoVjmFWVcpFhXHvNF')
        t = Transaction([inp], [out])
        t.sign(pk.private_byte(), 0)
        self.assertTrue(t.verify(), msg="Can not verify transaction '%s'")


class TestTransactionsScriptType(unittest.TestCase):

    def test_transaction_script_type_p2pkh(self):
        s = binascii.unhexlify('76a914af8e14a2cecd715c363b3a72b55b59a31e2acac988ac')
        self.assertEqual('p2pkh', script_type(s))

    def test_transaction_script_type_p2pkh_2(self):
        s = binascii.unhexlify('76a914a13fdfc301c89094f5dc1089e61888794130e38188ac')
        self.assertEqual('p2pkh', script_type(s))

    def test_transaction_script_type_p2sh(self):
        s = binascii.unhexlify('a914e3bdbeab033c7e03fd4cbf3a03ff14533260f3f487')
        self.assertEqual('p2sh', script_type(s))

    def test_transaction_script_type_nulldata(self):
        s = binascii.unhexlify('6a20985f23805edd2938e5bd9f744d36ccb8be643de00b369b901ae0b3fea911a1dd')
        res = script_deserialize(s)
        self.assertEqual('nulldata', res[0])
        self.assertEqual(b'985f23805edd2938e5bd9f744d36ccb8be643de00b369b901ae0b3fea911a1dd',
                         binascii.hexlify(res[1][0]))

    def test_transaction_script_type_nulldata_2(self):
        s = binascii.unhexlify('6a')
        res = script_deserialize(s)
        self.assertEqual('nulldata', res[0])
        self.assertEqual(b'', binascii.hexlify(res[1][0]))

    def test_transaction_script_type_multisig(self):
        s = binascii.unhexlify('514104fcf07bb1222f7925f2b7cc15183a40443c578e62ea17100aa3b44ba66905c95d4980aec4cd2f6e'
                               'b426d1b1ec45d76724f26901099416b9265b76ba67c8b0b73d210202be80a0ca69c0e000b97d507f45b9'
                               '8c49f58fec6650b64ff70e6ffccc3e6d0052ae')
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
        self.assertRaisesRegexp(TransactionError, 'is not an op_n code', script_type, s)

    def test_transaction_script_type_empty_unknown(self):
        res = script_type(b'')
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
            to_string(ds[1][0]), '3044022034519a85fb5299e180865dda936c5d53edabaaf6d15cd1740aac9878b76238e'
                                 '002207345fcb5a62deeb8d9d80e5b412bd24d09151c2008b7fef10eb5f13e484d1e0d01')
        self.assertEqual(
            to_string(ds[1][1]), '0207c9ece04a9b5ef3ff441f3aad6bb63e323c05047a820ab45ebbe61385aa7446')
