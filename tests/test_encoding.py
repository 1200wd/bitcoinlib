# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Key, Encoding and Mnemonic Class
#    © 2016 - 2021 January - 1200 Web Development <http://1200wd.com/>
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

from bitcoinlib.config.opcodes import op
from bitcoinlib.encoding import *
from bitcoinlib.encoding import _bech32_polymod, _codestring_to_array


class TestEncodingMethodsChangeBase(unittest.TestCase):

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
        self.assertEqual(b'\x00\xd7{\xf7b\x8c\x19\xe6\x99\x01\r)xz)\xaf\xcf\x8e\x92\xadZ\x05=U\xd7',
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
        self.assertEqual(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f',
                         change_base("000102030405060708090a0b0c0d0e0f", 16, 256))

    def test_change_base32_base3(self):
        self.assertEqual(',   . .. ., .   ,. .,  ,. .., . ,..  .,. ,..,, . . .,.,..  ,...,, ,, .,.,,,.,,,...  . , .,,,'
                         '. ...,, .,.,.  ,,..,,,,.', change_base("Oh what a fun we have !", 256, 3))

    # Tests for bug with leading zero's
    def test_change_base_leading_zeros(self):
        self.assertEqual(b'\x00\x00\x03', change_base("000003", 16, 256))

    def test_change_base_leading_zeros2(self):
        self.assertEqual('1L', change_base('0013', 16, 58))

    # def test_change_base_leading_zeros3(self):  # Incorrect  hex...
    #     self.assertEqual('1L', change_base('013', 16, 58))

    def test_change_base_leading_zeros4(self):
        self.assertEqual(b'\x04G\x81', change_base('044781', 16, 256))

    def test_change_base_leading_zeros_binascii(self):
        y = 251863285056225027460663457133976813779860093019161001622713253221998044380
        self.assertEqual(64, len(change_base(y, 10, 16, 64)))

    def test_change_base_zero_int(self):
        self.assertEqual(0, change_base(b'\0', 256, 10))

    def test_change_base_encodings_bytes(self):
        self.assertEqual('4c52127a72fb42b82439ab18697dcfcfb96ac63ba8209833b2e29f2302b8993f45e743412d65c7a571da70259d4'
                         'f6795e98af20e6e57603314a662a49c198199',
                         change_base(b'LR\x12zr\xfbB\xb8$9\xab\x18i}\xcf\xcf\xb9j\xc6;\xa8 \x983\xb2\xe2\x9f#\x02\xb8'
                                     b'\x99?E\xe7CA-e\xc7\xa5q\xdap%\x9dOg\x95\xe9\x8a\xf2\x0enW`3\x14\xa6b\xa4\x9c'
                                     b'\x19\x81\x99', 256, 16))

    def test_change_base_encodings_utf8(self):
        self.assertEqual('e782ba20e5ae8b20e69ab420e6b2bb20e4bcaf20e58f8a20e7819820e586b620e5bf9920e9808320e6b99820e8'
                         '898720e4be8b20e8ae9320e5bfa0',
                         change_base("為 宋 暴 治 伯 及 灘 冶 忙 逃 湘 艇 例 讓 忠", 256, 16))

    def test_change_base_list(self):
        self.assertEqual('00124c', change_base([b'\0', b'\x12', b'L'], 256, 16, 6))

    def test_change_base_bytes_as_string(self):
        s = '\xc8\xe9\t\x96\xc7\xc6\x08\x0e\xe0b\x84`\x0chN\xd9\x04\xd1L\\'
        self.assertEqual('c8e90996c7c6080ee06284600c684ed904d14c5c', change_base(s, 256, 16))

    def test_change_base_decimal_input_lenght_exception(self):
        self.assertRaisesRegex(EncodingError, "For a decimal input a minimum output length is required",
                                change_base, 100, 10, 2)

    def test_encoding_exceptions(self):
        self.assertRaisesRegex(EncodingError, "Unknown input format {}",
                                change_base, {}, 4, 2)
        self.assertRaisesRegex(EncodingError, "Byteint must be a list or defined as bytes",
                                varbyteint_to_int, 'fd1027')
        self.assertRaisesRegex(EncodingError, "Input must be a number type",
                                int_to_varbyteint, '1000')
        self.assertRaisesRegex(TypeError, "String value expected", normalize_string, 100)
        self.assertRaisesRegex(EncodingError, "Encoding base32 not supported", pubkeyhash_to_addr, '123',
                                encoding='base32')
        addr = 'qc1qy8qmc6262m68ny0ftlexs4h9paud8sgce3sf84'
        self.assertRaisesRegex(EncodingError, "Invalid bech32 address. Prefix 'qc', prefix expected is 'bc'",
                                addr_bech32_to_pubkeyhash, addr, prefix='bc')


class TestEncodingMethodsAddressConversion(unittest.TestCase):

    def test_address_to_pkh_conversion_1(self):
        self.assertEqual('cc194d0157dc8c2effb4aaff25a1bbd88a4a29a8',
                         addr_to_pubkeyhash('1KcBA4i4Qqu1oRjobyWU3R5UXUorLQ3jUg', True))

    def test_address_to_pkh_conversion_2(self):
        self.assertEqual('00' * 20,
                         addr_to_pubkeyhash('1111111111111111111114oLvT2', True))

    def test_address_to_pkh_conversion_3(self):
        self.assertEqual(b'\xFF' * 20,
                         addr_to_pubkeyhash('1QLbz7JHiBTspS962RLKV8GndWFwi5j6Qr', False))

    def test_pkh_to_addr_conversion_1(self):
        self.assertEqual('1LkthjzqGyhAWAmA9Dgbyp9pNMBXQj9ZZ3',
                         pubkeyhash_to_addr('d8b76f6dd0e8d17cd34c3703ad5a120ba83ff857'))

    def test_pkh_to_addr_conversion_2(self):
        self.assertEqual('1111111111111111111114oLvT2',
                         pubkeyhash_to_addr('00' * 20))

    def test_address_to_pkh_bech32(self):
        addr = 'bc1qy8qmc6262m68ny0ftlexs4h9paud8sgce3sf84'
        self.assertEqual(addr_to_pubkeyhash(addr), b'!\xc1\xbciZV\xf4y\x91\xe9_\xf2hV\xe5\x0fx\xd3\xc1\x18')
        self.assertEqual(addr_to_pubkeyhash(addr, as_hex=True), '21c1bc695a56f47991e95ff26856e50f78d3c118')

    def test_pkh_to_bech32_address(self):
        addr = pubkeyhash_to_addr('45d093a97d5710c80363c69618e826efad42edb1', encoding='bech32')
        self.assertEqual(addr, 'bc1qghgf82ta2ugvsqmrc6tp36pxa7k59md3czjhjc')

    def test_address_base58_zero_prefixes(self):
        self.assertEqual(pubkeyhash_to_addr_base58('00003acd8f60b766e48e9db32093b419c21de7e9'),
                         '111GxfgFVyDW3zcFpUF1upSZoL7GCRiLk')
        self.assertEqual(change_base('000000003acd8f60b766e48e9db32093b419c21de7e9b35f7e0d', 16, 58), '1111GxfgFVyDW3zcFpUF1upSZoL7GCRiLk')
        self.assertEqual(change_base('0000003acd8f60b766e48e9db32093b419c21de7e9b35f7e0d', 16, 58), '111GxfgFVyDW3zcFpUF1upSZoL7GCRiLk')
        self.assertEqual(change_base('1111GxfgFVyDW3zcFpUF1upSZoL7GCRiLk', 58, 256).hex(),
                         '000000003acd8f60b766e48e9db32093b419c21de7e9b35f7e0d')
        self.assertRaisesRegex(EncodingError, "Invalid address hash160 length, should be 25 characters not",
                                addr_base58_to_pubkeyhash, '1111GxfgFVyDW3zcFpUF1upSZoL7GCRiLk')


class TestEncodingMethodsStructures(unittest.TestCase):

    def test_varbyteint_to_int_1(self):
        self.assertEqual(100, varbyteint_to_int(b'd')[0])

    def test_varbyteint_to_int_2(self):
        self.assertEqual(254, varbyteint_to_int(b'\xfe\xfe\x00')[0])

    def test_varbyteint_to_int_3(self):
        self.assertEqual(18440744073009551600, varbyteint_to_int(b'\xff\xf0\xd8\x9f\xf9\x07\xaf\xea\xff')[0])

    def test_int_to_varbyteint_1(self):
        self.assertEqual(b'd', int_to_varbyteint(100))

    def test_int_to_varbyteint_2(self):
        self.assertEqual(b'\xfd\xfd\x00', int_to_varbyteint(253))

    def test_int_to_varbyteint_3(self):
        self.assertEqual(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff', int_to_varbyteint(18446744073709551615))

    def test_varstr(self):
        self.assertEqual(b'\x1eThis string has a length of 30',
                         varstr('This string has a length of 30'))

    def test_convert_der_sig(self):
        sig = b'0E\x02!\x00\xe7\x1a\x8d\xd8>y\xfb\xd6/r\xa3\xd0\xd8\xa8\x1f\xdd\xbaS[\xd0\xf0\x88\xfa\x8b\xe1L' \
              b'\xd3F\x7f\xe5\x17\xae\x02 _l\xa4\x89LS\xcd\x8em&\xf7\x99uN\xb6\xfc\x0e\x86\xf6\x12\xd6\xdejL|' \
              b'\x07\xdcX \xa0\xe5\x18'
        self.assertEqual('e71a8dd83e79fbd62f72a3d0d8a81fddba535bd0f088fa8be14cd3467fe517ae5f6ca4894c53cd8e6d26f'
                         '799754eb6fc0e86f612d6de6a4c7c07dc5820a0e518', convert_der_sig(sig))

    def test_to_bytes_hex(self):
        self.assertEqual(b'\xde\xad\xbe\xef', to_bytes('deadbeef'))

    def test_to_bytes_nohex(self):
        self.assertEqual(b'deadbeefnohex', to_bytes('deadbeefnohex'))

    def test_to_bytes_nounhexlify(self):
        self.assertEqual(b'deadbeef', to_bytes('deadbeef', unhexlify=False))

    def test_to_bytes_unicode(self):
        self.assertEqual(b'\x07\xdcX \xa0\xe5\x18!]!,\xd5\x18\x8a\xe0,V5\xfa\xab',
                         to_bytes(u'07dc5820a0e518215d212cd5188ae02c5635faab'))

    def test_to_bytes_byteshex(self):
        self.assertEqual(b'\x07\xdcX \xa0\xe5\x18!]!,\xd5\x18\x8a\xe0,V5\xfa\xab',
                         to_bytes(b'07dc5820a0e518215d212cd5188ae02c5635faab'))

    def test_to_hexstring_string(self):
        self.assertEqual('deadbeef', to_hexstring('deadbeef'))

    def test_to_hexstring_bytes(self):
        self.assertEqual('707974686f6e6973636f6f6c', to_hexstring(b'pythoniscool'))

    def test_to_hexstring_bytes2(self):
        self.assertEqual('07dc5820a0e518215d212cd5188ae02c5635faab',
                         to_hexstring(b'\x07\xdcX \xa0\xe5\x18!]!,\xd5\x18\x8a\xe0,V5\xfa\xab'))

    def test_to_hexstring_unicode(self):
        self.assertEqual('07dc5820a0e518215d212cd5188ae02c5635faab',
                         to_hexstring(u'07dc5820a0e518215d212cd5188ae02c5635faab'))

    def test_der_encode_sig(self):
        r = 80828100789555555332401870818771238079532314371107341426356071258591122886343
        s = 15674820848044112551623338734376985640551839688984719714434052277382938010325
        der_sig = '3045022100b2b31575f8536b284410d01217f688be3a9faf4ba0ba3a9093f983e40d630' \
                  'ec7022022a7a25b01403cff0d00b3b853d230f8e96ff832b15d4ccc75203cb65896a2d5'
        self.assertEqual(to_hexstring(der_encode_sig(r, s)), der_sig)


VALID_CHECKSUM = [
    "A12UEL5L",
    "an83characterlonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1tt5tgs",
    "abcdef1qpzry9x8gf2tvdw0s3jn54khce6mua7lmqqqxw",
    "11qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqc8247j",
    "split1checkupstagehandshakeupstreamerranterredcaperred2y9e3w",
]

INVALID_CHECKSUM = [
    " 1nwldj5",
    "\x7F" + "1axkwrx",
    "an84characterslonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1569pvx",
    "pzry9x0s0muk",
    "1pzry9x0s0muk",
    "x1b4n0q5v",
    "li1dgmt3",
    "de1lg7wt\xff",
]

VALID_ADDRESS = [
    ["BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4", "0014751e76e8199196d454941c45d1b3a323f1433bd6"],
    ["tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7",
     "00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262"],
    ["tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy",
     "0020000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433"],
]

INVALID_ADDRESS = [
    "tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty",
    "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5",
    "BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2",
    "bc1rw5uspcuh",
    "bc10w508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90",
    "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P",
    "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sL5k7",
    "bc1zw508d6qejxtdg4y5r3zarvaryvqyzf3du",
    "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3pjxtptv",
    "bc1gmk9yu",
]

INVALID_ADDRESS_ENC = [
    ("BC", 0, 20),
    ("bc", 0, 21),
    ("bc", 17, 32),
    ("bc", 1, 1),
    ("bc", 16, 41),
]

BECH32M_VALID = [
    ('BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4', '0014751e76e8199196d454941c45d1b3a323f1433bd6'),
    ('tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7',
     '00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262'),
    ('bc1pw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kt5nd6y',
     '5128751e76e8199196d454941c45d1b3a323f1433bd6751e76e8199196d454941c45d1b3a323f1433bd6'),
    ('BC1SW50QGDZ25J', '6002751e'),
    ('bc1zw508d6qejxtdg4y5r3zarvaryvaxxpcs', '5210751e76e8199196d454941c45d1b3a323'),
    ('tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy',
     '0020000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433'),
    ('tb1pqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesf3hn0c',
     '5120000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433'),
    ('bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0',
     '512079be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'),
]

BECH32M_INVALID = [
    ('bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqh2y7hd', 'Invalid checksum (Bech32 instead of Bech32m)'),
    ('tb1z0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqglt7rf', 'Invalid checksum (Bech32 instead of Bech32m)'),
    ('BC1S0XLXVLHEMJA6C4DQV22UAPCTQUPFHLXM9H8Z3K2E72Q4K9HCZ7VQ54WELL', 'Invalid checksum (Bech32 instead of Bech32m)'),
    ('bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kemeawh', 'Invalid checksum (Bech32m instead of Bech32)'),
    ('tb1q0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq24jc47', 'Invalid checksum (Bech32m instead of Bech32)'),
    ('bc1p38j9r5y49hruaue7wxjce0updqjuyyx0kh56v8s25huc6995vvpql3jow4', "Character '111' not found in codebase"),
    ('BC130XLXVLHEMJA6C4DQV22UAPCTQUPFHLXM9H8Z3K2E72Q4K9HCZ7VQ7ZWS8R', 'Invalid witness version'),
    ('bc1pw5dgrnzv', 'Invalid decoded data length, must be between 2 and 40'),
    ('bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7v8n0nx0muaewav253zgeav',
     'Invalid decoded data length, must be between 2 and 40'),
    ('BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P', 'Invalid decoded data length, must be 20 or 32 bytes'),
    ('bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7v07qwwzcrf', "Invalid padding bits"),
    ('tb1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vpggkg4j', "Invalid padding bits"),
    ('bc1gmk9yu', 'Invalid checksum (Bech32 instead of Bech32m)'),
]

BECH32M_INVALID_PUBKEYHASH = [
    ('612079be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798', 'Witness version must be between 0 and '
                                                                             '16'),
    ('511979be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798', 'Incorrect pubkeyhash length'),
    ('0013751e76e8199196d454941c45d1b3a323f1433bd6', 'Incorrect pubkeyhash length'),
    ('6614751e76e8199196d454941c45d1b3a323f1433bd6', 'Witness version must be between 0 and 16')
]


class TestEncodingBech32SegwitAddresses(unittest.TestCase):
    """
    Reference tests for bech32 segwit adresses

    Copyright (c) 2017 Pieter Wuille
    Source: https://github.com/sipa/bech32/tree/master/ref/python
    """

    def test_valid_checksum(self):
        """Test checksum creation and validation."""
        for test in VALID_CHECKSUM:
            pos = test.rfind('1')
            test = test.lower()
            hrp = test[:pos]
            data = _codestring_to_array(test[pos + 1:], 'bech32')
            hrp_expanded = [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]
            self.assertEqual(_bech32_polymod(hrp_expanded + data), 1, msg="Invalid checksum for address %s" % test)
            test = test[:pos+1] + chr(ord(test[pos + 1]) ^ 1) + test[pos+2:]
            try:
                self.assertFalse(addr_bech32_to_pubkeyhash(test, hrp))
            except EncodingError:
                continue

    def test_invalid_checksum(self):
        """Test validation of invalid checksums."""
        for test in INVALID_CHECKSUM:
            try:
                pos = test.rfind('1')
                hrp = test[:pos]
                self.assertRaises(EncodingError, addr_bech32_to_pubkeyhash, test, hrp)
            except EncodingError as e:
                self.assertIn("not found in codebase", e.msg)

    def test_valid_address(self):
        """Test whether valid addresses decode to the correct output."""
        for (address, hexscript) in VALID_ADDRESS:
            scriptpubkey = addr_bech32_to_pubkeyhash(address, include_witver=True)
            self.assertEqual(scriptpubkey, bytes.fromhex(hexscript))
            addr = pubkeyhash_to_addr_bech32(scriptpubkey, address[:2].lower())
            self.assertEqual(address.lower(), addr)

    def test_invalid_address(self):
        """Test whether invalid addresses fail to decode."""
        for test in INVALID_ADDRESS:
            self.assertRaises(EncodingError, addr_bech32_to_pubkeyhash, "bc", test)
            self.assertRaises(EncodingError, addr_bech32_to_pubkeyhash, "tb", test)

    def test_quantity_class(self):
        self.assertEqual(str(Quantity(121608561109507200000, 'H/s', precision=10)), '121.6085611095 EH/s')
        self.assertEqual(str(Quantity(1 / 121608561109507200000, 'ots', precision=10)), '8.2231052722 zots')
        self.assertEqual(str(Quantity(0.0000000001, 'm', precision=2)), '100.00 pm')
        self.assertEqual(str(Quantity(121608561109507200000000000000000)), '121608561.110 Y')
        self.assertEqual(str(Quantity(1/1216085611095072000000000000000)), '0.000 y')
        self.assertEqual(str(Quantity(1/1216085611095072000000000000000, precision=10)), '0.0000008223 y')
        self.assertEqual(str(Quantity(10, 'pound', precision=0)), '10 pound')
        self.assertEqual(str(Quantity(0)), '0.000')

    # Source: https://github.com/bitcoin/bips/blob/master/bip-0350.mediawiki
    def test_bech32m_valid(self):
        for addr, pubkeyhash in BECH32M_VALID:
            assert pubkeyhash == addr_bech32_to_pubkeyhash(addr, include_witver=True).hex()
            prefix = addr.split('1')[0].lower()
            witver = change_base(addr.split('1')[1][0], 'bech32', 10)
            checksum_xor = addr_bech32_checksum(addr)
            addrc = pubkeyhash_to_addr_bech32(pubkeyhash, prefix, witver, checksum_xor=checksum_xor)
            assert addr.lower() == addrc

    def test_bech32_invalid(self):
        for addr, err in BECH32M_INVALID:
            try:
                addr_bech32_to_pubkeyhash(addr)
            except (EncodingError, TypeError) as e:
                assert str(e) == err

    def test_bech32_invalid_pubkeyhash(self):
        for pubkeyhash, err in BECH32M_INVALID_PUBKEYHASH:
            try:
                pubkeyhash_to_addr_bech32(pubkeyhash)
            except (EncodingError, TypeError) as e:
                assert str(e) == err


class TestEncodingConfig(unittest.TestCase):

    def test_config_opcodes(self):
        self.assertEqual(op.op_checklocktimeverify, 177)


class TestEncodingEncryption(unittest.TestCase):

    def test_encryption_aes(self):
        key = b'e2bfe15fc5d7067b567402dd9d7235fc088ac84eab8113bf8d7e3c288d2f1eff'
        data = b'A lot of people automatically dismiss e-currency as a lost cause because of all the companies that failed ' \
               b'since the 1990\'s. I hope it\'s obvious it was only the centrally controlled nature of those systems that ' \
               b'doomed them. I think this is the first time we\'re trying a decentralized, non-trust-based system.'
        encrypted_data = aes_encrypt(data, key)
        quote = aes_decrypt(encrypted_data, key)
        self.assertEqual(data, quote)

class TestEncodingCrypto(unittest.TestCase):

    def test_sha256(self):

        self.assertEqual(sha256(b'a' * 1000000).hex(),
            'cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0')
        self.assertEqual(sha256(b'a' * 1000000, as_hex=True),
            'cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0')


if __name__ == '__main__':
    unittest.main()
