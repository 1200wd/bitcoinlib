# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Common includes and helper methods
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

import ecdsa
import math

# secp256k1, http://www.oid-info.com/get/1.3.132.0.10
_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
_b = 0x0000000000000000000000000000000000000000000000000000000000000007L
_a = 0x0000000000000000000000000000000000000000000000000000000000000000L
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L
curve_secp256k1 = ecdsa.ellipticcurve.CurveFp(_p, _a, _b)
generator_secp256k1 = ecdsa.ellipticcurve.Point(curve_secp256k1, _Gx, _Gy, _r)

oid_secp256k1 = (1, 3, 132, 0, 10)
SECP256k1 = ecdsa.curves.Curve("SECP256k1", curve_secp256k1, generator_secp256k1, oid_secp256k1)
ec_order = _r

curve = curve_secp256k1
generator = generator_secp256k1

code_strings = {
    2: '01',
    3: ' ,.',
    10: '0123456789',
    16: '0123456789abcdef',
    32: 'abcdefghijklmnopqrstuvwxyz234567',
    58: '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz',
    256: ''.join([chr(x) for x in range(256)])
}



# General methods
def get_code_string(base):
    if base in code_strings:
        return code_strings[base]
    else:
        raise ValueError("Invalid base!")


def change_base(chars, base_from, base_to, min_lenght=0, output_even=-1):
    code_str = get_code_string(base_to)
    code_str_from = get_code_string(base_from)
    output = ''
    input_dec = 0
    addzeros = 0
    if output_even == -1:
        if base_to == 16:
            output_even = True
        else:
            output_even = False

    inp = chars
    # Convert input to decimal
    if isinstance(inp, (int, long)):
        input_dec = inp
    elif isinstance(inp, str):
        factor = 1
        while len(inp):
            pos = code_str_from.find(inp[-1:])
            if pos == -1:
                pos = code_str_from.find(inp[-1:].lower())
            if pos == -1:
                raise ValueError("Unknown character in input format")
            input_dec += pos * factor
            # if pos*factor == 0 and input in [0]:

            if not pos * factor:
                if not len(inp.strip(code_str_from[0])):
                    addzeros += 1
            inp = inp[:-1]
            factor *= base_from
    else:
        raise ValueError("Unknown input format")

    # Convert decimal to output base
    while int(input_dec) != 0:
        r = int(input_dec) % base_to
        input_dec = str((int(input_dec)-r) / base_to)
        output = code_str[r] + output

    if base_to == 10:
        return int(output)

    pos_fact = math.log(base_to, base_from)
    expected_length = len(str(chars)) / pos_fact
    zeros = int(addzeros / pos_fact)
    if addzeros == 1:
        zeros = 1

    for _ in range(zeros):
        if base_to != 10 and not expected_length == len(output):
            output = code_str[0] + output

    # Add zero's to make even number of digits on Hex output (or if specified)
    if output_even and len(output) % 2:
        output = code_str[0] + output

    # Add leading zero's
    while len(output) < min_lenght:
        output = code_str[0] + output

    return output
