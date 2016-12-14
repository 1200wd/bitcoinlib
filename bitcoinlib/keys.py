# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Public key cryptography and Hierarchical Deterministic Key Management
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

import binascii
import hashlib
import hmac
import numbers
import random
import struct
import sys

import ecdsa
import scrypt
from Crypto.Cipher import AES

from bitcoinlib.config.secp256k1 import secp256k1_generator as generator, secp256k1_curve as curve, \
    secp256k1_p, secp256k1_n
from bitcoinlib.encoding import change_base
from bitcoinlib.config.networks import *


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
    if isinstance(key, numbers.Number):
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
    elif len(key) == 66 and keytype != 'public':
        return 'hex_compressed'
    elif len(key) == 58 and key[:1] == '6':
        return 'wif_protected'
    elif key[:1] in ['K', 'L', 'c']:
        return 'wif_compressed'
    elif key[:1] in ['5', '9']:
        return 'wif'
    else:
        raise ValueError("Unrecognised key format")


def ec_point(p):
    """
    Method for eliptic curve multiplication

    :param p: A point on the eliptic curve
    :return: Point multiplied by generator G
    """
    point = generator
    point *= int(p)
    return point


class Key:
    """
    Class to generate, import and convert public cryptograpic key pairs used for bitcoin.

    If no key is specified when creating class a cryptographically secure Private Key is
    generated using the os.urandom() function.
    """

    def __init__(self, import_key=None, network=NETWORK_BITCOIN, compressed=True, passphrase=''):
        """
        Initialize a Key object

        :param import_key: If specified import given private or public key.
        If not specified a new private key is generated.
        :param network: Bitcoin normal or testnet address
        :param passphrase: Optional passphrase if imported key is password protected
        :return:
        """
        self._public = None
        self._public_uncompressed = None
        self._compressed = compressed
        self._network = network
        if not import_key:
            self._secret = random.SystemRandom().randint(0, secp256k1_n)
            return

        key_format = get_key_format(import_key)

        if key_format == "wif_protected":
            import_key, key_format = self._bip38_decrypt(import_key, passphrase)

        if key_format in ['public_uncompressed', 'public']:
            self._secret = None
            if key_format == 'public_uncompressed':
                self._public = import_key
                self._x = import_key[2:66]
                self._y = import_key[66:130]
                self._compressed = False
            else:
                self._public = import_key
                self._x = import_key[2:66]
                self._compressed = True
                # Calculate y from x with y=x^3 + 7 function
                sign = import_key[:2] == '03'
                x = change_base(self._x, 16, 10)
                ys = (x**3+7) % secp256k1_p
                y = ecdsa.numbertheory.square_root_mod_prime(ys, secp256k1_p)
                if y & 1 != sign:
                    y = secp256k1_p - y
                self._y = change_base(y, 10, 16, 32)
        else:
            # Overrule method compressed input
            if key_format in ['bin_compressed', 'hex_compressed', 'wif_compressed']:
                self._compressed = True
            elif key_format == 'wif':
                self._compressed = False

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
                    raise ValueError("Invalid checksum, not a valid WIF key")
                if key[0:1] in network_get_values('wif'):
                    if key[-1:] == b'\x01':
                        self._compressed = True
                        key = key[:-1]
                    else:
                        self._compressed = False
                    network = get_network_by_value('wif', key[0:1])
                    if len(network) == 1:
                        self._network = network[0]
                    else:
                        raise ValueError("Unrecognised WIF private key, version byte unknown. Found: %s" % network)
                else:
                    raise ValueError("Unrecognised WIF private key, prefix unknown")
                key = key[1:]
                self._secret = change_base(key, 256, 10)

    def __repr__(self):
        """
        :return: Decimal private key if available, otherwise a public key
        """
        if self._secret:
            return str(self.private_dec())
        else:
            return self._public

    @staticmethod
    def _bip38_decrypt(encrypted_privkey, passphrase):
        """
        BIP0038 non-ec-multiply decryption. Returns WIF privkey.
        Based on code from https://github.com/nomorecoin/python-bip38-testing
        This method is called by Key class init function when importing BIP0038 key.

        :param encrypted_privkey: Encrypted Private Key using WIF protected key format
        :param passphrase: Required passphrase for decryption
        :return: Private Key WIF
        """
        d = change_base(encrypted_privkey, 58, 256)[2:]
        flagbyte = d[0:1]
        d = d[1:]
        if flagbyte == b'\xc0':
            compressed = False
        elif flagbyte == b'\xe0':
            compressed = True
        else:
            raise Warning("Unrecognised password protected key format. Flagbyte incorrect.")
        addresshash = d[0:4]
        d = d[4:-4]
        key = scrypt.hash(passphrase, addresshash, 16384, 8, 8)
        derivedhalf1 = key[0:32]
        derivedhalf2 = key[32:64]
        encryptedhalf1 = d[0:16]
        encryptedhalf2 = d[16:32]
        aes = AES.new(derivedhalf2)
        decryptedhalf2 = aes.decrypt(encryptedhalf2)
        decryptedhalf1 = aes.decrypt(encryptedhalf1)
        priv = decryptedhalf1 + decryptedhalf2
        priv = binascii.unhexlify('%064x' % (int(binascii.hexlify(priv), 16) ^ int(binascii.hexlify(derivedhalf1), 16)))
        if compressed:
            priv = b'\0' + priv
            key_format = 'wif_compressed'
        else:
            key_format = 'wif'
        k = Key(priv, compressed=compressed)
        wif = k.wif()
        addr = k.address()
        if isinstance(addr, str) and sys.version_info > (3,):
            addr = addr.encode('utf-8')
        if hashlib.sha256(hashlib.sha256(addr).digest()).digest()[0:4] != addresshash:
            print('Addresshash verification failed! Password is likely incorrect.')
        return wif, key_format

    def bip38_encrypt(self, passphrase):
        """
        BIP0038 non-ec-multiply encryption. Returns BIP0038 encrypted privkey.
        Based on code from https://github.com/nomorecoin/python-bip38-testing

        :param passphrase: Required passphrase for encryption
        :return: BIP38 passphrase encrypted private key
        """
        if self._compressed:
            flagbyte = b'\xe0'
            addr = self.address()
        else:
            flagbyte = b'\xc0'
            addr = self.address_uncompressed()

        privkey = self.private_hex()
        if isinstance(addr, str) and sys.version_info > (3,):
            addr = addr.encode('utf-8')
        addresshash = hashlib.sha256(hashlib.sha256(addr).digest()).digest()[0:4]
        key = scrypt.hash(passphrase, addresshash, 16384, 8, 8)
        derivedhalf1 = key[0:32]
        derivedhalf2 = key[32:64]
        aes = AES.new(derivedhalf2)
        encryptedhalf1 = aes.encrypt(binascii.unhexlify('%0.32x' % (int(privkey[0:32], 16) ^
                                                                    int(binascii.hexlify(derivedhalf1[0:16]), 16))))
        encryptedhalf2 = aes.encrypt(binascii.unhexlify('%0.32x' % (int(privkey[32:64], 16) ^
                                                                    int(binascii.hexlify(derivedhalf1[16:32]), 16))))
        encrypted_privkey = b'\x01\x42' + flagbyte + addresshash + encryptedhalf1 + encryptedhalf2
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

    def wif(self):
        """
        Get Private Key in Wallet Import Format, steps:
        (1) Convert to Binary and add 0x80 hex
        (2) Calculate Double SHA256 and add as checksum to end of key

        :return: Base58Check encoded Private Key WIF
        """
        if not self._secret:
            return False
        version = NETWORKS[self._network]['wif']
        key = version + change_base(str(self._secret), 10, 256, 32)
        if self._compressed:
            key += b'\1'
        key += hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]
        return change_base(key, 256, 58)

    def _create_public(self):
        """
        Create public key point and hex repressentation from private key.

        :return:
        """
        if self._secret:
            point = ec_point(self._secret)
            self._x = change_base(int(point.x()), 10, 16, 64)
            self._y = change_base(int(point.y()), 10, 16, 64)
            if point.y() % 2:
                prefix = '03'
            else:
                prefix = '02'
            self._public = prefix + self._x
            self._public_uncompressed = '04' + self._x + self._y
        if hasattr(self, '_x') and hasattr(self, '_y') and self._x and self._y:
            if change_base(self._y, 16, 10) % 2:
                prefix = '03'
            else:
                prefix = '02'
            self._public = prefix + self._x
            self._public_uncompressed = '04' + self._x + self._y
        else:
            raise ValueError("Key error, no secret key or public key point found.")

    def public(self, compressed=None):
        if not self._public or not self._public_uncompressed:
            self._create_public()
        if (self._compressed and compressed is None) or compressed:
            return self._public
        else:
            return self._public_uncompressed

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
        # if sys.version_info > (3,):
        #     key = key.encode('utf-8')
        return hashlib.new('ripemd160', hashlib.sha256(key).digest()).hexdigest()

    def address(self, compressed=None):
        if not self._public or not self._public_uncompressed:
            self._create_public()
        if (self._compressed and compressed is None) or compressed:
            key = change_base(self._public, 16, 256)
        else:
            key = change_base(self._public_uncompressed, 16, 256)
        versionbyte = NETWORKS[self._network]['address']
        key = versionbyte + hashlib.new('ripemd160', hashlib.sha256(key).digest()).digest()
        checksum = hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]
        return change_base(key + checksum, 256, 58)

    def address_uncompressed(self):
        return self.address(compressed=False)

    def compressed(self):
        return self._compressed

    def info(self):
        if self._secret:
            print("SECRET EXPONENT")
            print(" Private Key (hex)              %s" % change_base(self._secret, 256, 16))
            print(" Private Key (long)             %s" % change_base(self._secret, 256, 10))
            print(" Private Key (wif)              %s" % self.wif())
        else:
            print("PUBLIC KEY ONLY, NO SECRET EXPONENT")
        print("")
        print(" Compressed                  %s" % self.compressed())
        print("PUBLIC KEY")
        print(" Public Key (hex)            %s" % self.public())
        print(" Public Key uncompr. (hex)   %s" % self.public_uncompressed())
        print(" Address (b58)               %s" % self.address())
        print(" Address uncompressed (b58)  %s" % self.address_uncompressed())
        point_x, point_y = self.public_point()
        print(" Point x                     %s" % point_x)
        print(" Point y                     %s" % point_y)
        print("\n")


class HDKey:
    """
    Class for Hierarchical Deterministic keys as defined in BIP0032

    Besides a private or public key a HD Key has a chain code, allowing to create
    a structure of related keys.

    The structure and key-path are defined in BIP0043 and BIP0044.
    """

    @staticmethod
    def from_seed(import_seed):
        """
        Used by class init function, import key from seed

        :param import_seed: Hex representation of private key seed
        :return: HDKey class object
        """
        seed = change_base(import_seed, 16, 256)
        I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
        key = I[:32]
        chain = I[32:]
        return HDKey(key=key, chain=chain)

    def __init__(self, import_key=None, key=None, chain=None, depth=0, parent_fingerprint=b'\0\0\0\0',
                 child_index=0, isprivate=True, network=NETWORK_BITCOIN, addresstype=''):
        """
        Hierarchical Deterministic Key class init function.
        If no import_key is specified a key will be generated with system cryptographically random function.

        :param import_key: HD Key in WIF format to import
        :param key: Private or public key
        :param chain: A chain code
        :param depth: Integer of level of depth in path (BIP0043/BIP0044)
        :param parent_fingerprint: 4-byte fingerprint of parent
        :param child_index: Index number of child as integer
        :param isprivate: True for private, False for public key
        :param network: Bitcoin normal or test network. Derived from import_key if possible.
        :param addresstype: Pay-to-script, etc.
        :return:
        """
        self._network = network
        if not (key and chain):
            if not import_key:
                # Generate new Master Key
                seedbits = random.SystemRandom().getrandbits(512)
                seed = change_base(str(seedbits), 10, 256, 64)
                key, chain = self._key_derivation(seed)
            elif len(import_key) == 64:
                key = import_key[:32]
                chain = import_key[32:]
            elif import_key[:4] in ['xprv', 'xpub', 'tprv', 'tpub', 'Ltpv', 'Ltpb']:
                if import_key[:1] == 't':
                    self._network = NETWORK_BITCOIN_TESTNET
                # Derive key, chain, depth, child_index and fingerprint part from extended key WIF
                bkey = change_base(import_key, 58, 256)
                if ord(bkey[45:46]):
                    isprivate = False
                    key = bkey[45:78]
                else:
                    key = bkey[46:78]
                depth = ord(bkey[4:5])
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
            print("SECRET EXPONENT")
            print(" Private Key (hex)           %s" % change_base(self._key, 256, 16))
            print(" Private Key (long)          %s" % self._secret)
            print(" Private Key (wif)           %s" % self.private().wif())
            print("")
        print("PUBLIC KEY")
        print(" Public Key (hex)            %s" % self.public())
        print(" Address (b58)               %s" % self.public().address())
        print(" Fingerprint (hex)           %s" % change_base(self.fingerprint(), 256, 16))
        point_x, point_y = self.public().public_point()
        print(" Point x                     %s" % point_x)
        print(" Point y                     %s" % point_y)
        print("")
        print("EXTENDED KEY INFO")
        print(" Chain code (hex)            %s" % change_base(self.chain(), 256, 16))
        print(" Child Index                 %s" % self.child_index())
        print(" Parent Fingerprint (hex)    %s" % change_base(self.parent_fingerprint(), 256, 16))
        print(" Depth                       %s" % self.depth())
        print(" Extended Public Key (wif)   %s" % self.extended_wif_public())
        print(" Extended Private Key (wif)  %s" % self.extended_wif(public=False))
        print("\n")

    def _key_derivation(self, seed):
        chain = hasattr(self, '_chain') and self._chain or b"Bitcoin seed"
        I = hmac.new(chain, seed, hashlib.sha512).digest()
        key = I[:32]
        chain = I[32:]
        return key, chain

    def fingerprint(self):
        return hashlib.new('ripemd160', hashlib.sha256(self.public().public_byte()).digest()).digest()[:4]

    def extended_wif(self, public=None, child_index=None):
        rkey = self._key
        if not self._isprivate and public is False:
            return ''
        if self._isprivate and not public:
            raw = NETWORKS[self._network]['hdkey_private']
            typebyte = b'\x00'
        else:
            raw = NETWORKS[self._network]['hdkey_public']
            typebyte = b''
            if public:
                rkey = self.public().public_byte()
        if child_index:
            self._child_index = child_index
        raw += change_base(self._depth, 10, 256, 1) + self._parent_fingerprint + \
            struct.pack('>L', self._child_index) + self._chain + typebyte + rkey
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
                self._public_key_object = Key(self._public, network=self._network)
            else:
                pub = Key(self._key).public()
                self._public_key_object = Key(pub, network=self._network)
        return self._public_key_object

    def public_uncompressed(self):
        if not self._public_uncompressed:
            pub = Key(self._key).public_uncompressed()
            return Key(pub, network=self._network)
        return self._public_uncompressed

    def private(self):
        if self._key:
            return Key(self._key, network=self._network)

    def subkey_for_path(self, path):
        """
        Determine subkey for HD Key for given path.
        Path format: m / purpose' / coin_type' / account' / change / address_index
        Example: m/44'/0'/0'/0/2
        See BIP0044 bitcoin proposal for more explanation.

        :param path: BIP0044 key path
        :return: HD Key class object of subkey
        """
        key = self

        first_public = False
        if path[0] == 'm':  # Use Private master key
            path = path[2:]
        # TODO: Write code to use public master key
        elif path[0] == 'M':  # Use Public master key
            path = path[2:]
            first_public = True
        if path:
            levels = path.split("/")
            for level in levels:
                if not level:
                    raise ValueError("Could not parse path. Index is empty.")
                hardened = level[-1] in "'HhPp"
                if hardened:
                    level = level[:-1]
                index = int(level)
                if index < 0:
                    raise ValueError("Could not parse path. Index must be a positive integer.")
                if first_public or not key.isprivate():
                    key = key.child_public(index=index)  # TODO hardened=hardened key?
                    first_public = False
                else:
                    key = key.child_private(index=index, hardened=hardened)
        return key

    def child_private(self, index=0, hardened=False):
        """
        Use Child Key Derivation (CDK) to derive child private key of current HD Key object.

        :param index: Key index number
        :param hardened: Specify if key must be hardened (True) or normal (False)
        :return: HD Key class object
        """
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
        """
        Use Child Key Derivation to derive child public key of current HD Key object.

        :param index: Key index number
        :return: HD Key class object
        """
        if index > 0x80000000:
            raise ValueError("Cannot derive hardened key from public private key. Index must be less then 0x80000000")
        data = self.public().public_byte() + struct.pack('>L', index)
        key, chain = self._key_derivation(data)
        key = change_base(key, 256, 10)
        if key > secp256k1_n:
            raise ValueError("Key cannot be greater then secp256k1_n. Try another index number.")

        x, y = self.public().public_point()
        Ki = ec_point(key) + ecdsa.ellipticcurve.Point(curve, x, y, secp256k1_n)

        if change_base(Ki.y(), 16, 10) % 2:
            prefix = '03'
        else:
            prefix = '02'
        xhex = change_base(Ki.x(), 10, 16, 64)
        secret = change_base(prefix + xhex, 16, 256)
        return HDKey(key=secret, chain=chain, depth=self._depth+1, parent_fingerprint=self.fingerprint(),
                     child_index=index, isprivate=False)


if __name__ == '__main__':
    #
    # KEYS EXAMPLES
    #
    
    print("\n=== Import public key ===")
    K = Key('025c0de3b9c8ab18dd04e3511243ec2952002dbfadc864b9628910169d9b9b00ec')
    K.info()

    print("\n=== Import Private Key ===")
    k = Key('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX')
    print("Private key     %s" % k.wif())
    print("Private key hex %s " % k.private_hex())
    print("Compressed      %s\n" % k.compressed())

    print("\n=== Import Testnet Key ===")
    k = Key('92Pg46rUhgTT7romnV7iGW6W1gbGdeezqdbJCzShkCsYNzyyNcc')
    k.info()

    print("\n==== Import uncompressed Private Key and Encrypt with BIP38 ===")
    k = Key('5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR')
    print("Private key     %s" % k.wif())
    print("Encrypted pk    %s " % k.bip38_encrypt('TestingOneTwoThree'))
    print("Is Compressed   %s\n" % k.compressed())

    print("\n==== Import and Decrypt BIP38 Key ===")
    k = Key('6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg', passphrase='TestingOneTwoThree')
    print("Private key     %s" % k.wif())
    print("Is Compressed   %s\n" % k.compressed())

    print("\n==== Generate random HD Key on testnet ===")
    hdk = HDKey(network=NETWORK_BITCOIN_TESTNET)
    print("Random BIP32 HD Key on testnet %s" % hdk.extended_wif())

    print("\n==== Import HD Key from seed ===")
    k = HDKey.from_seed('000102030405060708090a0b0c0d0e0f')
    print("HD Key WIF for seed 000102030405060708090a0b0c0d0e0f:  %s" % k.extended_wif())

    print("\n==== Generate random Litecoin key ===")
    lk = HDKey(network=NETWORK_LITECOIN)
    lk.info()

    print("\n==== Derive path with Child Key derivation ===")
    print("Derive path path 'm/0H/1':")
    print("  Private Extended WIF: %s" % k.subkey_for_path('m/0H/1').extended_wif())
    print("  Public Extended WIF : %s\n" % k.subkey_for_path('m/0H/1').extended_wif_public())

    print("\n==== Test Child Key Derivation ===")
    print("Use the 2 different methods to derive child keys. One through derivation from public parent, "
          "and one thought private parent. They should be the same.")
    K = HDKey('xpub6ASuArnXKPbfEVRpCesNx4P939HDXENHkksgxsVG1yNp9958A33qYoPiTN9QrJmWFa2jNLdK84bWmyqTSPGtApP8P'
              '7nHUYwxHPhqmzUyeFG')
    k = HDKey('xprv9wTYmMFdV23N21MM6dLNavSQV7Sj7meSPXx6AV5eTdqqGLjycVjb115Ec5LgRAXscPZgy5G4jQ9csyyZLN3PZLxoM'
              '1h3BoPuEJzsgeypdKj')

    index = 1000
    pub_with_pubparent = K.child_public(index).public().address()
    pub_with_privparent = k.child_private(index).public().address()
    if pub_with_privparent != pub_with_pubparent:
        print("Error index %4d: pub-child %s, priv-child %s" % (index, pub_with_privparent, pub_with_pubparent))
    else:
        print("Child Key Derivation for key %d worked!" % index)
        print("%s == %s" % (pub_with_pubparent, pub_with_privparent))
