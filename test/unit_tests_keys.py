# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Unit Tests
#    © 1200 Web Development <http://1200wd.com/>
#    2016 november
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

from bitcoinlib.keys import *
from bitcoinlib.mnemonic import Mnemonic

# Number of bulktests for generation of private, public keys and hdkeys. Set to 0 to disable
# WARNING: Can be slow!
BULKTESTCOUNT = 10

class TestGlobalMethods(unittest.TestCase):

    def test_change_base_hex_bit(self):
        self.assertEqual('11110001', change_base('F1', 16, 2))

    def test_change_base_hex_bit_lowercase(self):
        self.assertEqual('10100011', change_base('a3', 16, 2))

    def test_change_base_bit_hex(self):
        self.assertEqual('f1', change_base('11110001', 2, 16))

    def test_change_base_hex_dec(self):
        self.assertEqual(61441, change_base('f001', 16, 10))

    def test_change_base_dec_hex(self):
        self.assertEqual('f001', change_base('61441', 10, 16, 4))

    def test_change_base_b58_dec(self):
        self.assertEqual(5283658277747592673868818217239156372404875337009783985623,
                         change_base('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 10))

    def test_change_base_b58_bin(self):
        self.assertEqual('\x00\xd7{\xf7b\x8c\x19\xe6\x99\x01\r)xz)\xaf\xcf\x8e\x92\xadZ\x05=U\xd7',
                         change_base('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 256))

    def test_change_base_b58_hex(self):
        self.assertEqual('00D77BF7628C19E699010D29787A29AFCF8E92AD5A053D55D7',
                         change_base('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 16).upper())

    def test_change_base_dec_b58(self):
        self.assertEqual('LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx',
                         change_base('5283658277747592673868818217239156372404875337009783985623', 10, 58, 33))

    def test_change_base_padding(self):
        self.assertEqual('0011', change_base(3, 10, 2, 4))

    def test_change_base_bin_b58(self):
        self.assertEqual('16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM',
                         change_base("\x00\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee\xd6\x19g\xf6", 256, 58))

    def test_change_base_hex_bin(self):
        self.assertEqual('\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f',
                         change_base("000102030405060708090a0b0c0d0e0f", 16, 256))

    def test_change_base32_base3(self):
        self.assertEqual(',   . .. ., .   ,. .,  ,. .., . ,..  .,. ,..,, . . .,.,..  ,...,, ,, .,.,,,.,,,...  . , .,,,'
                         '. ...,, .,.,.  ,,..,,,,.', change_base("Oh what a fun we have !", 256, 3))

    # Tests for bug with leading zero's
    def test_change_base_leading_zeros(self):
        self.assertEqual('\x00\x00\x03', change_base("000003", 16, 256))

    def test_change_base_leading_zeros2(self):
        self.assertEqual('1L', change_base('0013', 16, 58))

    def test_change_base_leading_zeros3(self):
        self.assertEqual('1L', change_base('013', 16, 58))

    def test_change_base_leading_zeros4(self):
        self.assertEqual('\x04G\x81', change_base('044781',16,256))

    def test_change_base_zero_int(self):
        self.assertEqual(0, change_base(b'\0', 256, 10))


class TestPrivateKeyConversions(unittest.TestCase):

    def setUp(self):
        self.privatekey_hex = 'b954f71933986e3de76d3a94454dc52ec082c662ba67ca3ba48ff72bc2704a58'
        self.k = Key(self.privatekey_hex)

    def test_private_key_conversions_dec(self):
        self.assertEqual(83827997552125623280808720137320612316470870230953489181279239295529837939288,
                         self.k.private_dec())

    def test_private_key_conversions_hex(self):
        self.assertEqual('b954f71933986e3de76d3a94454dc52ec082c662ba67ca3ba48ff72bc2704a58', self.k.private_hex())

    def test_private_key_conversions_wif_uncompressed(self):
        self.assertEqual('5KDudqswBNJ8mf2k7Gxn72UknDBh7GFjj9NGJrY22SY1hjKS1gF', self.k.wif(False))

    def test_private_key_conversions_wif(self):
        self.assertEqual('L3RyKcjp8kzdJ6rhGhTC5bXWEYnC2eL3b1vrZoduXMht6m9MQeHy', self.k.wif())

    def test_private_key_public(self):
        self.assertEqual('034781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d5', self.k.public())

    def test_private_key_public_uncompressed(self):
        self.assertEqual('044781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d57a380bc32c26f46e733c'
                         'd991064c2e7f7d532b9c9ca825671a8809ab6876c78b', self.k.public_uncompressed())


class TestPrivateKeyImport(unittest.TestCase):

    def test_private_key_import_wif(self):
        self.k = Key('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX')
        self.assertEqual('88ccb90221d9b44df8dd317307de2d6019c9c7448dccaa1e45bae77e5a022b7b', self.k.private_hex())

    def test_private_key_import_wif_uncompressed(self):
        self.k = Key('5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS')
        self.assertEqual('c4bbcb1fbec99d65bf59d85c8cb62ee2db963f0fe106f483d9afa73bd4e39a8a', self.k.private_hex())

    def test_private_key_import_generate_random(self):
        self.k = Key()
        self.assertIn(self.k.wif()[0], ['K', 'L'])
        self.assertEqual(52, len(self.k.wif()))

    def test_private_key_import_error_1(self):
        self.assertRaisesRegexp(ValueError, "Invalid checksum, not a valid WIF compressed key",
                                Key, 'L1odb1uUozbfK2NrsMyhJfvRsxGM2axixgPL8vG9BUBnE6W1VyTX')

    def test_private_key_import_error_2(self):
        self.assertRaisesRegexp(ValueError, "Unrecognised key format",
                                Key, 'M1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX')


class TestPublicKeyConversion(unittest.TestCase):

    def setUp(self):
        self.publickey_hex = '044781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d57a380bc32c26f46e733cd' \
                             '991064c2e7f7d532b9c9ca825671a8809ab6876c78b'
        self.K = Key(self.publickey_hex)
        self.KC = Key('034781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d5')

    def test_public_key_get_address_uncompressed(self):
        self.assertEqual('12ooWDQp6mujkVpEWHdfHmfM4rU17bokWw', self.K.address_uncompressed())

    def test_public_key_get_address(self):
        self.assertEqual('1P2X35YnajqoBXtPpQXJzV1QMnqSZQsn82', self.KC.address())

    def test_public_key_get_point(self):
        self.assertEqual((32343711077743629729728681292399790965391040816412086995020432364076041835733,
                          55281192143835269607479311758661973079027103826274522268778194868406595274635),
                         self.K.public_point())

    def test_public_key_get_hash160_uncompressed(self):
        self.assertEqual('13d21450578cd8f8645d2e56e684deb7cd77864b', self.K.hash160())

    def test_public_key_get_hash160(self):
        self.assertEqual('f19c417fd97e364afb06e1edd2c0e6a7ecf1af00', self.KC.hash160())

    def test_public_key_try_private(self):
        self.assertFalse(self.K.private_hex())

    def test_public_key_import_error(self):
        self.assertRaisesRegexp(ValueError, "Unrecognised key format",
                                Key, ['064781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d5', 'public'])


class TestPublicKeyUncompressed(unittest.TestCase):

    def setUp(self):
        self.K = Key('025c0de3b9c8ab18dd04e3511243ec2952002dbfadc864b9628910169d9b9b00ec')

    def test_public_key_point(self):
        self.assertEqual((41637322786646325214887832269588396900663353932545912953362782457239403430124L,
                          16388935128781238405526710466724741593761085120864331449066658622400339362166L),
                         self.K.public_point(),)

    def test_public_key_uncompressed(self):
        self.assertEqual('045c0de3b9c8ab18dd04e3511243ec2952002dbfadc864b9628910169d9b9b00ec243bcefdd4347074d4'
                         '4bd7356d6a53c495737dd96295e2a9374bf5f02ebfc176',
                         self.K.public_uncompressed())

    def test_public_key_address_uncompressed(self):
        # print self.K.address()
        self.assertEqual('1thMirt546nngXqyPEz532S8fLwbozud8', self.K.address_uncompressed())


class TestHDKeysImport(unittest.TestCase):

    def setUp(self):
        self.k = HDKey.from_seed('000102030405060708090a0b0c0d0e0f')
        self.k2 = HDKey.from_seed('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a878'
                                  '4817e7b7875726f6c696663605d5a5754514e4b484542')
        self.xpub = HDKey('xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqse'
                          'fD265TMg7usUDFdp6W1EGMcet8')

    def test_hdkey_import_seed_1(self):

        self.assertEqual('xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TG'
                         'tRBeJgk33yuGBxrMPHi', self.k.extended_wif())
        self.assertEqual('xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TM'
                         'g7usUDFdp6W1EGMcet8', self.k.extended_wif(public=True))

    def test_hdkey_import_seed_2(self):
        self.assertEqual('xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3L'
                         'qFtT2emdEXVYsCzC2U', self.k2.extended_wif())
        self.assertEqual('xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJ'
                         'Y47LJhkJ8UB7WEGuduB', self.k2.extended_wif_public())

    def test_hdkey_random(self):
        self.k = HDKey()
        self.assertEqual('xprv', self.k.extended_wif()[:4])
        self.assertEqual(111, len(self.k.extended_wif()))

    def test_hdkey_import_extended_private_key(self):
        extkey = 'xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4m' \
                 'LTj34bhnZX7UiM'
        self.k = HDKey(extkey)
        self.assertEqual(extkey, self.k.extended_wif())

    def test_hdkey_import_extended_public_key(self):
        extkey = 'xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7' \
                 'DogT5Uv6fcLW5'
        self.k = HDKey(extkey)
        self.assertEqual(extkey, self.k.extended_wif())

    def test_hdkey_import_public(self):
        self.assertEqual('15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', self.xpub.public().address())
        self.assertEqual('0339a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2', self.xpub.public().public_hex())

    def test_hdkey_import_public_try_private(self):
        self.assertFalse(self.xpub.public().wif())
        self.assertFalse(self.xpub.public().private_hex())
        self.assertFalse(self.xpub.public().private_byte())


class TestHDKeysChildKeyDerivation(unittest.TestCase):

    def setUp(self):
        self.k = HDKey.from_seed('000102030405060708090a0b0c0d0e0f')
        self.k2 = HDKey.from_seed('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a87848'
                                 '17e7b7875726f6c696663605d5a5754514e4b484542')

    def test_hdkey_path_m_0h(self):
        self.assertEqual('xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7'
                         'XnxHrnYeSvkzY7d2bhkJ7', self.k.subkey_for_path('m/0H').extended_wif())
        self.assertEqual('xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9x'
                         'v5ski8PX9rL2dZXvgGDnw', self.k.subkey_for_path('m/0H').extended_wif(public=True))

    def test_hdkey_path_m_0h_1(self):
        self.assertEqual('xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H'
                         '2EU4pWcQDnRnrVA1xe8fs', self.k.subkey_for_path('m/0H/1').extended_wif())
        self.assertEqual('xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqc'
                         'k2AxYysAA7xmALppuCkwQ', self.k.subkey_for_path('m/0H/1').extended_wif(public=True))

    def test_hdkey_path_m_0h_1_2h(self):
        self.assertEqual('xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjAN'
                         'TtpgP4mLTj34bhnZX7UiM', self.k.subkey_for_path('m/0h/1/2h').extended_wif())
        self.assertEqual('xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4'
                         'trkrX7x7DogT5Uv6fcLW5', self.k.subkey_for_path('m/0h/1/2h').extended_wif(public=True))

    def test_hdkey_path_m_0h_1_2h_1000000000(self):
        self.assertEqual('xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUi'
                         'hUZREPSL39UNdE3BBDu76', self.k.subkey_for_path('m/0h/1/2h/2/1000000000').extended_wif())
        self.assertEqual('xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTv'
                         'XEYBVPamhGW6cFJodrTHy',
                         self.k.subkey_for_path('m/0h/1/2h/2/1000000000').extended_wif(public=True))

    def test_hdkey_path_key2(self):
        self.assertEqual('xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEc'
                         'BYJUuekgW4BYPJcr9E7j',
                         self.k2.subkey_for_path('m/0/2147483647h/1/2147483646h/2').extended_wif())
        self.assertEqual('xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb'
                         '9rXpVGyy3bdW6EEgAtqt',
                         self.k2.subkey_for_path('m/0/2147483647h/1/2147483646h/2').extended_wif(public=True))

    def test_hdkey_path_invalid(self):
        with self.assertRaises(ValueError):
            self.k2.subkey_for_path('m/0/').extended_wif()

    def test_hdkey_path_invalid2(self):
        with self.assertRaises(ValueError):
            self.k2.subkey_for_path('m/-1').extended_wif()


class TestHDKeysPublicChildKeyDerivation(unittest.TestCase):

    def setUp(self):
        self.K = HDKey('xpub6ASuArnXKPbfEVRpCesNx4P939HDXENHkksgxsVG1yNp9958A33qYoPiTN9QrJmWFa2jNLdK84bWmyqTSPGtApP8P'
                       '7nHUYwxHPhqmzUyeFG')
        self.k = HDKey('xprv9wTYmMFdV23N21MM6dLNavSQV7Sj7meSPXx6AV5eTdqqGLjycVjb115Ec5LgRAXscPZgy5G4jQ9csyyZLN3PZLxoM'
                       '1h3BoPuEJzsgeypdKj')

    def test_hdkey_derive_public_child_key(self):
        self.assertEqual('1BvgsfsZQVtkLS69NvGF8rw6NZW2ShJQHr', self.K.child_public(0).public().address())

    def test_hdkey_derive_public_child_key2(self):
        self.assertEqual('17JbSP83rPWmbdcdtiiTNqBE8MgGN8kmUk', self.K.child_public(8).public().address())

    def test_hdkey_private_key(self):
        self.assertEqual('KxABnXp7SiuWi218c14KkjEMV7SjcfXnvsWaveNVxWZU1Rwi8zNQ',
                         self.k.child_private(7).private().wif())

    def test_hdkey_private_key_hardened(self):
        self.k2 = HDKey('xprv9s21ZrQH143K31AgNK5pyVvW23gHnkBq2wh5aEk6g1s496M8ZMjxncCKZKgb5j'
              'ZoY5eSJMJ2Vbyvi2hbmQnCuHBujZ2WXGTux1X2k9Krdtq')
        self.assertEqual('xprv9wTErTSu5AWGkDeUPmqBcbZWX1xq85ZNX9iQRQW9DXwygFp7iRGJo79dsVctcsCHsnZ3XU3DhsuaGZbDh8iDkB'
                         'N45k67UKsJUXM1JfRCdn1', str(self.k2.subkey_for_path('3/2H')))


class TestHDKeysTestnet(unittest.TestCase):

    def test_hdkey_testnet_random(self):
        self.k = HDKey(addresstype=ADDRESSTYPE_TESTNET)

        self.assertEqual('tprv', self.k.extended_wif()[:4])
        self.assertEqual('tpub', self.k.extended_wif_public()[:4])
        self.assertIn(self.k.public().address()[:1], ['m', 'n'])

    def test_hdkey_testnet_import(self):
        self.k = HDKey('tprv8ZgxMBicQKsPf2S18qpSypHPZBK7mdiwvXHPh5TSjGjm2pLacP4tEqVjLVyagTLLgSZK4YyBNb4eytBykE755Kc'
                       'L9YXAqPtfERNRfwRt54M')

        self.assertEqual('cPSokRrLueavzAmVBmAXwgALkumRNMN9pErvRLAXvx58NBJAkEYJ', self.k.private().wif())
        self.assertEqual('tpubD6NzVbkrYhZ4YVTo2VV3PDwW8Cq3vxurVptAybVk9YY9sJbMEmtURL7bWgKxXSWSahXu6HbHkdpjBGzwYYkJm'
                         'u2VmoeHuiTmzHZpJo8Cdpb', self.k.extended_wif_public())
        self.assertEqual('n4c8TKkqUmj3b8VJrTioiZuciyaCDRd6iE', self.k.public().address())


# From Copyright (c) 2013 Pavol Rusnak <https://github.com/trezor/python-mnemonic>
class TestMnemonics(unittest.TestCase):

    def _check_list(self, language, vectors):
        mnemo = Mnemonic(language)
        for v in vectors:
            if v[0]:
                phrase = mnemo.to_mnemonic(v[0])
            else:
                phrase = v[1]
            seed = change_base(mnemo.to_seed(phrase, v[4]), 256, 16)
            print("Test %s => %s" % (v[0], phrase))
            self.assertEqual(v[1], phrase)
            self.assertEqual(v[2], seed)
            k = HDKey.from_seed(seed)
            self.assertEqual(k.extended_wif(), v[3])

    def test_vectors(self):
        with open('mnemonics_tests.json', 'r') as f:
            vectors = json.load(f)
        for lang in vectors.keys():
            self._check_list(lang, vectors[lang])

class TestBip38(unittest.TestCase):

    def setUp(self):
        with open('bip38_protected_key_tests.json', 'r') as f:
            self.vectors = json.load(f)

    def test_encrypt_private_key(self):
        for v in self.vectors["valid"]:
            k = Key(v['wif'])
            print "Check %s + %s = %s " % (v['wif'], v['passphrase'], v['bip38'])
            self.assertEqual(str(v['bip38']), k.bip38_encrypt(str(v['passphrase'])))

    def test_decrypt_bip38_key(self):
        for v in self.vectors["valid"]:
            k = Key(v['bip38'], passphrase=str(v['passphrase']))
            print "Check %s - %s = %s " % (v['bip38'], v['passphrase'], v['wif'])
            self.assertEqual(str(v['wif']), k.wif())

    def test_bip38_invalid_keys(self):
        for v in self.vectors["invalid"]["verify"]:
            print "Checking invalid key %s" % v['base58']
            self.assertRaisesRegexp(ValueError, "Unrecognised key format", Key, [str(v['base58'])])



class TestKeysBulk(unittest.TestCase):

    def setUp(self):
        self.K = HDKey('xpub6ASuArnXKPbfEVRpCesNx4P939HDXENHkksgxsVG1yNp9958A33qYoPiTN9QrJmWFa2jNLdK84bWmyqTSPGtApP8P'
                       '7nHUYwxHPhqmzUyeFG')
        self.k = HDKey('xprv9wTYmMFdV23N21MM6dLNavSQV7Sj7meSPXx6AV5eTdqqGLjycVjb115Ec5LgRAXscPZgy5G4jQ9csyyZLN3PZLxoM'
                       '1h3BoPuEJzsgeypdKj')

    def test_hdkey_derive_from_public_and_private_index(self):
        global BULKTESTCOUNT
        if not BULKTESTCOUNT:
            self.skipTest("Skip bulktesting. Bulktestcount == 0")
        for i in range(BULKTESTCOUNT):
            pub_with_pubparent = self.K.child_public(i).public().address()
            pub_with_privparent = self.k.child_private(i).public().address()
            if pub_with_privparent != pub_with_pubparent:
                print "Error index %4d: pub-child %s, priv-child %s" % (i, pub_with_privparent, pub_with_pubparent)
            self.assertEqual(pub_with_pubparent, pub_with_privparent)

    def test_hdkey_derive_from_public_and_private_random(self):
        global BULKTESTCOUNT
        if not BULKTESTCOUNT:
            self.skipTest("Skip bulktesting. Bulktestcount == 0")
        for i in range(BULKTESTCOUNT):
            k = HDKey()
            K = HDKey(k.extended_wif_public())
            pub_with_pubparent = K.child_public().public().address()
            pub_with_privparent = k.child_private().public().address()
            if pub_with_privparent != pub_with_pubparent:
                print "Error random key: %4d: pub-child %s, priv-child %s" % (i, pub_with_privparent, pub_with_pubparent)
            self.assertEqual(pub_with_pubparent, pub_with_privparent)


if __name__ == '__main__':
    unittest.main()
