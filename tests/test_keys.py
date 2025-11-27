# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Key, Encoding and Mnemonic Class
#    © 2017-2024 March - 1200 Web Development <http://1200wd.com/>
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

import os
import unittest
import json
from unicodedata import normalize
from bitcoinlib.networks import NETWORK_DEFINITIONS
from bitcoinlib.keys import *

# Number of bulktests for generation of private, public keys, HDKeys and signatures. Set to 0 to disable
# WARNING: Can be slow for a larger number of tests
BULKTESTCOUNT = 250


class TestKeyClasses(unittest.TestCase):

    def test_keys_classes_dunder_methods(self):
        pk = 'xprv9s21ZrQH143K4EDmQNMBqXwUTcrRoUctKkTegGsaBcMLnR1fJkMjVSRwVswjHzJspfWCUwzge1F521cY4wfWD54tzXVUqeo' \
             'TFkZo17HiK2y'
        k = HDKey(pk)
        self.assertEqual(str(k), '03dc86716b2be27a0575558bac73279290ac22c3ea0240e42a2152d584f2b4006b')
        self.assertEqual(len(k), 33)
        self.assertEqual(int(k), 95796105828208927954168018443072630832764875640480247096632116413925408206516)
        k2 = HDKey(pk)
        self.assertTrue(k == k2)
        pubk2 = HDKey(k.wif_public())
        self.assertEqual(str(pubk2), '03dc86716b2be27a0575558bac73279290ac22c3ea0240e42a2152d584f2b4006b')
        self.assertTrue(k.public() == pubk2)
        self.assertEqual(hash(k), hash(k))

        secret_a = 91016841482436413813855602003356453732719866824300837492458390942862039054048
        secret_b = 78671675202523181504169507283123166972338313435344626818080535590471773062636
        secret_a_add_b = 53896427447643399894454124277791712852220615980570559927933763391815650622347
        secret_a_min_b = 12345166279913232309686094720233286760381553388956210674377855352390265991412
        ka = HDKey(secret_a)
        ka2 = HDKey(secret_a)
        kb = HDKey(secret_b)
        self.assertEqual(str(ka), '02dff8866c7dc58055d9823dbc0ef098be76d8a1c87e545a13559460669b56a6a6')
        self.assertEqual(len(ka), 33)
        self.assertTrue(ka == ka2)
        pub_ka = HDKey(ka.wif_public())
        self.assertEqual(str(pub_ka), '02dff8866c7dc58055d9823dbc0ef098be76d8a1c87e545a13559460669b56a6a6')
        self.assertTrue(ka.public() == pub_ka)
        self.assertEqual((ka + kb).secret, secret_a_add_b)
        self.assertEqual((kb + ka).secret, secret_a_add_b)
        self.assertEqual((ka - kb).secret, secret_a_min_b)

    def test_keys_classes_dunder_methods_mul(self):
        secret_a = 101842203467542661703461476767681059717614296435193763347876672834253776929083
        secret_b = 48056918761728599432510813046582785545807011954742048381717688544631745412510
        secret_a_mul_b = 88863767166841201737805106153187292662619702602208852020796235484522800819015
        ka = HDKey(secret_a)
        kb = HDKey(secret_b)
        self.assertEqual((ka * kb).secret, secret_a_mul_b)
        self.assertEqual((kb * ka).secret, secret_a_mul_b)

    def test_keys_proof_distributivity_of_scalar_operations(self):
        # Proof: (a - b) * c == a * c - b * c over SECP256k1
        ka = HDKey()
        kb = HDKey()
        kc = HDKey()
        self.assertTrue(((ka - kb) * kc) == ((ka * kc) - (kb * kc)))

    def test_keys_inverse(self):
        secret = 95695802915573022935630358993164660366922511389187789518108651759801046161623
        inv_x = 18153291153288219155018628681705413538294494009875615719062204619491226452658
        inv_y = 67935514921393906349711087930011707333238709725906400058836382320969451605430
        k = Key(secret)
        k_inv = -k
        self.assertEqual(k_inv.x, inv_x)
        self.assertEqual(k_inv.y, inv_y)

    def test_keys_inverse2(self):
        k = HDKey()
        pub_k = k.public()
        self.assertEqual(k.address(), pub_k.address())
        self.assertEqual((-k).address(), pub_k.inverse().address())
        self.assertEqual((-k).address(), k.inverse().address())

        pkwif = 'Mtpv7L6Q8tPadPv8iUDKAXk1wyCmdJ6q2y2d3AixyoGVMH3WeoCDwkLbpUBXXB5HHbueeqTikkeBGTBV7tCcgJtEfm1wCt4ZcQixz7TtV5CAXfd'
        k = HDKey(pkwif, network='litecoin', compressed=False, witness_type='p2sh-segwit')
        pub_k = k.public()
        self.assertEqual(pub_k, pub_k.inverse())

        k = HDKey(pkwif, network='litecoin', witness_type='p2sh-segwit')
        pub_k = k.public()
        pub_k_inv = pub_k.inverse()
        self.assertEqual(pub_k_inv.address(), "MQVYsZ5o5uhN2X6QMbu9RVu5YADiq859MY")
        self.assertEqual(pub_k_inv.witness_type, 'p2sh-segwit')
        self.assertEqual(pub_k_inv.network.name, 'litecoin')
        self.assertEqual(k.address(), pub_k.address())
        self.assertEqual((-k).address(), pub_k_inv.address())
        self.assertEqual((-k).address(), k.inverse().address())

    def test_dict_and_json_outputs(self):
        k = HDKey()
        k.address(script_type='p2wsh', encoding='bech32')
        self.assertTrue(isinstance(json.loads(k.address_obj.as_json()), dict))
        self.assertTrue(isinstance(k.address_obj.as_dict(), dict))
        self.assertTrue(isinstance(json.loads(k.as_json()), dict))
        self.assertTrue(isinstance(k.as_dict(), dict))
        k = Key()
        self.assertTrue(isinstance(json.loads(k.as_json()), dict))
        self.assertTrue(isinstance(k.as_dict(), dict))
        self.assertTrue(isinstance(json.loads(k.as_json(include_private=True)), dict))
        self.assertTrue(isinstance(k.as_dict(include_private=True), dict))

    def test_path_expand(self):
        self.assertListEqual(path_expand([0], witness_type='legacy'), ['m', "44'", "0'", "0'", '0', '0'])
        self.assertListEqual(path_expand([10, 20], witness_type='legacy'), ['m', "44'", "0'", "0'", '10', '20'])
        self.assertListEqual(path_expand([10, 20]), ['m', "84'", "0'", "0'", '10', '20'])
        self.assertListEqual(path_expand([], witness_type='p2sh-segwit'), ['m', "49'", "0'", "0'", '0', '0'])
        self.assertListEqual(path_expand([99], witness_type='p2sh-segwit', multisig=True),
                             ['m', "48'", "0'", "0'", "1'", '0', '99'])
        self.assertRaisesRegex(BKeyError, "Invalid path provided. Path should be shorter than 6 items.",
                                path_expand, [0, 1, 2, 3, 4, 5, 6])
        self.assertRaisesRegex(BKeyError, "Please provide path as list with at least 1 item",
                                path_expand, 5)

    def test_keys_create_public_point(self):
        k = HDKey()
        p = (k.x, k.y)
        k2 = HDKey(p)
        self.assertEqual(k, k2)
        self.assertEqual(k.public(), k2)
        self.assertEqual(k.address(), k2.address())

        k = HDKey(compressed=False, witness_type='legacy')
        p = (k.x, k.y)
        k2 = HDKey(p, compressed=False, witness_type='legacy')
        self.assertEqual(k, k2)
        self.assertEqual(k.public(), k2)
        self.assertEqual(k.address(), k2.address())


class TestGetKeyFormat(unittest.TestCase):

    def test_format_wif_uncompressed(self):
        key = '5Hwgr3u458GLafKBgxtssHSPqJnYoGrSzgQsPwLFhLNYskDPyyA'
        self.assertEqual('wif', get_key_format(key)['format'])

    def test_format_wif_compressed(self):
        key = 'L2Q5U2zjxeoSf3dcNZsk19Z9bGr7RMeCTigvv7gJNJQq9uzQnF47'
        self.assertEqual('wif_compressed', get_key_format(key)['format'])

    def test_format_bin_uncompressed(self):
        key = b'\x04\xa8\x82\xd4\x14\xe4x\x03\x9c\xd5\xb5*\x92\xff\xb1=\xd5\xe6\xbdE\x15It9\xdf\xfdi\x1a\x0f\x12\xaf' \
              b'\x95u\xfa4\x9bV\x94\xed1U\xb16\xf0\x9ec\x97Z\x17\x00\xc9\xf4\xd4\xdf\x84\x93#\xda\xc0l\xf3\xbddX\xcd'
        self.assertEqual('bin', get_key_format(key)['format'])

    def test_format_hdkey_private(self):
        key = 'xprv9s21ZrQH143K2JF8RafpqtKiTbsbaxEeUaMnNHsm5o6wCW3z8ySyH4UxFVSfZ8n7ESu7fgir8imbZKLYVBxFPND1pniTZ81v' \
              'Kfd45EHKX73'
        self.assertEqual('hdkey_private', get_key_format(key)['format'])

    def test_format_hdkey_public(self):
        key = 'xpub6AHA9hZDN11k2ijHMeS5QqHx2KP9aMBRhTDqANMnwVtdyw2TDYRmF8PjpvwUFcL1Et8Hj59S3gTSMcUQ5gAqTz3Wd8EsMTmF3' \
              'DChhqPQBnU'
        self.assertEqual('hdkey_public', get_key_format(key)['format'])

    def test_format_hdkey_private_litecoin(self):
        key = 'ttpv96BtqegdxXceS41gmguxRWjtFdG11XqquvaPcpionXB8oQ2zkXYY9vCvykdfLEeeihx1SxP3t7ranmqLHKbmgfiMFR7967urhq' \
              'oAq5eBHur'
        self.assertEqual('hdkey_private', get_key_format(key)['format'])
        self.assertIn('litecoin_testnet', get_key_format(key)['networks'])

    def test_format_hdkey_mnemonic(self):
        self.assertEqual(get_key_format('abandon car zoo')['format'], 'mnemonic')

    def test_format_key_exceptions(self):
        self.assertRaisesRegex(BKeyError, "Key empty, please specify a valid key", get_key_format, '')
        self.assertRaisesRegex(BKeyError, "Attribute 'is_private' must be False or True", get_key_format,
                                '666368e477a8ddd46808c527cc3c506719bb3f52a927b6c13532984b714b56ad', 3)


class TestPrivateKeyConversions(unittest.TestCase):

    def setUp(self):
        self.privatekey_hex = 'b954f71933986e3de76d3a94454dc52ec082c662ba67ca3ba48ff72bc2704a58'
        self.k = Key(self.privatekey_hex, compressed=True)
        self.ku = Key(self.privatekey_hex, compressed=False)

    def test_private_key_conversions_dec(self):
        self.assertEqual(83827997552125623280808720137320612316470870230953489181279239295529837939288,
                         self.k.secret)

    def test_private_key_conversions_hex(self):
        self.assertEqual('b954f71933986e3de76d3a94454dc52ec082c662ba67ca3ba48ff72bc2704a58', self.k.private_hex)

    def test_private_key_conversions_wif_uncompressed(self):
        self.assertEqual('5KDudqswBNJ8mf2k7Gxn72UknDBh7GFjj9NGJrY22SY1hjKS1gF', self.ku.wif())

    def test_private_key_conversions_wif(self):
        self.assertEqual('L3RyKcjp8kzdJ6rhGhTC5bXWEYnC2eL3b1vrZoduXMht6m9MQeHy', self.k.wif())
        self.assertEqual('XHVtmt8BSSd5MRs5JTT4apiX9a3mUSwHxbGm6Ky6qiyyVvFRhmU7', self.k.wif(prefix='cc'))
        self.assertEqual('XHVtmt8BSSd5MRs5JTT4apiX9a3mUSwHxbGm6Ky6qiyyVvFRhmU7', self.k.wif(prefix=b'\xcc'))

    def test_private_key_public(self):
        self.assertEqual('034781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d5', self.k.public_hex)

    def test_private_key_public_uncompressed(self):
        self.assertEqual('044781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d57a380bc32c26f46e733c'
                         'd991064c2e7f7d532b9c9ca825671a8809ab6876c78b', self.ku.public_uncompressed_hex)


class TestPrivateKeyImport(unittest.TestCase):

    def test_private_key_import_key(self):
        self.k = Key(61876261089097932796193024729035977913579848833009517639587741086858579422075)
        self.assertEqual('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX', self.k.wif())

    def test_private_key_import_key_str(self):
        self.k = Key('61876261089097932796193024729035977913579848833009517639587741086858579422075')
        self.assertEqual('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX', self.k.wif())

    def test_private_key_import_key_hex_compressed(self):
        self.k = Key('1E99423A4ED27608A15A2616A2B0E9E52CED330AC530EDCC32C8FFC6A526AEDD01')
        self.assertEqual('KxFC1jmwwCoACiCAWZ3eXa96mBM6tb3TYzGmf6YwgdGWZgawvrtJ', self.k.wif())

    def test_private_key_import_key_byte(self):
        pk = b':\xbaAb\xc7%\x1c\x89\x12\x07\xb7G\x84\x05Q\xa7\x199\xb0\xde\x08\x1f\x85\xc4\xe4L\xf7\xc1>A\xda\xa6\x01'
        self.k = Key(pk)
        self.assertEqual('KyBsPXxTuVD82av65KZkrGrWi5qLMah5SdNq6uftawDbgKa2wv6S', self.k.wif())

    def test_private_key_import_hex(self):
        pk = '4781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d57a380bc32c26f46e733cd' \
             '991064c2e7f7d532b9c9ca825671a8809ab6876c78b'
        k = Key(pk)
        self.assertEqual('f93677c417d4750c7a5806f849739265cc46b8a9', k.hash160.hex())

    def test_private_key_import_wif(self):
        self.k = Key('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX')
        self.assertEqual('88ccb90221d9b44df8dd317307de2d6019c9c7448dccaa1e45bae77e5a022b7b', self.k.private_hex)

    def test_private_key_import_wif_uncompressed(self):
        self.k = Key('5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS')
        self.assertFalse(self.k.compressed)
        self.assertEqual('c4bbcb1fbec99d65bf59d85c8cb62ee2db963f0fe106f483d9afa73bd4e39a8a', self.k.private_hex)

    def test_private_key_import_generate_random(self):
        self.k = Key()
        self.assertIn(self.k.wif()[0], ['K', 'L'])
        self.assertEqual(52, len(self.k.wif()))

    def test_private_key_import_error_1(self):
        self.assertRaisesRegex(BKeyError, "Invalid checksum, not a valid WIF key",
                                Key, 'L1odb1uUozbfK2NrsMyhJfvRsxGM2axixgPL8vG9BUBnE6W1VyTX')

    def test_private_key_import_error_2(self):
        self.assertRaisesRegex(BKeyError, "Unrecognised key format",
                                Key, 'M1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX')

    def test_private_key_import_testnet(self):
        self.k = Key('92Pg46rUhgTT7romnV7iGW6W1gbGdeezqdbJCzShkCsYNzyyNcc', 'testnet')
        self.assertEqual('92Pg46rUhgTT7romnV7iGW6W1gbGdeezqdbJCzShkCsYNzyyNcc', self.k.wif())
        self.assertEqual('mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn', self.k.address())

    def test_private_key_import(self):
        wif = 'KxDQjJwvLdNNGhsipGgmceWaPjRndZuaQB9B2tgdHsw5sQ8Rtqje'
        self.assertEqual(Key.from_wif(wif).address(), '1Nro9WkpaKm9axmcfPVp79dAJU1Gx7VmMZ')
        wif = 'L1NUEdnjKvK547BrFjRnuSvyLn2Ndkyjz9gQwc9dTF9ucRDV7SsP'
        self.assertEqual(Key.from_wif(wif).address(), '1LuhZSrbPrd45RLa2EZ2JnrA4NtLf6sb58')
        wif = '68vBWcBndYGLpd4KmeNTk1gS1A71zyDX6uVQKCxq6umYKyYUav5'
        self.assertFalse(Key.from_wif(wif).compressed)
        wif = '5Hwgr3u458GLafKBgxtssHSPqJnYoGrSzgQsPwLFhLNYskDPyyA'
        self.assertFalse(Key.from_wif(wif).compressed)
        self.assertEqual(Key.from_wif(wif).address(), '17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem')


class TestPublicKeyConversion(unittest.TestCase):

    def setUp(self):
        self.publickey_hex = '043be860d524b1aef015d0e501333d5e62fd39652bfb89e6720c3eb1cb10754370eeee80b04abf2f80dec' \
                             '69431498723f6411e8e03446796fa250f8dfe3fa8ff84'
        self.K = Key(self.publickey_hex)
        self.KC = Key('034781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d5')

    def test_public_key_get_address_uncompressed(self):
        self.assertEqual('1BwbZw1fG91jMYsXh6hfnvPGXBaMcughNL', self.K.address_uncompressed())

    def test_public_key_get_address(self):
        self.assertEqual('1P2X35YnajqoBXtPpQXJzV1QMnqSZQsn82', self.KC.address())

    def test_public_key_get_point(self):
        self.assertEqual((27097034899423571266687886742220335326047800315940073646681141977460289913712,
                          108071855740589417275074236385664540865647915362450545389459678127463347060612),
                         self.K.public_point())

    def test_public_key_get_hash160_uncompressed(self):
        self.assertEqual('78049354383f043fb15a04be58a289ef8a2c03fa', self.K.hash160.hex())

    def test_public_key_get_hash160(self):
        self.assertEqual('f19c417fd97e364afb06e1edd2c0e6a7ecf1af00', self.KC.hash160.hex())

    def test_public_key_try_private(self):
        self.assertFalse(self.K.private_hex)

    def test_public_key_import_error(self):
        self.assertRaisesRegex(BKeyError, "Unrecognised key format",
                                Key, '064781e448a7ff0e1b66f1a249b4c952dae33326cf57c0a643738886f4efcd14d5')

    def test_litecoin_private_key(self):
        KC_LTC = Key('0bc295d0b20b0e2ff6ab2c4982583d4f84936a17689aaca031a803dcf4a3b139', network='litecoin')
        self.assertEqual(KC_LTC.wif(), 'T3SqWmDzttRHnfypMorvRgPpG48UH1ZE7apvoLUGTDidKtf3Ts2u')
        self.assertEqual(KC_LTC.address(), 'LeA97dLDPrjRsPhwrQJxUWJUPErGo516Ct')
        self.assertEqual(KC_LTC.public_hex, '02967b4671563ceeab16f22c36605d97fbf254fadba0fa48f75c03f27d11584f92')


class TestPublicKeyUncompressed(unittest.TestCase):

    def setUp(self):
        self.K = Key('025c0de3b9c8ab18dd04e3511243ec2952002dbfadc864b9628910169d9b9b00ec')

    def test_public_key_point(self):
        x = 41637322786646325214887832269588396900663353932545912953362782457239403430124
        y = 16388935128781238405526710466724741593761085120864331449066658622400339362166
        px, py = self.K.public_point()
        self.assertEqual(px, x)
        self.assertEqual(py, y)

    def test_public_key_uncompressed(self):
        self.assertEqual('045c0de3b9c8ab18dd04e3511243ec2952002dbfadc864b9628910169d9b9b00ec243bcefdd4347074d4'
                         '4bd7356d6a53c495737dd96295e2a9374bf5f02ebfc176',
                         self.K.public_uncompressed_hex)

    def test_public_key_address_uncompressed(self):
        self.assertEqual('1thMirt546nngXqyPEz532S8fLwbozud8', self.K.address_uncompressed())


class TestHDKeysImport(unittest.TestCase):

    def setUp(self):
        self.k = HDKey.from_seed('000102030405060708090a0b0c0d0e0f', witness_type='legacy')
        self.k2 = HDKey.from_seed('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a878'
                                  '4817e7b7875726f6c696663605d5a5754514e4b484542', witness_type='legacy')
        self.xpub = HDKey('xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqse'
                          'fD265TMg7usUDFdp6W1EGMcet8', witness_type='legacy')

    def test_hdkey_import_seed_1(self):

        self.assertEqual('xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TG'
                         'tRBeJgk33yuGBxrMPHi', self.k.wif(is_private=True))
        self.assertEqual('xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TM'
                         'g7usUDFdp6W1EGMcet8', self.k.wif())

    def test_hdkey_import_seed_2(self):
        self.assertEqual('xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3L'
                         'qFtT2emdEXVYsCzC2U', self.k2.wif(is_private=True))
        self.assertEqual('xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJ'
                         'Y47LJhkJ8UB7WEGuduB', self.k2.wif_public())

    def test_hdkey_random_legacy(self):
        self.k = HDKey(witness_type='legacy')
        self.assertEqual('xprv', self.k.wif(is_private=True)[:4])
        self.assertEqual(111, len(self.k.wif(is_private=True)))

    def test_hdkey_random(self):
        self.k = HDKey()
        self.assertEqual('zprv', self.k.wif(is_private=True)[:4])
        self.assertEqual(111, len(self.k.wif(is_private=True)))

    def test_hdkey_import_extended_private_key(self):
        extkey = 'xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4m' \
                 'LTj34bhnZX7UiM'
        self.k = HDKey(extkey)
        self.assertEqual(extkey, self.k.wif(is_private=True))

    def test_hdkey_import_extended_public_key(self):
        extkey = 'xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7' \
                 'DogT5Uv6fcLW5'
        self.k = HDKey(extkey)
        self.assertEqual(extkey, self.k.wif())

    def test_hdkey_import_simple_key(self):
        self.k = HDKey('L45TpiVN3C8Q3MoosGDzug1acpnFjysseBLVboszztmEyotdSJ9g', witness_type='legacy')
        self.assertEqual(
            'xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFAbeoRRpMHE67jGmBQKCr2YovK2G23x5uzaztRbEW9pc'
            'j6SqMFd', self.k.wif(is_private=True))

    def test_hdkey_import_bip38_key(self):
        if USING_MODULE_SCRYPT:
            self.k = HDKey('6PYNKZ1EAgYgmQfmNVamxyXVWHzK5s6DGhwP4J5o44cvXdoY7sRzhtpUeo', witness_type='legacy',
                           password='TestingOneTwoThree')
            self.assertEqual('L44B5gGEpqEDRS9vVPz7QT35jcBG2r3CZwSwQ4fCewXAhAhqGVpP', self.k.wif_key())

    def test_hdkey_import_public(self):
        self.assertEqual('15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', self.xpub.address())
        self.assertEqual('0339a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2',
                         self.xpub.public_hex)

    def test_hdkey_import_public_try_private(self):
        try:
            self.xpub.wif()
        except KeyError as e:
            self.assertEqual('WIF format not supported for public key', e.args[0])
        try:
            self.xpub.private_hex
        except KeyError as e:
            self.assertEqual('WIF format not supported for public key', e.args[0])

    def test_hdkey_import_segwit_wifs(self):
        wifs = [
            ('zprvAe9nVpMfBzSSSCr8WHYiv5a6TeSojETexJfZhvu9oYuENwQkEqRHH7nnwGzscgkCCu9S2PrwnD1VJHXXfLUbSG8yqZoKpi2CaoY'
             'Kdz7pKM1', True),
            ('zpub6s98uKtZ2MzjegvbcK5jHDWq1gHJ8hBWKXbAWKJmMtSDFjjtnNjXpv7GnXmDGZzG36XMgLaC3JewffU5pukcUtYuEpRJEkVAiFU'
             'mdA5GaXM', False),
            ('yprvAEWM3LZ7vwNRTroi67SjcpexaVEdbEMAgHbiefDibSqssbrqyh9joH6BY6DRzkoGMX9nLxXoa5yYT64r3zQ2i9sQa51iQhzjwUj'
             '2UJ2GES4', True),
            ('Ypub6jkwv4tzCZJNe6j1JHZgwUmj6yCi5iEBNHrP1RDFyR13RwRNB5foJWeinpcBTqfv2uUe7mWSwsF1am4cVLN99xrkADPWrDick3S'
             'aP8nxY8N', False)
        ]
        for wif in wifs:
            self.assertEqual(HDKey(wif[0]).wif(is_private=wif[1]), wif[0])

    def test_hdkey_import_from_private_byte(self):
        keystr = b"fch\xe4w\xa8\xdd\xd4h\x08\xc5'\xcc<Pg\x19\xbb?R\xa9'\xb6\xc152\x98KqKV\xad\x91`G-a\xb1\xad\xd8eL" \
                 b"\xcc\x8an\x94\xa3\x93\xb5\xa5\xe6\xc3\xf1\x98\x91h6wt\xf0z=\x1f\x17"
        hdkey = HDKey(keystr, witness_type='legacy')
        self.assertEqual(hdkey.address(), '17N9VQbP89ThunSq7Yo2VooXCFTW1Lp8bd')

    def test_hdkey_import_private_uncompressed(self):
        wif = ('BC12Se7KL1uS2bA6QNFneYit57Ac2wGdCrn5CTr94xr1NqLxvPozYzpm4d72ojPFnpLyAgpoXdad78PL9HaATYH2Y695hYcs8AF'
               '1iLxUL5fk2jQv')
        pk_hex = '681e34705a758455e75d761a8d33aaef6d0507e3750fb7c3848ab119438626a3'
        pubkey_uncompressed = (
            '04007d7ff2fbf9486746f8beffc34e7a68f06a4938edd3b1eed4a2fe23148423c7e8d714ef853988adc2fef434'
            '3ccdcb07356cfd9b8f361e3c8ec43598210c946d')
        pubkey_compressed = '03007d7ff2fbf9486746f8beffc34e7a68f06a4938edd3b1eed4a2fe23148423c7'

        k = HDKey(wif, compressed=False)
        self.assertFalse(k.compressed)
        self.assertEqual(k.private_hex, pk_hex)
        self.assertEqual(k.public_hex, pubkey_uncompressed)

        k2 = HDKey.from_wif(wif, compressed=False)
        self.assertFalse(k2.compressed)
        self.assertEqual(k2.private_hex, pk_hex)
        self.assertEqual(k2.public_hex, pubkey_uncompressed)

        k3 = HDKey.from_wif(wif)
        self.assertTrue(k3.compressed)
        self.assertEqual(k3.private_hex, pk_hex)
        self.assertEqual(k3.public_hex, pubkey_compressed)


class TestHDKeysChildKeyDerivation(unittest.TestCase):

    def setUp(self):
        self.k = HDKey.from_seed('000102030405060708090a0b0c0d0e0f', witness_type='legacy')
        self.k2 = HDKey.from_seed('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8'
                                  '784817e7b7875726f6c696663605d5a5754514e4b484542', witness_type='legacy')

    def test_hdkey_path_m_0h(self):
        sk = self.k.subkey_for_path('m/0H')
        self.assertEqual('xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7'
                         'XnxHrnYeSvkzY7d2bhkJ7', sk.wif(is_private=True))
        self.assertEqual('xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9x'
                         'v5ski8PX9rL2dZXvgGDnw', sk.wif())

    def test_hdkey_path_m_0h_1(self):
        sk = self.k.subkey_for_path('m/0H/1')
        self.assertEqual('xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H'
                         '2EU4pWcQDnRnrVA1xe8fs', sk.wif(is_private=True))
        self.assertEqual('xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqc'
                         'k2AxYysAA7xmALppuCkwQ', sk.wif())

    def test_hdkey_path_m_0h_1_2h(self):
        sk = self.k.subkey_for_path('m/0h/1/2h')
        self.assertEqual('xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjAN'
                         'TtpgP4mLTj34bhnZX7UiM', sk.wif(is_private=True))
        self.assertEqual('xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4'
                         'trkrX7x7DogT5Uv6fcLW5', sk.wif())

    def test_hdkey_path_m_0h_1_2h_1000000000(self):
        sk = self.k.subkey_for_path('m/0h/1/2h/2/1000000000')
        self.assertEqual('xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUi'
                         'hUZREPSL39UNdE3BBDu76', sk.wif(is_private=True))
        self.assertEqual('xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTv'
                         'XEYBVPamhGW6cFJodrTHy',
                         sk.wif_public())

    def test_hdkey_path_key2(self):
        sk = self.k2.subkey_for_path('m/0/2147483647h/1/2147483646h/2')
        self.assertEqual('xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEc'
                         'BYJUuekgW4BYPJcr9E7j',
                         sk.wif(is_private=True))
        self.assertEqual('xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb'
                         '9rXpVGyy3bdW6EEgAtqt',
                         sk.wif_public())

    def test_hdkey_path_M_0_1_public(self):
        sk = self.k.subkey_for_path('M/0/1')
        self.assertEqual('xpub6AvUGrnEpfvJBbfx7sQ89Q8hEMPM65UteqEX4yUbUiES2jHfjexmfJoxCGSwFMZiPBaKQT1RiKWrKfuDV4vpgVs'
                         '4Xn8PpPTR2i79rwHd4Zr', sk.wif())

    def test_hdkey_path_invalid(self):
        with self.assertRaises(BKeyError):
            self.k2.subkey_for_path('m/0/').wif()

    def test_hdkey_path_invalid2(self):
        with self.assertRaises(BKeyError):
            self.k2.subkey_for_path('m/-1').wif()

    def test_hdkey_bip44_account(self):
        pk = 'tprv8ZgxMBicQKsPdvHCP6VxtFgowj2k7nBJnuRiVWE4DReDFojkLjyqdT8mtR6XJK9dRBcaa3RwvqiKFjsEQVhKfQmHZCCYf4jRTWv' \
             'JuVuK67n'
        k = HDKey(pk)
        self.assertEqual(k.public_master(3, 45, as_private=True).private_hex,
                         '232b9d7b48fa4ca6e842f09f6811ff03cf33ba0582b4cca5752deec2e746c186')

    def test_hdkey_bip44_account_litecoin(self):
        pk = 'Ltpv71G8qDifUiNes8hK1m3ZjL3bW76X4AKF3J26FVDM5awe6mWdyyzZgTrbvkK5z4WQyKkyVnDvC56KfRaHHhcZjWcWvRFCzBYUsCc' \
             'FoNNHjck'
        k = HDKey(pk, network='litecoin')
        self.assertEqual(k.public_master().address(), 'LZ4gg2m6uNY3vj9RUFkderRP18ChTwWyiq')

    def test_hdkey_derive_from_public_error(self):
        k = HDKey().public()
        self.assertRaisesRegex(BKeyError, "Need a private key to create child private key", k.child_private)
        k0 = HDKey()
        k1 = k0.child_private(10, hardened=True)
        self.assertRaisesRegex(BKeyError, "Cannot derive hardened key from public private key",
                                k1.child_public, 2147483659)


class TestHDKeysPublicChildKeyDerivation(unittest.TestCase):

    def setUp(self):
        self.K = HDKey('xpub6ASuArnXKPbfEVRpCesNx4P939HDXENHkksgxsVG1yNp9958A33qYoPiTN9QrJmWFa2jNLdK84bWmyqTSPGtApP8P'
                       '7nHUYwxHPhqmzUyeFG')
        self.k = HDKey('xprv9wTYmMFdV23N21MM6dLNavSQV7Sj7meSPXx6AV5eTdqqGLjycVjb115Ec5LgRAXscPZgy5G4jQ9csyyZLN3PZLxoM'
                       '1h3BoPuEJzsgeypdKj')

    def test_hdkey_derive_public_child_key(self):
        self.assertEqual('1BvgsfsZQVtkLS69NvGF8rw6NZW2ShJQHr', self.K.child_public(0).address())

    def test_hdkey_derive_public_child_key2(self):
        self.assertEqual('17JbSP83rPWmbdcdtiiTNqBE8MgGN8kmUk', self.K.child_public(8).address())

    def test_hdkey_private_key(self):
        self.assertEqual('KxABnXp7SiuWi218c14KkjEMV7SjcfXnvsWaveNVxWZU1Rwi8zNQ',
                         self.k.child_private(7).wif_key())

    def test_hdkey_private_key_hardened(self):
        self.k2 = HDKey('xprv9s21ZrQH143K31AgNK5pyVvW23gHnkBq2wh5aEk6g1s496M8ZMjxncCKZKgb5j'
                        'ZoY5eSJMJ2Vbyvi2hbmQnCuHBujZ2WXGTux1X2k9Krdtq')
        self.assertEqual('xprv9wTErTSu5AWGkDeUPmqBcbZWX1xq85ZNX9iQRQW9DXwygFp7iRGJo79dsVctcsCHsnZ3XU3DhsuaGZbDh8iDkB'
                         'N45k67UKsJUXM1JfRCdn1', str(self.k2.subkey_for_path('3/2H').wif(is_private=True)))

    def test_hdkey_litecoin(self):
        k = HDKey('Ltpv71G8qDifUiNetj2H4no6Q4oB8o2eUH8tSU2BsJDGyKTyMJ6ejPDXHWtQeTzKQdEeEexxyw3vSAYtxnAz3qYZc'
                  '59jfTiqHLzjKkwJ9iDJ1uC', network='litecoin')
        self.assertEqual('LWsiwZnGg74CFHEaLPzfASxktrzDYYSwvM', k.child_public(0).address())
        self.assertEqual('LfH72Fgeikvhu1y5rtMAkQ5SS5aJJUafLX', k.child_public(100).address())
        self.assertEqual('T65a5dNtdayWp9F638f8fokiyixCA4fhyzb7FWFYXjejqjaxKRSc', k.child_private(6).wif_key())
        self.assertEqual('Ltpv75tiiksDF3fUqK8jkAfwY1h3zDLs3oCFQa5wXDNh981n6LDJZ6juFWUJwwkN3pKbr3diSdMkZfYAhwhkhjP9qG'
                         'wviSbMXtEJYxoH2m3FbDQ', str(k.subkey_for_path('3H/1').wif(is_private=True)))


class TestHDKeys(unittest.TestCase):

    def test_hdkey_testnet_random(self):
        self.k = HDKey(network='testnet', witness_type='legacy')

        self.assertEqual('tprv', self.k.wif(is_private=True)[:4])
        self.assertEqual('tpub', self.k.wif_public()[:4])
        self.assertIn(self.k.address()[:1], ['m', 'n'])

    def test_hdkey_testnet_import(self):
        self.k = HDKey('tprv8ZgxMBicQKsPf2S18qpSypHPZBK7mdiwvXHPh5TSjGjm2pLacP4tEqVjLVyagTLLgSZK4YyBNb4eytBykE755Kc'
                       'L9YXAqPtfERNRfwRt54M')

        self.assertEqual('cPSokRrLueavzAmVBmAXwgALkumRNMN9pErvRLAXvx58NBJAkEYJ', self.k.wif_key())
        self.assertEqual('tpubD6NzVbkrYhZ4YVTo2VV3PDwW8Cq3vxurVptAybVk9YY9sJbMEmtURL7bWgKxXSWSahXu6HbHkdpjBGzwYYkJm'
                         'u2VmoeHuiTmzHZpJo8Cdpb', self.k.wif_public())
        self.assertEqual('n4c8TKkqUmj3b8VJrTioiZuciyaCDRd6iE', self.k.address())

    def test_hdkey_uncompressed_key_conversion(self):
        key = Key('5JGSWMSfKiXVDvXzUeod8HeSsGRpHWQgrETithYjZKcxWNpexVK')
        hdkey = HDKey(key)
        hdkey_uncompressed = HDKey(hdkey.wif(is_private=True), compressed=False)
        hdkey_compressed = HDKey(hdkey.wif(is_private=True))

        self.assertFalse(key.compressed)
        self.assertFalse(hdkey.compressed)
        self.assertEqual(hdkey_uncompressed.private_hex, hdkey_compressed.private_hex)
        self.assertEqual(hdkey_uncompressed.wif(), hdkey.wif())
        self.assertEqual(hdkey_compressed.wif_key(), 'KyD9aZEG9cHZa3Hnh3rnTAUHAs6XhroYtJQwuBy4qfBhzHGEApgv')

    def test_hdkey_wif_prefixes(self):
        for network in list(NETWORK_DEFINITIONS.keys()):
            k = HDKey(network=network)
            for witness_type in ['legacy', 'p2sh-segwit', 'segwit']:
                for multisig in [False, True]:
                    if (network[:4] == 'doge' or network[:4] == 'dash') and witness_type != 'legacy':
                        break
                    kwif = k.wif_private(witness_type=witness_type, multisig=multisig)
                    hdkey = wif_prefix_search(kwif, witness_type=witness_type, multisig=multisig, network=network)
                    pwif = k.wif_public(witness_type=witness_type, multisig=multisig)
                    hdkey_pub = wif_prefix_search(pwif, witness_type=witness_type, multisig=multisig, network=network)
                    self.assertTrue(kwif[:4] == hdkey[0]['prefix_str'])
                    self.assertTrue(pwif[:4] == hdkey_pub[0]['prefix_str'])

    def test_hdkey_info(self):
        k = HDKey()
        self.assertIsNone(k.info())

    def test_hdkey_network_change(self):
        pk = '688e4b153100f6d4526a00a3fffb47d971a32a54950ec00fab8c22fa8480edfe'
        k = HDKey(pk, witness_type='legacy')
        k.network_change('litecoin')
        self.assertEqual(k.address(), 'LPsPTgctprGZ6FEc7QFAugr6qg8XV3X4tg')

    def test_hdkey_formats(self):
        pkhex = '036e770e764c8c03acd620030c2844dd09d7c756ecedeb0521fe075301caf0e6ad'
        k = HDKey(pkhex)
        self.assertEqual(k.as_bytes(), bytes.fromhex(pkhex))
        self.assertEqual(k.as_hex(), pkhex)


class TestBip38(unittest.TestCase):

    def setUp(self):
        workdir = os.path.dirname(__file__)
        with open('%s/%s' % (workdir, 'bip38_protected_key_tests.json'), 'r') as f:
            self.vectors = json.load(f)

    def test_encrypt_private_key(self):
        if not USING_MODULE_SCRYPT:
            return
        for v in self.vectors["valid"]:
            if v.get('test_encrypt') is False:
                continue
            k = Key(v['wif'])
            # print("Check %s + %s = %s " % (v['wif'], v['passphrase'], v['bip38']))
            self.assertEqual(str(v['bip38']), k.encrypt(str(v['passphrase'])))

    def test_decrypt_bip38_key(self):
        if not USING_MODULE_SCRYPT:
            return
        for v in self.vectors["valid"]:
            k = Key(v['bip38'], password=str(v['passphrase']))
            # print("Check %s - %s = %s " % (v['bip38'], v['passphrase'], v['wif']))
            self.assertEqual(str(v['wif']), k.wif())

    def test_bip38_invalid_keys(self):
        if not USING_MODULE_SCRYPT:
            return
        for v in self.vectors["invalid"]["verify"]:
            # print("Checking invalid key %s" % v['base58'])
            self.assertRaisesRegex(Exception, "", Key, str(v['base58']))

    def test_bip38_other_networks(self):
        if not USING_MODULE_SCRYPT:
            return
        networks = ['testnet', 'litecoin', 'dogecoin']
        for network in networks:
            k = Key(network=network)
            enc_key = k.encrypt('password')
            k2 = Key(enc_key, password='password', network=network)
            self.assertEqual(k.wif(), k2.wif())

    def test_bip38_hdkey_method(self):
        pkwif = '5HtasZ6ofTHP6HCwTqTkLDuLQisYPah7aUnSKfC7h4hMUVw2gi5'
        bip38_wif = '6PRNFFkZc2NZ6dJqFfhRoFNMR9Lnyj7dYGrzdgXXVMXcxoKTePPX1dWByq'
        k = HDKey(pkwif, witness_type='legacy')
        self.assertEqual(k.encrypt('Satoshi'), bip38_wif)

    def test_bip38_intermediate_password(self):
        password1 = 'passphraseb7ruSN4At4Rb8hPTNcAVezfsjonvUs4Qo3xSp1fBFsFPvVGSbpP2WTJMhw3mVZ'
        intpwd1 = bip38_intermediate_password(passphrase="TestingOneTwoThree", lot=199999, sequence=1,
                                    owner_salt="75ed1cdeb254cb38")
        self.assertEqual(password1, intpwd1)
        self.assertEqual(bip38_intermediate_password(passphrase="TestingOneTwoThree")[:10], 'passphrase')

        intermediate_codes = [
            {"passphrase": "MOLON LABE", "lot": None, "sequence": None, "owner_salt": "d7ebe42cf42a79f4",
             "intermediate_passphrase": "passphraserDFxboKK9cTkBQMb73vdzgsXB5L6cCMFCzTVoMTpMWYD8SJXv3jcKyHbRWBcza"},
            {"passphrase": "MOLON LABE", "lot": 100000, "sequence": 1, "owner_salt": "d7ebe42cf42a79f4",
             "intermediate_passphrase": "passphrasedYVZ6EdRqSmcHHsYWmJ7wzWcWYuDQmf9EGH9Pnrv67eHy4qswaAGGc8Et3eeGp"},
            {"passphrase": "MOLON LABE", "lot": 100000, "sequence": 1, "owner_salt": "d7ebe42c",
             "intermediate_passphrase": "passphrasedYVZ6EdRqSmcHHsYWmJ7wzWcWYuDQmf9EGH9Pnrv67eHy4qswaAGGc8Et3eeGp"}
        ]
        for ic in intermediate_codes:
            intermediate_password = bip38_intermediate_password(ic['passphrase'], ic['lot'], ic['sequence'],
                                                                ic['owner_salt'])
            self.assertEqual(intermediate_password, ic['intermediate_passphrase'])

    def test_bip38_create_new_encrypted_wif(self):
        create_new_encrypted_wif = [
            {"intermediate_passphrase": "passphraserDFxboKK9cTkBQMb73vdzgsXB5L6cCMFCzTVoMTpMWYD8SJXv3jcKyHbRWBcza",
             "seed": "9b6cad86daddae99ac3b76c1e47e61bc7f4665d02e10c290",
             "encrypted_wif": "6PnQDk5XngQugiy1Fi2kzzgKAQrxZrtQDGNFiQTMamjiJcjBT4LhXdnhNf",
             "confirmation_code": "cfrm38VUF9PjRxQojZERDySt9Q7Z9FSdhQkMP5RFsouS4y3Emf2YD2CXXMCypQvv94dJujaPTfq",
             "public_key": "0348ca8b4e7c0c75ecfd4b437535d186a12f3027be0c29d2125e9c0dec48677caa",
             "compressed": True, "address": "16uZsrjjENCVsXwJqw2kMWGwWbDKQ12a1h", "network": "bitcoin"},
            {"intermediate_passphrase": "passphrasedYVZ6EdRqSmcHHsYWmJ7wzWcWYuDQmf9EGH9Pnrv67eHy4qswaAGGc8Et3eeGp",
             "seed": "9b6cad86daddae99ac3b76c1e47e61bc7f4665d02e10c290",
             "encrypted_wif": "6PgRAPfrPWjPXfC6x9XB139RHzUP8GFcVen5Ju3qJDhRP69Q4Vd8Wbct6B",
             "confirmation_code": "cfrm38V8kEzECGczWJmEoGuYfkoamcmVij3tHUhD6DEEquSRXp61HzhnT8jwQwBBZiKs9Jg4LXZ",
             "public_key": "04597967956e7f4c0e13ed7cd98baa9d7697a7f685d4347168e4a011c5fe6ba628e06ef89587c17afb5504"
                           "4336e44648dfa944ca85a4af0a7b28c29d4eefd0da92",
             "compressed": False, "address": "1KRg2YJxuHiNcqfp9gVpkgRFhcvALy1zgk", "network": "bitcoin"},
            {"intermediate_passphrase": "passphrasedYVZ6EdRqSmcHHsYWmJ7wzWcWYuDQmf9EGH9Pnrv67eHy4qswaAGGc8Et3eeGp",
             "seed": "9b6cad86daddae99ac3b76c1e47e61bc7f4665d02e10c290",
             "encrypted_wif": "6PgEuJVC5CJV4m9f5NgmW1MQCV56XyQ3ZASqckdz4s3PAznxKRi9H6JW5c",
             "confirmation_code": "cfrm38V8AorwLxaG1GThhCDdS2Av74pRkojnePAS69nscD93DDVchgcjg1o8mxpXSJRaZbXFUYv",
             "public_key": "04597967956e7f4c0e13ed7cd98baa9d7697a7f685d4347168e4a011c5fe6ba628e06ef89587c17afb5504"
                           "4336e44648dfa944ca85a4af0a7b28c29d4eefd0da92",
             "compressed": False, "address": "LdedHkcnywxRseMyKpV82hV1uqHSU2m1ez", "network": "litecoin"}
        ]
        for ew in create_new_encrypted_wif:
            res = bip38_create_new_encrypted_wif(ew["intermediate_passphrase"], ew["compressed"], ew["seed"],
                                                 network=ew["network"])
            self.assertEqual(res['encrypted_wif'], ew['encrypted_wif'])
            self.assertEqual(res['confirmation_code'], ew['confirmation_code'])
            self.assertEqual(res['address'], ew['address'])

    def test_bip38_decrypt_wif(self):
        bip38_decrypt_test_vectors = [
            {"encrypted_wif": "6PRL8jj6dLQjBBJjHMdUKLSNLEpjTyAfmt8GnCnfT87NeQ2BU5eAW1tcsS",
             "passphrase": "TestingOneTwoThree",
             "network": "testnet", "wif": "938jwjergAxARSWx2YSt9nSBWBz24h8gLhv7EUfgEP1wpMLg6iX",
             "private_key": "cbf4b9f70470856bb4f40f80b87edb90865997ffee6df315ab166d713af433a5", "wif_type": "wif",
             "public_key": "04d2ce831dd06e5c1f5b1121ef34c2af4bcb01b126e309234adbc3561b60c9360ea7f23327b49ba7f10d17fad15f068b8807dbbc9e4ace5d4a0b40264eefaf31a4",
             "compressed": False, "seed": None, "address": "myM3eoxWDWxFe7GYHZw8K21rw7QDNZeDYM", "lot": None,
             "sequence": None},
            {"encrypted_wif": "6PYVB5nHnumbUua1UmsAMPHWHa76Ci48MY79aKYnpKmwxeGqHU2XpXtKvo",
             "passphrase": "TestingOneTwoThree",
             "network": "testnet", "wif": "cURAYbG6FtvUasdBsooEmmY9MqUfhJ8tdybQWV7iA4BAwunCT2Fu",
             "private_key": "cbf4b9f70470856bb4f40f80b87edb90865997ffee6df315ab166d713af433a5",
             "wif_type": "wif-compressed",
             "public_key": "02d2ce831dd06e5c1f5b1121ef34c2af4bcb01b126e309234adbc3561b60c9360e",
             "compressed": True, "seed": None, "address": "mkaJhmE5vvaXG17uZdCm6wKpckEfnG4yt9", "lot": None,
             "sequence": None},
        ]

        for tv in bip38_decrypt_test_vectors:
            res = bip38_decrypt(tv['encrypted_wif'], tv['passphrase'])
            self.assertEqual(res[0].hex(), tv['private_key'])
            self.assertEqual(res[2], tv['compressed'])


class TestKeysBulk(unittest.TestCase):
    """
    Test Child Key Derivation

    Use the 2 different methods to derive child keys. One through derivation from public parent,
    and one thought private parent. They should be the same.
    """

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
            pub_with_pubparent = self.K.child_public(i).address()
            pub_with_privparent = self.k.child_private(i).address()
            # if pub_with_privparent != pub_with_pubparent:
            #     print("Error index %4d: pub-child %s, priv-child %s" % (i, pub_with_privparent, pub_with_pubparent))
            self.assertEqual(pub_with_pubparent, pub_with_privparent)

    def test_hdkey_derive_from_public_and_private_random(self):
        global BULKTESTCOUNT
        if not BULKTESTCOUNT:
            self.skipTest("Skip bulktesting. Bulktestcount == 0")
        for i in range(BULKTESTCOUNT):
            k = HDKey()
            pubk = HDKey(k.wif_public())
            pub_with_pubparent = pubk.child_public().address()
            pub_with_privparent = k.child_private().address()
            # if pub_with_privparent != pub_with_pubparent:
            #     print("Error random key: %4d: pub-child %s, priv-child %s" %
            #           (i, pub_with_privparent, pub_with_pubparent))
            self.assertEqual(pub_with_pubparent, pub_with_privparent)


class TestAddress(unittest.TestCase):
    """
    Tests for Address class. Address format, conversion and representation

    """

    def test_keys_address_import_conversion(self):
        address_legacy = '3LPrWmWj1pYPEs8dGsPtWfmg2E9LhL5BHj'
        address = 'MSbzpevgxwPp3NQXNkPELK25Lvjng7DcBk'
        ac = Address.parse(address_legacy, network_overrides={"prefix_address_p2sh": "32"})
        self.assertEqual(ac.address, address)

    def test_keys_address_encodings(self):
        pk = '7cc7ed043b4240945e744387f8943151de86843025682bf40fa94ef086eeb686'
        a = Address(pk, network='testnet', witness_type='legacy')
        self.assertEqual(a.address, 'mmAXD1HJtV9pdffPvBJkuT4qQrbFMwb4pR')
        self.assertEqual(a.with_prefix(b'\x88'), 'wpcbpijWdzjj5W9ZXfdj2asW9U2q7gYCmw')
        a = Address(pk, script_type='p2sh', network='testnet', witness_type='legacy')
        self.assertEqual(a.address, '2MxtnuEcoEpYJ9WWkzqcr87ChujVRk1DFsZ')
        a = Address(pk, encoding='bech32', network='testnet')
        self.assertEqual(a.address, 'tb1q8hehumvm039nxnwwtqdjr7qmm46sfxrdw7vc3g')

    def test_keys_address_deserialize_exceptions(self):
        self.assertRaisesRegex(BKeyError, "Invalid address 17N9VQbP89ThunSq7Yo2VooXCFTW1Lp8bb, checksum incorrect",
                                deserialize_address, '17N9VQbP89ThunSq7Yo2VooXCFTW1Lp8bb', encoding='base58')
        self.assertRaisesRegex(EncodingError,
                                "Address 17N9VQbP89ThunSq7Yo2VooXCFTW1Lp8bd is not in specified encoding bs",
                                deserialize_address, '17N9VQbP89ThunSq7Yo2VooXCFTW1Lp8bd', encoding='bs')
        self.assertRaisesRegex(EncodingError,
                                "Invalid address 17N9VQbP89ThunSq7Yo2VooXCFTW1Lp8bb: "
                                "Invalid bech32 character in bech string",
                                deserialize_address, '17N9VQbP89ThunSq7Yo2VooXCFTW1Lp8bb', encoding='bech32')
        self.assertRaisesRegex(EncodingError,
                                "Address bc1qk077yl8zf6yty25rgrys8h40j8adun267y3m44 is not in specified "
                                "encoding base58",
                                deserialize_address, 'bc1qk077yl8zf6yty25rgrys8h40j8adun267y3m44', encoding='base58')

    def test_keys_address_deserialize_litecoin(self):
        address = '3N59KFZBzpnq4EoXo2cDn2GKjX1dfkv1nB'
        addr_dict = deserialize_address(address, network='litecoin_legacy')
        self.assertEqual(addr_dict['network'], 'litecoin_legacy')

    def test_keys_address_litecoin_import(self):
        address = 'LUPKYv9Z7AvQgxuVkDdqQrBDswsQJMxsN8'
        a = Address.parse(address)
        self.assertEqual(a.hashed_data, '647ea562d9e72daca10fa476297f10576f284ba4')
        self.assertEqual(a.network.name, 'litecoin')
        self.assertEqual(a.address_orig, 'LUPKYv9Z7AvQgxuVkDdqQrBDswsQJMxsN8')

    def test_keys_address_deserialize_bech32(self):
        address = 'bc1qk077yl8zf6yty25rgrys8h40j8adun267y3m44'
        addr_dict = deserialize_address(address)
        self.assertEqual(addr_dict['public_key_hash'], 'b3fde27ce24e88b22a8340c903deaf91fade4d5a')
        self.assertEqual(addr_dict['encoding'], 'bech32')
        self.assertEqual(addr_dict['script_type'], 'p2wpkh')

    def test_key_address_p2sh_p2wpkh(self):
        pk = 'd80229e1b5eae5b4f9e11698d73f5468e45631e6d256e500ceb51f4f49d99e78'
        addr = Address(HDKey(pk).public_byte, script_type='p2sh_p2wpkh')
        self.assertEqual(addr.redeemscript, b"\x00\x14\x1e\xf4h\x07'\x1bM4RJ\xb9b\x11\xb9X\x81h\xdei:")
        self.assertEqual(addr.address, '3Disr2CmERuYuuMkkfGrjRUHqDENQvtNep')

    def test_keys_address_deserialize_bech32_p2wsh(self):
        address = 'bc1qcuk5gxz4v962tne5mld4ztjakktmlupqd7jxn5k57774fuyzzplszs4ppd'
        addr_dict = deserialize_address(address)
        self.assertEqual(addr_dict['public_key_hash'],
                         'c72d4418556174a5cf34dfdb512e5db597bff0206fa469d2d4f7bd54f082107f')
        self.assertEqual(addr_dict['encoding'], 'bech32')
        self.assertEqual(addr_dict['script_type'], 'p2wsh')

    def test_keys_address_conversion(self):
        self.assertEqual(addr_convert('1GMDUKLom6bJuY37RuFNc6PHv1rv2Hziuo', prefix='bc', to_encoding='bech32'),
                         'bc1q4pwfmstmw8q80nxtxud2h42lev9xzcjqwqyq7t')
        self.assertEqual(addr_convert('1GMDUKLom6bJuY37RuFNc6PHv1rv2Hziuo', prefix=b'\x05'),
                         '3H3EPrqFJzugzhjYYzuy2ikE4Y9dWPJjnQ')
        self.assertEqual(addr_convert('bc1q4pwfmstmw8q80nxtxud2h42lev9xzcjqwqyq7t', prefix=b'\x00',
                                      to_encoding='base58'), '1GMDUKLom6bJuY37RuFNc6PHv1rv2Hziuo')
        self.assertEqual(addr_convert('bc1q4pwfmstmw8q80nxtxud2h42lev9xzcjqwqyq7t', prefix='tb'),
                         'tb1q4pwfmstmw8q80nxtxud2h42lev9xzcjqyxln9c')

    def test_keys_address_import_ambigue_bech32(self):
        # Import bech32 address with only base58 characters
        pk = '73c32f225a98ac084565429d5a15148dad5d9f6ef7cc7a5d901c9dfd6bb6027a'
        addr = Address(HDKey(pk).public_hex, witness_type='segwit')
        self.assertEqual(deserialize_address(addr.address, encoding='bech32')['encoding'], 'bech32')

    def test_keys_hdkey_segwit(self):
        k1 = HDKey('L1TZxZ9RgwFKiGPm6P7J9REQFKG9ymwLSsTwQSwxzLyDJs3CcRkF', witness_type='segwit')
        self.assertEqual(k1.address(), 'bc1qmk9myu4zf590ae2mfq3m63rlfhd5scatl4ckmw')
        self.assertEqual(k1.address_obj.data, '024429dd84f7c12c83f1920d60c7edb60c61d03fa5b8a8b526f4608ae9af89d9f3')
        phrase = 'scan display embark segment deputy lesson vanish second wonder erase crumble swing'
        k2 = HDKey.from_passphrase(phrase, witness_type='segwit', multisig=True)
        self.assertEqual(k2.address(), 'bc1qvj6c7n0hpl9t5r80zya4uukf0zens8ulxgwc0avnxsengtr5juss4pqeqy')

    def test_keys_address_p2tr(self):
        public_hash = b'\xa3|9\x03\xc8\xd0\xdbe\x12\xe2\xb4\x0b\r\xff\xa0^Z:\xb76\x03\xce\x8c\x9cKwq\xe5A#(\xf9'
        address = 'bc1p5d7rjq7g6rdk2yhzks9smlaqtedr4dekq08ge8ztwac72sfr9rusxg3297'
        self.assertEqual(Address(hashed_data=public_hash, script_type='p2tr', encoding='bech32').address, address)

    def test_keys_address_p2tr_bcrt(self):
        # Compared with taproot-workshop p2tr address generation
        hashed_data = '07bd8d4b39db0ee37e17a5e814b41a8aa33ef3a72742bcc65c716e4ce0f1d8cf'
        addr = Address(hashed_data=hashed_data, script_type='p2tr', prefix='bcrt',
                       encoding='bech32').address
        self.assertEqual(addr, 'bcrt1pq77c6jeemv8wxlsh5h5pfdq6323naua8yapte3juw9hyec83mr8sw2eggg')

    def test_keys_address_witness_types(self):
        data = b'\x03\xb0\x12\x86\x15bt\xc9\x0f\xa7\xd0\xf6\xe6\x17\xc9\xc6\xafS\xa0u/ou\x8d\xa5\x1d\x1c\xc9h4nl\xb8'
        a = Address(data)
        self.assertEqual(a.address, 'bc1q36cn4tunsaptdskkf29lerzym0uznqw26pxffm')
        self.assertEqual(a.witness_type, 'segwit')
        a = Address(data, witness_type='segwit')
        self.assertEqual(a.address, 'bc1q36cn4tunsaptdskkf29lerzym0uznqw26pxffm')
        self.assertEqual(a.witness_type, 'segwit')
        a = Address(data, witness_type='legacy')
        self.assertEqual(a.address, '1E1VGLvZ2YpgcSgr3DYm7ZTHbovKw9xLw6')
        self.assertEqual(a.witness_type, 'legacy')


class TestKeysSignatures(unittest.TestCase):

    def test_signatures(self):
        sig_tests = [
            # txid, key_hex, k, signature, DER encoded sign.
            ('0d12fdc4aac9eaaab9730999e0ce84c3bd5bb38dfd1f4c90c613ee177987429c',
             'b2da575054fb5daba0efde613b0b8e37159b8110e4be50f73cbe6479f6038f5b', 1002,
             '70b55404702ffa86ecfa4e88e0f354004a0965a5eea5fbbd297436001ae920df5da0917d7bd645c2a09671894375e3d353313'
             '8e8de09bc89cb251cbfae4cc523',
             '3044022070b55404702ffa86ecfa4e88e0f354004a0965a5eea5fbbd297436001ae920df02205da0917d7bd645c2a09671894'
             '375e3d3533138e8de09bc89cb251cbfae4cc523'),
            (b'\r\x12\xfd\xc4\xaa\xc9\xea\xaa\xb9s\t\x99\xe0\xce\x84\xc3\xbd[\xb3\x8d\xfd\x1fL\x90\xc6\x13\xee\x17y'
             b'\x87B\x9c',
             'b2da575054fb5daba0efde613b0b8e37159b8110e4be50f73cbe6479f6038f5b', 1002,
             '70b55404702ffa86ecfa4e88e0f354004a0965a5eea5fbbd297436001ae920df5da0917d7bd645c2a09671894375e3d353313'
             '8e8de09bc89cb251cbfae4cc523',
             '3044022070b55404702ffa86ecfa4e88e0f354004a0965a5eea5fbbd297436001ae920df02205da0917d7bd645c2a09671894'
             '375e3d3533138e8de09bc89cb251cbfae4cc523'),
            ('01000000978ee762c58d54f55f604c666218620cc3e665180f45098bb329d2a3d873cb733bb13029ce7b1f559ef5e747fcac4'
             '39f1455a2ec7c5f09b72290795e70665044babdf37f9e78ce9886cf8814d6c2fa590ade790dc7177da742867b3c5b35a81d00'
             '0000001976a91478fa2e39b03d5e98027665c3a69371c01ee031ee88aca086010000000000ffffffff98c930a52608751d9dd'
             '31d63c3ce09deb473e8de5c0a6ed2e3273dc6747d7bc60000000001000000',
             'b2da575054fb5daba0efde613b0b8e37159b8110e4be50f73cbe6479f6038f5b', 1002,
             '70b55404702ffa86ecfa4e88e0f354004a0965a5eea5fbbd297436001ae920df5da0917d7bd645c2a09671894375e3d353313'
             '8e8de09bc89cb251cbfae4cc523',
             '3044022070b55404702ffa86ecfa4e88e0f354004a0965a5eea5fbbd297436001ae920df02205da0917d7bd645c2a09671894'
             '375e3d3533138e8de09bc89cb251cbfae4cc523'),
            ('e63be0b7ef061a60dd03fab16c19c496a0f4905639413d41a8fd3a705f2e486b',
             'fd4b7465dadd8e8fe2dd8b8fa505c619e2959d5a6438daf7716a47e4617524a2', 1234567890,
             '2b698a0f0a4041b77e63488ad48c23e8e8838dd1fb7520408b121697b782ef226875b0fec3497d7cd812912003d5a44ed2965'
             '0d339299081debf75c29dc4dbc6',
             '304402202b698a0f0a4041b77e63488ad48c23e8e8838dd1fb7520408b121697b782ef2202206875b0fec3497d7cd81291200'
             '3d5a44ed29650d339299081debf75c29dc4dbc6'),
            ('c77545c8084b6178366d4e9a06cf99a28d7b5ff94ba8bd76bbbce66ba8cdef70',
             HDKey('xprv9s21ZrQH143K2YEun3sBzwSaFLn6bnBa6nkodJrDfZSty6L7Ba9JR5tMdhc7viB9dPu6LpQ9UqrsDsrJ8GNLQHf4SKA'
                   'zGrXL6Pp5kjojqzi', network='bitcoin'),
             92517795607469467391485978923218300650097355078673652603133403767271895603938,
             '40aa86a597ecd19aa60c1f18390543cc5c38049a18a8515aed095a4b15e1d8ea2226efba29871477ab925e75356fda036f06d'
             '293d02fc9b0f9d49e09d8149e9d',
             '3044022040aa86a597ecd19aa60c1f18390543cc5c38049a18a8515aed095a4b15e1d8ea02202226efba29871477ab925e753'
             '56fda036f06d293d02fc9b0f9d49e09d8149e9d')
        ]
        sig_method1 = sign(sig_tests[0][0], sig_tests[0][1], k=sig_tests[0][2])
        self.assertEqual(sig_method1.hex(), sig_tests[0][3])
        self.assertEqual(sig_method1.as_der_encoded(include_hash_type=False).hex(), sig_tests[0][4])
        count = 0
        for case in sig_tests:
            sig = Signature.create(case[0], case[1], k=case[2])
            self.assertEqual(sig.hex(), case[3], msg="Error in #%d: %s != %s" % (count, sig.hex(), case[3]))
            self.assertEqual(sig.as_der_encoded(include_hash_type=False).hex(), case[4])
            self.assertTrue(sig.verify())
            count += 1

    def test_signatures_rfc6979(self):
        # source: https://bitcointalk.org/index.php?topic=285142.40
        # Test Vectors for RFC 6979 ECDSA, secp256k1, SHA-256
        # (private key, message, expected k, expected signature)
        test_vectors = [
            (0x1, "Satoshi Nakamoto", 0x8F8A276C19F4149656B280621E358CCE24F5F52542772691EE69063B74F15D15,
             "934b1ea10a4b3c1757e2b0c017d0b6143ce3c9a7e6a4a49860d7a6ab210ee3d82442ce9d2b916064108014783e923ec36b4974"
             "3e2ffa1c4496f01a512aafd9e5"),
            (0x1, "All those moments will be lost in time, like tears in rain. Time to die...",
             0x38AA22D72376B4DBC472E06C3BA403EE0A394DA63FC58D88686C611ABA98D6B3,
             "8600dbd41e348fe5c9465ab92d23e3db8b98b873beecd930736488696438cb6b547fe64427496db33bf66019dacbf0039c04199"
             "abb0122918601db38a72cfc21"),
            (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140, "Satoshi Nakamoto",
             0x33A19B60E25FB6F4435AF53A3D42D493644827367E6453928554F43E49AA6F90,
             "fd567d121db66e382991534ada77a6bd3106f0a1098c231e47993447cd6af2d06b39cd0eb1bc8603e159ef5c20a5c8ad685a45b"
             "06ce9bebed3f153d10d93bed5"),
            (0xf8b8af8ce3c7cca5e300d33939540c10d45ce001b8f252bfbc57ba0342904181, "Alan Turing",
             0x525A82B70E67874398067543FD84C83D30C175FDC45FDEEE082FE13B1D7CFDF1,
             "7063ae83e7f62bbb171798131b4a0564b956930092b33b07b395615d9ec7e15c58dfcc1e00a35e1572f366ffe34ba0fc47db1e7"
             "189759b9fb233c5b05ab388ea"),
            (0xe91671c46231f833a6406ccbea0e3e392c76c167bac1cb013f6f1013980455c2,
             "There is a computer disease that anybody who works with computers knows about. It's a very serious "
             "disease and it interferes completely with the work. The trouble with computers is that you 'play' with "
             "them!",
             0x1F4B84C23A86A221D233F2521BE018D9318639D5B8BBD6374A8A59232D16AD3D,
             "b552edd27580141f3b2a5463048cb7cd3e047b97c9f98076c32dbdf85a68718b279fa72dd19bfae05577e06c7c0c1900c371fc"
             "d5893f7e1d56a37d30174671f6"),
            (0x69ec59eaa1f4f2e36b639716b7c30ca86d9a5375c7b38d8918bd9c0ebc80ba64,
             "Computer science is no more about computers than astronomy is about telescopes.", None,
             "7186363571d65e084e7f02b0b77c3ec44fb1b257dee26274c38c928986fea45d0de0b38e06807e46bda1f1e293f4f6323e854c"
             "86d58abdd00c46c16441085df6"),
            (0x0000000000000000000000000000000000000000000000000000000000000001,
             "Everything should be made as simple as possible, but not simpler.", None,
             "33a69cd2065432a30f3d1ce4eb0d59b8ab58c74f27c41a7fdb5696ad4e6108c96f807982866f785d3f6418d24163ddae117b7d"
             "b4d5fdf0071de069fa54342262"),
            (0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140,
             "Equations are more important to me, because politics is for the present, but an equation is something "
             "for eternity.", None,
             "54c4a33c6423d689378f160a7ff8b61330444abb58fb470f96ea16d99d4a2fed07082304410efa6b2943111b6a4e0aaa7b7db5"
             "5a07e9861d1fb3cb1f421044a5"),
            (0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140,
             "Not only is the Universe stranger than we think, it is stranger than we can think.", None,
             "ff466a9f1b7b273e2f4c3ffe032eb2e814121ed18ef84665d0f515360dab3dd06fc95f5132e5ecfdc8e5e6e616cc77151455d"
             "46ed48f5589b7db7771a332b283"),
            (0x0000000000000000000000000000000000000000000000000000000000000001,
             "How wonderful that we have met with a paradox. Now we have some hope of making progress.", None,
             "c0dafec8251f1d5010289d210232220b03202cba34ec11fec58b3e93a85b91d375afdc06b7d6322a590955bf264e7aaa15584"
             "7f614d80078a90292fe205064d3"),
            (0x00000000000000000000000000007246174ab1e92e9149c6e446fe194d072637,
             "...if you aren't, at any given time, scandalized by code you wrote five or even three years ago, you're "
             "not learning anywhere near enough", None,
             "fbfe5076a15860ba8ed00e75e9bd22e05d230f02a936b653eb55b61c99dda4870e68880ebb0050fe4312b1b1eb0899e1b82da89"
             "baa5b895f612619edf34cbd37"),
            (0x000000000000000000000000000000000000000000056916d0f9b31dc9b637f3,
             "The question of whether computers can think is like the question of whether submarines can swim.", None,
             "cde1302d83f8dd835d89aef803c74a119f561fbaef3eb9129e45f30de86abbf906ce643f5049ee1f27890467b77a6a8e11ec46"
             "61cc38cd8badf90115fbd03cef")
        ]

        for vector in test_vectors:
            msg_hash = hashlib.sha256(to_bytes(vector[1])).digest()
            secret = int(vector[0])
            if USE_FASTECDSA:
                rfc6979 = RFC6979(msg_hash, secret, secp256k1_n, hashlib.sha256, prehashed=True)
                k = rfc6979.gen_nonce()
                expected = vector[2]
                if expected is not None:
                    self.assertEqual(k, expected)

            else:
                k = ecdsa.rfc6979.generate_k(ecdsa.SECP256k1.generator.order(), secret, hashlib.sha256,
                                             msg_hash)
                self.assertTrue((vector[2] is None) or vector[2] == k)
            sig = sign(msg_hash, secret, k=k).hex()
            self.assertEqual(sig, vector[3])

    def test_signatures_from_r_and_s(self):
        r = 0x657912a72d3ac8169fe8eaecd5ab401c94fc9981717e3e6dd4971889f785790c
        s = 0x00ed3bf3456eb76677fd899c8ccd1cc6d1ebc631b94c42f7c4578f28590d651c6e
        expected_der = '30450220657912a72d3ac8169fe8eaecd5ab401c94fc9981717e3e6dd4971889f785790c022100ed3bf345' \
                       '6eb76677fd899c8ccd1cc6d1ebc631b94c42f7c4578f28590d651c6e01'
        expected_sig_bytes = b'ey\x12\xa7-:\xc8\x16\x9f\xe8\xea\xec\xd5\xab@\x1c\x94\xfc\x99\x81q~>m\xd4\x97\x18' \
                             b'\x89\xf7\x85y\x0c\xed;\xf3En\xb7fw\xfd\x89\x9c\x8c\xcd\x1c\xc6\xd1\xeb\xc61\xb9LB' \
                             b'\xf7\xc4W\x8f(Y\re\x1cn'
        expected_sig_hex = '657912a72d3ac8169fe8eaecd5ab401c94fc9981717e3e6dd4971889f785790ced3bf3456eb76677fd899' \
                           'c8ccd1cc6d1ebc631b94c42f7c4578f28590d651c6e'

        sig = Signature(r, s)
        self.assertEqual(sig.as_der_encoded().hex(), expected_der)
        self.assertEqual(sig.bytes(), expected_sig_bytes)
        self.assertEqual(sig.hex(), expected_sig_hex)

    def test_signatures_rs_out_of_curve(self):
        outofcurveint = 115792089237316195423570985008687907852837564279074904382605163141518161494339
        self.assertRaisesRegex(BKeyError, "r is not a positive integer smaller than the curve order",
                                Signature, outofcurveint, 10)
        self.assertRaisesRegex(BKeyError, "r is not a positive integer smaller than the curve order",
                                Signature, 0, 10)
        self.assertRaisesRegex(BKeyError, "s is not a positive integer smaller than the curve order",
                                Signature, 11, outofcurveint)

    def test_signatures_dunder(self):
        sig1 = Signature.parse_hex('3045022100c949a465a057f3ca7d20e80511e93d0be21e3efbeb8720ca3e0adfbce6883d0a022070b'
                                   '2c6bee101a4ffcb854bae34dbd1f35c31140a46559148a1fa883eedede03401')
        sig2 = Signature.parse_hex('3045022100b5ce13dc408c65208cf475b44b2012845d4d3fb7a2cacfa35f6b5143761f976f02207d8'
                                   '581d6004779c7f168e90496d544407d5f0e2eecd44c50fcef1006a86731ec01')
        self.assertEqual(len(sig1), 72)
        # self.assertEqual(sig1 + sig2, sig1.as_der_encoded() + sig2.as_der_encoded())
        # self.assertEqual(sig1 + sig2, b'0E\x02!\x00\xc9I\xa4e\xa0W\xf3\xca} \xe8\x05\x11\xe9=\x0b\xe2\x1e>'
        #                               b'\xfb\xeb\x87 \xca>\n\xdf\xbc\xe6\x88=\n\x02 p\xb2\xc6\xbe\xe1'
        #                               b'\x01\xa4\xff\xcb\x85K\xae4\xdb\xd1\xf3\\1\x14\nFU\x91H\xa1\xfa\x88>\xed'
        #                               b'\xed\xe04\x010E\x02!\x00\xb5\xce\x13\xdc@\x8ce \x8c\xf4u\xb4K \x12\x84]M?'
        #                               b'\xb7\xa2\xca\xcf\xa3_kQCv\x1f\x97o\x02 }\x85\x81\xd6\x00Gy\xc7\xf1'
        #                               b'h\xe9\x04\x96\xd5D@}_\x0e.\xec\xd4LP\xfc\xef\x10\x06\xa8g1\xec\x01')
        self.assertEqual(str(sig1), '3045022100c949a465a057f3ca7d20e80511e93d0be21e3efbeb8720ca3e0adfbce6883d0a0220'
                                    '70b2c6bee101a4ffcb854bae34dbd1f35c31140a46559148a1fa883eedede03401')
        self.assertEqual(bytes(sig1), b'0E\x02!\x00\xc9I\xa4e\xa0W\xf3\xca} \xe8\x05\x11\xe9=\x0b\xe2\x1e>'
                                      b'\xfb\xeb\x87 \xca>\n\xdf\xbc\xe6\x88=\n\x02 p\xb2\xc6\xbe\xe1'
                                      b'\x01\xa4\xff\xcb\x85K\xae4\xdb\xd1\xf3\\1\x14\nFU\x91H\xa1\xfa\x88>\xed'
                                      b'\xed\xe04\x01')
        self.assertFalse(sig1 == sig2)

    def test_signatures_compare(self):
        network = 'signet'
        witness_type = 'segwit'
        private_hex = HDKey(network=network, witness_type=witness_type).private_hex
        pk = HDKey(private_hex)
        pk2 = HDKey(private_hex)
        message = 'signature testing 123'

        sig1 = pk.sign_message(message)
        sig2 = pk2.sign_message(message)

        self.assertEqual(sig1, sig2)


class TestKeysTaproot(unittest.TestCase):

    def test_keys_taproot_addresses(self):
        # Test taproot addresses
        addresses = ['bc1p8denc9m4sqe9hluasrvxkkdqgkydrk5ctxre5nkk4qwdvefn0sdsc6eqxe',
                     'tb1p0fqgfy3awa5kn3kkfgceqv795kljfyrhtw0ps38xv06uwxjnraaqlnee59']

        for address in addresses:
            addr_dict = deserialize_address(address)
            address_encode = pubkeyhash_to_addr_bech32(addr_dict['public_key_hash_bytes'], addr_dict['prefix'],
                                                       addr_dict['witver'])
            self.assertEqual(address, address_encode)
            self.assertEqual(addr_dict['script_type'], 'p2tr')

        # Test address with other witver value
        address_fantasy = deserialize_address('lc108denc9m4sqe9hluasrvxkkdqgkydrk5ctxre5nkk4qwdvefn0sdsggm3lr')
        self.assertEqual(address_fantasy['witver'], 15)
        self.assertEqual(address_fantasy['public_key_hash'],
                         '3b733c177580325bff9d80d86b59a04588d1da9859879a4ed6a81cd665337c1b')

        # Test pubkeyhash_to_addr_bech32 with only witver or checksum_xor
        address = 'bc1p05k5gxz4v962tne5z8d4ztjakktmzypqd7jxn5k57774fuyzzplshuxrmd'
        pubkeyhash = '7d2d4418556174a5cf3411db512e5db597b110206fa469d2d4f7bd54f082107f'
        p2tr_address = pubkeyhash_to_addr_bech32(pubkeyhash, 'bc', checksum_xor=BECH32M_CONST)
        p2tr_address2 = pubkeyhash_to_addr_bech32(pubkeyhash, 'bc', witver=1)
        self.assertEqual(p2tr_address, address)
        self.assertEqual(p2tr_address2, address)
        addr_dict = deserialize_address(p2tr_address2)
        self.assertEqual(addr_dict['public_key_hash'], pubkeyhash)
        self.assertEqual(addr_dict['script_type'], 'p2tr')


class TestKeysMessages(unittest.TestCase):

    def test_keys_message_sign_and_verify_bitcoin_core(self):
        # Test with local bitcoin core node
        # $ bitcoin - cli signmessage "17J4q9GZg68s88ve9tzBJD9RURogmQMnnu" "Eat more cheese!"
        # H16wBg2U8oD9FR1Ht/y8C2NYxUl+qkzQfB4wBD3wplMOdsYlMoPgAoqJ0LY33KHDeZkc395Pi0e6mLDbYKr6alo=
        # $ bitcoin - cli verifymessage "17J4q9GZg68s88ve9tzBJD9RURogmQMnnu" "H16wBg2U8oD9FR1Ht/y8C2NYxUl+qkzQfB4wBD3wplMOdsYlMoPgAoqJ0LY33KHDeZkc395Pi0e6mLDbYKr6alo=" "Eat more cheese!"
        address = "17J4q9GZg68s88ve9tzBJD9RURogmQMnnu"
        message = "Eat more cheese!"
        sig = "H16wBg2U8oD9FR1Ht/y8C2NYxUl+qkzQfB4wBD3wplMOdsYlMoPgAoqJ0LY33KHDeZkc395Pi0e6mLDbYKr6alo="
        self.assertTrue(verify_message(message, sig, address))

    def test_keys_message_signing_pycoin(self):
        # Compared with pycoin library output - step-by-step compared results
        wif = 'L4gXBvYrXHo59HLeyem94D9yLpRkURCHmCwQtPuWW9m6o1X8p8sp'
        addr = '1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv'
        msg = 'test message A'
        expected_sig_base64 = ("H43ecBSnp1+Q0iJ7wbtBc/cELGILn0NvKb5UrTeJqA07hyY+FA7SBVWN"
                               "+0phX6ysIGdNe99EJPobpcNwl4ht790=")
        expected_sig_der = ("30460221008dde7014a7a75f90d2227bc1bb4173f7042c620b9f436f29be54ad3789a80d3b02210087263e140"
                            "ed205558dfb4a615facac20674d7bdf4424fa1ba5c37097886defdd01")
        expected_signed_message = \
            "-----BEGIN BITCOIN SIGNED MESSAGE-----\n" \
            "test message A\n" \
            "-----BEGIN SIGNATURE-----\n" \
            "1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv\n" \
            "H43ecBSnp1+Q0iJ7wbtBc/cELGILn0NvKb5UrTeJqA07hyY+FA7SBVWN+0phX6ysIGdNe99EJPobpcNwl4ht790=\n" \
            "-----END BITCOIN SIGNED MESSAGE-----\n" \

        pk = HDKey(wif, witness_type='legacy')
        self.assertEqual(pk.address(), addr)

        sig = pk.sign_message(msg, force_canonical=False)
        self.assertEqual(64169125251067142060049740121784818273156574831540951431018131832714377563451, sig.r)
        self.assertEqual(61129803196235745037234955305700148791464496745709279972088993803821678194653, sig.s)

        pub_key = pk.public()
        self.assertTrue(pub_key.verify_message(msg, sig))
        self.assertTrue(sig.verify())

        sigb64 = sig.as_base64()
        self.assertEqual(sigb64, expected_sig_base64)

        sig3 = Signature.parse_base64(sigb64)
        self.assertEqual(sig3.as_der_encoded().hex(), expected_sig_der)
        self.assertTrue(pub_key.verify_message(msg, sig3))

        self.assertEqual(sig.as_signed_message(msg), expected_signed_message)

    def test_keys_message_signing_and_verification(self):
        private_hex = '06cffb14a8b9a901c60486e139f435cc7042d9ce78c65ebf94e7a62697e1dbfa'
        message = 'bitcoinlib rocks'
        test_messages = [
            # network, witness_type, expected_sig
            ('litecoin', 'legacy',        # tested with litecoinpool.org
             'IJZPEvxNKTqXNe2NBvKhFIrDrnl14S629hH9y5jR+EO3SwYi6/Rpc+F40X3cCmXVZcrXfqPxpavLMzoQSdFaK/0='),
            ('bitcoin', 'legacy',
             # tested with verifybitcoinmessage, checkmsg.org, bitcoinmessage.tools, bitcoin core, etc
             'IC5ZJ73WMxnDfvtmncgSlGRyIxBoAUibqUrdGCDeV+bfkaWI/95pv+Oo+l8Zmfy6o+dc43wU5snuYo4Xa9BCQOM='),
            ('bitcoin', 'p2sh-segwit',    # tested with verifybitcoinmessage
             'JC5ZJ73WMxnDfvtmncgSlGRyIxBoAUibqUrdGCDeV+bfkaWI/95pv+Oo+l8Zmfy6o+dc43wU5snuYo4Xa9BCQOM='),
            ('bitcoin', 'segwit',         # tested with verifybitcoinmessage
             'KC5ZJ73WMxnDfvtmncgSlGRyIxBoAUibqUrdGCDeV+bfkaWI/95pv+Oo+l8Zmfy6o+dc43wU5snuYo4Xa9BCQOM='),
            ('testnet', 'legacy',         # tested with bluewallet.github.io, verifybitcoinmessage
             'IC5ZJ73WMxnDfvtmncgSlGRyIxBoAUibqUrdGCDeV+bfkaWI/95pv+Oo+l8Zmfy6o+dc43wU5snuYo4Xa9BCQOM='),
            ('testnet4', 'segwit',        # tested with bluewallet.github.io, verifybitcoinmessage
             'KC5ZJ73WMxnDfvtmncgSlGRyIxBoAUibqUrdGCDeV+bfkaWI/95pv+Oo+l8Zmfy6o+dc43wU5snuYo4Xa9BCQOM='),
            ('signet', 'segwit',          # tested with bluewallet.github.io, verifybitcoinmessage
             'KC5ZJ73WMxnDfvtmncgSlGRyIxBoAUibqUrdGCDeV+bfkaWI/95pv+Oo+l8Zmfy6o+dc43wU5snuYo4Xa9BCQOM='),
        ]
        for tmsg in test_messages:
            # print(f"network={tmsg[0]}, witness_type={tmsg[1]}")
            pk = HDKey(private_hex, network=tmsg[0], witness_type=tmsg[1])

            # Sign message and check base64 signature
            sig = pk.sign_message(message, force_canonical=False)
            self.assertEqual(sig.as_base64(), tmsg[2])

            # Verify message with public key
            pub_key = pk.public()
            self.assertEqual(pub_key.witness_type, tmsg[1])
            self.assertTrue(pub_key.verify_message(message, sig))

    def test_keys_message_verify_found_signed_messages(self):
        # RFC2440
        messages = [
# From pycoin library
"""-----BEGIN BITCOIN SIGNED MESSAGE-----
test message AAAAAAAAAA
-----BEGIN SIGNATURE-----
1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv
ID1VEsaxxrBFXNmWVTL5RKZQ5jZNSO845UFr1I5COO05bzt2wy187igIFBqhNEMtL+mV5Xhww9+eFUish1n+Xgg=
-----END BITCOIN SIGNED MESSAGE-----""",

# go-bitcoin-message-tool
"""-----BEGIN BITCOIN SIGNED MESSAGE-----
ECDSA is the most fun I have ever experienced
-----BEGIN BITCOIN SIGNATURE-----
16wrm6zJek6REbxbJSLsBHehn3Lj1vo57t
H3x5bM2MpXK9MyLLbIGWQjZQNTP6lfuIjmPqMrU7YZ5CCm5bS9L+zCtrfIOJaloDb0mf9QBSEDIs4UCd/jou1VI=
-----END BITCOIN SIGNATURE-----""",

"""-----BEGIN BITCOIN SIGNED MESSAGE-----
ECDSA is the most fun I have ever experienced
-----BEGIN BITCOIN SIGNATURE-----
bc1qdn4nnn59570wlkdn4tq23whw6y5e6c28p7chr5

J8xT/nFS2YpzmW6kDCoH4hjjLKjR2k7o9fHq2je/natNdMmYzQ7Gik5EHV1gVbkVOl7M74d7g2fEBl+csGqyqJ8=
-----END BITCOIN SIGNATURE-----""",

"""-----BEGIN BITCOIN SIGNED MESSAGE-----
f1591bfb04a89f723e1f14eb01a6b2f6f507eb0967d0a5d7822b329b98018ae4  coldcard-export.json
-----BEGIN BITCOIN SIGNATURE-----
mtHSVByP9EYZmB26jASDdPVm19gvpecb5R
IFOvGVJrm31S0j+F4dVfQ5kbRKWKcmhmXIn/Lw8iIgaCG5QNZswjrN4X673R7jTZo1kvLmiD4hlIrbuLh/HqDuk=
-----END BITCOIN SIGNATURE-----""",

"""-----BEGIN BITCOIN SIGNED MESSAGE-----
Anything one man can imagine, other men can make real
-----BEGIN BITCOIN SIGNATURE-----
1Fo65aKq8s8iquMt6weF1rku1moWVEd5Ua
IIONt3uYHbMh+vUnqDBGHP2gGu1Q2Fw0WnsKj05eT9P8KI2kGgPniiPirCd5IeLRnRdxeiehDxxsyn/VujUaX8o=
-----END BITCOIN SIGNATURE-----""",

"""Username: Bit2c
Public key: 0396267072e597ad5d043db7c73e13af84a77a7212871f1aade607fb0f2f96e1a8
Public key address: 15etuU8kwLFCBbCNRsgQTvWgrGWY9829ej
URL: https://www.bitrated.com/u/Bit2c

-----BEGIN BITCOIN SIGNED MESSAGE-----
We will try to contact both parties to gather information and evidence, and do my best to make rightful judgement. Evidence may be submitted to us on https://www.bit2c.co.il/home/contact or in a private message to info@bit2c.co.il or in any agreed way.

https://www.bit2c.co.il
-----BEGIN SIGNATURE-----
15etuU8kwLFCBbCNRsgQTvWgrGWY9829ej
H2utKkquLbyEJamGwUfS9J0kKT4uuMTEr2WX2dPU9YImg4LeRpyjBelrqEqfM4QC8pJ+hVlQgZI5IPpLyRNxvK8=
-----END BITCOIN SIGNED MESSAGE-----""",

# https://bitcoin.stackexchange.com/questions/77324/how-are-bitcoin-signed-messages-generated
"""-----BEGIN BITCOIN SIGNED MESSAGE-----
Test
-----BEGIN BITCOIN SIGNATURE-----
1BqtNgMrDXnCek3cdDVSer4BK7knNTDTSR
ILoOBJK9kVKsdUOnJPPoDtrDtRSQw2pyMo+2r5bdUlNkSLDZLqMs8h9mfDm/alZo3DK6rKvTO0xRPrl6DPDpEik=
-----END BITCOIN SIGNATURE-----""",
        ]

        for msg_sig in messages:
            # print(msg_sig)
            message, sig_b64, addr, nw = signed_message_parse(msg_sig)
            self.assertTrue(verify_message(message, sig_b64, addr, nw))

    def test_keys_message_verify_found_signed_messages_invalid(self):
        messages = [
# https://bitcoin.stackexchange.com/questions/77324/how-are-bitcoin-signed-messages-generated
"""-----BEGIN BITCOIN SIGNED MESSAGE-----
Test
-----BEGIN BITCOIN SIGNATURE-----
1FZHv7fubXkMcgbDBUeehgPf28cHP86f7V
ILoOBJK9kVKsdUOnJPPoDtrDtRSQw2pyMo+2r5bdUlNkSLDZLqMs8h9mfDm/alZo3DK6rKvTO0xRPrl6DPDpEik=
-----END BITCOIN SIGNATURE-----""",
        ]

        for msg_sig in messages:
            message, sig_b64, addr, nw = signed_message_parse(msg_sig)
            self.assertFalse(verify_message(message, sig_b64, addr, nw))

        # Test result when changing message, address or sig
        SIGNED_MESSAGE = """-----BEGIN BITCOIN SIGNED MESSAGE-----
Bitcoinlib is cool!
-----BEGIN SIGNATURE-----
bc1qed0dq6a7gshfvap4j946u44kk73gs3a0d5p3sw
ILtL9qkUb+2nfxY3bUqfoWsVSwhMSos+DVY7p3EqmzQ6qF2gHNPvILwrsZ2AKlIqPmJjln4OKpW+d86wBn27yJw=
-----END BITCOIN SIGNED MESSAGE-----"""
        message, sig_b64, addr, nw = signed_message_parse(SIGNED_MESSAGE)
        self.assertTrue(verify_message(message, sig_b64, addr, nw))

        wrong_message = "Bitcoinlib sucks!"
        self.assertFalse(verify_message(wrong_message, sig_b64, addr))
        wrong_sig = 'IGlGc5mQo2jl4AYp6GwFPhHm9M6XJ4ZQqqmHxaR0ugiPprkVpFhLsqWref7/7xbZD1KsIdQqZW9s1LCUiX7IzQQ='
        self.assertFalse(verify_message(message, wrong_sig, addr))
        wrong_addr = 'bc1qx75nvpnpxhxhlru98pjw37yux2zknvqrkgp4c4'
        self.assertFalse(verify_message(message, sig_b64, wrong_addr))
        self.assertFalse(verify_message('', sig_b64, addr))

    def test_keys_messages_sign_and_verify_bulk(self):
        import string
        for _ in range(BULKTESTCOUNT // 5):
            message = ''.join(random.choices(string.ascii_letters + string.digits, k=200))
            pk = HDKey()
            sig = pk.sign_message(message)
            bsm = sig.as_signed_message(message)
            # print(bsm)
            m, s, a, nw = signed_message_parse(bsm)
            self.assertTrue(verify_message(m, s, a, nw))

    def test_keys_message_verify_trezor(self):
        # Test with https://www.bitkassa.nl/signmessage-local
        pkwif = 'L5QrCGq1XJY3s5kYGH512pP4dcBmEY2sUYZ2NnKi7jt9H8UXRKta'
        message = 'Tested with https://www.bitkassa.nl/signmessage-local'
        expected_sig = 'IB77gJYCT6HW7QTyfrTPM6j7dmTJze490EVo6C2gtJf0HkqyLX0S7mwYle9nNPrddVM+wND2ygHyWpuBE00etkw='
        expected_addr = '15mgozmrZ7j6ZTpKQQ26MhR3q1wQ296oEb'
        pk = HDKey(pkwif, witness_type='legacy')
        sig = pk.sign_message(message)
        self.assertEqual(sig.as_base64(), expected_sig)
        self.assertTrue(verify_message(message, sig, expected_addr))

        # Trezor test
        message = """-----BEGIN BITCOIN TESTNET SIGNED MESSAGE-----
Sign testnet with Trezor
-----BEGIN SIGNATURE-----
tb1qld5enve8wdd8dfw5net62k2klpz3atefzndpen
KK6hBpVOiA2B7FayE0tk2l/EQ6DQcqsWUtvLZZdQi2WWSlD2ZSFMEG9q58zb0TfPBzMLThwFk1YhX7aI0Av6yoM=
-----END BITCOIN TESTNET SIGNED MESSAGE-----"""
        message, sig_b64, addr, nw = signed_message_parse(message)
        self.assertTrue(verify_message(message, sig_b64, addr, nw))

        # Trezor Dogecoin test
        message = """-----BEGIN DOGECOIN SIGNED MESSAGE-----
Dogecoin rocks!
-----BEGIN SIGNATURE-----
DGYyzjZCrcTFc4NX1g4iLfwRLwxavt3q8r
IHQ6zcQV+lXFHfzktU/NU1PcobHJhmOOqHism4L5fPcKPXQnZFiNPXyjLb1JG9GknzA5I0z4GWPGGh8bpcZ1vAk=
-----END DOGECOIN SIGNED MESSAGE-----"""
        message, sig_b64, addr, nw = signed_message_parse(message)
        self.assertTrue(verify_message(message, sig_b64, addr, nw))

        # Trezor Litecoin test
        message = """-----BEGIN LITECOIN SIGNED MESSAGE-----
Hello Litecoin!
-----BEGIN SIGNATURE-----
ltc1q6ewt25qxf7h96g7jklv8h77zcunrn86fl9yu4s
KIRCb9mBPBfpEZy02dvIHDw+o58MQfXkXk5EDmYmH7LCc9DLKuUrZ+1/114fyBbttIFdEL42zvr8Wxa+6pIVKcM=
-----END LITECOIN SIGNED MESSAGE-----
"""
        message, sig_b64, addr, nw = signed_message_parse(message)
        self.assertTrue(verify_message(message, sig_b64, addr, nw))

    def test_keys_sign_message_errors(self):
        address = "17J4q9GZg68s88ve9tzBJD9RURogmQMnnu"
        message = "Eat more cheese!"
        sig = "H16wBg2U8oD9FR1Ht/y8C2NYxUl+qkzQfB4wBD3wplMOdsYlMoPgAoqJ0LY33KHDeZkc395Pi0e6mLDbYKr6alo="
        s = Signature.parse_base64(sig)
        self.assertRaisesRegex(BKeyError, "Public key is unknown, please provide address to derive public "
                                          "key", s.verify_message, message)
        self.assertTrue(s.verify_message(message, address))
        # Now it works without Address, because public key has been derived before
        self.assertTrue(s.verify_message(message))

    def test_keys_message_sign_verify_electrum(self):
        #
        # Electrum uses a different method to determine recovery id and also grinds r values. So the tests below
        # are a copy of the Electrum unittests, but with grinding disabled and a different recovery ID.
        #
        msg1 = b'Chancellor on brink of second bailout for banks'
        addr1 = '15hETetDmcXm1mM4sEf7U2KXC9hDHFMSzz'
        expected_sig1 = 'IP9jMOnj4MFbH3d7t4yCQ9i7DgZU/VZ278w3+ySv2F4yIsdqjsc5ng3kmN8OZAThgyfCZOQxZCWza9V5XzlVY0Y='
        pk = HDKey('L1TnU2zbNaAqMoVh65Cyvmcjzbrj41Gs9iTLcWbpJCMynXuap6UN', witness_type='legacy')
        self.assertEqual(pk.address(), addr1)
        sig1 = pk.sign_message(msg1, force_canonical=True)
        self.assertEqual(sig1.as_base64(), expected_sig1)

        msg2 = 'Electrum'
        addr2 = '1GPHVTY8UD9my6jyP4tb2TYJwUbDetyNC6'
        expected_sig2 = 'G84dmJ8TKIDKMT9qBRhpX2sNmR0y5t+POcYnFFJCs66lJmAs3T8A6Sbpx7KA6yTQ9djQMabwQXRrDomOkIKGn18='
        pk = HDKey('5Hxn5C4SQuiV6e62A1MtZmbSeQyrLFhu5uYks62pU5VBUygK2KD', witness_type='legacy')
        self.assertEqual(pk.address(), addr2)
        sig2 = pk.sign_message(msg2, force_canonical=True)
        self.assertEqual(sig2.as_base64(), expected_sig2)
        self.assertTrue(verify_message(msg2, sig2, addr2))

        addr = "15hETetDmcXm1mM4sEf7U2KXC9hDHFMSzz"
        sig_low_s = 'Hzsu0U/THAsPz/MSuXGBKSULz2dTfmrg1NsAhFp+wH5aKfmX4Db7ExLGa7FGn0m6Mf43KsbEOWpvUUUBTM3Uusw='
        sig_high_s = 'IDsu0U/THAsPz/MSuXGBKSULz2dTfmrg1NsAhFp+wH5a1gZoH8kE7O05lE65YLZFzLx3sh/rDzXMbo1dQAJhhnU='
        msg = 'Chancellor on brink of second bailout for banks'
        self.assertTrue(verify_message(msg, sig_low_s, addr))
        self.assertTrue(verify_message(msg, sig_high_s, addr))

        # p2wpkh-p2sh
        msg = 'Electrum'
        addr = "3DYoBqQ5N6dADzyQjy9FT1Ls4amiYVaqTG"
        pk = HDKey('L1cgMEnShp73r9iCukoPE3MogLeueNYRD9JVsfT1zVHyPBR3KqBY', witness_type='p2sh-segwit')
        self.assertEqual(pk.address(), addr)
        sig = pk.sign_message(msg, force_canonical=True)
        self.assertEqual(sig.as_base64(),
                         'IyFaND+87TtVbRhkTfT3mPNBCQcJ32XXtNZGW8sFldJsNpOPCegEmdcCf5Thy18hdMH88GLxZLkOby/EwVUuSeA=')
        self.assertTrue(pk.verify_message(msg, sig))
        self.assertTrue(verify_message(msg, sig, pk.address_obj))
        self.assertRaisesRegex(BKeyError, "Public key from signature and provided address do not match" ,
                               verify_message, msg, sig, HDKey().address())
        self.assertFalse(verify_message('heyheyhey', sig, pk.address_obj))
        self.assertTrue(sig.verify_message(msg, addr))

        # p2wpkh
        pk2 = HDKey("L1cgMEnShp73r9iCukoPE3MogLeueNYRD9JVsfT1zVHyPBR3KqBY", witness_type='segwit')
        addr2 = "bc1qq2tmmcngng78nllq2pvrkchcdukemtj56uyue0"
        self.assertEqual(pk2.address(), addr2)
        sig2 = pk2.sign_message(msg, force_canonical=True)
        self.assertTrue(verify_message(msg, sig2, addr2))
        self.assertFalse(verify_message('heyheyhey', sig2, addr2))
        self.assertRaisesRegex(BKeyError, "Public key from signature and provided address do not match" ,
                               verify_message, msg, sig1, addr2)

    def test_keys_message_sign_verify_trezor(self):
        # Test vectors from Trezor
        # See: Trezor github tests/device_tests/bitcoin/test_signmessage.py
        # removed non-standard uncompressed segwit keys
        #

        MESSAGE_NFKD = u"Pr\u030ci\u0301s\u030cerne\u030c z\u030clut\u030couc\u030cky\u0301 ku\u030an\u030c u\u0301pe\u030cl d\u030ca\u0301belske\u0301 o\u0301dy za\u0301ker\u030cny\u0301 uc\u030cen\u030c be\u030cz\u030ci\u0301 pode\u0301l zo\u0301ny u\u0301lu\u030a"
        MESSAGE_NFC = u"P\u0159\xed\u0161ern\u011b \u017elu\u0165ou\u010dk\xfd k\u016f\u0148 \xfap\u011bl \u010f\xe1belsk\xe9 \xf3dy z\xe1ke\u0159n\xfd u\u010de\u0148 b\u011b\u017e\xed pod\xe9l z\xf3ny \xfal\u016f"
        NFKD_NFC_SIGNATURE = "2046a0b46e81492f82e0412c73701b9740e6462c603575ee2d36c7d7b4c20f0f33763ca8cb3027ea8e1ce5e83fda8b6746fea8f5c82655d78fd419e7c766a5e17a"

        VECTORS = (  # case name, coin_name, path, script_type, address, message, signature
            # ==== Bitcoin script types ====
            (
                "p2pkh uncompressed",
                "Bitcoin",
                "m/44h/0h/0h/0/0",
                False,
                "1JAd7XCBzGudGpJQSDSfpmJhiygtLQWaGL",
                "This is an example of a signed message.",
                "20fd8f2f7db5238fcdd077d5204c3e6949c261d700269cefc1d9d2dcef6b95023630ee617f6c8acf9eb40c8edd704c9ca74ea4afc393f43f35b4e8958324cbdd1c",
                "legacy",
            ),
            (
                "p2pkh compressed",
                "Bitcoin",
                "m/44h/0h/0h/0/0",
                True,
                "1JAd7XCBzGudGpJQSDSfpmJhiygtLQWaGL",
                "This is an example of a signed message.",
                "20fd8f2f7db5238fcdd077d5204c3e6949c261d700269cefc1d9d2dcef6b95023630ee617f6c8acf9eb40c8edd704c9ca74ea4afc393f43f35b4e8958324cbdd1c",
                "legacy",
            ),
            (
                "segwit-p2sh compressed",
                "Bitcoin",
                "m/49h/0h/0h/0/0",
                True,
                "3L6TyTisPBmrDAj6RoKmDzNnj4eQi54gD2",
                "This is an example of a signed message.",
                "1f744de4516fac5c140808015664516a32fead94de89775cec7e24dbc24fe133075ac09301c4cc8e197bea4b6481661d5b8e9bf19d8b7b8a382ecdb53c2ee0750d",
                "p2sh-segwit",
            ),
            (
                "segwit-native",
                "Bitcoin",
                "m/84h/0h/0h/0/0",
                True,
                "bc1qannfxke2tfd4l7vhepehpvt05y83v3qsf6nfkk",
                "This is an example of a signed message.",
                "20b55d7600d9e9a7e2a49155ddf3cfdb8e796c207faab833010fa41fb7828889bc47cf62348a7aaa0923c0832a589fab541e8f12eb54fb711c90e2307f0f66b194",
                "segwit"
            ),
            # ==== Bitcoin with long message ====
            (
                "p2pkh long message",
                "Bitcoin",
                "m/44h/0h/0h/0/0",
                False,
                "1JAd7XCBzGudGpJQSDSfpmJhiygtLQWaGL",
                "VeryLongMessage!" * 64,
                "200a46476ceb84d06ef5784828026f922c8815f57aac837b8c013007ca8a8460db63ef917dbebaebd108b1c814bbeea6db1f2b2241a958e53fe715cc86b199d9c3",
                "legacy",
            ),
            (
                "segwit-native long message",
                "Bitcoin",
                "m/84h/0h/0h/0/0",
                False,
                "bc1qannfxke2tfd4l7vhepehpvt05y83v3qsf6nfkk",
                "VeryLongMessage!" * 64,
                "28c6f86e255eaa768c447d635d91da01631ac54af223c2c182d4fa3676cfecae4a199ad33a74fe04fb46c39432acb8d83de74da90f5f01123b3b7d8bc252bc7f71",
                "segwit",
            ),
            (
                "NFKD message",
                "Bitcoin",
                "m/44h/0h/0h/0/1",
                False,
                "1GWFxtwWmNVqotUPXLcKVL2mUKpshuJYo",
                MESSAGE_NFKD,
                NFKD_NFC_SIGNATURE,
                "legacy",
            ),
            (
                "NFC message",
                "Bitcoin",
                "m/44h/0h/0h/0/1",
                False,
                "1GWFxtwWmNVqotUPXLcKVL2mUKpshuJYo",
                MESSAGE_NFC,
                NFKD_NFC_SIGNATURE,
                "legacy",
            ),
            (
                "p2pkh testnet",
                "Testnet",
                "m/44h/1h/0h/0/0",
                False,
                "mvbu1Gdy8SUjTenqerxUaZyYjmveZvt33q",
                "This is an example of a signed message.",
                "2030cd7f116c0481d1936cfef48137fd23ee56aaf00787bfa08a94837466ec9909390c3efacfc56bae5782f1db4cf49ae05f242b5f62a47f871ec46bf1a3253e7f",
                "legacy",
            ),
            (
                "segwit-native",
                "Testnet",
                "m/84h/1h/0h/0/0",
                False,
                "tb1qkvwu9g3k2pdxewfqr7syz89r3gj557l3uuf9r9",
                "This is an example of a signed message.",
                "27758b3393396ad9fe48f6ce81f63410145e7b2b69a5dfc1d48b5e6e623e91e08e3afb60bda1546f9c6f9fb5bd0a41887b784c266036dd4b4015a0abc1137daa1d",
                "segwit",
            ),
        )

        for v in VECTORS:
            # print(f"Testing vector {v[0]}")
            sigb64 = b2a_base64(bytes.fromhex(v[6]))
            s = Signature.parse_base64(sigb64)
            addr = Address.parse(v[4])
            addr.witness_type = v[7]
            msg = v[5]

            if v[0] == "NFKD message":
                msg = normalize('NFKC', msg)

            self.assertEqual(a2b_base64(s.as_base64()).hex(), v[6])
            self.assertTrue(s.verify_message(msg, addr))

    def test_keys_message_sign_network_witness_check(self):
        for network in NETWORK_DEFINITIONS:
            for witness_type in ['legacy', 'segwit', 'p2sh-segwit']:
                message = f"Signed message for the {network} network and witness_type {witness_type}"
                # print(message)
                pk = HDKey(network=network, witness_type=witness_type)
                sig = pk.sign_message(message)
                self.assertTrue(sig.verify_message(message))
                signed_message = sig.as_signed_message(message)
                m, s, a, nw = signed_message_parse(signed_message)
                self.assertTrue(verify_message(m, s, a, nw))


if __name__ == '__main__':
    unittest.main()
