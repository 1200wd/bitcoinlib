# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Common includes and helper methods
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

import sys
import math
import numbers
import hashlib
from bitcoinlib.main import *

_logger = logging.getLogger(__name__)


class EncodingError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg

bytesascii = b''
for x in range(256):
    bytesascii += bytes(bytearray((x,)))

code_strings = {
    2: b'01',
    3: b' ,.',
    10: b'0123456789',
    16: b'0123456789abcdef',
    32: b'abcdefghijklmnopqrstuvwxyz234567',
    58: b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz',
    256: b''.join([bytes(bytearray((x,))) for x in range(256)]),
}


def get_code_string(base):
    if base in code_strings:
        return code_strings[base]
    else:
        return list(range(0, base))


def to_bytearray(inp, code_str_from):
    if inp in code_str_from:
        return inp
    else:
        return inp.lower()


def normalize_var(var, base):
    """
    For Python 2 convert variabele to string
    For Python 3 convert to bytes
    Convert decimals to integer type
    :param var: input variable in any format
    :param base: specify variable format, i.e. 10 for decimal, 16 for hex
    :return: string for Python 2, bytes for Python 3, decimal for base10
    """
    try:
        if sys.version > '3' and isinstance(var, str):
            var = var.encode('ISO-8859-1')
    except ValueError:
        try:
            var = var.encode('utf-8')
        except ValueError:
            raise EncodingError("Unknown character '%s' in input format" % var)

    if sys.version < '3' and isinstance(var, unicode):
        try:
            var = str(var)
        except UnicodeEncodeError:
            raise EncodingError("Cannot convert this unicode to string format")

    if base==10:
        return int(var)
    else:
        return var


def change_base(chars, base_from, base_to, min_lenght=0, output_even=None, output_as_list=None):
    """
    Convert input chars from one base to another.

    From and to base can be any base. If base is not found a array of index numbers will be returned

    Examples:
    > change_base('FF', 16, 10) will return 256
    > change_base(100, 16, 2048) will return [100]

    :param chars: Input string
    :param base_from: Base number from input string
    :param base_to: Base number for output
    :param min_lenght: Minimal output length. Required for decimal,
           advised for all output to avoid leading zeros conversion problems.
    :param output_even: Specify if output must contain a even number of characters.
           Sometimes handy for hex conversions.
    :param output_as_list: Always output as list instead of string.
    :return: Base converted input as string or list.
    """
    if base_from == 10 and not min_lenght:
        raise EncodingError("For a decimal input a minimum output lenght is required!")
    code_str = get_code_string(base_to)
    if int(base_to) not in code_strings:
        output_as_list = True

    code_str_from = get_code_string(base_from)
    if not isinstance(code_str_from, (bytes, list)):
        raise EncodingError("Code strings must be a list or defined as bytes")
    output = []
    input_dec = 0
    addzeros = 0
    inp = normalize_var(chars, base_from)

    if output_even is None and base_to == 16:
        output_even = True

    if isinstance(inp, numbers.Number):
        input_dec = inp
    elif isinstance(inp, (str, list, bytes)):
        factor = 1
        while len(inp):
            if isinstance(inp, list):
                item = inp.pop()
            else:
                item = inp[-1:]
                inp = inp[:-1]
            itemindex = to_bytearray(item, code_str_from)
            try:
                pos = code_str_from.index(itemindex)
            except ValueError:
                raise EncodingError("Unknown character '%s' in input" % item)
            input_dec += pos * factor

            # Add leading zero if there are leading zero's in input
            if not pos * factor:
                if sys.version < '3':
                    firstchar = code_str_from[0]
                else:
                    firstchar = chr(code_str_from[0]).encode('utf-8')
                if (len(inp) and isinstance(inp, list) and inp[0] == code_str_from[0]) \
                        or (isinstance(inp, (str, bytes)) and not len(inp.strip(firstchar))) \
                        or isinstance(inp, list):
                    addzeros += 1
            factor *= base_from
    else:
        raise EncodingError("Unknown input format %s" % inp)

    # Convert decimal to output base
    while int(input_dec) != 0:
        r = int(input_dec) % base_to
        input_dec = str((int(input_dec)-r) // base_to)
        output = [code_str[r]] + output

    if base_to != 10:
        pos_fact = math.log(base_to, base_from)
        expected_length = len(str(chars)) / pos_fact
        zeros = int(addzeros / pos_fact)
        if addzeros == 1:
            zeros = 1

        for _ in range(zeros):
            if base_to != 10 and not expected_length == len(output):
                output = [code_str[0]] + output

        # Add zero's to make even number of digits on Hex output (or if specified)
        if output_even and len(output) % 2:
            output = [code_str[0]] + output

        # Add leading zero's
        while len(output) < min_lenght:
            output = [code_str[0]] + output

    if not output_as_list and isinstance(output, list):
        if len(output) == 0:
            output = 0
        elif isinstance(output[0], bytes):
            output = b''.join(output)
        elif isinstance(output[0], int):
            co = ''
            for c in output:
                co += chr(c)
            output = co
        else:
            output = ''.join(output)
    if base_to == 10:
        return int(0) or (output != '' and int(output))
    if sys.version > '3' and base_to == 256:
        return output.encode('ISO-8859-1')
    else:
        return output


def addr2pubkeyhash(address, as_hex=False):
    address = change_base(address, 58, 256, 25)
    check = address[-4:]
    pkh = address[:-4]
    checksum = hashlib.sha256(hashlib.sha256(pkh).digest()).digest()[0:4]
    assert (check == checksum), "Invalid address, checksum incorrect"
    if as_hex:
        return change_base(pkh, 256, 16)[2:]
    else:
        return pkh[1:]


if __name__ == '__main__':
    #
    # SOME EXAMPLES
    #

    examples = [
        ('4c52127a72fb42b82439ab18697dcfcfb96ac63ba8209833b2e29f2302b8993f45e743412d65c7a571da70259d4f6795e98af20e6e'
         '57603314a662a49c198199', 16, 256),
        ('LRzrûB¸$9«i}ÏÏ¹jÆ;¨ 3²â#¸?EçCA-eÇ¥qÚp%OgéònW`3¦b¤', 256, 16),
        # ('LRzrûB¸$9«i}ÏÏ¹jÆ;¨ 3²â#¸?EçCA-eÇ¥qÚp%OgéònW`3¦b¤', 16, 256),  # Test EncodingError
        ('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX', 58, 16),
        ('FF', 16, 10),
        ('AF', 16, 2),
        (200, 10, 16, 2),
        (200, 10, 16, 4),
        ('thisisfunny', 32, 3),
        ('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 16),
        ('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 32),
        ('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 256),
        ('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 2048),
        ([b'\0', b'\x12', b'L'], 256, 16, 6),
        ("為 宋 暴 治 伯 及 灘 冶 忙 逃 湘 艇 例 讓 忠", 256, 16),
        (b'\x00\t\xc6\xe7\x11\x18\xd8\xf1+\xeck\\a\x88K5g|\n\n\xe3*\x02\x1f\x87', 256, 58),
        (b'\0', 256, 10),
        ("\x00\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee\xd6\x19g\xf6", 256, 58),
        (b'LR\x12zr\xfbB\xb8$9\xab\x18i}\xcf\xcf\xb9j\xc6;\xa8 \x983\xb2\xe2\x9f#\x02\xb8\x99?E\xe7CA-e\xc7\xa5q'
         b'\xdap%\x9dOg\x95\xe9\x8a\xf2\x0enW`3\x14\xa6b\xa4\x9c\x19\x81\x99', 256, 16),
    ]

    print("\n=== Change base: convert from base N to base M ===")
    for example in examples:
        print("\n>>> change_base%s     # Change from base%d to base%d" %
              (example, example[1], example[2]))
        print("%s" % change_base(*example))

    print("\n=== Conversion of Bitcoin Addresses and Public Keys ===")
    addrs = ['12ooWd8Xag7hsgP9PBPnmyGe36VeUrpMSH', '1111111111111111111114oLvT2',
             '1QLbz7JHiBTspS962RLKV8GndWFwi5j6Qr']
    for addr in addrs:
        print("Public Key Hash of address '%s' is '%s'" % (addr, addr2pubkeyhash(addr, True)))
