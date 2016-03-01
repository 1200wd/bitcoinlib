# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Unit tests
#    Copyright (C) 2016 February 
#    1200 Web Development
#    http://1200wd.com/
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

from bitcoinlib.keys import *


class TestGlobalMethods(unittest.TestCase):

    def test_change_base_hex_bit(self):
        self.assertEqual(change_base('F1', 16, 2), '11110001')

    def test_change_base_hex_bit_lowercase(self):
        self.assertEqual(change_base('a3', 16, 2), '10100011')

    def test_change_base_bit_hex(self):
        self.assertEqual(change_base('11110001', 2, 16), 'f1')

    def test_change_base_hex_dec(self):
        self.assertEqual(change_base('f001', 16, 10), '61441')

    def test_change_base_dec_hex(self):
        self.assertEqual(change_base('61441', 10, 16), 'f001')

    def test_change_base_b58_dec(self):
        self.assertEqual(change_base('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 10), '5283658277747592673868818217239156372404875337009783985623')

    def test_change_base_b58_bin(self):
        self.assertEqual(change_base('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 256), '\x00\xd7{\xf7b\x8c\x19\xe6\x99\x01\r)xz)\xaf\xcf\x8e\x92\xadZ\x05=U\xd7')

    def test_change_base_dec_b58(self):
        self.assertEqual(change_base('5283658277747592673868818217239156372404875337009783985623', 10, 58), 'LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx')

    def test_change_base_padding(self):
        self.assertEqual(change_base(3, 10, 2, 4), '0011')

    def test_change_base_bin_b58(self):
        self.assertEqual(change_base("\x00\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee\xd6\x19g\xf6", 256, 58), '16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM')


class TestPrivateKeyConversions(unittest.TestCase):

    def setUp(self):
        self.privatekey_hex = 'b954f71933986e3de76d3a94454dc52ec082c662ba67ca3ba48ff72bc2704a58'
        self.k = PrivateKey(self.privatekey_hex)

    def test_private_key_conversions_dec(self):
        self.assertEqual(self.k.get_dec(), '83827997552125623280808720137320612316470870230953489181279239295529837939288')

    def test_private_key_conversions_hex(self):
        self.assertEqual(self.k.get_hex(), 'b954f71933986e3de76d3a94454dc52ec082c662ba67ca3ba48ff72bc2704a58')

    def test_private_key_conversions_bit(self):
        self.assertEqual(self.k.get_bit(), '1011100101010100111101110001100100110011100110000110111000111101111001110110110100111010100101000100010101001101110001010010111011000000100000101100011001100010101110100110011111001010001110111010010010001111111101110010101111000010011100000100101001011000')

    def test_private_key_conversions_wif_uncompressed(self):
        self.assertEqual(self.k.get_wif(False), '5KDudqswBNJ8mf2k7Gxn72UknDBh7GFjj9NGJrY22SY1hjKS1gF')

    def test_private_key_conversions_wif(self):
        self.assertEqual(self.k.get_wif(), 'L3RyKcjp8kzdJ6rhGhTC5bXWEYnC2eL3b1vrZoduXMht6m9MQeHy')

    def test_private_key_get_public(self):
        self.assertEqual(self.k.get_public(), '034781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d5')

    def test_private_key_get_public_uncompressed(self):
        self.assertEqual(self.k.get_public(False), '044781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d57a380bc32c26f46e733cd991064c2e7f7d532b9c9ca825671a8809ab6876c78b')


class TestPrivateKeyImport(unittest.TestCase):

    def test_private_key_import_wif(self):
        self.k = PrivateKey('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX')
        self.assertEqual(self.k.get_hex(), '88ccb90221d9b44df8dd317307de2d6019c9c7448dccaa1e45bae77e5a022b7b')

    def test_private_key_import_wif_uncompressed(self):
        self.k = PrivateKey('5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS')
        self.assertEqual(self.k.get_hex(), 'c4bbcb1fbec99d65bf59d85c8cb62ee2db963f0fe106f483d9afa73bd4e39a8a')


class TestPublicKeyConversion(unittest.TestCase):

    def setUp(self):
        self.publickey_hex = '044781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d57a380bc32c26f46e733cd991064c2e7f7d532b9c9ca825671a8809ab6876c78b'
        self.K = PublicKey(self.publickey_hex)
        self.KC = PublicKey('034781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d5')

    def test_public_key_get_address_uncompressed(self):
        self.assertEqual(self.K.get_address(), '12ooWDQp6mujkVpEWHdfHmfM4rU17bokWw')

    def test_public_key_get_address(self):

        self.assertEqual(self.KC.get_address(), '1P2X35YnajqoBXtPpQXJzV1QMnqSZQsn82')

    def test_public_key_get_point(self):
        self.assertEqual(self.K.get_point(), (32343711077743629729728681292399790965391040816412086995020432364076041835733, 55281192143835269607479311758661973079027103826274522268778194868406595274635))

    def test_public_key_get_hash160_uncompressed(self):
        self.assertEqual(self.K.get_hash160(), '13d21450578cd8f8645d2e56e684deb7cd77864b')

    def test_public_key_get_hash160(self):
        self.assertEqual(self.KC.get_hash160(), 'f19c417fd97e364afb06e1edd2c0e6a7ecf1af00')


if __name__ == '__main__':
    unittest.main()
