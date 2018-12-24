# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Public key cryptography and Hierarchical Deterministic Key Management
#    © 2016 - 2018 August - 1200 Web Development <http://1200wd.com/>
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
from copy import deepcopy

import ecdsa
try:
    import scrypt
    USING_MODULE_SCRYPT = True
except ImportError:
    import pyscrypt as scrypt
    USING_MODULE_SCRYPT = False

import pyaes

from bitcoinlib.main import *
from bitcoinlib.networks import Network, DEFAULT_NETWORK, network_by_value, prefix_search
from bitcoinlib.config.secp256k1 import secp256k1_generator as generator, secp256k1_curve as curve, \
    secp256k1_p, secp256k1_n
from bitcoinlib.encoding import change_base, to_bytes, to_hexstring, EncodingError, addr_to_pubkeyhash, \
    pubkeyhash_to_addr, varstr, double_sha256, hash160
from bitcoinlib.mnemonic import Mnemonic


_logger = logging.getLogger(__name__)

if not USING_MODULE_SCRYPT:
    _logger.warning("Using 'pyscrypt' module instead of 'scrypt' which could result in slow hashing of BIP38 password "
                    "protected keys.")


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
    Determines the type (private or public), format and network key.
    
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
    script_types = None

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
                    else:
                        prefix_data = prefix_search(key_hex[:8])
                        if prefix_data:
                            networks = [n['network'] for n in prefix_data]
                            isprivate = prefix_data[0]['is_private']
                            script_types = prefix_data[0]['script_types']
                            key_format = 'hdkey_public'
                            if isprivate:
                                key_format = 'hdkey_private'

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
            "isprivate": isprivate,
            "script_types": script_types
        }


def ec_point(p):
    """
    Method for elliptic curve multiplication

    :param p: A point on the elliptic curve
    
    :return Point: Point multiplied by generator G
    """
    p = int(p)
    point = generator
    point *= p
    return point


def deserialize_address(address, encoding=None, network=None):
    """
    Deserialize address. Calculate public key hash and try to determine script type and network.

    The 'network' dictionary item with contain the network with highest priority if multiple networks are found. Same applies for the script type.

    Specify the network argument if known to avoid unexpected results.

    If more networks and or script types are found you can find these in the 'networks' field.

    :param address: A base58 or bech32 encoded address
    :type address: str
    :param encoding: Encoding scheme used for address encoding. Attempts to guess encoding if not specified.
    :type encoding: str
    :param network: Bitcoin, testnet, litecoin or other network
    :type network: str

    :return dict: with information about this address
    """

    if encoding is not None and encoding not in SUPPORTED_ADDRESS_ENCODINGS:
        raise KeyError("Encoding '%s' not found in supported address encodings %s" %
                       (encoding, SUPPORTED_ADDRESS_ENCODINGS))
    if encoding is None or encoding == 'base58':
        address_bytes = change_base(address, 58, 256, 25)
        if address_bytes:
            check = address_bytes[-4:]
            key_hash = address_bytes[:-4]
            checksum = double_sha256(key_hash)[0:4]
            if check != checksum and encoding == 'base58':
                raise KeyError("Invalid address %s, checksum incorrect" % address)
            elif check == checksum:
                address_prefix = key_hash[0:1]
                networks_p2pkh = network_by_value('prefix_address', address_prefix)
                networks_p2sh = network_by_value('prefix_address_p2sh', address_prefix)
                public_key_hash = key_hash[1:]
                script_type = ''
                networks = []
                if networks_p2pkh and not networks_p2sh:
                    script_type = 'p2pkh'
                    networks = networks_p2pkh
                elif networks_p2sh:
                    script_type = 'p2sh'
                    networks = networks_p2sh
                if network:
                    if network not in networks:
                        raise KeyError("Network %s not found in extracted networks: %s" % (network, networks))
                elif len(networks) >= 1:
                    network = networks[0]
                return {
                    'address': address,
                    'encoding': 'base58',
                    'public_key_hash': change_base(public_key_hash, 256, 16),
                    'public_key_hash_bytes': public_key_hash,
                    'prefix': address_prefix,
                    'network': network,
                    'script_type': script_type,
                    'networks': networks,
                }
    if encoding == 'bech32' or encoding is None:
        try:
            public_key_hash = addr_to_pubkeyhash(address, encoding='bech32')
            if not public_key_hash:
                raise EncodingError("Invalid bech32 address %s" % address)
            prefix = address[:address.rfind('1')]
            networks = network_by_value('prefix_bech32', prefix)
            if len(public_key_hash) == 20:
                script_type = 'p2wpkh'
            elif len(public_key_hash) == 32:
                script_type = 'p2wsh'
            else:
                raise KeyError("Unknown script type for address %s. Invalid length %d" %
                               (address, len(public_key_hash)))
            return {
                'address': address,
                'encoding': 'bech32',
                'public_key_hash': change_base(public_key_hash, 256, 16),
                'public_key_hash_bytes': public_key_hash,
                'prefix': prefix,
                'network': '' if not networks else networks[0],
                'script_type': script_type,
                'networks': networks,
            }
        except EncodingError as err:
            raise EncodingError("Invalid address %s: %s" % (address, err))
    else:
        raise EncodingError("Address %s is not in specified encoding %s" % (address, encoding))


def addr_convert(addr, prefix, encoding=None, to_encoding=None):
    """
    Convert base-58 encoded address to address with another prefix

    :param addr: Base58 address
    :type addr: str
    :param prefix: New address prefix
    :type prefix: str, bytes
    :param encoding: Encoding of original address: base58 or bech32. Leave empty to extract from address
    :type encoding: str
    :param to_encoding: Encoding of converted address: base58 or bech32. Leave empty use same encoding as original address
    :type to_encoding: str

    :return str: New converted address
    """

    if encoding is None:
        da = deserialize_address(addr)
        encoding = da['encoding']
    pkh = addr_to_pubkeyhash(addr, encoding=encoding)
    if to_encoding is None:
        to_encoding = encoding
    if isinstance(prefix, str) and to_encoding == 'base58':
        prefix = to_hexstring(prefix)
    return pubkeyhash_to_addr(pkh, prefix=prefix, encoding=to_encoding)


class Address:
    """
    Class to store, convert and analyse various address types as representation of public keys or scripts hashes
    """

    @classmethod
    def import_address(cls, address, encoding=None, network=None, network_overrides=None):
        """
        Import an address to the Address class. Specify network if available, otherwise it will be
        derived form the address.

        :param address: Address to import
        :type address: str
        :param encoding: Address encoding. Default is base58 encoding, for native segwit addresses specify bech32 encoding. Leave empty to derive from address
        :type encoding: str
        :param network: Bitcoin, testnet, litecoin or other network
        :type network: str
        :param network_overrides: Override network settings for specific prefixes, i.e.: {"prefix_address_p2sh": "32"}. Used by settings in providers.json
        :type network_overrides: dict

        :return Address:
        """
        if encoding is None and address[:3].split("1")[0] in ['bc', 'tb', 'ltc', 'tltc', 'tdash', 'tdash', 'bclt']:
            encoding = 'bech32'
        addr_dict = deserialize_address(address, encoding=encoding)
        public_key_hash_bytes = addr_dict['public_key_hash_bytes']
        prefix = addr_dict['prefix']
        if network is None:
            network = addr_dict['network']
        script_type = addr_dict['script_type']
        return Address(hashed_data=public_key_hash_bytes, network=network, prefix=prefix, script_type=script_type,
                       encoding=addr_dict['encoding'], network_overrides=network_overrides)

    def __init__(self, data='', hashed_data='', network=DEFAULT_NETWORK, prefix=None, script_type=None,
                 encoding=None, witness_type=None, network_overrides=None):
        """
        Initialize an Address object. Specify a public key, redeemscript or a hash.

        :param data: Public key, redeem script or other type of script.
        :type data: str, bytes
        :param hashed_data: Hash of a public key or script. Will be generated if 'data' parameter is provided
        :type hashed_data: str, bytes
        :param network: Bitcoin, testnet, litecoin or other network
        :type network: str, Network
        :param prefix: Address prefix. Use default network / script_type prefix if not provided
        :type prefix: str, bytes
        :param script_type: Type of script, i.e. p2sh or p2pkh.
        :type script_type: str
        :param encoding: Address encoding. Default is base58 encoding, for native segwit addresses specify bech32 encoding
        :type encoding: str
        :param witness_type: Specify 'legacy', 'segwit' or 'p2sh-segwit'. Legacy for old-style bitcoin addresses, segwit for native segwit addresses and p2sh-segwit for segwit embedded in a p2sh script. Leave empty to derive automatically from script type if possible
        :type witness_type: str
        :param network_overrides: Override network settings for specific prefixes, i.e.: {"prefix_address_p2sh": "32"}. Used by settings in providers.json
        :type network_overrides: dict

        """
        self.network = network
        if not (data or hashed_data):
            raise KeyError("Please specify data (public key or script) or hashed_data argument")
        if not isinstance(network, Network):
            self.network = Network(network)
        self.data_bytes = to_bytes(data)
        self.data = to_hexstring(data)
        self.script_type = script_type
        self.encoding = encoding
        if witness_type is None:
            if self.script_type in ['p2wpkh', 'p2wsh']:
                witness_type = 'segwit'
            elif self.script_type in ['p2sh_p2wpkh', 'p2sh_p2wsh']:
                witness_type = 'p2sh-segwit'
        self.witness_type = witness_type
        if self.encoding is None:
            if self.script_type in ['p2wpkh', 'p2wsh'] or self.witness_type == 'segwit':
                self.encoding = 'bech32'
            else:
                self.encoding = 'base58'
        self.hash_bytes = to_bytes(hashed_data)
        self.prefix = prefix
        self.redeemscript = b''
        if not self.hash_bytes:
            if (self.encoding == 'bech32' and self.script_type in ['p2sh', 'p2sh_multisig']) or \
                            self.script_type in ['p2wsh', 'p2sh_p2wsh']:
                self.hash_bytes = hashlib.sha256(self.data_bytes).digest()
            else:
                self.hash_bytes = hash160(self.data_bytes)
        self.hashed_data = to_hexstring(self.hash_bytes)
        if self.encoding == 'base58':
            # if self.script_type is None:
            #     self.script_type = 'p2pkh'
            if self.witness_type == 'p2sh-segwit':
                self.redeemscript = b'\0' + varstr(self.hash_bytes)
                self.hash_bytes = hash160(self.redeemscript)
            if self.prefix is None:
                if self.script_type in ['p2sh', 'p2sh_p2wpkh', 'p2sh_p2wsh', 'p2sh_multisig'] or \
                                self.witness_type == 'p2sh-segwit':
                    self.prefix = self.network.prefix_address_p2sh
                else:
                    self.prefix = self.network.prefix_address
            else:
                self.prefix = to_bytes(prefix)
        elif self.encoding == 'bech32':
            if self.script_type is None:
                self.script_type = 'p2wpkh'
            if self.prefix is None:
                self.prefix = self.network.prefix_bech32
        else:
            raise KeyError("Encoding %s not supported" % self.encoding)
        self.address = pubkeyhash_to_addr(bytearray(self.hash_bytes), prefix=self.prefix, encoding=self.encoding)
        self.address_orig = None
        provider_prefix = None
        if network_overrides and 'prefix_address_p2sh' in network_overrides and self.script_type == 'p2sh':
            provider_prefix = network_overrides['prefix_address_p2sh']
        self.address_orig = self.address
        if provider_prefix:
            self.address = addr_convert(self.address, provider_prefix)

    def __repr__(self):
        return "<Address(address=%s)" % self.address

    def with_prefix(self, prefix):
        """
        Convert address using another prefix

        :param prefix: Address prefix
        :type prefix: str, bytes

        :return str: Converted address
        """
        return addr_convert(self.address, prefix)


class Key:
    """
    Class to generate, import and convert public cryptographic key pairs used for bitcoin.

    If no key is specified when creating class a cryptographically secure Private Key is
    generated using the os.urandom() function.
    """

    def __init__(self, import_key=None, network=None, compressed=True, passphrase='', is_private=None):
        """
        Initialize a Key object. Import key can be in WIF, bytes, hexstring, etc.
        If a private key is imported a public key will be derived. If a public is imported the private key data will
        be empty.
        
        Both compressed and uncompressed key version is available, the Key.compressed boolean attribute tells if the
        original imported key was compressed or not.

        :param import_key: If specified import given private or public key. If not specified a new private key is generated.
        :type import_key: str, int, bytes, bytearray
        :param network: Bitcoin, testnet, litecoin or other network
        :type network: str, Network
        :param compressed: Is key compressed or not, default is True
        :type compressed: bool
        :param passphrase: Optional passphrase if imported key is password protected
        :type passphrase: str
        :param is_private: Specify if imported key is private or public. Default is None: derive from provided key
        :type is_private: bool
        
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
        self._hash160 = None
        if not import_key:
            import_key = random.SystemRandom().randint(0, secp256k1_n)
        kf = get_key_format(import_key)
        self.key_format = kf["format"]
        network_name = None
        if network is not None:
            self.network = network
            if not isinstance(network, Network):
                self.network = Network(network)
            network_name = self.network.name
        network = check_network_and_key(import_key, network_name, kf["networks"])
        self.network = Network(network)
        self.isprivate = is_private
        if is_private is None:
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
                if checksum != double_sha256(key)[:4]:
                    raise BKeyError("Invalid checksum, not a valid WIF key")
                found_networks = network_by_value('prefix_wif', key[0:1])
                if not len(found_networks):
                    raise BKeyError("Unrecognised WIF private key, version byte unknown. Versionbyte: %s" % key[0:1])
                if self.network.name not in found_networks:
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
        self.address_obj = Address(self.public_byte, network=self.network)

    def __repr__(self):
        return "<Key(public_hex=%s, network=%s)" % (self.public_hex, self.network.name)

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
        if isinstance(passphrase, str) and sys.version_info > (3,):
            passphrase = passphrase.encode('utf-8')
        addresshash = d[0:4]
        d = d[4:-4]
        key = scrypt.hash(passphrase, addresshash, 16384, 8, 8, 64)
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
        if double_sha256(addr)[0:4] != addresshash:
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
        if isinstance(passphrase, str) and sys.version_info > (3,):
            passphrase = passphrase.encode('utf-8')
        addresshash = double_sha256(addr)[0:4]
        key = scrypt.hash(passphrase, addresshash, 16384, 8, 8, 64)
        derivedhalf1 = key[0:32]
        derivedhalf2 = key[32:64]
        aes = pyaes.AESModeOfOperationECB(derivedhalf2)
        encryptedhalf1 = aes.encrypt(binascii.unhexlify('%0.32x' % (int(privkey[0:32], 16) ^
                                                                    int(binascii.hexlify(derivedhalf1[0:16]), 16))))
        encryptedhalf2 = aes.encrypt(binascii.unhexlify('%0.32x' % (int(privkey[32:64], 16) ^
                                                                    int(binascii.hexlify(derivedhalf1[16:32]), 16))))
        encrypted_privkey = b'\x01\x42' + flagbyte + addresshash + encryptedhalf1 + encryptedhalf2
        encrypted_privkey += double_sha256(encrypted_privkey)[:4]
        return change_base(encrypted_privkey, 256, 58)

    def wif(self, prefix=None):
        """
        Get Private Key in Wallet Import Format, steps:
        # Convert to Binary and add 0x80 hex
        # Calculate Double SHA256 and add as checksum to end of key

        :param prefix: Specify versionbyte prefix in hexstring or bytes. Normally doesn't need to be specified, method uses default prefix from network settings
        :type prefix: str, bytes

        :return str: Base58Check encoded Private Key WIF
        """
        if not self.secret:
            raise KeyError("WIF format not supported for public key")
        if prefix is None:
            versionbyte = self.network.prefix_wif
        else:
            if not isinstance(prefix, (bytes, bytearray)):
                versionbyte = binascii.unhexlify(prefix)
            else:
                versionbyte = prefix
        key = versionbyte + change_base(self.secret, 10, 256, 32)
        if self.compressed:
            key += b'\1'
        key += double_sha256(key)[:4]
        return change_base(key, 256, 58)

    def public(self):
        """
        Get public version of current key. Removes all private information from current key

        :return Key: Public key
        """
        key = deepcopy(self)
        key.isprivate = False
        key.private_byte = None
        key.private_hex = None
        key.secret = None
        return key

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
        Get public key in RIPEMD-160 + SHA256 format
        
        :return bytes:
        """
        if not self._hash160:
            if self.compressed:
                pb = self.public_byte
            else:
                pb = self.public_uncompressed_byte
            self._hash160 = hash160(pb)
        return self._hash160

    def address(self, compressed=None, prefix=None, script_type=None, encoding='base58'):
        """
        Get address derived from public key
        
        :param compressed: Always return compressed address
        :type compressed: bool
        :param prefix: Specify versionbyte prefix in hexstring or bytes. Normally doesn't need to be specified, method uses default prefix from network settings
        :type prefix: str, bytes
        :param script_type: Type of script, i.e. p2sh or p2pkh.
        :type script_type: str
        :param encoding: Address encoding. Default is base58 encoding, for segwit you can specify bech32 encoding
        :type encoding: str
        
        :return str: Base58 encoded address 
        """
        if (self.compressed and compressed is None) or compressed:
            data = self.public_byte
        else:
            data = self.public_uncompressed_byte
        if not self.compressed and encoding == 'bech32':
            raise KeyError("Uncompressed keys are non-standard for segwit/bech32 encoded addresses")
        if not(self.address_obj and self.address_obj.prefix == prefix and self.address_obj.encoding == encoding):
            self.address_obj = Address(data, prefix=prefix, network=self.network, script_type=script_type,
                                       encoding=encoding)
        return self.address_obj.address

    def address_uncompressed(self, prefix=None):
        """
        Get uncompressed address from public key

        :param prefix: Specify versionbyte prefix in hexstring or bytes. Normally doesn't need to be specified, method uses default prefix from network settings
        :type prefix: str, bytes

        :return str: Base58 encoded address 
        """
        return self.address(compressed=False, prefix=prefix)

    def info(self):
        """
        Prints key information to standard output
        
        """

        print(" Network                     %s" % self.network.name)
        print(" Compressed                  %s" % self.compressed)
        if self.secret:
            print("SECRET EXPONENT")
            print(" Private Key (hex)              %s" % self.private_hex)
            print(" Private Key (long)             %s" % self.secret)
            print(" Private Key (wif)              %s" % self.wif())
        else:
            print("PUBLIC KEY ONLY, NO SECRET EXPONENT")
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
        :type network: str, Network
        
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
        :type network: str, Network

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
        :type network: str, Network
        :param key_type: HD BIP32 or normal Private Key. Default is 'bip32'
        :type key_type: str
        :param passphrase: Optional passphrase if imported key is password protected
        :type passphrase: str
        :param compressed: Is key compressed or not, default is True
        :type compressed: bool

        :return HDKey: 
        """

        self.key_format = None
        if (key and not chain) or (not key and chain):
            raise KeyError("Please specify both key and chain, use import_key attribute "
                           "or use simple Key class instead")
        self.compressed = compressed
        self.key = None

        network_name = None
        self.network = None
        if network is not None:
            self.network = network
            if not isinstance(network, Network):
                self.network = Network(network)
            network_name = self.network.name

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
                self.network = Network(check_network_and_key(import_key, network_name, kf["networks"]))
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
            self.key = Key(key, passphrase=passphrase, network=self.network, compressed=compressed)
        self.depth = depth
        self.parent_fingerprint = parent_fingerprint
        self.child_index = child_index
        self.isprivate = isprivate
        if not self.network:
            self.network = Network()
        self.public_byte = self.key.public_byte
        self.public_uncompressed_byte = self.key.public_uncompressed_byte
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
               (self.public_hex, self.wif_public(), self.network.name)

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
        print(" Public Key Hash160          %s" % change_base(self.hash160(), 256, 16))
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
        if self.isprivate:
            print(" Extended Private Key (wif)  %s" % self.wif(is_private=True))
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
            'public_hash160': self.hash160(),
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
            'extended_wif_private': self.wif(is_private=True),
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
        Get key fingerprint: the last for bytes of the hash160 of this key.

        :return bytes:
        """

        return self.hash160()[:4]

    def wif(self, is_private=None, child_index=None, prefix=None, witness_type='legacy', multisig=False):
        """
        Get Extended WIF of current key
        
        :param is_private: Return public or private key
        :type is_private: bool
        :param child_index: Change child index of output WIF key
        :type child_index: int
        :param prefix: Specify version prefix in hexstring or bytes. Normally doesn't need to be specified, method uses default prefix from network settings
        :type prefix: str, bytes
        :param witness_type: Specify witness type, default is legacy. Use 'segwit' for segregated witness.
        :type witness_type: str
        :param multisig: Key is part of a multisignature wallet?
        :type multisig: bool

        :return str: Base58 encoded WIF key 
        """
        rkey = self.private_byte or self.public_byte
        if prefix and not isinstance(prefix, (bytes, bytearray)):
            prefix = binascii.unhexlify(prefix)
        if self.isprivate and is_private:
            if not prefix:
                prefix = self.network.wif_prefix(is_private=True, witness_type=witness_type, multisig=multisig)
            typebyte = b'\x00'
        else:
            if not prefix:
                prefix = self.network.wif_prefix(witness_type=witness_type, multisig=multisig)
            typebyte = b''
            if not is_private:
                rkey = self.public_byte
        if child_index:
            self.child_index = child_index
        raw = prefix + struct.pack('B', self.depth) + self.parent_fingerprint + \
            struct.pack('>L', self.child_index) + self.chain + typebyte + rkey
        chk = double_sha256(raw)[:4]
        ret = raw+chk
        return change_base(ret, 256, 58, 111)

    def wif_public(self, prefix=None, witness_type='legacy', multisig=False):
        """
        Get Extended WIF public key. Wrapper for the wif() method

        :param prefix: Specify version prefix in hexstring or bytes. Normally doesn't need to be specified, method uses default prefix from network settings
        :type prefix: str, bytes
        :param witness_type: Specify witness type, default is legacy. Use 'segwit' for segregated witness.
        :type witness_type: str
        :param multisig: Key is part of a multisignature wallet?
        :type multisig: bool
        
        :return str: Base58 encoded WIF key
        """
        return self.wif(is_private=False, prefix=prefix, witness_type=witness_type, multisig=multisig)

    def wif_private(self, prefix=None, witness_type='legacy', multisig=False):
        """
        Get Extended WIF private key. Wrapper for the wif() method

        :param prefix: Specify version prefix in hexstring or bytes. Normally doesn't need to be specified,
        method uses default prefix from network settings
        :type prefix: str, bytes
        :param witness_type: Specify witness type, default is legacy. Use 'segwit' for segregated witness.
        :type witness_type: str
        :param multisig: Key is part of a multisignature wallet?
        :type multisig: bool

        :return str: Base58 encoded WIF key
        """
        return self.wif(is_private=True, prefix=prefix, witness_type=witness_type, multisig=multisig)

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

    def account_multisig_key(self, account_id=0, witness_type='legacy', set_network=None):
        """
        Derives a multisig account key according to BIP44/45 definition.
        Wrapper for the 'account_key' method.

        :param account_id: Account ID. Leave empty for account 0
        :type account_id: int
        :param witness_type: Specify witness type, default is legacy. Use 'segwit' for segregated witness.
        :type witness_type: str
        :param set_network: Derive account key for different network. Please note this calls the network_change method and changes the network for current key!
        :type set_network: str

        :return HDKey:
        """
        script_type = 0
        if self.key_type == 'single':
            return self
        if witness_type == 'legacy':
            purpose = 45
        elif witness_type == 'p2sh-segwit':
            purpose = 48
            script_type = 1
        elif witness_type == 'segwit':
            purpose = 48
            script_type = 2
        else:
            raise KeyError("Unknown witness type %s" % witness_type)
        path = "%s/%d'" % ('m' if self.isprivate else 'M', purpose)
        if purpose == 45:
            return self.subkey_for_path(path)
        elif purpose == 48:
            path += "/%d'/%d'/%d'" % (self.network.bip44_cointype, account_id, script_type)
            return self.subkey_for_path(path)
        else:
            raise KeyError("Unknown purpose %d, cannot determine wallet public cosigner key" % purpose)

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
            network = self.network.name
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
            raise BKeyError("Key cannot be greater than secp256k1_n. Try another index number.")
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
            network = self.network.name
        if index > 0x80000000:
            raise BKeyError("Cannot derive hardened key from public private key. Index must be less than 0x80000000")
        data = self.public_byte + struct.pack('>L', index)
        key, chain = self._key_derivation(data)
        key = change_base(key, 256, 10)
        if key > secp256k1_n:
            raise BKeyError("Key cannot be greater than secp256k1_n. Try another index number.")

        x, y = self.key.public_point()
        ki = ec_point(key) + ecdsa.ellipticcurve.Point(curve, x, y, secp256k1_n)

        # if change_base(Ki.y(), 16, 10) % 2:
        if ki.y() % 2:
            prefix = '03'
        else:
            prefix = '02'
        xhex = change_base(ki.x(), 10, 16, 64)
        secret = binascii.unhexlify(prefix + xhex)
        return HDKey(key=secret, chain=chain, depth=self.depth+1, parent_fingerprint=self.fingerprint(),
                     child_index=index, isprivate=False, network=network)

    def public(self):
        """
        Public version of current private key. Strips all private information from HDKey object, returns deepcopy
        version of current object

        :return HDKey:
        """

        hdkey = deepcopy(self)
        hdkey.isprivate = False
        hdkey.secret = None
        hdkey.private_hex = None
        hdkey.private_byte = None
        hdkey.key_hex = hdkey.public_hex
        hdkey.key = self.key.public()
        return hdkey

    def hash160(self):
        """
        Get RIPEMD-160 + SHA256 hash of public key

        :return bytes:
        """

        return self.key.hash160()
