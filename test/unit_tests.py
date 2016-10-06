# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Unit tests
#    Copyright (C) 2016 October
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
        self.assertEqual('11110001', change_base('F1', 16, 2))

    def test_change_base_hex_bit_lowercase(self):
        self.assertEqual('10100011', change_base('a3', 16, 2))

    def test_change_base_bit_hex(self):
        self.assertEqual('f1', change_base('11110001', 2, 16))

    def test_change_base_hex_dec(self):
        self.assertEqual('61441', change_base('f001', 16, 10))

    def test_change_base_dec_hex(self):
        self.assertEqual('f001', change_base('61441', 10, 16))

    def test_change_base_b58_dec(self):
        self.assertEqual('5283658277747592673868818217239156372404875337009783985623', change_base('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 10))

    def test_change_base_b58_bin(self):
        self.assertEqual('\x00\xd7{\xf7b\x8c\x19\xe6\x99\x01\r)xz)\xaf\xcf\x8e\x92\xadZ\x05=U\xd7', change_base('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 256))

    def test_change_base_b58_hex(self):
        self.assertEqual('00D77BF7628C19E699010D29787A29AFCF8E92AD5A053D55D7', change_base('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 16).upper())

    def test_change_base_dec_b58(self):
        self.assertEqual('LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', change_base('5283658277747592673868818217239156372404875337009783985623', 10, 58))

    def test_change_base_padding(self):
        self.assertEqual('0011', change_base(3, 10, 2, 4))

    def test_change_base_bin_b58(self):
        self.assertEqual('16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM', change_base("\x00\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee\xd6\x19g\xf6", 256, 58))

    def test_change_base_hex_bin(self):
        self.assertEqual('\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f', change_base("000102030405060708090a0b0c0d0e0f", 16, 256))

    def test_change_base32_base3(self):
        self.assertEqual(',   . .. ., .   ,. .,  ,. .., . ,..  .,. ,..,, . . .,.,..  ,...,, ,, .,.,,,.,,,...  . , .,,,. ...,, .,.,.  ,,..,,,,.', change_base("Oh what a fun we have !", 256, 3))

    # Tests for bug with leading zero's
    def test_change_base_leading_zeros(self):
        self.assertEqual('\x00\x00\x03', change_base("000003", 16, 256))

    def test_change_base_leading_zeros2(self):
        self.assertEqual('1L', change_base('0013', 16, 58))

    def test_change_base_leading_zeros3(self):
        self.assertEqual('1L', change_base('013', 16, 58))

    def test_change_base_leading_zeros4(self):
        self.assertEqual('\x04G\x81', change_base('044781',16,256))



class TestPrivateKeyConversions(unittest.TestCase):

    def setUp(self):
        self.privatekey_hex = 'b954f71933986e3de76d3a94454dc52ec082c662ba67ca3ba48ff72bc2704a58'
        self.k = PrivateKey(self.privatekey_hex)

    def test_private_key_conversions_dec(self):
        self.assertEqual('83827997552125623280808720137320612316470870230953489181279239295529837939288', self.k.get_dec())

    def test_private_key_conversions_hex(self):
        self.assertEqual('b954f71933986e3de76d3a94454dc52ec082c662ba67ca3ba48ff72bc2704a58', self.k.get_hex())

    def test_private_key_conversions_bits(self):
        self.assertEqual('1011100101010100111101110001100100110011100110000110111000111101111001110110110100111010100101000100010101001101110001010010111011000000100000101100011001100010101110100110011111001010001110111010010010001111111101110010101111000010011100000100101001011000', self.k.get_bit())

    def test_private_key_conversions_wif_uncompressed(self):
        self.assertEqual('5KDudqswBNJ8mf2k7Gxn72UknDBh7GFjj9NGJrY22SY1hjKS1gF', self.k.get_wif(False))

    def test_private_key_conversions_wif(self):
        self.assertEqual('L3RyKcjp8kzdJ6rhGhTC5bXWEYnC2eL3b1vrZoduXMht6m9MQeHy', self.k.get_wif())

    def test_private_key_get_public(self):
        self.assertEqual('034781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d5', self.k.get_public())

    def test_private_key_get_public_uncompressed(self):
        self.assertEqual('044781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d57a380bc32c26f46e733cd991064c2e7f7d532b9c9ca825671a8809ab6876c78b', self.k.get_public(False))


class TestPrivateKeyImport(unittest.TestCase):

    def test_private_key_import_wif(self):
        self.k = PrivateKey('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX')
        self.assertEqual('88ccb90221d9b44df8dd317307de2d6019c9c7448dccaa1e45bae77e5a022b7b', self.k.get_hex())

    def test_private_key_import_wif_uncompressed(self):
        self.k = PrivateKey('5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS')
        self.assertEqual('c4bbcb1fbec99d65bf59d85c8cb62ee2db963f0fe106f483d9afa73bd4e39a8a', self.k.get_hex())


class TestPublicKeyConversion(unittest.TestCase):

    def setUp(self):
        self.publickey_hex = '044781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d57a380bc32c26f46e733cd991064c2e7f7d532b9c9ca825671a8809ab6876c78b'
        self.K = PublicKey(self.publickey_hex)
        self.KC = PublicKey('034781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d5')

    def test_public_key_get_address_uncompressed(self):
        self.assertEqual('12ooWDQp6mujkVpEWHdfHmfM4rU17bokWw', self.K.get_address())

    def test_public_key_get_address(self):
        self.assertEqual('1P2X35YnajqoBXtPpQXJzV1QMnqSZQsn82', self.KC.get_address())

    def test_public_key_get_point(self):
        self.assertEqual((32343711077743629729728681292399790965391040816412086995020432364076041835733, 55281192143835269607479311758661973079027103826274522268778194868406595274635), self.K.get_point())

    def test_public_key_get_hash160_uncompressed(self):
        self.assertEqual('13d21450578cd8f8645d2e56e684deb7cd77864b', self.K.get_hash160())

    def test_public_key_get_hash160(self):
        self.assertEqual('f19c417fd97e364afb06e1edd2c0e6a7ecf1af00', self.KC.get_hash160())

class TestHDkeys(unittest.TestCase):

    def test_hdprivate_key_import_seed_1(self):
        self.k = HDkey.from_seed('000102030405060708090a0b0c0d0e0f')
        self.assertEqual('xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi', self.k.extended_key())

    def test_hdprivate_key_import_seed_2(self):
        self.k = HDkey.from_seed('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542')
        self.assertEqual('xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U', self.k.extended_key())


if __name__ == '__main__':
    unittest.main()
