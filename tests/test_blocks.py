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
from bitcoinlib.blocks import *


class TestBlocks(unittest.TestCase):

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
        self.assertEqual(b.tx_count, 1)
