# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Unit Tests for Key, Encoding and Mnemonic Class
#    © 2016 November - 1200 Web Development <http://1200wd.com/>
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

from bitcoinlib.encoding import change_base


class TestEncodingMethods(unittest.TestCase):

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

    def test_change_base_leading_zeros3(self):
        self.assertEqual('1L', change_base('013', 16, 58))

    def test_change_base_leading_zeros4(self):
        self.assertEqual(b'\x04G\x81', change_base('044781', 16, 256))

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


if __name__ == '__main__':
    unittest.main()
