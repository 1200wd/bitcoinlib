# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Common includes and helper methods
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

import math


code_strings = {
    2: '01',
    3: ' ,.',
    10: '0123456789',
    16: '0123456789abcdef',
    32: 'abcdefghijklmnopqrstuvwxyz234567',
    58: '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz',
    256: ''.join([chr(x) for x in range(256)]),
}



def get_code_string(base):
    if base in code_strings:
        return code_strings[base]
    else:
        return range(0,base)


def change_base(chars, base_from, base_to, min_lenght=0, output_even=-1, output_as_list=None):
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
        raise ValueError("For a decimal input a minimum output lenght is required!")
    code_str = get_code_string(base_to)
    if not output_as_list:
        if isinstance(code_str, list):
            output_as_list = True
        else:
            output_as_list = False
    code_str_from = get_code_string(base_from)
    output = []
    input_dec = 0
    addzeros = 0
    inp = chars
    if output_even == -1:
        if base_to == 16:
            output_even = True
        else:
            output_even = False

    if isinstance(inp, unicode):
        try:
            inp = str(inp)
        except UnicodeEncodeError:
            raise ValueError("Cannot convert this unicode to string format")

    if isinstance(inp, (int, long)):
        input_dec = inp
    elif isinstance(inp, (str, list)):
        factor = 1
        while len(inp):
            if isinstance(inp, list):
                item = inp.pop()
            else:
                item = inp[-1:]
                inp = inp[:-1]
            try:
                pos = code_str_from.index(item)
            except ValueError:
                try:
                    pos = code_str_from.index(item.lower())
                except ValueError:
                    raise ValueError("Unknown character '%s' in input format" % item)
            input_dec += pos * factor
            # Add leading zero if there are leading zero's in input
            if not pos * factor:
                if (len(inp) and isinstance(inp, list) and inp[0] == code_str_from[0]) \
                        or (isinstance(inp, str) and not len(inp.strip(code_str_from[0]))):
                    addzeros += 1
            factor *= base_from
    else:
        raise ValueError("Unknown input format %s" % inp)

    # Convert decimal to output base
    while int(input_dec) != 0:
        r = int(input_dec) % base_to
        input_dec = str((int(input_dec)-r) / base_to)
        output = [code_str[r]] + output

    if base_to == 10:
        output = ''.join(output)
        return int(0) or (output != '' and int(output))

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

    if not output_as_list:
        output = ''.join(output)
    return output
