# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Transaction Class
#    © 2019 November - 1200 Web Development <http://1200wd.com/>
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
import pickle
from bitcoinlib.blocks import *
from tests.test_custom import CustomAssertions


class TestBlocks(unittest.TestCase, CustomAssertions):

    def setUp(self):
        if not PY3:
            self.skipTest("Python 2 not supported for Blocks unittest")

        filename = os.path.join(os.path.dirname(__file__), "block250000.pickle")
        pickle_in = open(filename, "rb")
        self.rb250000 = pickle.load(pickle_in)
        pickle_in.close()

        filename = os.path.join(os.path.dirname(__file__), "block330000.pickle")
        pickle_in = open(filename, "rb")
        self.rb330000 = pickle.load(pickle_in)
        pickle_in.close()

    def test_blocks_parse_genesis(self):
        raw_block = '0100000000000000000000000000000000000000000000000000000000000000000000003ba3edfd7a7b12b27ac72c3' \
                    'e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a29ab5f49ffff001d1dac2b7c010100000001000000000000000000' \
                    '0000000000000000000000000000000000000000000000ffffffff4d04ffff001d0104455468652054696d657320303' \
                    '32f4a616e2f32303039204368616e63656c6c6f72206f6e206272696e6b206f66207365636f6e64206261696c6f7574' \
                    '20666f722062616e6b73ffffffff0100f2052a01000000434104678afdb0fe5548271967f1a67130b7105cd6a828e03' \
                    '909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5fac00000000'
        b = Block.from_raw(to_bytes(raw_block), height=0)
        self.assertEqual(to_hexstring(b.block_hash), '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f')
        self.assertEqual(b.height, 0)
        self.assertEqual(b.version_int, 1)
        self.assertEqual(b.prev_block, 32 * b'\x00')
        self.assertEqual(to_hexstring(b.merkle_root), '4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b')
        self.assertEqual(to_hexstring(b.bits), '1d00ffff')
        self.assertEqual(b.time, 1231006505)
        self.assertEqual(to_hexstring(b.nonce), '7c2bac1d')
        self.assertEqual(b.difficulty, 1)
        self.assertEqual(b.target_hex, '00000000ffff0000000000000000000000000000000000000000000000000000')
        self.assertEqual(b.tx_count, 1)
        self.assertEqual(str(b),
                         '<Block(000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f, 0, transactions: 1)>')

    def test_blocks_create_block(self):
        block_hash = '00000000000023b05c9ae15577257daf17029604eba0a58824e93306e44d0c62'
        height = 123123
        version = 1
        merkle_root = '37495012489500f0c7ca8bf5bfa116cc8cf46d34214cfbd3b73f6d84d4e667f0'
        prev_block = '000000000000668a34cfab030cf33b865cf3f5eaac46c70f665b70524528f078'
        bits = 443192243
        time = 1305042430
        nonce = 3568752398
        b = Block(block_hash, version, prev_block, merkle_root, time, bits, nonce, height=height)
        expected_dict = {'block_hash': '00000000000023b05c9ae15577257daf17029604eba0a58824e93306e44d0c62',
                         'height': 123123, 'version': 1,
                         'prev_block': '000000000000668a34cfab030cf33b865cf3f5eaac46c70f665b70524528f078',
                         'merkle_root': '37495012489500f0c7ca8bf5bfa116cc8cf46d34214cfbd3b73f6d84d4e667f0',
                         'timestamp': 1305042430, 'bits': 443192243, 'nonce': 3568752398,
                         'target': '0000000000006a93b30000000000000000000000000000000000000000000000',
                         'difficulty': 157416.40184364893}
        self.assertDictEqualExt(b.as_dict(), expected_dict)

    def test_blocks_parse_block_and_transactions(self):
        b = Block.from_raw(self.rb250000, parse_transactions=True)
        self.assertEqual(to_hexstring(b.block_hash), '000000000000003887df1f29024b06fc2200b55f8af8f35453d7be294df2d214')
        self.assertEqual(b.height, 250000)
        self.assertEqual(b.version_int, 2)
        self.assertEqual(b.prev_block, to_bytes('0000000000000009c2e82d884ec07b4aafb64ca3ef83baca2b6b0b5eb72c8f02'))
        self.assertEqual(b.merkle_root, to_bytes('16ec1eafaca8ca59d182cbf94f29b50b06ac4207b883f380b9bf547fe8fed723'))
        self.assertEqual(b.bits_int, 0x1972dbf2)
        self.assertEqual(b.time, 1375533383)
        self.assertEqual(b.nonce_int, 0x917661)
        self.assertEqual(int(b.difficulty), 37392766)
        self.assertEqual(b.target, 720982641204331278205950312227594303241470815982254303477760)
        self.assertEqual(b.tx_count, 156)
        self.assertEqual(b.transactions[0].txid, '7ae2ab185a6e501753f6e29e5b6a98ba040098acb7c11ffed9430f22ed5263a3')
        self.assertEqual(b.transactions[49].txid, '3b6d97f107cba804270f4d22fafda3295b3bfb735366da6c1473157cc94a5f7c')
        self.assertEqual(b.transactions[122].txid, 'a5cc9bd850b6eedc3e466b3e0f5c85fb640de0a3537259eb0cae761d0a4f78b4')
        self.assertEqual(b.transactions[155].txid, 'e3d6cb87bd37ca53509cdc9ecdabf82ef966d9b25a2598b7de87c8173beb40d5')
        self.assertTrue(b.check_proof_of_work())

    def test_blocks_parse_block_exceptions(self):
        self.assertRaisesRegex(ValueError, "Specified block height is different than calculated block height "
                               "according to BIP0034", Block.from_raw, self.rb250000, parse_transactions=False,
                               height=100)
        self.assertRaisesRegex(ValueError, "Provided block hash does not correspond to calculated block hash "
                                           "000000000000003887df1f29024b06fc2200b55f8af8f35453d7be294df2d214",
                               Block.from_raw, self.rb250000, parse_transactions=False,
                               block_hash='000000000000003887df1f29024b06fc2200b55f8af8f35453d7be294df2d214')
        incomplete_raw = '010000008a27a4849da1fea18e8f062e7948eb839ca3665d0b129d8095e1ea1a0000000049460f6df908fdf763' \
                         '4a5e73a984cf49e0555ba5066d52ffacaf5c892b2d3aeeeca7c04b15112a1cf36e610303010000000100000000' \
                         '00000000000000000000000000000000000000000000000000000000ffffffff080415112a1c02cc00ffffffff' \
                         '0100f2052a01000000434104c1b5671c8975087cc796d6ea73d2407591528b5c669106f9b6ab6ef6e373a57553' \
                         'e14866aaeffc44a9f58e5ee0c7faa7add7474f0a2c55a22cb40b949fdc933cac000000000100000002eaa6b49c' \
                         'd5b9393ec478df7b6baddaca9738686b07be605f05e57b750ad7a876000000004a493046022100e0bc99e312e4' \
                         '28ea1559b5bc2e3210f3a7202a7f8b2ee124c6ea9aeda497ecac022100ccda2dc6aac965b4ba3116bc52983853' \
                         '8ac0c99fe1a295941d00b5e351f86f0f01ffffffffc91489013f73209650e8b3e3bece46d78e678f02883c4b4e' \
                         '5f3540624c39d00d00000000494830450221008e991969e0ba7ddcb036c42286403ceb495f6654a13854b01f36' \
                         'fcedc373320d02206a7bb838a88350e492b5f4eecd6b060f5e50b0c76d2353857db97fb48e5d61bb01ffffffff' \
                         '0100e40b54020000001976a914b5cd7aaed869cd5ccb45868e8666e7e934a2373688ac00000000'
        self.assertRaisesRegex(ValueError, "Number of found transactions 2 is not equal to expected number 3",
                               Block.from_raw, to_bytes(incomplete_raw), parse_transactions=True)

    def test_blocks_parse_block_and_transactions_2(self):
        b = Block.from_raw(self.rb330000, parse_transactions=True, limit=5)
        self.assertEqual(to_hexstring(b.block_hash), '00000000000000000faabab19f17c0178c754dbed023e6c871dcaf74159c5f02')
        self.assertEqual(b.height, 330000)
        self.assertEqual(b.version_int, 2)
        self.assertEqual(b.version_bin, '00000000000000000000000000000010')
        self.assertListEqual(b.version_bips(), ['BIP34'])
        self.assertEqual(b.prev_block, to_bytes('000000000000000003e20f90920dc065da4a507bcf045f44b9abac7fabff4857'))
        self.assertEqual(b.merkle_root, to_bytes('5a97519772c615a875c12859f447d9c1fea922f7e36bd08e96cc95eee235d28f'))
        self.assertEqual(b.bits_int, 404472624)
        self.assertEqual(b.time, 1415983209)
        self.assertEqual(b.nonce_int, 3756201140)
        self.assertEqual(int(b.difficulty), 39603666252)
        self.assertEqual(b.tx_count, 81)
        self.assertEqual(b.transactions[0].txid, 'dfd63430f8d14f6545117d74b20da63efd4a75c7e28f723b3dead431b88469ee')
        self.assertEqual(b.transactions[4].txid, '717bc8b42f12baf771b6719c2e3b2742925fe3912917c716abef03e35fe49020')
        self.assertEqual(len(b.transactions), 5)
        b.parse_transactions(70)
        self.assertEqual(len(b.transactions), 75)
        b.parse_transactions(10)
        self.assertEqual(len(b.transactions), 81)
        self.assertEqual(b.transactions[80].txid, '7c8483c890942334ecb73db3802f7571b06047b5c15febe3bad11e460065709b')

    def test_block_serialize(self):
        b = Block.from_raw(self.rb330000, parse_transactions=True)
        rb_ser = b.serialize()
        self.assertEqual(rb_ser, self.rb330000)
