# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    ENCODING - Helper methods for encoding and conversion
#    © 2018 January - 1200 Web Development <http://1200wd.com/>
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
from copy import deepcopy
import ecdsa
import struct
import hashlib
import binascii
import unicodedata
from bitcoinlib.main import *

_logger = logging.getLogger(__name__)


# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3


class EncodingError(Exception):
    """ Log and raise encoding errors """
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
    'base32': b'abcdefghijklmnopqrstuvwxyz234567',
    58: b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz',
    256: b''.join([bytes(bytearray((x,))) for x in range(256)]),
    'bech32': b'qpzry9x8gf2tvdw0s3jn54khce6mua7l'
}


def _get_code_string(base):
    if base in code_strings:
        return code_strings[base]
    else:
        return list(range(0, base))


def _in_code_string_check(inp, code_str_from):
    if not PY3 and isinstance(inp, bytearray):
        inp = str(inp)
    if inp in code_str_from:
        return inp
    else:
        return inp.lower()


def normalize_var(var, base=256):
    """
    For Python 2 convert variabele to string
    For Python 3 convert to bytes
    Convert decimals to integer type

    :param var: input variable in any format
    :type var: str, byte, bytearray, unicode
    :param base: specify variable format, i.e. 10 for decimal, 16 for hex
    :type base: int

    :return: Normalized var in string for Python 2, bytes for Python 3, decimal for base10
    """
    try:
        if PY3 and isinstance(var, str):
            var = var.encode('ISO-8859-1')
    except ValueError:
        try:
            var = var.encode('utf-8')
        except ValueError:
            raise EncodingError("Unknown character '%s' in input format" % var)

    if not PY3 and isinstance(var, unicode):
        try:
            var = str(var)
        except UnicodeEncodeError:
            raise EncodingError("Cannot convert this unicode to string format")

    if base == 10:
        return int(var)
    elif isinstance(var, list):
        return deepcopy(var)
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
    :type chars: any
    :param base_from: Base number or name from input
    :type base_from: int, str
    :param base_to: Base number or name for output
    :type base_to: int, str
    :param min_lenght: Minimal output length. Required for decimal, advised for all output to avoid leading zeros conversion problems.
    :type min_lenght: int
    :param output_even: Specify if output must contain a even number of characters. Sometimes handy for hex conversions.
    :type output_even: bool
    :param output_as_list: Always output as list instead of string.
    :type output_as_list: bool

    :return str, list: Base converted input as string or list.
    """
    if base_from == 10 and not min_lenght:
        raise EncodingError("For a decimal input a minimum output lenght is required!")

    code_str = _get_code_string(base_to)

    if not isinstance(base_to, int):
        base_to = len(code_str)
    elif int(base_to) not in code_strings:
        output_as_list = True

    code_str_from = _get_code_string(base_from)
    if not isinstance(code_str_from, (bytes, list)):
        raise EncodingError("Code strings must be a list or defined as bytes")
    output = []
    input_dec = 0
    addzeros = 0
    inp = normalize_var(chars, base_from)

    # Use binascii and int for standard conversions to speedup things
    if not min_lenght:
        if base_from == 256 and base_to == 16:
            return to_hexstring(binascii.hexlify(inp))
        elif base_from == 16 and base_to == 256:
            return binascii.unhexlify(inp)
    if base_from == 16 and base_to == 10:
        return int(inp, 16)

    if output_even is None and base_to == 16:
        output_even = True

    if isinstance(inp, numbers.Number):
        input_dec = inp
    elif isinstance(inp, (str, list, bytes, bytearray)):
        factor = 1
        while len(inp):
            if isinstance(inp, list):
                item = inp.pop()
            else:
                item = inp[-1:]
                inp = inp[:-1]
            itemindex = _in_code_string_check(item, code_str_from)
            try:
                pos = code_str_from.index(itemindex)
            except ValueError:
                raise EncodingError("Unknown character '%s' in input" % item)
            input_dec += pos * factor

            # Add leading zero if there are leading zero's in input
            if not pos * factor:
                if not PY3:
                    firstchar = code_str_from[0]
                else:
                    firstchar = chr(code_str_from[0]).encode('utf-8')
                if isinstance(inp, list):
                    if not len([x for x in inp if x != firstchar]):
                        addzeros += 1
                elif not len(inp.strip(firstchar)):
                    addzeros += 1
            factor *= base_from
    else:
        raise EncodingError("Unknown input format %s" % inp)

    # Convert decimal to output base
    while input_dec != 0:
        input_dec, remainder = divmod(input_dec, base_to)
        output = [code_str[remainder]] + output

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
    if PY3 and base_to == 256:
        return output.encode('ISO-8859-1')
    else:
        return output


def varbyteint_to_int(byteint):
    """
    Convert CompactSize Variable length integer in byte format to integer.

    See https://en.bitcoin.it/wiki/Protocol_documentation#Variable_length_integer for specification

    :param byteint: 1-9 byte representation as integer

    :return: normal integer
    """
    # byteint = to_bytearray(byteint)
    if not isinstance(byteint, (bytes, list, bytearray)):
        raise EncodingError("Byteint be a list or defined as bytes")
    if PY3 or isinstance(byteint, (list, bytearray)):
        ni = byteint[0]
    else:
        ni = ord(byteint[0])
    if ni < 253:
        return ni, 1
    if ni == 253:  # integer of 2 bytes
        size = 2
    elif ni == 254:  # integer of 4 bytes
        size = 4
    else:  # integer of 8 bytes
        size = 8
    return change_base(byteint[1:1+size][::-1], 256, 10), size + 1


def int_to_varbyteint(inp):
    """
    Convert integer to CompactSize Variable length integer in byte format.

    See https://en.bitcoin.it/wiki/Protocol_documentation#Variable_length_integer for specification

    :param inp: Integer to convert
    :type inp: int

    :return: byteint: 1-9 byte representation as integer
    """
    if not isinstance(inp, numbers.Number):
        raise EncodingError("Input must be a number type")
    if inp < 0xfd:
        return struct.pack('B', inp)
    elif inp < 0xffff:
        return struct.pack('<cH', b'\xfd', inp)
    elif inp < 0xffffffff:
        return struct.pack('<cL', b'\xfe', inp)
    else:
        return struct.pack('<cQ', b'\xff', inp)


def varstr(s):
    """
    Convert string to bytestring preceeded with length byte

    :param s: bytestring
    :type s: bytes

    :return bytes: varstring
    """
    s = normalize_var(s)
    return int_to_varbyteint(len(s)) + s


def convert_der_sig(s, as_hex=True):
    """
    Convert DER encoded signature to signature

    :param s: DER signature
    :type s: bytes
    :param as_hex: Output as hexstring
    :type as_hex: bool

    :return bytes, str: Signature
    """
    if not s:
        return ""
    sg, junk = ecdsa.der.remove_sequence(s)
    if junk != b'':
        raise EncodingError("Junk found in encoding sequence %s" % junk)
    x, sg = ecdsa.der.remove_integer(sg)
    y, sg = ecdsa.der.remove_integer(sg)
    sig = '%064x%064x' % (x, y)
    if as_hex:
        return sig
    else:
        return binascii.unhexlify(sig)


def addr_to_pubkeyhash(address, as_hex=False):
    """
    Convert address to public key hash

    :param address: Cryptocurrency address in base-58 format
    :type address: str
    :param as_hex: Output as hexstring
    :type as_hex: bool

    :return bytes, str: public key hash
    """
    try:
        address = change_base(address, 58, 256, 25)
    except EncodingError as err:
        raise EncodingError("Invalid address %s: %s" % (address, err))
    check = address[-4:]
    pkh = address[:-4]
    checksum = hashlib.sha256(hashlib.sha256(pkh).digest()).digest()[0:4]
    assert (check == checksum), "Invalid address, checksum incorrect"
    if as_hex:
        return change_base(pkh, 256, 16)[2:]
    else:
        return pkh[1:]


def pubkeyhash_to_addr(pkh, versionbyte=b'\x00'):
    """
    Convert public key hash to address

    :param pkh: Public key hash
    :type pkh: bytes, str
    :param versionbyte: Prefix version byte of network, default is bitcoin '\x00'
    :type versionbyte: bytes

    :return str: Base-58 encoded address

    """
    pkh = to_bytearray(pkh)
    key = versionbyte + pkh
    addr256 = key + hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]
    return change_base(addr256, 256, 58)


def _bech32_polymod(values):
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def pubkeyhash_to_addr_bech32(witprog, hrp='bc', witver=b'\0', seperator='1'):
    data = witver + to_bytes(witprog)

    # Expand the HRP into values for checksum computation
    hrp_expanded = [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]
    polymod = _bech32_polymod(hrp_expanded + [0, 0, 0, 0, 0, 0]) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]

    return hrp + seperator + change_base(data, 256, 'bech32') + change_base(checksum, 32, 'bech32')


def script_to_pubkeyhash(script):
    """
    Creates a RIPEMD-160 hash of a locking, unlocking, redeemscript, etc

    :param script: Script
    :type script: bytes

    :return bytes: RIPEMD-160 hash of script
    """
    return hashlib.new('ripemd160', hashlib.sha256(script).digest()).digest()


def to_bytearray(s):
    """
    Convert String, Unicode or Bytes to Python 2 and 3 compatible ByteArray
    :param s: String, Unicode, Bytes or ByteArray
    :return: ByteArray
    """
    if isinstance(s, (str, unicode if not PY3 else str)):
        try:
            s = binascii.unhexlify(s)
        except:
            pass
    return bytearray(s)


def to_bytes(s, unhexlify=True):
    """
    Convert String, Unicode or ByteArray to Bytes
    :param s: String, Unicode, Bytes or ByteArray
    :param unhexlify: Try to unhexlify hexstring
    :return: Bytes var
    """
    s = normalize_var(s)
    if unhexlify:
        try:
            s = binascii.unhexlify(s)
            return s
        except:
            pass
    return s


def to_hexstring(var):
    """
    Convert Bytes or ByteArray to printable string
    :param var: Bytes, ByteArray or other input variable
    :return:
    """
    var = normalize_var(var)

    if isinstance(var, (str, bytes)):
        try:
            binascii.unhexlify(var)
            if PY3:
                return str(var, 'ISO-8859-1')
            else:
                return var
        except:
            pass

    s = binascii.hexlify(var)
    if PY3:
        return str(s, 'ISO-8859-1')
    else:
        return s


def normalize_string(txt):
    """
    Normalize a string to the default NFKD unicode format
    See https://en.wikipedia.org/wiki/Unicode_equivalence#Normalization

    :param txt: string value
    :type txt: bytes, bytearray, str

    :return: string

    """
    if isinstance(txt, str if sys.version < '3' else bytes):
        utxt = txt.decode('utf8')
    elif isinstance(txt, unicode if sys.version < '3' else str):
        utxt = txt
    else:
        raise TypeError("String value expected")

    return unicodedata.normalize('NFKD', utxt)
