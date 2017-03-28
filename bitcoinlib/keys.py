# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Public key cryptography and Hierarchical Deterministic Key Management
#    © 2017 March - 1200 Web Development <http://1200wd.com/>
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

from bitcoinlib.main import *
from bitcoinlib.networks import Network, DEFAULT_NETWORK, network_by_value, network_values_for
from bitcoinlib.config.secp256k1 import secp256k1_generator as generator, secp256k1_curve as curve, \
    secp256k1_p, secp256k1_n
from bitcoinlib.encoding import change_base, to_bytes, to_hexstring, EncodingError

_logger = logging.getLogger(__name__)


class BKeyError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def check_network_and_key(key, network):
    kf = get_key_format(key)
    if kf['networks']:
        if network is not None and network not in kf['networks']:
            raise KeyError("Specified key %s is from different network then specified: %s" % (kf['networks'], network))
        elif network is None and len(kf['networks']) == 1:
            return kf['networks'][0]
        elif network is None and len(kf['networks']) > 1:
            raise KeyError("Could not determine network of specified key, multiple networks found: %s" % kf['networks'])
    if network is None:
        return DEFAULT_NETWORK
    else:
        return network


def get_key_format(key, key_type=None):
    """
    Determins the type and format of a public or private key by length and prefix.
    This method does not validate if a key is valid.

    :param key: Any private or public key
    :param keytype: 'private' or 'public', is most cases not required as methods takes best guess
    :return: key_format of key as string
    """
    if not key:
        raise BKeyError("Key empty, please specify a valid key")
    key_format = ""
    networks = None

    if isinstance(key, (bytes, bytearray)) and len(key) in [64, 66, 128, 130]:
        key = to_hexstring(key)

    if key_type not in [None, 'private', 'public']:
        raise BKeyError("Keytype must be 'private' or 'public")
    elif isinstance(key, numbers.Number):
        key_format = 'decimal'
        key_type = 'private'
    elif isinstance(key, (bytes, bytearray)) and len(key) == 33 and key[-1:] in [b'\2', b'\3']:
        key_format = 'bin_compressed'
        key_type = 'public'
    elif isinstance(key, (bytes, bytearray)) and (len(key) == 33 and key[-1:] == b'\4'):
        key_format = 'bin'
        key_type = 'public'
    elif isinstance(key, (bytes, bytearray)) and len(key) == 33 and key[-1:] == b'\1':
        key_format = 'bin_compressed'
        key_type = 'private'
    elif isinstance(key, (bytes, bytearray)) and len(key) == 32:
        key_format = 'bin'
        key_type = 'private'
    elif len(key) == 130 and key[:2] == '04' and key_type != 'private':
        key_format = 'public_uncompressed'
        key_type = 'public'
    elif len(key) == 128:
        key_format = 'hex'
        if key_type != 'public':
            key_type = 'private'
    elif len(key) == 66 and key[:2] in ['02', '03'] and key_type != 'private':
        key_format = 'public'
        key_type = 'public'
    elif len(key) == 64:
        key_format = 'hex'
        if key_type != 'public':
            key_type = 'private'
    elif len(key) == 66 and key_type != 'public' and key[-2:] in ['01']:
        key_format = 'hex_compressed'
        key_type = 'private'
    elif len(key) == 58 and key[:2] == '6P':
        key_format = 'wif_protected'
        key_type = 'private'
    else:
        try:
            key_hex = change_base(key, 58, 16)
            networks = network_by_value('prefix_wif', key_hex[:2])
            if networks:
                if key_hex[-10:-8] == '01':
                    key_format = 'wif_compressed'
                else:
                    key_format = 'wif'
                key_type = 'private'
            else:
                networks = network_by_value('prefix_hdkey_private', key_hex[:8])
                if networks:
                    key_format = 'hdkey_private'
                    key_type = 'private'
                else:
                    networks = network_by_value('prefix_hdkey_public', key_hex[:8])
                    if networks:
                        key_format = 'hdkey_public'
                        key_type = 'public'
        except (TypeError, EncodingError):
            pass
    if not key_format:
        try:
            int(key)
            if 70 < len(key) < 78:
                key_format = 'decimal'
                key_type = 'private'
        except (TypeError, ValueError):
            pass
    if not key_format:
        raise BKeyError("Key: %s. Unrecognised key format" % key)
    else:
        return {
            "format": key_format,
            "networks": networks,
            "type": key_type
        }


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

    def __init__(self, import_key=None, network=None, compressed=True, passphrase=''):
        """
        Initialize a Key object

        :param import_key: If specified import given private or public key.
        If not specified a new private key is generated.
        :param network: Bitcoin, testnet, litecoin or other network
        :param passphrase: Optional passphrase if imported key is password protected
        :return:
        """
        self.public_hex = None
        self.public_uncompressed_hex = None
        self.public_byte = None
        self.public_uncompressed_byte = None
        self.private_byte = None
        self.private_hex = None
        self._x = None
        self._y = None
        self.secret = None
        self.compressed = compressed
        if not import_key:
            import_key = random.SystemRandom().randint(0, secp256k1_n)
        kf = get_key_format(import_key)
        self.key_format = kf["format"]
        network = check_network_and_key(import_key, network)
        self.network = Network(network)
        if kf['type'] == 'private':
            self.isprivate = True
        elif kf['type'] == 'public':
            self.isprivate = False
        else:
            raise KeyError("Could not determine if key is private or public")

        if self.key_format == "wif_protected":
            # TODO: return key as byte to make more efficient
            import_key, self.key_format = self._bip38_decrypt(import_key, passphrase)

        if self.key_format in ['public_uncompressed', 'public']:
            self.secret = None
            if self.key_format == 'public_uncompressed':
                self.public_uncompressed_hex = import_key
                self._x = import_key[2:66]
                self._y = import_key[66:130]
                self.compressed = False
                if int(self._y, 16) % 2:
                    prefix = '03'
                else:
                    prefix = '02'
                self.public_hex = prefix + self._x
            else:
                self.public_hex = import_key
                self._x = import_key[2:66]
                self.compressed = True
                # Calculate y from x with y=x^3 + 7 function
                sign = import_key[:2] == '03'
                x = int(self._x, 16)
                ys = (x**3+7) % secp256k1_p
                y = ecdsa.numbertheory.square_root_mod_prime(ys, secp256k1_p)
                if y & 1 != sign:
                    y = secp256k1_p - y
                self._y = change_base(y, 10, 16, 32)
                self.public_uncompressed_hex = '04' + self._x + self._y
            self.public_byte = binascii.unhexlify(self.public_hex)
            self.public_uncompressed_byte = binascii.unhexlify(self.public_uncompressed_hex)
        elif self.isprivate and self.key_format == 'decimal':
            self.secret = import_key
            self.private_hex = change_base(import_key, 10, 16, 64)
            self.private_byte = binascii.unhexlify(self.private_hex)
        elif self.isprivate:
            if self.key_format == 'hex':
                key_hex = import_key
                key_byte = binascii.unhexlify(key_hex)
                # self.compressed = False
            elif self.key_format == 'hex_compressed':
                key_hex = import_key[:-2]
                key_byte = binascii.unhexlify(key_hex)
                self.compressed = True
            elif self.key_format == 'bin':
                key_byte = import_key
                key_hex = to_hexstring(key_byte)
                # self.compressed = False
            elif self.key_format == 'bin_compressed':
                key_byte = import_key[:-1]
                key_hex = to_hexstring(key_byte)
                self.compressed = True
            elif self.key_format in ['wif', 'wif_compressed']:
                # Check and remove Checksum, prefix and postfix tags
                key = change_base(import_key, 58, 256)
                checksum = key[-4:]
                key = key[:-4]
                if checksum != hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]:
                    raise BKeyError("Invalid checksum, not a valid WIF key")
                found_networks = network_by_value('prefix_wif', key[0:1])
                if not len(found_networks):
                    raise BKeyError("Unrecognised WIF private key, version byte unknown. Versionbyte: %s" % key[0:1])
                if self.network.network_name not in found_networks:
                    if len(found_networks) > 1:
                        raise BKeyError("More then one network found with this versionbyte, please specify network. "
                                        "Networks found: %s" % found_networks)
                    else:
                        _logger.warning("Current network %s is different then the one found in key: %s" %
                                        (network, found_networks[0]))
                        self.network = Network(found_networks[0])
                if key[-1:] == b'\x01':
                    self.compressed = True
                    key = key[:-1]
                else:
                    self.compressed = False
                key_byte = key[1:]
                key_hex = to_hexstring(key_byte)
            else:
                raise KeyError("Unknown key format %s" % self.key_format)

            if not (key_byte or key_hex):
                raise KeyError("Cannot format key in hex or byte format")
            self.private_hex = key_hex
            self.secret = int(key_hex, 16)
        else:
            raise KeyError("Cannot import key. Public key format unknown")

        if self.isprivate and not (self.public_byte or self.public_hex):
            if not self.isprivate:
                raise KeyError("Private key has no known secret number")
            point = ec_point(self.secret)
            self._x = change_base(int(point.x()), 10, 16, 64)
            self._y = change_base(int(point.y()), 10, 16, 64)
            if point.y() % 2:
                prefix = '03'
            else:
                prefix = '02'
            self.public_hex = prefix + self._x
            self.public_uncompressed_hex = '04' + self._x + self._y
            self.public_byte = binascii.unhexlify(self.public_hex)
            self.public_uncompressed_byte = binascii.unhexlify(self.public_uncompressed_hex)

    def __repr__(self):
        """
        :return: Decimal private key if available, otherwise a public key
        """
        if self.secret:
            return self.secret
        else:
            return self.public_hex

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
        # TODO: Also check first 2 bytes
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
            # FIXME: This works but does probably not follow the BIP38 standards (was before: priv = b'\0' + priv)
            priv += b'\1'
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
        if self.compressed:
            flagbyte = b'\xe0'
            addr = self.address()
        else:
            flagbyte = b'\xc0'
            addr = self.address_uncompressed()

        privkey = self.private_hex
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

    # def private_dec(self):
    #     if not self.secret:
    #         return False
    #     return self.secret
    #
    # def private_hex(self):
    #     if not self.secret:
    #         return False
    #     return change_base(self.secret, 10, 16, 64)
    #
    # def private_byte(self):
    #     if not self.secret:
    #         return False
    #     return change_base(self.secret, 10, 256, 32)

    def wif(self):
        """
        Get Private Key in Wallet Import Format, steps:
        (1) Convert to Binary and add 0x80 hex
        (2) Calculate Double SHA256 and add as checksum to end of key

        :return: Base58Check encoded Private Key WIF
        """
        if not self.secret:
            raise KeyError("WIF format not supported for public key")
        version = self.network.prefix_wif
        key = version + change_base(self.secret, 10, 256, 32)
        if self.compressed:
            key += b'\1'
        key += hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]
        return change_base(key, 256, 58)

    # def _create_public(self):
    #     """
    #     Create public key point and hex repressentation from private key.
    #
    #     :return:
    #     """
    #     if self.secret:
    #         point = ec_point(self.secret)
    #         self._x = change_base(int(point.x()), 10, 16, 64)
    #         self._y = change_base(int(point.y()), 10, 16, 64)
    #         if point.y() % 2:
    #             prefix = '03'
    #         else:
    #             prefix = '02'
    #         self.public_hex = prefix + self._x
    #         self.public_uncompressed_hex = '04' + self._x + self._y
    #     if hasattr(self, '_x') and hasattr(self, '_y') and self._x and self._y:
    #         if int(self._y, 16) % 2:
    #             prefix = '03'
    #         else:
    #             prefix = '02'
    #         self.public_hex = prefix + self._x
    #         self.public_uncompressed_hex = '04' + self._x + self._y
    #     else:
    #         raise BKeyError("Key error, no secret key or public key point found.")

    def public(self, return_compressed=None):
        # if not self.public_hex or not self.public_uncompressed_hex:
        #     self._create_public()
        if (self.compressed and return_compressed is None) or return_compressed:
            return self.public_hex
        else:
            return self.public_uncompressed_hex

    # def public_uncompressed(self):
    #     if not self.public_uncompressed_hex:
    #         self._create_public()
    #     return self.public_uncompressed_hex

    def public_point(self):
        # if not self.public_hex or not self.public_uncompressed_hex:
        #     self._create_public()
        x = self._x and int(self._x, 16)
        y = self._y and int(self._y, 16)
        return (x, y)

    # def public_byte(self):
    #     if not self.public_hex or not self.public_uncompressed_hex:
    #         self._create_public()
    #     return change_base(self.public_hex if self.compressed else self.public_uncompressed_hex, 16, 256, 32)

    def hash160(self):
        # pb = self.public_byte()
        if self.compressed:
            pb = self.public_byte
        else:
            pb = self.public_uncompressed_byte
        return hashlib.new('ripemd160', hashlib.sha256(pb).digest()).hexdigest()

    def address(self, compressed=None):
        # if not self.public_hex or not self.public_uncompressed_hex:
        #     self._create_public()
        if (self.compressed and compressed is None) or compressed:
            key = self.public_byte
        else:
            key = change_base(self.public_uncompressed_hex, 16, 256)
        versionbyte = self.network.prefix_address
        key = versionbyte + hashlib.new('ripemd160', hashlib.sha256(key).digest()).digest()
        checksum = hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]
        return change_base(key + checksum, 256, 58)

    def address_uncompressed(self):
        return self.address(compressed=False)

    def info(self):
        if self.secret:
            print("SECRET EXPONENT")
            print(" Private Key (hex)              %s" % self.private_hex)
            print(" Private Key (long)             %s" % self.secret)
            print(" Private Key (wif)              %s" % self.wif())
        else:
            print("PUBLIC KEY ONLY, NO SECRET EXPONENT")
        print("")
        print(" Compressed                  %s" % self.compressed)
        print("PUBLIC KEY")
        print(" Public Key (hex)            %s" % self.public_hex)
        print(" Public Key uncompr. (hex)   %s" % self.public_uncompressed_hex)
        print(" Public Key Hash160          %s" % self.hash160())
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
    def from_seed(import_seed, network=DEFAULT_NETWORK):
        """
        Used by class init function, import key from seed

        :param import_seed: Private key seed as bytes or hexstring
        :param network: Network to use
        :return: HDKey class object
        """
        seed = to_bytes(import_seed)
        I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
        key = I[:32]
        chain = I[32:]
        return HDKey(key=key, chain=chain, network=network)

    def __init__(self, import_key=None, key=None, chain=None, depth=0, parent_fingerprint=b'\0\0\0\0',
                 child_index=0, isprivate=True, network=None, key_type='bip32', passphrase=''):
        """
        Hierarchical Deterministic Key class init function.
        If no import_key is specified a key will be generated with system cryptographically random function.

        :param import_key: HD Key to import in WIF format or as byte with key (32 bytes) and chain (32 bytes)
        :param key: Private or public key (32 bytes)
        :param chain: A chain code (32 bytes)
        :param depth: Integer of level of depth in path (BIP0043/BIP0044)
        :param parent_fingerprint: 4-byte fingerprint of parent
        :param child_index: Index number of child as integer
        :param isprivate: True for private, False for public key
        :param network: Network name. Derived from import_key if possible.
        :param key_type: HD BIP32 or normal Private Key
        :return:
        """

        if (key and not chain) or (not key and chain):
            raise KeyError("Please specify both key and chain, or use simple Key class instead")
        if not (key and chain):
            if not import_key:
                # Generate new Master Key
                seedbits = random.SystemRandom().getrandbits(512)
                seed = change_base(str(seedbits), 10, 256, 64)
                key, chain = self._key_derivation(seed)
            elif len(import_key) == 64:
                key = import_key[:32]
                chain = import_key[32:]
            else:
                bkey = change_base(import_key, 58, 256)
                hdkey_code = bkey[:4]
                if hdkey_code in network_values_for('prefix_hdkey_private') + network_values_for('prefix_hdkey_public'):
                    network = check_network_and_key(import_key, network)

                    # Derive key, chain, depth, child_index and fingerprint part from extended key WIF
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
                    try:
                        ki = Key(import_key, passphrase=passphrase, network=network)
                        chain = b'\0'*32
                        key = ki.private_byte
                        key_type = 'private'
                    except BKeyError as e:
                        raise BKeyError("[BKeyError] %s" % e)

        self.key = key
        self.key_hex = binascii.hexlify(key)
        self.chain = chain
        self.depth = depth
        self.parent_fingerprint = parent_fingerprint
        self.child_index = child_index
        self.isprivate = isprivate
        self._public_key_object = None
        self.public_uncompressed_hex = None
        if not network:
            network = DEFAULT_NETWORK
        self.network = Network(network)
        if isprivate:
            self.public_hex = None
            self.secret = change_base(key, 256, 10)
        else:
            self.public_hex = self.key_hex
            self.secret = None
        self.key_type = key_type

    def __repr__(self):
        return self.extended_wif()

    def info(self):
        if self.isprivate:
            print("SECRET EXPONENT")
            print(" Private Key (hex)           %s" % self.key_hex)
            print(" Private Key (long)          %s" % self.secret)
            print(" Private Key (wif)           %s" % self.private().wif())
            print("")
        print("PUBLIC KEY")
        print(" Public Key (hex)            %s" % self.public())
        print(" Public Key Hash160          %s" % self.public().hash160())
        print(" Address (b58)               %s" % self.public().address())
        print(" Fingerprint (hex)           %s" % change_base(self.fingerprint(), 256, 16))
        point_x, point_y = self.public().public_point()
        print(" Point x                     %s" % point_x)
        print(" Point y                     %s" % point_y)
        print("")
        print("EXTENDED KEY INFO")
        print(" Key Type                    %s" % self.key_type)
        print(" Chain code (hex)            %s" % change_base(self.chain, 256, 16))
        print(" Child Index                 %s" % self.child_index)
        print(" Parent Fingerprint (hex)    %s" % change_base(self.parent_fingerprint, 256, 16))
        print(" Depth                       %s" % self.depth)
        print(" Extended Public Key (wif)   %s" % self.extended_wif_public())
        print(" Extended Private Key (wif)  %s" % self.extended_wif(public=False))
        print("\n")

    def _key_derivation(self, seed):
        chain = hasattr(self, 'chain') and self.chain or b"Bitcoin seed"
        I = hmac.new(chain, seed, hashlib.sha512).digest()
        key = I[:32]
        chain = I[32:]
        return key, chain

    def fingerprint(self):
        return hashlib.new('ripemd160', hashlib.sha256(self.public().public_byte).digest()).digest()[:4]

    def extended_wif(self, public=None, child_index=None):
        rkey = self.key
        if not self.isprivate and public is False:
            return ''
        if self.isprivate and not public:
            raw = self.network.prefix_hdkey_private
            typebyte = b'\x00'
        else:
            raw = self.network.prefix_hdkey_public
            typebyte = b''
            if public:
                rkey = self.public().public_byte
        if child_index:
            self.child_index = child_index
        raw += change_base(self.depth, 10, 256, 1) + self.parent_fingerprint + \
            struct.pack('>L', self.child_index) + self.chain + typebyte + rkey
        chk = hashlib.sha256(hashlib.sha256(raw).digest()).digest()[:4]
        ret = raw+chk
        return change_base(ret, 256, 58, 111)

    def extended_wif_public(self):
        return self.extended_wif(public=True)

    def public(self):
        if not self._public_key_object:
            if self.public_hex:
                self._public_key_object = Key(self.public_hex, network=self.network.network_name)
            else:
                pub = Key(self.key).public()
                self._public_key_object = Key(pub, network=self.network.network_name)
        return self._public_key_object

    # def public_uncompressed(self):
    #     if not self.public_uncompressed_hex:
    #         pub = Key(self.key).public_uncompressed()
    #         return Key(pub, network=self.network.network_name)
    #     return self.public_uncompressed_hex

    def private(self):
        if self.key and self.isprivate:
            return Key(self.key, network=self.network.network_name)
        else:
            raise KeyError("No private key available")

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
        elif path[0] == 'M':  # Use Public master key
            path = path[2:]
            first_public = True
        if path:
            levels = path.split("/")
            for level in levels:
                if not level:
                    raise BKeyError("Could not parse path. Index is empty.")
                hardened = level[-1] in "'HhPp"
                if hardened:
                    level = level[:-1]
                index = int(level)
                if index < 0:
                    raise BKeyError("Could not parse path. Index must be a positive integer.")
                if first_public or not key.isprivate:
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
        if not self.isprivate:
            raise BKeyError("Need a private key to create child private key")
        if hardened:
            index |= 0x80000000
            data = b'\0' + self.key + struct.pack('>L', index)
        else:
            data = self.public().public_byte + struct.pack('>L', index)
        key, chain = self._key_derivation(data)

        key = change_base(key, 256, 10)
        if key > secp256k1_n:
            raise BKeyError("Key cannot be greater then secp256k1_n. Try another index number.")
        newkey = (key + self.secret) % secp256k1_n
        if newkey == 0:
            raise BKeyError("Key cannot be zero. Try another index number.")
        newkey = change_base(newkey, 10, 256, 32)

        return HDKey(key=newkey, chain=chain, depth=self.depth+1, parent_fingerprint=self.fingerprint(),
                     child_index=index, network=self.network.network_name)

    def child_public(self, index=0):
        """
        Use Child Key Derivation to derive child public key of current HD Key object.

        :param index: Key index number
        :return: HD Key class object
        """
        if index > 0x80000000:
            raise BKeyError("Cannot derive hardened key from public private key. Index must be less then 0x80000000")
        data = self.public().public_byte + struct.pack('>L', index)
        key, chain = self._key_derivation(data)
        key = change_base(key, 256, 10)
        if key > secp256k1_n:
            raise BKeyError("Key cannot be greater then secp256k1_n. Try another index number.")

        x, y = self.public().public_point()
        Ki = ec_point(key) + ecdsa.ellipticcurve.Point(curve, x, y, secp256k1_n)

        # if change_base(Ki.y(), 16, 10) % 2:
        if Ki.y() % 2:
            prefix = '03'
        else:
            prefix = '02'
        xhex = change_base(Ki.x(), 10, 16, 64)
        secret = change_base(prefix + xhex, 16, 256)
        return HDKey(key=secret, chain=chain, depth=self.depth+1, parent_fingerprint=self.fingerprint(),
                     child_index=index, isprivate=False, network=self.network.network_name)


if __name__ == '__main__':
    #
    # KEYS EXAMPLES
    #

    print("\n=== Generate random key ===")
    k = Key()
    k.info()

    print("\n=== Import Public key ===")
    K = Key('025c0de3b9c8ab18dd04e3511243ec2952002dbfadc864b9628910169d9b9b00ec')
    K.info()

    print("\n==== Import Private key as decimal ===")
    pk = 45552833878247474734848656701264879218668934469350493760914973828870088122784
    k = Key(import_key=pk, network='testnet')
    k.info()

    print("\n==== Import Private key as byte ===")
    pk = b':\xbaAb\xc7%\x1c\x89\x12\x07\xb7G\x84\x05Q\xa7\x199\xb0\xde\x08\x1f\x85\xc4\xe4L\xf7\xc1>A\xda\xa6\x01'
    k = Key(pk)
    k.info()

    print("\n=== Import Private WIF Key ===")
    k = Key('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX')
    print("Private key     %s" % k.wif())
    print("Private key hex %s " % k.private_hex)
    print("Compressed      %s\n" % k.compressed)

    print("\n=== Import Private Testnet Key ===")
    k = Key('92Pg46rUhgTT7romnV7iGW6W1gbGdeezqdbJCzShkCsYNzyyNcc', network='testnet')
    k.info()

    print("\n==== Import Private Litecoin key ===")
    pk = 'T43gB4F6k1Ly3YWbMuddq13xLb56hevUDP3RthKArr7FPHjQiXpp'
    k = Key(import_key=pk)
    k.info()

    print("\n==== Import uncompressed Private Key and Encrypt with BIP38 ===")
    k = Key('5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR')
    print("Private key     %s" % k.wif())
    print("Encrypted pk    %s " % k.bip38_encrypt('TestingOneTwoThree'))
    print("Is Compressed   %s\n" % k.compressed)

    print("\n==== Import and Decrypt BIP38 Key ===")
    k = Key('6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg', passphrase='TestingOneTwoThree')
    print("Private key     %s" % k.wif())
    print("Is Compressed   %s\n" % k.compressed)

    print("\n==== Generate random HD Key on testnet ===")
    hdk = HDKey(network='testnet')
    print("Random BIP32 HD Key on testnet %s" % hdk.extended_wif())

    print("\n==== Import HD Key from seed ===")
    k = HDKey.from_seed('000102030405060708090a0b0c0d0e0f')
    print("HD Key WIF for seed 000102030405060708090a0b0c0d0e0f:  %s" % k.extended_wif())
    print("Key type is : %s" % k.key_type)

    print("\n==== Import simple private key as HDKey ===")
    k = HDKey('L5fbTtqEKPK6zeuCBivnQ8FALMEq6ZApD7wkHZoMUsBWcktBev73')
    print("HD Key WIF for Private Key L5fbTtqEKPK6zeuCBivnQ8FALMEq6ZApD7wkHZoMUsBWcktBev73:  %s" % k.extended_wif())
    print("Key type is : %s" % k.key_type)

    print("\n==== Generate random Litecoin key ===")
    lk = HDKey(network='litecoin')
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
