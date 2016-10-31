# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Public key cryptography and Hierarchical Deterministic Key Management
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

import hashlib
import hmac
import random
import struct
import ecdsa
from Crypto.Cipher import AES
import scrypt
import binascii

from secp256k1 import secp256k1_generator as generator, secp256k1_curve as curve, secp256k1_p, secp256k1_n
from encoding import change_base

HDKEY_XPRV = '0488ADE4'.decode('hex')
HDKEY_XPUB = '0488B21E'.decode('hex')
HDKEY_TPRV = '04358394'.decode('hex')
HDKEY_TPUB = '043587CF'.decode('hex')
ADDRESSTYPE_BITCOIN = b'\x00'
ADDRESSTYPE_P2SH = b'\x05'
ADDRESSTYPE_TESTNET = b'\x6F'
PRIVATEKEY_WIF = b'\x80'
PRIVATEKEY_WIF_TESTNET = b'\xEF'


#TODO: Make more advanced, see https://en.bitcoin.it/wiki/List_of_address_prefixes
def get_key_format(key, keytype=None):
    """
    Determins the type and format of a public or private key by length and prefix.
    This method does not validate if a key is valid.
    :param key: Any private or public key
    :param keytype: 'private' or 'public', is most cases not required as methods takes best guess
    :return: format of key as string
    """
    if keytype not in [None, 'private', 'public']:
        raise ValueError("Keytype must be 'private' or 'public")
    if isinstance(key, (int, long, float)):
        return 'decimal'
    elif len(key) == 130 and key[:2] == '04' and keytype != 'private':
        return "public_uncompressed"
    elif len(key) == 66 and key[:2] in ['02', '03'] and keytype != 'private':
        return "public"
    elif len(key) == 32:
        return 'bin'
    elif len(key) == 33:
        return 'bin_compressed'
    elif len(key) == 64:
        return 'hex'
    elif len(key) == 66  and keytype != 'public':
        return 'hex_compressed'
    elif len(key) == 58  and key[:1] == '6':
        return 'wif_protected'
    elif key[:1] in ('K', 'L'):
        return 'wif_compressed'
    elif key[:1] == '5':
        return 'wif'
    else:
        raise ValueError("Unrecognised key format")

def ec_point(p):
    point = generator
    point *= int(p)
    return point


class Key:
    """
    Class to generate, import and convert public cryptograpic key pairs used for bitcoin.

    If no key is specified when creating class a cryptographically secure Private Key is
    generated using the os.urandom() function.
    """

    def __init__(self, import_key=None, addresstype=ADDRESSTYPE_BITCOIN, passphrase=''):
        self._public = None
        self._public_uncompressed = None
        self._addresstype = addresstype
        if not import_key:
            self._secret = random.SystemRandom().randint(0, secp256k1_n)
            return

        key_format = get_key_format(import_key)
        if key_format == "wif_protected":
            import_key = self._bip38_decrypt(import_key, passphrase)
            key_format = "wif"
        if key_format in ['public_uncompressed', 'public']:
            self._secret = None
            if key_format=='public_uncompressed':
                self._public = import_key
                self._x = import_key[2:66]
                self._y = import_key[66:130]
            else:
                self._public = import_key
                self._x = import_key[2:66]
                # Calculate y from x with y=x^3 + 7 function
                sign = import_key[:2] == '03'
                x = change_base(self._x,16,10)
                ys = (x**3+7) % secp256k1_p
                y = ecdsa.numbertheory.square_root_mod_prime(ys, secp256k1_p)
                if y & 1 != sign:
                    y = secp256k1_p - y
                self._y = change_base(y, 10, 16, 32)
        else:
            if key_format in ['hex', 'hex_compressed']:
                self._secret = change_base(import_key, 16, 10)
            elif key_format == 'decimal':
                self._secret = import_key
            elif key_format in ['bin', 'bin_compressed']:
                self._secret = change_base(import_key, 256, 10)
            elif key_format in ['wif', 'wif_compressed']:
                # Check and remove Checksum, prefix and postfix tags
                key = change_base(import_key, 58, 256)
                checksum = key[-4:]
                key = key[:-4]
                if checksum != hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]:
                    raise ValueError("Invalid checksum, not a valid WIF compressed key")
                if import_key[0] in "KL":
                    if key[-1:] != chr(1):
                        raise ValueError("Not a valid WIF private compressed key. key[-1:] != chr(1) failed")
                    key = key[:-1]
                if key[:1] != chr(128):
                    raise ValueError("Not a valid WIF private key. key[:1] != chr(128) failed")
                key = key[1:]
                self._secret = change_base(key, 256, 10)

    def __repr__(self):
        if self._secret:
            return str(self.private_dec())
        else:
            return self._public

    @staticmethod
    def _bip38_decrypt(encrypted_privkey, passphrase):
        """
        BIP0038 non-ec-multiply decryption. Returns WIF privkey.
        Based on code from https://github.com/nomorecoin/python-bip38-testing
        :param encrypted_privkey:
        :param passphrase:
        :return:
        """
        d = change_base(encrypted_privkey, 58, 256)[2:]
        flagbyte = d[0:1]
        d = d[1:]
        if flagbyte == '\xc0':
            compressed = False
        elif flagbyte == '\xe0':
            compressed = True
        else:
            raise Warning("Unrecognised password protected key format. Flagbyte incorrect.")
        addresshash = d[0:4]
        d = d[4:-4]
        key = scrypt.hash(passphrase,addresshash, 16384, 8, 8)
        derivedhalf1 = key[0:32]
        derivedhalf2 = key[32:64]
        encryptedhalf1 = d[0:16]
        encryptedhalf2 = d[16:32]
        aes = AES.new(derivedhalf2)
        decryptedhalf2 = aes.decrypt(encryptedhalf2)
        decryptedhalf1 = aes.decrypt(encryptedhalf1)
        priv = decryptedhalf1 + decryptedhalf2
        priv = binascii.unhexlify('%064x' % (long(binascii.hexlify(priv), 16) ^ long(binascii.hexlify(derivedhalf1), 16)))
        k = Key(priv)
        wif = k.wif(compressed=compressed)
        addr = k.address_uncompressed()
        if hashlib.sha256(hashlib.sha256(addr).digest()).digest()[0:4] != addresshash:
            print('Addresshash verification failed! Password is likely incorrect.')
        return wif

    def bip38_encrypt(self, passphrase, compressed=True):
        """
        BIP0038 non-ec-multiply encryption. Returns BIP0038 encrypted privkey.
        Based on code from https://github.com/nomorecoin/python-bip38-testing
        :param passphrase:
        :param compressed:
        :return:
        """
        if compressed:
            flagbyte = '\xe0'
        else:
            flagbyte = '\xc0'
        addr = self.address_uncompressed()
        privkey = self.private_hex()
        addresshash = hashlib.sha256(hashlib.sha256(addr).digest()).digest()[0:4]
        key = scrypt.hash(passphrase, addresshash, 16384, 8, 8)
        derivedhalf1 = key[0:32]
        derivedhalf2 = key[32:64]
        aes = AES.new(derivedhalf2)
        encryptedhalf1 = aes.encrypt(binascii.unhexlify('%0.32x' % (long(privkey[0:32], 16) ^
                                                                    long(binascii.hexlify(derivedhalf1[0:16]), 16))))
        encryptedhalf2 = aes.encrypt(binascii.unhexlify('%0.32x' % (long(privkey[32:64], 16) ^
                                                                    long(binascii.hexlify(derivedhalf1[16:32]), 16))))
        encrypted_privkey = ('\x01\x42' + flagbyte + addresshash + encryptedhalf1 + encryptedhalf2)
        encrypted_privkey += hashlib.sha256(hashlib.sha256(encrypted_privkey).digest()).digest()[:4]
        return change_base(encrypted_privkey, 256, 58)

    def private_dec(self):
        if not self._secret:
            return False
        return self._secret

    def private_hex(self):
        if not self._secret:
            return False
        return change_base(str(self._secret), 10, 16, 64)

    def private_byte(self):
        if not self._secret:
            return False
        return change_base(str(self._secret), 10, 256, 32)

    def wif(self, compressed=True):
        """
        Get Private Key in Wallet Import Format, steps:
        (1) Convert to Binary and add 0x80 hex
        (2) Calculate Double SHA256 and add as checksum to end of key

        :param compressed: Get compressed private key, which means private key will be used to generate compressed public keys.
        :return: Base58Check encoded Private Key WIF
        """
        if not self._secret:
            return False
        if self._addresstype == ADDRESSTYPE_TESTNET:
            version = PRIVATEKEY_WIF_TESTNET
        else:
            version = PRIVATEKEY_WIF
        key = version + change_base(str(self._secret), 10, 256, 32)
        if compressed:
            key += chr(1)
        key += hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]
        return change_base(key, 256, 58)

    def _create_public(self):
        if self._secret:
            point = ec_point(self._secret)
            self._x = change_base(int(point.x()), 10, 16, 64)
            self._y = change_base(int(point.y()), 10, 16, 64)
            if point.y() % 2: prefix = '03'
            else: prefix = '02'
            self._public = prefix + self._x
            self._public_uncompressed = '04' + self._x + self._y
        if hasattr(self, '_x') and hasattr(self, '_y') and self._x and self._y:
            if change_base(self._y, 16, 10) % 2: prefix = '03'
            else: prefix = '02'
            self._public = prefix + self._x
            self._public_uncompressed = '04' + self._x + self._y
        else:
            raise ValueError("Key error, no secret key or public key point found.")

    def public(self):
        if not self._public:
            self._create_public()
        return self._public

    def public_uncompressed(self):
        if not self._public_uncompressed:
            self._create_public()
        return self._public_uncompressed

    def public_point(self):
        if not self._public:
            self._create_public()
        x = self._x and int(change_base(self._x, 16, 10))
        y = self._y and int(change_base(self._y, 16, 10))
        return (x, y)

    def public_hex(self):
        if not self._public:
            self._create_public()
        return self._public

    def public_byte(self):
        if not self._public:
            self._create_public()
        return change_base(self._public, 16, 256, 32)

    def hash160(self):
        if not self._public:
            self._create_public()
        key = change_base(self._public, 16, 256)
        return hashlib.new('ripemd160', hashlib.sha256(key).digest()).hexdigest()

    def address(self, compressed=True):
        if not self._public or not self._public_uncompressed:
            self._create_public()
        if compressed:
            key = change_base(self._public, 16, 256)
        else:
            key = change_base(self._public_uncompressed, 16, 256)
        key = str(self._addresstype) + hashlib.new('ripemd160', hashlib.sha256(key).digest()).digest()
        checksum = hashlib.sha256(hashlib.sha256(key).digest()).digest()
        return change_base(key + checksum[:4], 256, 58)

    def address_uncompressed(self):
        return self.address(compressed=False)

    def info(self):
        if self._secret:
            print "SECRET EXPONENT"
            print " Private Key (hex)              ", change_base(self._secret, 256, 16)
            print " Private Key (long)             ", change_base(self._secret, 256, 10)
            print " Private Key (wif)              ", self.wif()
            print " Private Key (wif uncompressed) ", self.wif(compressed=False)
            print ""
        print "PUBLIC KEY"
        print " Public Key (hex)            ", self.public()
        print " Public Key (hex)            ", self.public_uncompressed()
        print " Address (b58)               ", self.address()
        print " Address uncompressed (b58)  ", self.address_uncompressed()
        point_x, point_y = self.public_point()
        print " Point x                     ", point_x
        print " Point y                     ", point_y


class HDKey:

    @staticmethod
    def from_seed(import_seed):
        seed = change_base(import_seed, 16, 256)
        I = hmac.new("Bitcoin seed", seed, hashlib.sha512).digest()
        key = I[:32]
        chain = I[32:]
        return HDKey(key=key, chain=chain)

    def __init__(self, import_key=None, key=None, chain=None, depth=0, parent_fingerprint=b'\0\0\0\0',
                 child_index = 0, isprivate=True, addresstype=ADDRESSTYPE_BITCOIN):
        if not (key and chain):
            if not import_key:
                # Generate new Master Key
                seedbits = random.SystemRandom().getrandbits(512)
                seed = change_base(str(seedbits), 10, 256, 64)
                key, chain = self._key_derivation(seed)
            elif len(import_key) == 64:
                key = import_key[:32]
                chain = import_key[32:]
            elif import_key[:4] in ['xprv', 'xpub', 'tprv', 'tpub']:
                if import_key[:1] == 't':
                    addresstype = ADDRESSTYPE_TESTNET
                bkey = change_base(import_key, 58, 256)
                if ord(bkey[45]):
                    isprivate = False
                    key = bkey[45:78]
                else:
                    key = bkey[46:78]
                depth = ord(bkey[4])
                parent_fingerprint = bkey[5:9]
                child_index = int(change_base(bkey[9:13], 256, 10))
                chain = bkey[13:45]
                # chk = bkey[78:82]
            else:
                raise ValueError("Key format not recognised")

        self._key = key
        self._chain = chain
        self._depth = depth
        self._parent_fingerprint = parent_fingerprint
        self._child_index = child_index
        self._isprivate = isprivate
        self._path = None
        self._public_key_object = None
        self._public_uncompressed = None
        if isprivate:
            self._public = None
            self._secret = change_base(key, 256, 10)
        else:
            self._public = change_base(key, 256, 16)
            self._secret = None
        self._addresstype = addresstype

    def __repr__(self):
        return self.extended_wif()

    def info(self):
        if self._isprivate:
            print "SECRET EXPONENT"
            print " Private Key (hex)           ", change_base(self._key, 256, 16)
            print " Private Key (long)          ", self._secret
            print " Private Key (wif)           ", self.private().wif()
            print ""
        print "PUBLIC KEY"
        print " Public Key (hex)            ", self.public()
        print " Address (b58)               ", self.public().address()
        print " Fingerprint (hex)           ", change_base(self.fingerprint(), 256, 16)
        point_x, point_y = self.public().public_point()
        print " Point x                     ", point_x
        print " Point y                     ", point_y
        print ""
        print "EXTENDED KEY INFO"
        print " Chain code (hex)            ", change_base(self.chain(), 256, 16)
        print " Child Index                 ", self.child_index()
        print " Parent Fingerprint (hex)    ", change_base(self.parent_fingerprint(), 256, 16)
        print " Depth                       ", self.depth()
        print " Extended Public Key (wif)   ", self.extended_wif_public()
        print " Extended Private Key (wif)  ", self.extended_wif(public=False)

    def _key_derivation(self, seed):
        chain = hasattr(self, '_chain') and self._chain or "Bitcoin seed"
        I = hmac.new(chain, seed, hashlib.sha512).digest()
        key = I[:32]
        chain = I[32:]
        return key, chain

    def fingerprint(self):
        return hashlib.new('ripemd160', hashlib.sha256(self.public().public_byte()).digest()).digest()[:4]

    def extended_wif(self, public=None, child_index=None):
        rkey = self._key
        if not self._isprivate and public == False:
            return ''
        if self._isprivate and not public:
            if self._addresstype == ADDRESSTYPE_TESTNET:
                raw = HDKEY_TPRV
            else:
                raw = HDKEY_XPRV
            typebyte = '\x00'
        else:
            if self._addresstype == ADDRESSTYPE_TESTNET:
                raw = HDKEY_TPUB
            else:
                raw = HDKEY_XPUB
            typebyte = ''
            if public:
                rkey = self.public().public_byte()
        if child_index:
            self._child_index = child_index
        raw += chr(self._depth) + self._parent_fingerprint + \
              struct.pack('>L', self._child_index) + \
              self._chain + typebyte + rkey
        chk = hashlib.sha256(hashlib.sha256(raw).digest()).digest()[:4]
        ret = raw+chk
        return change_base(ret, 256, 58, 111)

    def extended_wif_public(self):
        return self.extended_wif(public=True)

    def key(self):
        return self._key or ''

    def chain(self):
        return self._chain or ''

    def depth(self):
        return self._depth or 0

    def parent_fingerprint(self):
        return self._parent_fingerprint or b'\0\0\0\0'

    def child_index(self):
        return self._child_index or 0

    def isprivate(self):
        return self._isprivate

    def public(self):
        if not self._public_key_object:
            if self._public:
                self._public_key_object = Key(self._public, addresstype=self._addresstype)
            else:
                pub = Key(self._key).public()
                self._public_key_object = Key(pub, addresstype=self._addresstype)
        return self._public_key_object

    def public_uncompressed(self):
        if not self._public_uncompressed:
            pub = Key(self._key).public_uncompressed()
            return Key(pub, addresstype=self._addresstype)
        return self._public_uncompressed

    def private(self):
        if self._key:
            return Key(self._key, addresstype=self._addresstype)

    def subkey_for_path(self, path):
        key = self

        if path[0] == 'm': # Use private master key
            path = path[2:]
        # TODO: Write code to use public master key
        # if path[0] == 'M': # Use public master key
        #     path = path[2:]
        if path:
            levels = path.split("/")
            for level in levels:
                if not level:
                    raise ValueError("Could not parse path. Index is empty.")
                hardened = level[-1] in "'HhPp"
                if hardened:
                    level = level[:-1]
                index = int(level)
                if index<0:
                    raise ValueError("Could not parse path. Index must be a positive integer.")
                key = key.child_private(index=index, hardened=hardened)
        return key

    def child_private(self, index=0, hardened=False):
        if not self._isprivate:
            raise ValueError("Need a private key to create child private key")
        if hardened:
            index |= 0x80000000
            data = b'\0' + self._key + struct.pack('>L', index)
        else:
            data = self.public().public_byte() + struct.pack('>L', index)
        key, chain = self._key_derivation(data)

        key = change_base(key, 256, 10)
        if key > secp256k1_n:
            raise ValueError("Key cannot be greater then secp256k1_n. Try another index number.")
        newkey = (key + self._secret) % secp256k1_n
        if newkey == 0:
            raise ValueError("Key cannot be zero. Try another index number.")
        newkey = change_base(newkey, 10, 256, 32)

        return HDKey(key=newkey, chain=chain, depth=self._depth+1, parent_fingerprint=self.fingerprint(),
                     child_index=index)

    def child_public(self, index=0):
        if index > 0x80000000:
            raise ValueError("Cannot derive hardened key from public private key. Index must be less then 0x80000000")
        data = self.public().public_byte() + struct.pack('>L', index)
        key, chain = self._key_derivation(data)
        key = change_base(key, 256, 10)
        if key > secp256k1_n:
            raise ValueError("Key cannot be greater then secp256k1_n. Try another index number.")

        x, y = self.public().public_point()
        Ki = ec_point(key) + ecdsa.ellipticcurve.Point(curve, x, y, secp256k1_n)

        if change_base(Ki.y(), 16, 10) % 2: prefix = '03'
        else: prefix = '02'
        xhex = change_base(Ki.x(), 10, 16, 64)
        secret = change_base(prefix + xhex, 16, 256)
        return HDKey(key=secret, chain=chain, depth=self._depth+1, parent_fingerprint=self.fingerprint(),
                     child_index=index, isprivate=False)



if __name__ == '__main__':
    # Import public key
    # K = Key('025c0de3b9c8ab18dd04e3511243ec2952002dbfadc864b9628910169d9b9b00ec')
    # K.info()

    # Import private key
    # k = Key('5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR')
    # k.info()
    # print k.bip38_encrypt('TestingOneTwoThree')
    # print "6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg"
    # print len("6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg")

    ki = Key('6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg', passphrase='TestingOneTwoThree')
    print ki.info()


    # Generate random HD Key on testnet
    # hdk = HDKey(addresstype = ADDRESSTYPE_TESTNET)
    # hdk.info()
