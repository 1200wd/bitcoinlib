# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Public key cryptography and Hierarchical Deterministic Key Management
#    © 2017 September - 1200 Web Development <http://1200wd.com/>
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
import pyaes

from bitcoinlib.main import *
from bitcoinlib.networks import Network, DEFAULT_NETWORK, network_by_value
from bitcoinlib.config.secp256k1 import secp256k1_generator as generator, secp256k1_curve as curve, \
    secp256k1_p, secp256k1_n
from bitcoinlib.encoding import change_base, to_bytes, to_hexstring, EncodingError
from bitcoinlib.mnemonic import Mnemonic


_logger = logging.getLogger(__name__)


class BKeyError(Exception):
    """
    Handle Key class Exceptions

    """
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def check_network_and_key(key, network=None, kf_networks=None, default_network=DEFAULT_NETWORK):
    """
    Check if given key corresponds with given network and return network if it does. If no network is specified
    this method tries to extract the network from the key. If no network can be extracted from the key the
    default network will be returned.
    
    A KeyError will be raised if key does not corresponds with network or if multiple network are found.
    
    :param key: Key in any format recognized by get_key_format function
    :type key: str, int, bytes, bytearray
    :param network: Optional network. Method raises KeyError if keys belongs to another network
    :type network: str
    :param kf_networks: Optional list of networks which is returned by get_key_format. If left empty the get_key_format function will be called.
    :type kf_networks: list
    :param default_network: Specify different default network, leave empty for default (bitcoin)
    :type default_network: str
    
    :return str: Network name
    """
    if not kf_networks:
        kf = get_key_format(key)
        if kf['networks']:
            kf_networks = kf['networks']
    if kf_networks:
        if network is not None and network not in kf_networks:
            raise KeyError("Specified key %s is from different network then specified: %s" % (kf_networks, network))
        elif network is None and len(kf_networks) == 1:
            return kf_networks[0]
        elif network is None and len(kf_networks) > 1:
            if default_network in kf_networks:
                return default_network
            elif 'testnet' in kf_networks:
                return 'testnet'
            raise KeyError("Could not determine network of specified key, multiple networks found: %s" % kf_networks)
    if network is None:
        return default_network
    else:
        return network


def get_key_format(key, isprivate=None):
    """
    Determins the type (private or public), format and network key.
    
    This method does not validate if a key is valid.

    :param key: Any private or public key
    :type key: str, int, bytes, bytearray
    :param isprivate: Is key private or not?
    :type isprivate: bool
    
    :return dict: Dictionary with format, network and isprivate
    """
    if not key:
        raise BKeyError("Key empty, please specify a valid key")
    key_format = ""
    networks = None

    if isinstance(key, (bytes, bytearray)) and len(key) in [128, 130]:
        key = to_hexstring(key)

    if not (isprivate is None or isinstance(isprivate, bool)):
        raise BKeyError("Attribute 'is_private' must be False or True")
    elif isinstance(key, numbers.Number):
        key_format = 'decimal'
        isprivate = True
    elif isinstance(key, (bytes, bytearray)) and len(key) in [33, 65] and key[:1] in [b'\2', b'\3']:
        key_format = 'bin_compressed'
        isprivate = False
    elif isinstance(key, (bytes, bytearray)) and (len(key) in [33, 65] and key[:1] == b'\4'):
        key_format = 'bin'
        isprivate = False
    elif isinstance(key, (bytes, bytearray)) and len(key) == 33 and key[-1:] == b'\1':
        key_format = 'bin_compressed'
        isprivate = True
    elif isinstance(key, (bytes, bytearray)) and len(key) == 32:
        key_format = 'bin'
        isprivate = True
    elif len(key) == 130 and key[:2] == '04' and not isprivate:
        key_format = 'public_uncompressed'
        isprivate = False
    elif len(key) == 128:
        key_format = 'hex'
        if isprivate is None:
            isprivate = True
    elif len(key) == 66 and key[:2] in ['02', '03'] and not isprivate:
        key_format = 'public'
        isprivate = False
    elif len(key) == 64:
        key_format = 'hex'
        if isprivate is None:
            isprivate = True
    elif len(key) == 66 and key[-2:] in ['01'] and not(isprivate is False):
        key_format = 'hex_compressed'
        isprivate = True
    elif len(key) == 58 and key[:2] == '6P':
        key_format = 'wif_protected'
        isprivate = True
    else:
        try:
            key_hex = change_base(key, 58, 16)
            networks = network_by_value('prefix_wif', key_hex[:2])
            if networks:
                if key_hex[-10:-8] == '01':
                    key_format = 'wif_compressed'
                else:
                    key_format = 'wif'
                isprivate = True
            else:
                networks = network_by_value('prefix_hdkey_private', key_hex[:8])
                if networks:
                    key_format = 'hdkey_private'
                    isprivate = True
                else:
                    networks = network_by_value('prefix_hdkey_public', key_hex[:8])
                    if networks:
                        key_format = 'hdkey_public'
                        isprivate = False
                    # TODO: Recognise address key and implement in Key en HDKey classs
                    # else:
                    #     networks = network_by_value('prefix_address_p2sh', key_hex[:2]) + \
                    #                network_by_value('prefix_address', key_hex[:2])
                    #     if networks:
                    #         key_format = 'address'
                    #         isprivate = False

        except (TypeError, EncodingError):
            pass
    if not key_format:
        try:
            int(key)
            if 70 < len(key) < 78:
                key_format = 'decimal'
                isprivate = True
        except (TypeError, ValueError):
            pass
    if not key_format:
        raise BKeyError("Key: %s. Unrecognised key format" % key)
    else:
        return {
            "format": key_format,
            "networks": networks,
            "isprivate": isprivate
        }


def ec_point(p):
    """
    Method for eliptic curve multiplication

    :param p: A point on the eliptic curve
    
    :return Point: Point multiplied by generator G
    """
    p = int(p)
    point = generator
    point *= p
    return point


def deserialize_address(address):
    """
    Deserialize cryptocurrency address. Calculate public key hash and try to determine script type and network.

    If one and only one network is found the 'network' dictionary item with contain this network. Same applies for the script type.

    If more networks and or script types are found you can find these in 'networks_p2sh' and 'networks_p2pkh'.

    :param address: A base-58 encoded address
    :type address: str

    :return dict: with information about this address
    """
    try:
        address_bytes = change_base(address, 58, 256, 25)
    except EncodingError as err:
        raise EncodingError("Invalid address %s: %s" % (address, err))
    check = address_bytes[-4:]
    key_hash = address_bytes[:-4]
    checksum = hashlib.sha256(hashlib.sha256(key_hash).digest()).digest()[0:4]
    assert (check == checksum), "Invalid address, checksum incorrect"
    address_prefix = key_hash[0:1]
    networks_p2pkh = network_by_value('prefix_address', address_prefix)
    networks_p2sh = network_by_value('prefix_address_p2sh', address_prefix)
    public_key_hash = key_hash[1:]
    script_type = ''
    network = ''
    if networks_p2pkh and not networks_p2sh:
        script_type = 'p2pkh'
        if len(networks_p2pkh) == 1:
            network = networks_p2pkh[0]
    elif networks_p2sh and not networks_p2pkh:
        script_type = 'p2sh'
        if len(networks_p2sh) == 1:
            network = networks_p2sh[0]

    return {
        'address': address,
        'public_key_hash': change_base(public_key_hash, 256, 16),
        'public_key_hash_bytes': public_key_hash,
        'network': network,
        'script_type': script_type,
        'networks_p2sh': networks_p2sh,
        'networks_p2pkh': networks_p2pkh
    }


class Key:
    """
    Class to generate, import and convert public cryptograpic key pairs used for bitcoin.

    If no key is specified when creating class a cryptographically secure Private Key is
    generated using the os.urandom() function.
    """

    def __init__(self, import_key=None, network=None, compressed=True, passphrase=''):
        """
        Initialize a Key object. Import key can be in WIF, bytes, hexstring, etc.
        If a private key is imported a public key will be derived. If a public is imported the private key data will
        be empty.
        
        Both compressed and uncompressed key version is available, the Key.compressed boolean attribute tells if the
        original imported key was compressed or not.

        :param import_key: If specified import given private or public key. If not specified a new private key is generated.
        :type import_key: str, int, bytes, bytearray
        :param network: Bitcoin, testnet, litecoin or other network
        :type network: str
        :param compressed: Is key compressed or not, default is True
        :type compressed: bool
        :param passphrase: Optional passphrase if imported key is password protected
        :type passphrase: str
        
        :return: Key object
        """
        self.public_hex = None
        self.public_uncompressed_hex = None
        self.public_compressed_hex = None
        self.public_byte = None
        self.public_uncompressed_byte = None
        self.public_compressed_byte = None
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
        network = check_network_and_key(import_key, network, kf["networks"])
        self.network = Network(network)
        if kf['isprivate']:
            self.isprivate = True
        elif kf['isprivate'] is None:
            raise KeyError("Could not determine if key is private or public")
        else:
            self.isprivate = False

        if self.key_format == "wif_protected":
            # TODO: return key as byte to make more efficient
            import_key, self.key_format = self._bip38_decrypt(import_key, passphrase)

        if not self.isprivate:
            self.secret = None
            pub_key = to_hexstring(import_key)
            if len(pub_key) == 130:
                self.public_uncompressed_hex = pub_key
                self._x = pub_key[2:66]
                self._y = pub_key[66:130]
                self.compressed = False
                if int(self._y, 16) % 2:
                    prefix = '03'
                else:
                    prefix = '02'
                self.public_hex = prefix + self._x
                self.public_compressed_hex = prefix + self._x
            else:
                self.public_hex = pub_key
                self._x = pub_key[2:66]
                self.compressed = True
                # Calculate y from x with y=x^3 + 7 function
                sign = pub_key[:2] == '03'
                x = int(self._x, 16)
                ys = (x**3+7) % secp256k1_p
                y = ecdsa.numbertheory.square_root_mod_prime(ys, secp256k1_p)
                if y & 1 != sign:
                    y = secp256k1_p - y
                self._y = change_base(y, 10, 16, 64)
                self.public_uncompressed_hex = '04' + self._x + self._y
                self.public_compressed_hex = pub_key
            self.public_compressed_byte = binascii.unhexlify(self.public_hex)
            self.public_uncompressed_byte = binascii.unhexlify(self.public_uncompressed_hex)
            if self.compressed:
                self.public_byte = self.public_compressed_byte
            else:
                self.public_byte = self.public_uncompressed_byte
        elif self.isprivate and self.key_format == 'decimal':
            self.secret = import_key
            self.private_hex = change_base(import_key, 10, 16, 64)
            self.private_byte = binascii.unhexlify(self.private_hex)
        elif self.isprivate:
            if self.key_format == 'hex':
                key_hex = import_key
                key_byte = binascii.unhexlify(key_hex)
            elif self.key_format == 'hex_compressed':
                key_hex = import_key[:-2]
                key_byte = binascii.unhexlify(key_hex)
                self.compressed = True
            elif self.key_format == 'bin':
                key_byte = import_key
                key_hex = to_hexstring(key_byte)
            elif self.key_format == 'bin_compressed':
                key_byte = import_key[:-1]
                key_hex = to_hexstring(key_byte)
                self.compressed = True
            elif self.isprivate and self.key_format in ['wif', 'wif_compressed']:
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
            self.private_byte = key_byte
            self.secret = int(key_hex, 16)
        else:
            raise KeyError("Cannot import key. Public key format unknown")

        if self.isprivate and not (self.public_byte or self.public_hex):
            if not self.isprivate:
                raise KeyError("Private key has no known secret number")
            point = ec_point(self.secret)
            self._x = change_base(point.x(), 10, 16, 64)
            self._y = change_base(point.y(), 10, 16, 64)
            if point.y() % 2:
                prefix = '03'
            else:
                prefix = '02'

            self.public_compressed_hex = prefix + self._x
            self.public_uncompressed_hex = '04' + self._x + self._y
            self.public_hex = self.public_compressed_hex if self.compressed else self.public_uncompressed_hex

            self.public_byte = binascii.unhexlify(self.public_hex)
            self.public_compressed_byte = binascii.unhexlify(self.public_compressed_hex)
            self.public_uncompressed_byte = binascii.unhexlify(self.public_uncompressed_hex)

    def __repr__(self):
        return "<Key(public_hex=%s, network=%s)" % (self.public_hex, self.network.network_name)

    @staticmethod
    def _bip38_decrypt(encrypted_privkey, passphrase):
        """
        BIP0038 non-ec-multiply decryption. Returns WIF private key.
        Based on code from https://github.com/nomorecoin/python-bip38-testing
        This method is called by Key class init function when importing BIP0038 key.

        :param encrypted_privkey: Encrypted private key using WIF protected key format
        :type encrypted_privkey: str
        :param passphrase: Required passphrase for decryption
        :type passphrase: str
        
        :return str: Private Key WIF
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
        aes = pyaes.AESModeOfOperationECB(derivedhalf2)
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
        :type passphrase: str
        
        :return str: BIP38 passphrase encrypted private key
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
        aes = pyaes.AESModeOfOperationECB(derivedhalf2)
        encryptedhalf1 = aes.encrypt(binascii.unhexlify('%0.32x' % (int(privkey[0:32], 16) ^
                                                                    int(binascii.hexlify(derivedhalf1[0:16]), 16))))
        encryptedhalf2 = aes.encrypt(binascii.unhexlify('%0.32x' % (int(privkey[32:64], 16) ^
                                                                    int(binascii.hexlify(derivedhalf1[16:32]), 16))))
        encrypted_privkey = b'\x01\x42' + flagbyte + addresshash + encryptedhalf1 + encryptedhalf2
        encrypted_privkey += hashlib.sha256(hashlib.sha256(encrypted_privkey).digest()).digest()[:4]
        return change_base(encrypted_privkey, 256, 58)

    def wif(self):
        """
        Get Private Key in Wallet Import Format, steps:
        # Convert to Binary and add 0x80 hex
        # Calculate Double SHA256 and add as checksum to end of key

        :return str: Base58Check encoded Private Key WIF
        """
        if not self.secret:
            raise KeyError("WIF format not supported for public key")
        version = self.network.prefix_wif
        key = version + change_base(self.secret, 10, 256, 32)
        if self.compressed:
            key += b'\1'
        key += hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]
        return change_base(key, 256, 58)

    def public(self, return_compressed=None):
        """
        Get public key
        
        :param return_compressed: If True always return a compressed version and if False always return uncompressed
        :type return_compressed: bool
        
        :return str: Public key hexstring 
        """
        if (self.compressed and return_compressed is None) or return_compressed:
            return self.public_hex
        else:
            return self.public_uncompressed_hex

    def public_uncompressed(self):
        """
        Get public key, uncompressed version
        
        :return str: Uncompressed public key hexstring 
        """
        return self.public_uncompressed_hex

    def public_point(self):
        """
        Get public key point on Elliptic curve
        
        :return tuple: (x, y) point
        """
        x = self._x and int(self._x, 16)
        y = self._y and int(self._y, 16)
        return (x, y)

    def hash160(self):
        """
        Get public key in Hash160 format
        
        :return bytes: Hash160 of public key 
        """
        if self.compressed:
            pb = self.public_byte
        else:
            pb = self.public_uncompressed_byte
        return hashlib.new('ripemd160', hashlib.sha256(pb).digest()).digest()

    def address(self, compressed=None):
        """
        Get address derived from public key
        
        :param compressed: Always return compressed address
        :type compressed: bool
        
        :return str: Base58 encoded address 
        """
        if (self.compressed and compressed is None) or compressed:
            key = self.public_byte
        else:
            key = self.public_uncompressed_byte
        versionbyte = self.network.prefix_address
        key = versionbyte + hashlib.new('ripemd160', hashlib.sha256(key).digest()).digest()
        checksum = hashlib.sha256(hashlib.sha256(key).digest()).digest()[:4]
        return change_base(key + checksum, 256, 58)

    def address_uncompressed(self):
        """
        Get uncompressed address from public key
        
        :return str: Base58 encoded address 
        """
        return self.address(compressed=False)

    def info(self):
        """
        Prints key information to standard output
        
        """
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
    def from_seed(import_seed, key_type='bip32', network=DEFAULT_NETWORK):
        """
        Used by class init function, import key from seed

        :param import_seed: Private key seed as bytes or hexstring
        :type import_seed: str, bytes
        :param key_type: Specify type of key, default is BIP32
        :type key_type: str
        :param network: Network to use
        :type network: str
        
        :return HDKey: 
        """
        seed = to_bytes(import_seed)
        I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
        key = I[:32]
        chain = I[32:]
        return HDKey(key=key, chain=chain, network=network, key_type=key_type)

    @staticmethod
    def from_passphrase(passphrase, password='', network=DEFAULT_NETWORK):
        """
        Create key from Mnemonic passphrase

        :param passphrase: Mnemonic passphrase, list of words as string seperated with a space character
        :type passphrase: str
        :param password: Password to protect passphrase
        :type password: str
        :param network: Network to use
        :type network: str

        :return HDKey:
        """
        return HDKey().from_seed(Mnemonic().to_seed(passphrase, password), network=network)

    def __init__(self, import_key=None, key=None, chain=None, depth=0, parent_fingerprint=b'\0\0\0\0',
                 child_index=0, isprivate=True, network=None, key_type='bip32', passphrase='', compressed=True):
        """
        Hierarchical Deterministic Key class init function.
        If no import_key is specified a key will be generated with systems cryptographically random function.
        Import key can be any format normal or HD key (extended key) accepted by get_key_format. 
        If a normal key with no chain part is provided, an chain with only 32 0-bytes will be used.

        :param import_key: HD Key to import in WIF format or as byte with key (32 bytes) and chain (32 bytes)
        :type import_key: str, bytes, int, bytearray
        :param key: Private or public key (length 32)
        :type key: bytes
        :param chain: A chain code (length 32)
        :type chain: bytes
        :param depth: Level of depth in BIP32 key path
        :type depth: int
        :param parent_fingerprint: 4-byte fingerprint of parent
        :type parent_fingerprint: bytes
        :param child_index: Index number of child as integer
        :type child_index: int
        :param isprivate: True for private, False for public key. Default is True
        :type isprivate: bool
        :param network: Network name. Derived from import_key if possible
        :type network: str
        :param key_type: HD BIP32 or normal Private Key. Default is 'bip32'
        :type key_type: str
        
        :return HDKey: 
        """

        self.key_format = None
        if (key and not chain) or (not key and chain):
            raise KeyError("Please specify both key and chain, use import_key attribute "
                           "or use simple Key class instead")
        self.compressed = compressed
        self.key = None

        if not (key and chain):
            if not import_key:
                # Generate new Master Key
                seedbits = random.SystemRandom().getrandbits(512)
                seed = change_base(str(seedbits), 10, 256, 64)
                key, chain = self._key_derivation(seed)
            elif isinstance(import_key, (bytearray, bytes if sys.version > '3' else bytearray)) \
                    and len(import_key) == 64:
                key = import_key[:32]
                chain = import_key[32:]
            elif isinstance(import_key, Key):
                self.key = import_key
                if not import_key.compressed:
                    _logger.warning("Uncompressed private keys are not standard for BIP32 keys, use at your own risk!")
                    self.compressed = False
                chain = b'\0' * 32
                key = self.key.private_byte
                key_type = 'private'
            else:
                kf = get_key_format(import_key)
                self.key_format = kf["format"]
                network = check_network_and_key(import_key, network, kf["networks"])
                self.network = Network(network)
                if self.key_format in ['hdkey_private', 'hdkey_public']:
                    bkey = change_base(import_key, 58, 256)
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
                        self.key = Key(import_key, passphrase=passphrase, network=network)
                        if not self.key.compressed:
                            _logger.warning(
                                "Uncompressed private keys are not standard for BIP32 keys, use at your own risk!")
                            self.compressed = False
                        # FIXME: Maybe its better to create a random chain?
                        chain = b'\0'*32
                        key = self.key.private_byte
                        key_type = 'private'
                    except BKeyError as e:
                        raise BKeyError("[BKeyError] %s" % e)

        if not isinstance(key, (bytes, bytearray)) or not(len(key) == 32 or len(key) == 33):
            raise KeyError("Invalid key specified must be in bytes with length 32. You can use "
                           "'import_key' attribute to import keys in other formats")
        self.chain = chain
        if self.key is None:
            self.key = Key(key, passphrase=passphrase, network=network, compressed=compressed)
        self.depth = depth
        self.parent_fingerprint = parent_fingerprint
        self.child_index = child_index
        self.isprivate = isprivate
        if not network:
            network = DEFAULT_NETWORK
            _logger.warning("No network specified when creating new HDKey, using default network")
        self.network = Network(network)
        self.public_byte = self.key.public_byte
        self.public_hex = self.key.public_hex
        self.secret = None
        self.private_hex = None
        self.private_byte = None
        if isprivate:
            self.secret = self.key.secret
            self.private_hex = self.key.private_hex
            self.private_byte = self.key.private_byte
            self.key_hex = self.private_hex
        else:
            self.key_hex = self.public_hex
        self.key_type = key_type

    def __repr__(self):
        return "<HDKey(public_hex=%s, wif_public=%s, network=%s)>" % \
               (self.public_hex, self.wif_public(), self.network.network_name)

    def info(self):
        """
        Prints key information to standard output
        
        """
        if self.isprivate:
            print("SECRET EXPONENT")
            print(" Private Key (hex)           %s" % self.private_hex)
            print(" Private Key (long)          %s" % self.secret)
            print(" Private Key (wif)           %s" % self.key.wif())
            print("")
        print("PUBLIC KEY")
        print(" Public Key (hex)            %s" % self.public_hex)
        print(" Public Key Hash160          %s" % change_base(self.key.hash160(), 256, 16))
        print(" Address (b58)               %s" % self.key.address())
        print(" Fingerprint (hex)           %s" % change_base(self.fingerprint(), 256, 16))
        point_x, point_y = self.key.public_point()
        print(" Point x                     %s" % point_x)
        print(" Point y                     %s" % point_y)
        print("")
        print("EXTENDED KEY INFO")
        print(" Key Type                    %s" % self.key_type)
        print(" Chain code (hex)            %s" % change_base(self.chain, 256, 16))
        print(" Child Index                 %s" % self.child_index)
        print(" Parent Fingerprint (hex)    %s" % change_base(self.parent_fingerprint, 256, 16))
        print(" Depth                       %s" % self.depth)
        print(" Extended Public Key (wif)   %s" % self.wif_public())
        print(" Extended Private Key (wif)  %s" % self.wif(public=False))
        print("\n")

    def dict(self):
        """
        Returns key information as dictionary

        """

        point_x, point_y = self.key.public_point()
        return {
            'private_hex': '' if not self.isprivate else self.private_hex,
            'private_long': '' if not self.isprivate else self.secret,
            'private_wif': '' if not self.isprivate else self.key.wif(),
            'public_hex': self.public_hex,
            'public_hash160': self.key.hash160(),
            'address': self.key.address(),
            'fingerprint': change_base(self.fingerprint(), 256, 16),
            'point_x': point_x,
            'point_y': point_y,
            'key_type': self.key_type,
            'chain_code': change_base(self.chain, 256, 16),
            'child_index': self.child_index,
            'fingerprint_parent': change_base(self.parent_fingerprint, 256, 16),
            'depth': self.depth,
            'extended_wif_public': self.wif_public(),
            'extended_wif_private': self.wif(public=False),
        }
        
    def _key_derivation(self, seed):
        """
        Derive extended private key with key and chain part from seed
        
        :param seed:
        :type seed: bytes
        
        :return tuple: key and chain bytes
        """
        chain = hasattr(self, 'chain') and self.chain or b"Bitcoin seed"
        I = hmac.new(chain, seed, hashlib.sha512).digest()
        key = I[:32]
        chain = I[32:]
        return key, chain

    def fingerprint(self):
        """
        Get fingerprint of keys public part

        :return bytes:
        """
        return hashlib.new('ripemd160', hashlib.sha256(self.public_byte).digest()).digest()[:4]

    def wif(self, public=None, child_index=None):
        """
        Get Extended WIF of current key
        
        :param public: Return public key?
        :type public: bool
        :param child_index: Change child index of output WIF key
        :type child_index: int
        
        :return str: Base58 encoded WIF key 
        """
        rkey = self.private_byte or self.public_byte
        if not self.isprivate and public is False:
            return ''
        if self.isprivate and not public:
            raw = self.network.prefix_hdkey_private
            typebyte = b'\x00'
        else:
            raw = self.network.prefix_hdkey_public
            typebyte = b''
            if public:
                rkey = self.public_byte
        if child_index:
            self.child_index = child_index
        raw += struct.pack('B', self.depth) + self.parent_fingerprint + \
            struct.pack('>L', self.child_index) + self.chain + typebyte + rkey
        chk = hashlib.sha256(hashlib.sha256(raw).digest()).digest()[:4]
        ret = raw+chk
        return change_base(ret, 256, 58, 111)

    def wif_public(self):
        """
        Get Extended WIF public key
        
        :return str: Base58 encoded WIF key
        """
        return self.wif(public=True)

    def subkey_for_path(self, path, network=None):
        """
        Determine subkey for HD Key for given path.
        Path format: m / purpose' / coin_type' / account' / change / address_index
        Example: m/44'/0'/0'/0/2
        See BIP0044 bitcoin proposal for more explanation.

        :param path: BIP0044 key path
        :type path: str
        :param network: Network name.
        :type network: str

        :return HDKey: HD Key class object of subkey
        """

        if self.key_type == 'single':
            raise KeyError("Key derivation cannot be used for 'single' type keys")
        key = self
        first_public = False
        if path[0] == 'm':  # Use Private master key
            path = path[2:]
        elif path[0] == 'M':  # Use Public master key
            path = path[2:]
            first_public = True
        if path:
            levels = path.split("/")
            if len(levels) > 1:
                _logger.warning("Path length > 1 can be slow for larger paths, use Wallet Class to generate keys paths")
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
                    key = key.child_public(index=index, network=network)  # TODO hardened=hardened key?
                    first_public = False
                else:
                    key = key.child_private(index=index, hardened=hardened, network=network)
        return key

    def account_key(self, account_id=0, purpose=44, set_network=None):
        """
        Derive account BIP44 key for current master key

        :param account_id: Account ID. Leave empty for account 0
        :type account_id: int
        :param purpose: BIP standard used, i.e. 44 for default, 45 for multisig
        :type purpose: int
        :param set_network: Derive account key for different network. Please note this calls the network_change method and changes the network for current key!
        :type set_network: str

        :return HDKey:

        """
        if self.depth == 3:
            return self
        elif self.depth != 0:
            raise KeyError("Need a master key to generate account key")
        if set_network:
            self.network_change(set_network)
        if self.isprivate:
            path = "m"
        else:
            path = "M"
        path += "/%d'" % purpose
        path += "/%d'" % self.network.bip44_cointype
        path += "/%d'" % account_id
        return self.subkey_for_path(path)

    def account_multisig_key(self, account_id=0, purpose=45, set_network=None):
        """
        Derives a multisig account key according to BIP44/45 definiation.
        Wrapper for the 'account_key' method.

        :param account_id: Account ID. Leave empty for account 0
        :type account_id: int
        :param purpose: BIP standard used, leave empty for 45 which is the default for multisig
        :type purpose: int
        :param set_network: Derive account key for different network. Please note this calls the network_change method and changes the network for current key!
        :type set_network: str

        :return HDKey:
        """
        return self.account_key(account_id, purpose, set_network)

    def network_change(self, new_network):
        """
        Change network for current key

        :param new_network: Name of new network
        :type new_network: str

        :return bool: True
        """
        self.network = Network(new_network)
        return True

    def child_private(self, index=0, hardened=False, network=None):
        """
        Use Child Key Derivation (CDK) to derive child private key of current HD Key object.

        :param index: Key index number
        :type index: int
        :param hardened: Specify if key must be hardened (True) or normal (False)
        :type hardened: bool
        :param network: Network name.
        :type network: str

        :return HDKey: HD Key class object
        """
        if network is None:
            network = self.network.network_name
        if not self.isprivate:
            raise BKeyError("Need a private key to create child private key")
        if hardened:
            index |= 0x80000000
            data = b'\0' + self.private_byte + struct.pack('>L', index)
        else:
            data = self.public_byte + struct.pack('>L', index)
        key, chain = self._key_derivation(data)

        key = change_base(key, 256, 10)
        if key > secp256k1_n:
            raise BKeyError("Key cannot be greater then secp256k1_n. Try another index number.")
        newkey = (key + self.secret) % secp256k1_n
        if newkey == 0:
            raise BKeyError("Key cannot be zero. Try another index number.")
        newkey = change_base(newkey, 10, 256, 32)

        return HDKey(key=newkey, chain=chain, depth=self.depth+1, parent_fingerprint=self.fingerprint(),
                     child_index=index, network=network)

    def child_public(self, index=0, network=None):
        """
        Use Child Key Derivation to derive child public key of current HD Key object.

        :param index: Key index number
        :type index: int
        :param network: Network name.
        :type network: str

        :return HDKey: HD Key class object
        """
        if network is None:
            network = self.network.network_name
        if index > 0x80000000:
            raise BKeyError("Cannot derive hardened key from public private key. Index must be less then 0x80000000")
        data = self.public_byte + struct.pack('>L', index)
        key, chain = self._key_derivation(data)
        key = change_base(key, 256, 10)
        if key > secp256k1_n:
            raise BKeyError("Key cannot be greater then secp256k1_n. Try another index number.")

        x, y = self.key.public_point()
        Ki = ec_point(key) + ecdsa.ellipticcurve.Point(curve, x, y, secp256k1_n)

        # if change_base(Ki.y(), 16, 10) % 2:
        if Ki.y() % 2:
            prefix = '03'
        else:
            prefix = '02'
        xhex = change_base(Ki.x(), 10, 16, 64)
        secret = binascii.unhexlify(prefix + xhex)
        return HDKey(key=secret, chain=chain, depth=self.depth+1, parent_fingerprint=self.fingerprint(),
                     child_index=index, isprivate=False, network=network)

    def public(self):
        """
        Public version of current private key.

        :return HDKey:
        """

        #TODO: more clevvvvver
        return HDKey(self.wif_public(), parent_fingerprint=self.parent_fingerprint, isprivate=self.isprivate,
                     key_type=self.key_type, network=self.network.network_name)
