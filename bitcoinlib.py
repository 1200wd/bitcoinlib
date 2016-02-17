# -*- coding: utf-8 -*-
#
#    bitoinlib - bitcoinlib.py
#    Copyright (C) 2016 February 
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
import hashlib
import random

# secp256k1, http://www.oid-info.com/get/1.3.132.0.10
_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
_b = 0x0000000000000000000000000000000000000000000000000000000000000007L
_a = 0x0000000000000000000000000000000000000000000000000000000000000000L
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L
curve_secp256k1 = ecdsa.ellipticcurve.CurveFp(_p, _a, _b)
generator_secp256k1 = ecdsa.ellipticcurve.Point(curve_secp256k1, _Gx, _Gy, _r)

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

def change_base(input, base_from, base_to, min_lenght=0):
    code_str = get_code_string(base_to)
    code_str_from = get_code_string(base_from)
    output = ''
    input_dec = 0

    # Convert input to decimal
    if isinstance(input, int):
        input_dec = input
    elif isinstance(input, str):
        factor = 1
        while len(input):
            pos = code_str_from.find(input[-1:])
            if pos == -1:
                pos = code_str_from.find(input[-1:].lower())
            if pos == -1:
                raise ValueError("Unknown character in input format")
            input_dec += pos * factor
            input = input[:-1]
            factor *= base_from
    else:
        raise ValueError("Unknown input format")

    # Convert decimal to output base
    while input_dec >= base_to:
        r = input_dec % base_to
        input_dec = (input_dec-r) / base_to
        output = code_str[r] + output
    if input_dec:
        output = code_str[input_dec] + output

    # Add leading zero's
    while len(output) < min_lenght:
        output = code_str[0] + output

    return output


class PrivateKey:
    """
    Class to handle Bitcoin Private Keys. Specify imput Private Key in hex format.

    If no key is specified when creating class a cryptographically secure Private Key is generated using the os.urandom() function
    """
    def __init__(self, private_key_hex=None):
        if private_key_hex:
            # TODO: Add check to validate key and/or to determine format and convert key
            self._secret = change_base(private_key_hex, 16, 10)
        if not self._secret:
            rng = random.SystemRandom()
            rng.random()
            self._secret = rng.randint(0, _r)

    def get_hex(self):
        return change_base(str(self._secret), 10, 16, 64)

    def get_bit(self):
        return change_base(str(self._secret), 10, 2, 256)

    def get_dec(self):
        return self._secret

    def get_wif(self, compressed=True):
        """
        Get Private Key in Wallet Import Format, steps:
        (1) Convert to Binary and add 0x80 hex
        (2) Calculate Double SHA256 and add as checksum to end of key

        :param compressed: Get compressed private key, which means private key will be used to generate compressed public keys.
        :return: Base58Check encoded Private Key WIF
        """
        key = chr(128) +change_base(str(self._secret), 10, 256, 32)
        if compressed:
            key += chr(1)
        key += hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]
        return change_base(key, 256, 58)

    def import_wif(self, private_key_wif, compressed=True):
        key = change_base(private_key_wif, 58, 256)

        # Split key and checksum and verify Private Key
        checksum = key[-4:]
        key = key[:-4]
        if checksum != hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]:
            raise ValueError("Invalid checksum, not a valid WIF compressed key")

        # Check and remove prefix and postfix tags
        if compressed:
            if key[-1:] != chr(1):
                raise ValueError("Not a valid WIF compressed key")
            key = key[:-1]
        if key[:1] != chr(128):
            raise ValueError("Not a valid WIF compressed key")
        key = key[1:]
        self._secret = change_base(key, 256, 10)

    def import_hex(self, private_key_hex):
        self._secret = change_base(private_key_hex, 16, 10)


class PublicKey:
    """
    Bitcoin Public Key class.
    """
    def __init__(self, public_key):
        self._public = public_key
        self._x = public_key[1:31]
        self._y = public_key[32:64]

    def get_point(self):
        x = int(change_base(self._x, 16, 10))
        y = int(change_base(self._y, 16, 10))
        return (x, y)

    def get_hex(self):
        return self._public

    def get_bit(self):
        return change_base(str(self._public), 10, 2, 256)

    def get_dec(self):
        return self._public

    def get_wif(self, compressed=True):
        return

    def get_address(self, compressed=None):
        key_bin = change_base(self._public, 16, 256)
        return hashlib.new('ripemd160', key_bin).hexdigest()

