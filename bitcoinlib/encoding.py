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
    32: b'abcdefghijklmnopqrstuvwxyz234567',
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


def array_to_codestring(array, base):
    codebase = code_strings[base]
    codestring = ""
    for i in array:
        if i < 0 or i > len(codebase):
            raise EncodingError("Index %i out of range for codebase" % i)
        if not PY3:
            codestring += codebase[i]
        else:
            codestring += chr(codebase[i])
    return codestring


def codestring_to_array(codestring, base):
    codestring = to_bytes(codestring)
    codebase = code_strings[base]
    array = []
    for s in codestring:
        try:
            array.append(codebase.index(s))
        except ValueError:
            raise EncodingError("Character '%s' not found in codebase" % s)
    return array


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
            try:
                var = var.encode('utf-8')
            except ValueError:
                raise EncodingError("Cannot convert this unicode to string format")

    if base == 10:
        return int(var)
    elif isinstance(var, list):
        return deepcopy(var)
    else:
        return var


def change_base(chars, base_from, base_to, min_length=0, output_even=None, output_as_list=None):
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
    :param min_length: Minimal output length. Required for decimal, advised for all output to avoid leading zeros conversion problems.
    :type min_length: int
    :param output_even: Specify if output must contain a even number of characters. Sometimes handy for hex conversions.
    :type output_even: bool
    :param output_as_list: Always output as list instead of string.
    :type output_as_list: bool

    :return str, list: Base converted input as string or list.
    """
    if base_from == 10 and not min_length:
        raise EncodingError("For a decimal input a minimum output length is required!")

    code_str = _get_code_string(base_to)

    if not isinstance(base_to, int):
        base_to = len(code_str)
    elif int(base_to) not in code_strings:
        output_as_list = True

    code_str_from = _get_code_string(base_from)
    if not isinstance(base_from, int):
        base_from = len(code_str)
    if not isinstance(code_str_from, (bytes, list)):
        raise EncodingError("Code strings must be a list or defined as bytes")
    output = []
    input_dec = 0
    addzeros = 0
    inp = normalize_var(chars, base_from)

    # Use binascii and int for standard conversions to speedup things
    if not min_length:
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
        while len(output) < min_length:
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
    if PY3 and base_to == 256 and not output_as_list:
        return output.encode('ISO-8859-1')
    else:
        return output


def varbyteint_to_int(byteint):
    """
    Convert CompactSize Variable length integer in byte format to integer.

    See https://en.bitcoin.it/wiki/Protocol_documentation#Variable_length_integer for specification

    :param byteint: 1-9 byte representation
    ;type byteint: int, list, bytearray

    :return: normal integer
    """
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
    :type s: bytes, str

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

    :param address: Crypto currency address in base-58 format
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
    """
    Internal function that computes the Bech32 checksum
    """
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def convertbits(data, frombits, tobits, pad=True):
    """
    'General power-of-2 base conversion'

    Source: https://github.com/sipa/bech32/tree/master/ref/python

    :param data: Data values to convert
    :type data: list
    :param frombits: Number of bits in source data
    :type frombits: int
    :param tobits: Number of bits in result data
    :type tobits: int
    :param pad: Use padding zero's or not. Default is True
    :type pad: bool

    :return list: Converted values
    """
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if not PY3 and isinstance(value, str):
            value = int(value, 16)
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


def pubkeyhash_to_addr_bech32(pubkeyhash, hrp='bc', witver=0, seperator='1'):
    """
    Encode public key hash as bech32 segwit address

    Format of address is prefix/hrp + seperator + bech32 address + checksum

    For more information see BIP173 proposal at https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki

    :param pubkeyhash: Public key hash
    :type pubkeyhash: str, bytes
    :param hrp: Address prefix called Human-readable part. Default is 'bc' an abbreviation of Bitcoin. Use 'tb' for testnet.
    :type hrp: str
    :param witver: Witness version between 0 and 16
    :type witver: int
    :param seperator: Seperator char between hrp and data, should always be left to '1' otherwise its not standard.
    :type seperator: str

    :return str: Bech32 encoded address
    """

    if not isinstance(pubkeyhash, bytes):
        pubkeyhash = to_bytes(pubkeyhash)
    if len(pubkeyhash) not in [20, 32]:
        if int(pubkeyhash[0]) != 0:
            witver = int(pubkeyhash[0]) - 0x50
        pubkeyhash = pubkeyhash[2:]

    data = [witver] + convertbits(pubkeyhash, 8, 5)

    # Expand the HRP into values for checksum computation
    hrp_expanded = [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]
    polymod = _bech32_polymod(hrp_expanded + data + [0, 0, 0, 0, 0, 0]) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]

    return hrp + seperator + array_to_codestring(data, 'bech32') + array_to_codestring(checksum, 'bech32')


def addr_bech32_to_pubkeyhash(bech, hrp='bc', as_hex=False, include_witver=False):
    """
    Decode bech32 / segwit address to public key hash

    Validate the Bech32 string, and determine HRP and data

    :param bech: Bech32 address to convert
    :type bech: str
    :param hrp: Address prefix called Human-readable part. Default is 'bc' an abbreviation of Bitcoin. Use 'tb' for testnet.
    :type hrp: str
    :param as_hex: Output public key hash as hex or bytes. Default is False
    :type as_hex: bool
    :param include_witver: Include witness version in output? Default is False
    :type include_witver: bool

    :return str: Public Key Hash
     
    """
    if ((any(ord(x) < 33 or ord(x) > 126 for x in bech)) or
            (bech.lower() != bech and bech.upper() != bech)):
        return False
    bech = bech.lower()
    pos = bech.rfind('1')
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return False
    if hrp != bech[:pos]:
        raise EncodingError("Invalid address. Prefix '%s', prefix expected is '%s'" % (bech[:pos], hrp))
    data = codestring_to_array(bech[pos+1:], 'bech32')
    hrp_expanded = [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]
    if not _bech32_polymod(hrp_expanded + data) == 1:
        return False
    data = data[:-6]
    decoded = bytearray(convertbits(data[1:], 5, 8, pad=False))
    if decoded is None or len(decoded) < 2 or len(decoded) > 40:
        return False
    if data[0] > 16:
        return False
    if data[0] == 0 and len(decoded) not in [20, 32]:
        return False
    prefix = b''
    if include_witver:
        datalen = len(decoded)
        prefix = bytearray([data[0] + 0x50 if data[0] else 0, datalen])
    if as_hex:
        return change_base(prefix + decoded, 256, 16)
    return prefix + decoded


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

    :param s: String to convert
    :type s: str, unicode, bytes, bytearray
    :param unhexlify: Try to unhexlify hexstring
    :type unhexlify: bool

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
    Convert Bytes or ByteArray to hexadecimal string

    :param var: Variable to convert to hex string
    :type var: bytes, bytearray, str

    :return: hexstring
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
