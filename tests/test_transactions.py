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
        self.assertEqual(res[0], 'multisig')
        self.assertEqual(res[3], 2)

    def test_transaction_script_type_multisig_2(self):
        s = binascii.unhexlify('5121032487c2a32f7c8d57d2a93906a6457afd00697925b0e6e145d89af6d3bca330162102308673d169'
                               '87eaa010e540901cc6fe3695e758c19f46ce604e174dac315e685a52ae')
        res = script_deserialize(s)
        self.assertEqual(res[0], 'multisig')
        self.assertEqual(res[2], 1)

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
        self.assertEqual(script_to_string(s), os)
