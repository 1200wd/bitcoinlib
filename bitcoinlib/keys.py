# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Public key cryptography and Hierarchical Deterministic Key Management
#    © 2016 - 2019 January - 1200 Web Development <http://1200wd.com/>
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
import sys
import os
import hmac
import numbers
import random
import warnings
from copy import deepcopy
import collections
import json
import pyaes

SCRYPT_ERROR = None
USING_MODULE_SCRYPT = os.getenv("USING_MODULE_SCRYPT") not in ["false", "False", "0", "FALSE"]
try:
    if USING_MODULE_SCRYPT != False:
        import scrypt
        USING_MODULE_SCRYPT = True
except ImportError as SCRYPT_ERROR:
    pass
if 'scrypt' not in sys.modules:
    import pyscrypt as scrypt
    USING_MODULE_SCRYPT = False

from bitcoinlib.main import *
from bitcoinlib.networks import Network, DEFAULT_NETWORK, network_by_value, wif_prefix_search
from bitcoinlib.config.secp256k1 import *
from bitcoinlib.encoding import *
from bitcoinlib.mnemonic import Mnemonic

rfc6979_warning_given = False
if USE_FASTECDSA:
    from fastecdsa import _ecdsa
    from fastecdsa.util import RFC6979
    from fastecdsa.curve import secp256k1 as fastecdsa_secp256k1
    from fastecdsa import keys as fastecdsa_keys
    from fastecdsa import point as fastecdsa_point
else:
    import ecdsa
    secp256k1_curve = ecdsa.ellipticcurve.CurveFp(secp256k1_p, secp256k1_a, secp256k1_b)
    secp256k1_generator = ecdsa.ellipticcurve.Point(secp256k1_curve, secp256k1_Gx, secp256k1_Gy, secp256k1_n)


_logger = logging.getLogger(__name__)

if not USING_MODULE_SCRYPT:
    if 'scrypt_error' not in locals():
        SCRYPT_ERROR = 'unknown'
    _logger.warning("Error when trying to import scrypt module", SCRYPT_ERROR)


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
    
    A BKeyError will be raised if key does not corresponds with network or if multiple network are found.
    
    :param key: Key in any format recognized by get_key_format function
    :type key: str, int, bytes, bytearray
    :param network: Optional network. Method raises BKeyError if keys belongs to another network
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
            raise BKeyError("Specified key %s is from different network then specified: %s" % (kf_networks, network))
        elif network is None and len(kf_networks) == 1:
            return kf_networks[0]
        elif network is None and len(kf_networks) > 1:
            if default_network in kf_networks:
                return default_network
            elif 'testnet' in kf_networks:
                return 'testnet'
            raise BKeyError("Could not determine network of specified key, multiple networks found: %s" % kf_networks)
    if network is None:
        return default_network
    else:
        return network


def get_key_format(key, is_private=None):
    """
    Determines the type (private or public), format and network key.
    
    This method does not validate if a key is valid.

    :param key: Any private or public key
    :type key: str, int, bytes, bytearray
    :param is_private: Is key private or not?
    :type is_private: bool
    
    :return dict: Dictionary with format, network and is_private
    """
    if not key:
        raise BKeyError("Key empty, please specify a valid key")
    key_format = ""
    networks = None
    script_types = []
    witness_types = ['legacy']
    multisig = [False]

    if isinstance(key, (bytes, bytearray)) and len(key) in [128, 130]:
        key = to_hexstring(key)

    if not (is_private is None or isinstance(is_private, bool)):
        raise BKeyError("Attribute 'is_private' must be False or True")
    elif isinstance(key, numbers.Number):
        key_format = 'decimal'
        is_private = True
    elif isinstance(key, (bytes, bytearray)) and len(key) in [33, 65] and key[:1] in [b'\2', b'\3']:
        key_format = 'bin_compressed'
        is_private = False
    elif isinstance(key, (bytes, bytearray)) and (len(key) in [33, 65] and key[:1] == b'\4'):
        key_format = 'bin'
        is_private = False
    elif isinstance(key, (bytes, bytearray)) and len(key) == 33 and key[-1:] == b'\1':
        key_format = 'bin_compressed'
        is_private = True
    elif isinstance(key, (bytes, bytearray)) and len(key) == 32:
        key_format = 'bin'
        is_private = True
    elif len(key) == 130 and key[:2] == '04' and not is_private:
        key_format = 'public_uncompressed'
        is_private = False
    elif len(key) == 128:
        key_format = 'hex'
        if is_private is None:
            is_private = True
    elif len(key) == 66 and key[:2] in ['02', '03'] and not is_private:
        key_format = 'public'
        is_private = False
    elif len(key) == 64:
        key_format = 'hex'
        if is_private is None:
            is_private = True
    elif len(key) == 66 and key[-2:] in ['01'] and not(is_private is False):
        key_format = 'hex_compressed'
        is_private = True
    elif len(key) == 58 and key[:2] == '6P':
        key_format = 'wif_protected'
        is_private = True
    else:
        try:
            key_hex = change_base(key, 58, 16)
            networks = network_by_value('prefix_wif', key_hex[:2])
            # TODO: First search for longer prefix, to avoid wrong matches
            if networks:
                if key_hex[-10:-8] == '01':
                    key_format = 'wif_compressed'
                else:
                    key_format = 'wif'
                is_private = True
            else:
                prefix_data = wif_prefix_search(key_hex[:8])
                if prefix_data:
                    networks = list(set([n['network'] for n in prefix_data]))
                    if is_private is None and len(set([n['is_private'] for n in prefix_data])) > 1:
                        raise BKeyError("Cannot determine if key is private or public, please specify is_private "
                                        "attribute")
                    is_private = prefix_data[0]['is_private']
                    script_types = list(set([n['script_type'] for n in prefix_data]))
                    witness_types = list(set([n['witness_type'] for n in prefix_data]))
                    multisig = list(set([n['multisig'] for n in prefix_data]))
                    key_format = 'hdkey_public'
                    if is_private:
                        key_format = 'hdkey_private'
        except (TypeError, EncodingError):
            pass
    if not key_format:
        try:
            int(key)
            if 70 < len(key) < 78:
                key_format = 'decimal'
                is_private = True
        except (TypeError, ValueError):
            pass
    if not key_format:
        try:
            da = deserialize_address(key)
            key_format = 'address'
            networks = da['network']
            is_private = False
            script_types = da['script_type']
        except (EncodingError, TypeError):
            pass
    if not key_format:
        raise BKeyError("Unrecognised key format")
    else:
        return {
            "format": key_format,
            "networks": networks,
            "is_private": is_private,
            "script_types": script_types,
            "witness_types": witness_types,
            "multisig": multisig
        }


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
    :param network: Specify network filter, i.e.: bitcoin, testnet, litecoin, etc. Wil trigger check if address is valid for this network
    :type network: str

    :return dict: with information about this address
    """

    if encoding is not None and encoding not in SUPPORTED_ADDRESS_ENCODINGS:
        raise BKeyError("Encoding '%s' not found in supported address encodings %s" %
                        (encoding, SUPPORTED_ADDRESS_ENCODINGS))
    if encoding is None or encoding == 'base58':
        address_bytes = change_base(address, 58, 256, 25)
        if address_bytes:
            check = address_bytes[-4:]
            key_hash = address_bytes[:-4]
            checksum = double_sha256(key_hash)[0:4]
            if check != checksum and encoding == 'base58':
                raise BKeyError("Invalid address %s, checksum incorrect" % address)
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
                        raise BKeyError("Network %s not found in extracted networks: %s" % (network, networks))
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
                raise BKeyError("Unknown script type for address %s. Invalid length %d" %
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
    if isinstance(prefix, TYPE_TEXT) and to_encoding == 'base58':
        prefix = to_hexstring(prefix)
    return pubkeyhash_to_addr(pkh, prefix=prefix, encoding=to_encoding)


def path_expand(path, path_template=None, level_offset=None, account_id=0, cosigner_id=0, purpose=44,
                address_index=0, change=0, witness_type=DEFAULT_WITNESS_TYPE, multisig=False, network=DEFAULT_NETWORK):
    """
    Create key path. Specify part of key path and path settings

    :param path: Part of path, for example [0, 2] for change=0 and address_index=2
    :type path: list, str
    :param path_template: Template for path to create, default is BIP 44: ["m", "purpose'", "coin_type'",  "account'", "change", "address_index"]
    :type path_template: list
    :param level_offset: Just create part of path. For example -2 means create path with the last 2 items (change, address_index) or 1 will return the master key 'm'
    :type level_offset: int
    :param account_id: Account ID
    :type account_id: int
    :param cosigner_id: ID of cosigner
    :type cosigner_id: int
    :param purpose: Purpose value
    :type purpose: int
    :param address_index: Index of key, normally provided to 'path' argument
    :type address_index: int
    :param change: Change key = 1 or normal = 0, normally provided to 'path' argument
    :type change: int
    :param witness_type: Witness type for paths with a script ID, specify 'p2sh-segwit' or 'segwit'
    :type witness_type: str
    :param multisig: Is path for multisig keys?
    :type multisig: bool
    :param network: Network name. Leave empty for default network
    :type network: str

    :return list:
    """
    if isinstance(path, TYPE_TEXT):
        path = path.split('/')
    if not path_template:
        ks = [k for k in WALLET_KEY_STRUCTURES if
              k['witness_type'] == witness_type and k['multisig'] == multisig and k['purpose'] is not None]
        if ks:
            purpose = ks[0]['purpose']
            path_template = ks[0]['key_path']
    if not isinstance(path, list):
        raise BKeyError("Please provide path as list with at least 1 item. Wallet key path format is %s" %
                        path_template)
    if len(path) > len(path_template):
        raise BKeyError("Invalid path provided. Path should be shorter than %d items. "
                        "Wallet key path format is %s" % (len(path_template), path_template))

    # If path doesn't start with m/M complement path
    poppath = deepcopy(path)
    if path == [] or path[0] not in ['m', 'M']:
        wallet_key_path = path_template
        if level_offset:
            wallet_key_path = wallet_key_path[:level_offset]
        new_path = []
        for pi in wallet_key_path[::-1]:
            if not len(poppath):
                new_path.append(pi)
            else:
                new_path.append(poppath.pop())
        new_path = new_path[::-1]
    else:
        new_path = deepcopy(path)

    # Replace variable names in path with corresponding values
    # network, account_id, _ = self._get_account_defaults(network, account_id)
    script_type_id = 1 if witness_type == 'p2sh-segwit' else 2
    var_defaults = {
        'network': network,
        'account': account_id,
        'purpose': purpose,
        'coin_type': Network(network).bip44_cointype,
        'script_type': script_type_id,
        'cosigner_index': cosigner_id,
        'change': change,
        'address_index': address_index
    }
    npath = new_path
    for i, pi in enumerate(new_path):
        if not isinstance(pi, TYPE_TEXT):
            pi = str(pi)
        if pi in "mM":
            continue
        hardened = False
        varname = pi
        if pi[-1:] == "'" or (pi[-1:] in "HhPp" and pi[:-1].isdigit()):
            varname = pi[:-1]
            hardened = True
        if path_template[i][-1:] == "'":
            hardened = True
        new_varname = (str(var_defaults[varname]) if varname in var_defaults else varname)
        if new_varname == varname and not new_varname.isdigit():
            raise BKeyError("Variable %s not found in Key structure definitions in main.py" % varname)
        if varname == 'address_index' and address_index is None:
            raise BKeyError("Please provide value for 'address_index' or 'path'")
        npath[i] = new_varname + ("'" if hardened else '')
    if "None'" in npath or "None" in npath:
        raise BKeyError("Could not parse all variables in path %s" % npath)
    return npath


class Address(object):
    """
    Class to store, convert and analyse various address types as representation of public keys or scripts hashes
    """

    @classmethod
    def import_address(cls, address, compressed=None, encoding=None, depth=None, change=None,
                       address_index=None, network=None, network_overrides=None):
        """
        Import an address to the Address class. Specify network if available, otherwise it will be
        derived form the address.

        :param address: Address to import
        :type address: str
        :param compressed: Is key compressed or not, default is None
        :type compressed: bool
        :param encoding: Address encoding. Default is base58 encoding, for native segwit addresses specify bech32 encoding. Leave empty to derive from address
        :type encoding: str
        :param depth: Level of depth in BIP32 key path
        :type depth: int
        :param change: Use 0 for normal address/key, and 1 for change address (for returned/change payments)
        :type change: int
        :param address_index: Index of address. Used in BIP32 key paths
        :type address_index: int
        :param network: Specify network filter, i.e.: bitcoin, testnet, litecoin, etc. Wil trigger check if address is valid for this network
        :type network: str
        :param network_overrides: Override network settings for specific prefixes, i.e.: {"prefix_address_p2sh": "32"}. Used by settings in providers.json
        :type network_overrides: dict

        :return Address:
        """
        if encoding is None and address[:3].split("1")[0] in ENCODING_BECH32_PREFIXES:
            encoding = 'bech32'
        addr_dict = deserialize_address(address, encoding=encoding, network=network)
        public_key_hash_bytes = addr_dict['public_key_hash_bytes']
        prefix = addr_dict['prefix']
        if network is None:
            network = addr_dict['network']
        script_type = addr_dict['script_type']
        return Address(hashed_data=public_key_hash_bytes,  prefix=prefix, script_type=script_type,
                       compressed=compressed, encoding=addr_dict['encoding'], depth=depth, change=change,
                       address_index=address_index, network=network, network_overrides=network_overrides)

    def __init__(self, data='', hashed_data='', prefix=None, script_type=None,
                 compressed=None, encoding=None, witness_type=None, depth=None, change=None,
                 address_index=None, network=DEFAULT_NETWORK, network_overrides=None):
        """
        Initialize an Address object. Specify a public key, redeemscript or a hash.

        :param data: Public key, redeem script or other type of script.
        :type data: str, bytes
        :param hashed_data: Hash of a public key or script. Will be generated if 'data' parameter is provided
        :type hashed_data: str, bytes
        :param prefix: Address prefix. Use default network / script_type prefix if not provided
        :type prefix: str, bytes
        :param script_type: Type of script, i.e. p2sh or p2pkh.
        :type script_type: str
        :param encoding: Address encoding. Default is base58 encoding, for native segwit addresses specify bech32 encoding
        :type encoding: str
        :param witness_type: Specify 'legacy', 'segwit' or 'p2sh-segwit'. Legacy for old-style bitcoin addresses, segwit for native segwit addresses and p2sh-segwit for segwit embedded in a p2sh script. Leave empty to derive automatically from script type if possible
        :type witness_type: str
        :param network: Bitcoin, testnet, litecoin or other network
        :type network: str, Network
        :param network_overrides: Override network settings for specific prefixes, i.e.: {"prefix_address_p2sh": "32"}. Used by settings in providers.json
        :type network_overrides: dict

        """
        self.network = network
        if not (data or hashed_data):
            raise BKeyError("Please specify data (public key or script) or hashed_data argument")
        if not isinstance(network, Network):
            self.network = Network(network)
        self.data_bytes = to_bytes(data)
        self.data = to_hexstring(data)
        self.script_type = script_type
        self.encoding = encoding
        self.compressed = compressed
        if witness_type is None:
            if self.script_type in ['p2wpkh', 'p2wsh']:
                witness_type = 'segwit'
            elif self.script_type in ['p2sh_p2wpkh', 'p2sh_p2wsh']:
                witness_type = 'p2sh-segwit'
        self.witness_type = witness_type
        self.depth = depth
        self.change = change
        self.address_index = address_index

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
            if self.script_type is None:
                self.script_type = 'p2pkh'
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
            raise BKeyError("Encoding %s not supported" % self.encoding)
        self.address = pubkeyhash_to_addr(bytearray(self.hash_bytes), prefix=self.prefix, encoding=self.encoding)
        self.address_orig = None
        provider_prefix = None
        if network_overrides and 'prefix_address_p2sh' in network_overrides and self.script_type == 'p2sh':
            provider_prefix = network_overrides['prefix_address_p2sh']
        self.address_orig = self.address
        if provider_prefix:
            self.address = addr_convert(self.address, provider_prefix)

    def __repr__(self):
        return "<Address(address=%s)>" % self.address

    def as_dict(self):
        """
        Get current Address class as dictionary. Byte values are represented by hexadecimal strings

        :return dict:
        """
        addr_dict = deepcopy(self.__dict__)
        del(addr_dict['data_bytes'])
        del(addr_dict['hash_bytes'])
        if isinstance(addr_dict['network'], Network):
            addr_dict['network'] = addr_dict['network'].name
        addr_dict['redeemscript'] = to_hexstring(addr_dict['redeemscript'])
        addr_dict['prefix'] = to_hexstring(addr_dict['prefix'])
        return addr_dict

    def as_json(self):
        """
        Get current key as json formatted string

        :return str:
        """
        adict = self.as_dict()
        return json.dumps(adict, indent=4)

    def with_prefix(self, prefix):
        """
        Convert address using another prefix

        :param prefix: Address prefix
        :type prefix: str, bytes

        :return str: Converted address
        """
        return addr_convert(self.address, prefix)


class Key(object):
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
            import_key = random.SystemRandom().randint(1, secp256k1_n - 1)
            self.key_format = 'decimal'
            networks_extracted = network
            assert is_private is True or is_private is None
            self.is_private = True  # Ignore provided attribute
        else:
            kf = get_key_format(import_key)
            if kf['format'] == 'address':
                raise BKeyError("Can not create Key object from address")
            self.key_format = kf["format"]
            networks_extracted = kf["networks"]
            self.is_private = is_private
            if is_private is None:
                if kf['is_private']:
                    self.is_private = True
                elif kf['is_private'] is None:
                    raise BKeyError("Could not determine if key is private or public")
                else:
                    self.is_private = False
        network_name = None
        if network is not None:
            self.network = network
            if not isinstance(network, Network):
                self.network = Network(network)
            network_name = self.network.name
        network = check_network_and_key(import_key, network_name, networks_extracted)
        self.network = Network(network)

        if self.key_format == "wif_protected":
            # TODO: return key as byte (?)
            # FIXME: Key format is changed so old 'wif_protected' is forgotten
            import_key, self.key_format = self._bip38_decrypt(import_key, passphrase)

        if not self.is_private:
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
                ys = pow(x, 3, secp256k1_p) + 7 % secp256k1_p
                y = mod_sqrt(ys)
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
        elif self.is_private and self.key_format == 'decimal':
            self.secret = import_key
            self.private_hex = change_base(import_key, 10, 16, 64)
            self.private_byte = binascii.unhexlify(self.private_hex)
        elif self.is_private:
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
            elif self.is_private and self.key_format in ['wif', 'wif_compressed']:
                # Check and remove Checksum, prefix and postfix tags
                key = change_base(import_key, 58, 256)
                checksum = key[-4:]
                key = key[:-4]
                if checksum != double_sha256(key)[:4]:
                    raise BKeyError("Invalid checksum, not a valid WIF key")
                found_networks = network_by_value('prefix_wif', key[0:1])
                if not len(found_networks):
                    raise BKeyError("Unrecognised WIF private key, version byte unknown. Versionbyte: %s" % key[0:1])
                self._wif = import_key
                self._wif_prefix = key[0:1]
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
                raise BKeyError("Unknown key format %s" % self.key_format)

            if not (key_byte or key_hex):
                raise BKeyError("Cannot format key in hex or byte format")
            self.private_hex = key_hex
            self.private_byte = key_byte
            self.secret = int(key_hex, 16)
        else:
            raise BKeyError("Cannot import key. Public key format unknown")

        if self.is_private and not (self.public_byte or self.public_hex):
            if not self.is_private:
                raise BKeyError("Private key has no known secret number")
            p = ec_point(self.secret)
            if USE_FASTECDSA:
                point_x = p.x
                point_y = p.y
            else:
                point_x = p.x()
                point_y = p.y()
            self._x = change_base(point_x, 10, 16, 64)
            self._y = change_base(point_y, 10, 16, 64)
            if point_y % 2:
                prefix = '03'
            else:
                prefix = '02'

            self.public_compressed_hex = prefix + self._x
            self.public_uncompressed_hex = '04' + self._x + self._y
            self.public_hex = self.public_compressed_hex if self.compressed else self.public_uncompressed_hex

            self.public_byte = binascii.unhexlify(self.public_hex)
            self.public_compressed_byte = binascii.unhexlify(self.public_compressed_hex)
            self.public_uncompressed_byte = binascii.unhexlify(self.public_uncompressed_hex)
        self._address_obj = None
        self._wif = None
        self._wif_prefix = None

    def __repr__(self):
        return "<Key(public_hex=%s, network=%s)>" % (self.public_hex, self.network.name)

    def __str__(self):
        if self.is_private:
            return self.private_hex
        else:
            return self.public_hex

    def __eq__(self, other):
        if other is None:
            return False
        if self.is_private and other.is_private:
            return self.private_hex == other.private_hex
        else:
            return self.public_hex == other.public_hex

    def __int__(self):
        if self.is_private:
            return self.secret
        else:
            return None

    def as_dict(self, include_private=False):
        """
        Get current Key class as dictionary. Byte values are represented by hexadecimal strings.

        :param include_private: Include private key information in dictionary
        :type include_private: bool

        :return collections.OrderedDict:
        """

        key_dict = collections.OrderedDict()
        key_dict['network'] = self.network.name
        key_dict['key_format'] = self.key_format
        key_dict['compressed'] = self.compressed
        key_dict['is_private'] = self.is_private
        if include_private:
            key_dict['private_hex'] = self.private_hex
            key_dict['secret'] = self.secret
            key_dict['wif'] = self.wif()
        key_dict['public_hex'] = self.public_hex
        key_dict['public_uncompressed_hex'] = self.public_uncompressed_hex
        key_dict['hash160'] = to_hexstring(self.hash160)
        key_dict['address'] = self.address()
        x, y = self.public_point()
        key_dict['point_x'] = x
        key_dict['point_y'] = y
        return key_dict

    def as_json(self, include_private=False):
        """
        Get current key as json formatted string

        :param include_private: Include private key information in dictionary
        :type include_private: bool

        :return str:
        """
        return json.dumps(self.as_dict(include_private=include_private), indent=4)

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
            raise BKeyError("WIF format not supported for public key")
        if prefix is None:
            versionbyte = self.network.prefix_wif
        else:
            if not isinstance(prefix, (bytes, bytearray)):
                versionbyte = binascii.unhexlify(prefix)
            else:
                versionbyte = prefix

        if self._wif and self._wif_prefix == versionbyte:
            return self._wif

        key = versionbyte + change_base(self.secret, 10, 256, 32)
        if self.compressed:
            key += b'\1'
        key += double_sha256(key)[:4]
        self._wif = change_base(key, 256, 58)
        self._wif_prefix = versionbyte
        return self._wif

    def public(self):
        """
        Get public version of current key. Removes all private information from current key

        :return Key: Public key
        """
        key = deepcopy(self)
        key.is_private = False
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

    @property
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

    @property
    def address_obj(self):
        """
        Get address object property. Create standard address object if not defined already.

        :return Address:
        """
        if not self._address_obj:
            self.address()
        return self._address_obj

    def address(self, compressed=None, prefix=None, script_type=None, encoding=None):
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
            self.compressed = True
        else:
            data = self.public_uncompressed_byte
            self.compressed = False
        if encoding is None:
            if self._address_obj:
                encoding = self._address_obj.encoding
            else:
                encoding = 'base58'
        if not self.compressed and encoding == 'bech32':
            raise BKeyError("Uncompressed keys are non-standard for segwit/bech32 encoded addresses")
        if self._address_obj and script_type is None:
            script_type = self._address_obj.script_type
        if not(self._address_obj and self._address_obj.prefix == prefix and self._address_obj.encoding == encoding):
            self._address_obj = Address(data, prefix=prefix, network=self.network, script_type=script_type,
                                        encoding=encoding, compressed=compressed)
        return self._address_obj.address

    def address_uncompressed(self, prefix=None, script_type=None, encoding=None):
        """
        Get uncompressed address from public key

        :param prefix: Specify versionbyte prefix in hexstring or bytes. Normally doesn't need to be specified, method uses default prefix from network settings
        :type prefix: str, bytes
        :param script_type: Type of script, i.e. p2sh or p2pkh.
        :type script_type: str
        :param encoding: Address encoding. Default is base58 encoding, for segwit you can specify bech32 encoding
        :type encoding: str

        :return str: Base58 encoded address
        """
        return self.address(compressed=False, prefix=prefix, script_type=script_type, encoding=encoding)

    def info(self):
        """
        Prints key information to standard output

        """

        print("KEY INFO")
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
        print(" Public Key Hash160          %s" % to_hexstring(self.hash160))
        print(" Address (b58)               %s" % self.address())
        point_x, point_y = self.public_point()
        print(" Point x                     %s" % point_x)
        print(" Point y                     %s" % point_y)


class HDKey(Key):
    """
    Class for Hierarchical Deterministic keys as defined in BIP0032

    Besides a private or public key a HD Key has a chain code, allowing to create
    a structure of related keys.

    The structure and key-path are defined in BIP0043 and BIP0044.
    """

    @staticmethod
    def from_seed(import_seed, key_type='bip32', network=DEFAULT_NETWORK, compressed=True,
                  encoding=None, witness_type=DEFAULT_WITNESS_TYPE, multisig=False):
        """
        Used by class init function, import key from seed

        :param import_seed: Private key seed as bytes or hexstring
        :type import_seed: str, bytes
        :param key_type: Specify type of key, default is BIP32
        :type key_type: str
        :param network: Network to use
        :type network: str, Network
        :param compressed: Is key compressed or not, default is True
        :type compressed: bool
        :param encoding: Encoding used for address, i.e.: base58 or bech32. Default is base58 or derive from witness type
        :type encoding: str
        :param witness_type: Witness type used when creating scripts: legacy, p2sh-segwit or segwit.
        :type witness_type: str
        :param multisig: Specify if key is part of multisig wallet, used when creating key representations such as WIF and addreses
        :type multisig: bool

        :return HDKey:
        """
        seed = to_bytes(import_seed)
        i = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
        key = i[:32]
        chain = i[32:]
        key_int = change_base(key, 256, 10)
        if key_int >= secp256k1_n:
            raise BKeyError("Key int value cannot be greater than secp256k1_n")
        return HDKey(key=key, chain=chain, network=network, key_type=key_type, compressed=compressed,
                     encoding=encoding, witness_type=witness_type, multisig=multisig)

    @staticmethod
    def from_passphrase(passphrase, password='', network=DEFAULT_NETWORK, compressed=True,
                        encoding=None, witness_type=DEFAULT_WITNESS_TYPE, multisig=False):
        """
        Create key from Mnemonic passphrase

        :param passphrase: Mnemonic passphrase, list of words as string seperated with a space character
        :type passphrase: str
        :param password: Password to protect passphrase
        :type password: str
        :param network: Network to use
        :type network: str, Network
        :param compressed: Is key compressed or not, default is True
        :type compressed: bool
        :param encoding: Encoding used for address, i.e.: base58 or bech32. Default is base58 or derive from witness type
        :type encoding: str
        :param witness_type: Witness type used when creating scripts: legacy, p2sh-segwit or segwit.
        :type witness_type: str
        :param multisig: Specify if key is part of multisig wallet, used when creating key representations such as WIF and addreses
        :type multisig: bool

        :return HDKey:
        """
        return HDKey.from_seed(Mnemonic().to_seed(passphrase, password), network=network, compressed=compressed,
                               encoding=encoding, witness_type=witness_type, multisig=multisig)

    def __init__(self, import_key=None, key=None, chain=None, depth=0, parent_fingerprint=b'\0\0\0\0',
                 child_index=0, is_private=True, network=None, key_type='bip32', passphrase='', compressed=True,
                 encoding=None, witness_type=None, multisig=False):
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
        :param is_private: True for private, False for public key. Default is True
        :type is_private: bool
        :param network: Network name. Derived from import_key if possible
        :type network: str, Network
        :param key_type: HD BIP32 or normal Private Key. Default is 'bip32'
        :type key_type: str
        :param passphrase: Optional passphrase if imported key is password protected
        :type passphrase: str
        :param compressed: Is key compressed or not, default is True
        :type compressed: bool
        :param encoding: Encoding used for address, i.e.: base58 or bech32. Default is base58 or derive from witness type
        :type encoding: str
        :param witness_type: Witness type used when creating scripts: legacy, p2sh-segwit or segwit.
        :type witness_type: str
        :param multisig: Specify if key is part of multisig wallet, used when creating key representations such as WIF and addreses
        :type multisig: bool

        :return HDKey:
        """

        if not encoding and witness_type:
            encoding = get_encoding_from_witness(witness_type)
        self.script_type = script_type_default(witness_type, multisig)

        if (key and not chain) or (not key and chain):
            raise BKeyError("Please specify both key and chain, use import_key attribute "
                            "or use simple Key class instead")
        if not (key and chain):
            if not import_key:
                # Generate new Master Key
                # seedbits = random.SystemRandom().randint(512)
                # seed = change_base(str(seedbits), 10, 256, 64)
                seed = os.urandom(64)
                key, chain = self._key_derivation(seed)
            elif isinstance(import_key, (bytearray, bytes if sys.version > '3' else bytearray)) \
                    and len(import_key) == 64:
                key = import_key[:32]
                chain = import_key[32:]
            elif isinstance(import_key, Key):
                if not import_key.compressed:
                    _logger.warning("Uncompressed private keys are not standard for BIP32 keys, use at your own risk!")
                    compressed = False
                chain = b'\0' * 32
                key = import_key.private_byte
                key_type = 'private'
            else:
                kf = get_key_format(import_key)
                if kf['format'] == 'address':
                    raise BKeyError("Can not create HDKey object from address")
                if len(kf['script_types']) == 1:
                    self.script_type = kf['script_types'][0]
                if len(kf['witness_types']) == 1 and not witness_type:
                    witness_type = kf['witness_types'][0]
                    encoding = get_encoding_from_witness(witness_type)
                if len(kf['multisig']) == 1:
                    multisig = kf['multisig'][0]
                network = Network(check_network_and_key(import_key, network, kf["networks"]))
                if kf['format'] in ['hdkey_private', 'hdkey_public']:
                    bkey = change_base(import_key, 58, 256)
                    # Derive key, chain, depth, child_index and fingerprint part from extended key WIF
                    if ord(bkey[45:46]):
                        is_private = False
                        key = bkey[45:78]
                    else:
                        key = bkey[46:78]
                    depth = ord(bkey[4:5])
                    parent_fingerprint = bkey[5:9]
                    child_index = int(change_base(bkey[9:13], 256, 10))
                    chain = bkey[13:45]
                    # chk = bkey[78:82]
                elif kf['format'] == 'address':
                    da = deserialize_address(import_key)
                    key = da['public_key_hash']
                    network = Network(da['network'])
                    is_private = False
                else:
                    key = import_key
                    chain = b'\0' * 32
                    key_type = 'private'

        if witness_type is None:
            witness_type = DEFAULT_WITNESS_TYPE

        Key.__init__(self, key, network, compressed, passphrase, is_private)

        self.encoding = encoding
        self.witness_type = witness_type
        self.multisig = multisig

        self.chain = chain
        self.depth = depth
        self.parent_fingerprint = parent_fingerprint
        self.child_index = child_index
        self.key_type = key_type

    def __repr__(self):
        return "<HDKey(public_hex=%s, wif_public=%s, network=%s)>" % \
               (self.public_hex, self.wif_public(), self.network.name)

    def info(self):
        """
        Prints key information to standard output

        """
        super(HDKey, self).info()

        print("EXTENDED KEY")
        print(" Key Type                    %s" % self.key_type)
        print(" Chain code (hex)            %s" % change_base(self.chain, 256, 16))
        print(" Child Index                 %s" % self.child_index)
        print(" Parent Fingerprint (hex)    %s" % change_base(self.parent_fingerprint, 256, 16))
        print(" Depth                       %s" % self.depth)
        print(" Extended Public Key (wif)   %s" % self.wif_public())
        print(" Witness type                %s" % self.witness_type)
        print(" Script type                 %s" % self.script_type)
        print(" Multisig                    %s" % self.multisig)
        if self.is_private:
            print(" Extended Private Key (wif)  %s" % self.wif(is_private=True))
        print("\n")

    def as_dict(self, include_private=False):
        """
        Get current HDKey class as dictionary. Byte values are represented by hexadecimal strings.

        :param include_private: Include private key information in dictionary
        :type include_private: bool

        :return collections.OrderedDict:
        """

        key_dict = super(HDKey, self).as_dict()
        if include_private:
            key_dict['fingerprint'] = to_hexstring(self.fingerprint)
            key_dict['chain_code'] = to_hexstring(self.chain)
            key_dict['fingerprint_parent'] = to_hexstring(self.parent_fingerprint)
        key_dict['child_index'] = self.child_index
        key_dict['depth'] = self.depth
        key_dict['extended_wif_public'] = self.wif_public()
        if include_private:
            key_dict['extended_wif_private'] = self.wif(is_private=True)
        return key_dict

    def as_json(self, include_private=False):
        """
        Get current key as json formatted string

        :param include_private: Include private key information in dictionary
        :type include_private: bool
        
        :return str:
        """
        return json.dumps(self.as_dict(include_private=include_private), indent=4)

    def _key_derivation(self, seed):
        """
        Derive extended private key with key and chain part from seed

        :param seed:
        :type seed: bytes

        :return tuple: key and chain bytes
        """
        chain = hasattr(self, 'chain') and self.chain or b"Bitcoin seed"
        i = hmac.new(chain, seed, hashlib.sha512).digest()
        key = i[:32]
        chain = i[32:]
        key_int = change_base(key, 256, 10)
        if key_int >= secp256k1_n:
            raise BKeyError("Key cannot be greater than secp256k1_n. Try another index number.")
        return key, chain

    @property
    def fingerprint(self):
        """
        Get key fingerprint: the last for bytes of the hash160 of this key.

        :return bytes:
        """

        return self.hash160[:4]

    def wif(self, is_private=None, child_index=None, prefix=None, witness_type=None, multisig=None):
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

        if not witness_type:
            witness_type = DEFAULT_WITNESS_TYPE if not self.witness_type else self.witness_type
        if not multisig:
            multisig = False if not self.multisig else self.multisig

        rkey = self.private_byte or self.public_byte
        if prefix and not isinstance(prefix, (bytes, bytearray)):
            prefix = binascii.unhexlify(prefix)
        if self.is_private and is_private:
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

    def wif_key(self, prefix=None):
        """
        Get WIF of Key object. Call to parent object Key.wif()

        :param prefix: Specify versionbyte prefix in hexstring or bytes. Normally doesn't need to be specified, method uses default prefix from network settings
        :type prefix: str, bytes
        :return str: Base58Check encoded Private Key WIF
        """
        return super(HDKey, self).wif(prefix)

    def wif_public(self, prefix=None, witness_type=None, multisig=None):
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

    def wif_private(self, prefix=None, witness_type=None, multisig=None):
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

    def address(self, compressed=None, prefix=None, script_type=None, encoding=None):
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
        if compressed is None:
            compressed = self.compressed
        if script_type is None:
            script_type = self.script_type
        if encoding is None:
            encoding = self.encoding
        return super(HDKey, self).address(compressed, prefix, script_type, encoding)

    def subkey_for_path(self, path, network=None):
        """
        Determine subkey for HD Key for given path.
        Path format: m / purpose' / coin_type' / account' / change / address_index
        Example: m/44'/0'/0'/0/2
        See BIP0044 bitcoin proposal for more explanation.

        :param path: BIP0044 key path
        :type path: str, list
        :param network: Network name.
        :type network: str

        :return HDKey: HD Key class object of subkey
        """

        if isinstance(path, TYPE_TEXT):
            path = path.split("/")
        if self.key_type == 'single':
            raise BKeyError("Key derivation cannot be used for 'single' type keys")
        key = self
        first_public = False
        if path[0] == 'm':  # Use Private master key
            path = path[1:]
        elif path[0] == 'M':  # Use Public master key
            path = path[1:]
            first_public = True
        if path:
            if len(path) > 1:
                _logger.info("Path length > 1 can be slow for larger paths, use Wallet Class to generate keys paths")
            for item in path:
                if not item:
                    raise BKeyError("Could not parse path. Index is empty.")
                hardened = item[-1] in "'HhPp"
                if hardened:
                    item = item[:-1]
                index = int(item)
                if index < 0:
                    raise BKeyError("Could not parse path. Index must be a positive integer.")
                if first_public or not key.is_private:
                    key = key.child_public(index=index, network=network)  # TODO hardened=hardened key?
                    first_public = False
                else:
                    key = key.child_private(index=index, hardened=hardened, network=network)
        return key

    @deprecated  # In version 0.4.5
    def account_key(self, account_id=0, purpose=44, set_network=None):  # pragma: no cover
        """
        Deprecated since version 0.4.5, use public_master() method instead

        Derive account BIP44 key for current master key

        :param account_id: Account ID. Leave empty for account 0
        :type account_id: int
        :param purpose: BIP standard used, i.e. 44 for default, 45 for multisig, 84 for segwit
        :type purpose: int
        :param set_network: Derive account key for different network. Please note this calls the network_change method and changes the network for current key!
        :type set_network: str

        :return HDKey:

        """
        warnings.warn("Deprecated since version 0.4.5, use public_master() method instead", DeprecationWarning)
        if self.depth == 3:
            return self
        elif self.depth != 0:
            raise BKeyError("Need a master key to generate account key")
        if set_network:
            self.network_change(set_network)
        if self.is_private:
            path = ["m"]
        else:
            path = ["M"]
        path.append("%d'" % purpose)
        path.append("%d'" % self.network.bip44_cointype)
        path.append("%d'" % account_id)
        return self.subkey_for_path(path)

    def public_master(self, account_id=0, purpose=None, multisig=None, witness_type=None, as_private=False):
        """
        Derives a public master key for current HDKey.

        :param account_id: Account ID. Leave empty for account 0
        :type account_id: int
        :param purpose: BIP standard used, i.e. 44 for default, 45 for multisig, 84 for segwit.
        :type purpose: int
        :param multisig: Key is part of a multisignature wallet?
        :type multisig: bool
        :param witness_type: Specify witness type, default is legacy. Use 'segwit' or 'p2sh-segwit' for segregated witness.
        :type witness_type: str
        :param as_private: Return private key if available. Default is to return public key

        :return HDKey:
        """
        if multisig:
            self.multisig = multisig
        if witness_type:
            self.witness_type = witness_type
        ks = [k for k in WALLET_KEY_STRUCTURES if
              k['witness_type'] == self.witness_type and k['multisig'] == self.multisig and k['purpose'] is not None]
        if len(ks) > 1:
            raise BKeyError("Please check definitions in WALLET_KEY_STRUCTURES. Multiple options found for "
                            "witness_type - multisig combination")
        if ks and not purpose:
            purpose = ks[0]['purpose']
        path_template = ks[0]['key_path']

        # Use last hardened key as public master root
        pm_depth = path_template.index([x for x in path_template if x[-1:] == "'"][-1]) + 1
        path = path_expand(path_template[:pm_depth], path_template, account_id=account_id, purpose=purpose,
                           witness_type=self.witness_type, network=self.network.name)
        if as_private:
            return self.subkey_for_path(path)
        else:
            return self.subkey_for_path(path).public()

    def public_master_multisig(self, account_id=0, purpose=None, witness_type=None, as_private=False):
        """
        Derives a public master key for current HDKey for use with multi signature wallets. Wrapper for the
        public_master() method.

        :param account_id: Account ID. Leave empty for account 0
        :type account_id: int
        :param purpose: BIP standard used, i.e. 44 for default, 45 for multisig, 84 for segwit.
        :type purpose: int
        :param witness_type: Specify witness type, default is legacy. Use 'segwit' or 'p2sh-segwit' for segregated witness.
        :type witness_type: str
        :param as_private: Return private key if available. Default is to return public key

        :return HDKey:
        """

        return self.public_master(account_id, purpose, True, witness_type, as_private)

    @deprecated  # In version 0.4.5
    def account_multisig_key(self, account_id=0, witness_type=DEFAULT_WITNESS_TYPE):  # pragma: no cover
        """
        Deprecated since version 0.4.5, use public_master() method instead

        Derives a multisig account key according to BIP44/45 definition.
        Wrapper for the 'account_key' method.

        :param account_id: Account ID. Leave empty for account 0
        :type account_id: int
        :param witness_type: Specify witness type, default is legacy. Use 'segwit' for segregated witness.
        :type witness_type: str

        :return HDKey:
        """
        warnings.warn("Deprecated since version 0.4.5, use public_master() method instead", DeprecationWarning)
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
            raise BKeyError("Unknown witness type %s" % witness_type)

        if self.depth == 3 and purpose == 44:
            return self
        elif self.depth == 4 and purpose == 45:
            return self
        elif self.depth != 0:
            raise BKeyError("Need a master key to generate account key")

        path = ["%s" % 'm' if self.is_private else 'M', "%d'" % purpose]
        if purpose == 45:
            return self.subkey_for_path(path)
        elif purpose == 48:
            path += ["%d'" % self.network.bip44_cointype, "%d'" % account_id, "%d'" % script_type]
            return self.subkey_for_path(path)
        else:
            raise BKeyError("Unknown purpose %d, cannot determine wallet public cosigner key" % purpose)

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
        if not self.is_private:
            raise BKeyError("Need a private key to create child private key")
        if hardened:
            index |= 0x80000000
            data = b'\0' + self.private_byte + struct.pack('>L', index)
        else:
            data = self.public_byte + struct.pack('>L', index)
        key, chain = self._key_derivation(data)

        key = change_base(key, 256, 10)
        if key >= secp256k1_n:
            raise BKeyError("Key cannot be greater than secp256k1_n. Try another index number.")
        newkey = (key + self.secret) % secp256k1_n
        if newkey == 0:
            raise BKeyError("Key cannot be zero. Try another index number.")
        newkey = change_base(newkey, 10, 256, 32)

        return HDKey(key=newkey, chain=chain, depth=self.depth+1, parent_fingerprint=self.fingerprint,
                     child_index=index, witness_type=self.witness_type, multisig=self.multisig,
                     encoding=self.encoding, network=network)

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
        if key >= secp256k1_n:
            raise BKeyError("Key cannot be greater than secp256k1_n. Try another index number.")

        x, y = self.public_point()
        if USE_FASTECDSA:
            ki = ec_point(key) + fastecdsa_point.Point(x, y, fastecdsa_secp256k1)
            ki_x = ki.x
            ki_y = ki.y
        else:
            ki = ec_point(key) + ecdsa.ellipticcurve.Point(secp256k1_curve, x, y, secp256k1_n)
            ki_x = ki.x()
            ki_y = ki.y()

        if ki_y % 2:
            prefix = '03'
        else:
            prefix = '02'
        xhex = change_base(ki_x, 10, 16, 64)
        secret = binascii.unhexlify(prefix + xhex)
        return HDKey(key=secret, chain=chain, depth=self.depth+1, parent_fingerprint=self.fingerprint,
                     child_index=index, is_private=False, witness_type=self.witness_type, multisig=self.multisig,
                     encoding=self.encoding, network=network)

    def public(self):
        """
        Public version of current private key. Strips all private information from HDKey object, returns deepcopy
        version of current object

        :return HDKey:
        """

        hdkey = deepcopy(self)
        hdkey.is_private = False
        hdkey.secret = None
        hdkey.private_hex = None
        hdkey.private_byte = None
        hdkey.key_hex = hdkey.public_hex
        # hdkey.key = self.key.public()
        return hdkey


class Signature(object):
    """
    Signature class for transactions. Used to create signatures to sign transaction and verification
    
    Sign a transaction hash with a private key and show DER encoded signature
    >>> sk = HDKey()
    >>> tx_hash = 'c77545c8084b6178366d4e9a06cf99a28d7b5ff94ba8bd76bbbce66ba8cdef70'
    >>> signature = sign(tx_hash, sk)
    >>> to_hexstring(signature.as_der_encoded())
    3044022040aa86a597ecd19aa60c1f18390543cc5c38049a18a8515aed095a4b15e1d8ea02202226efba29871477ab925e75356fda036f06d293d02fc9b0f9d49e09d8149e9d
    
    """

    @staticmethod
    def from_str(signature, public_key=None):
        """
        Create a signature from signature string with r and s part. Signature length must be 64 bytes or 128 
        character hexstring 
        
        :param signature: Signature string
        :type signature: bytes, str
        :param public_key: Public key as HDKey or Key object or any other string accepted by HDKey object
        :type public_key: HDKey, Key, str, hexstring, bytes
        
        :return Signature: 
        """

        der_signature = ''
        signature = to_bytes(signature)
        if len(signature) > 64 and signature.startswith(b'\x30'):
            der_signature = signature
            if der_signature.endswith(b'\x01'):
                der_signature = der_signature[:-1]
            signature = convert_der_sig(signature[:-1], as_hex=False)
        signature = to_hexstring(signature)
        if len(signature) != 128:
            raise BKeyError("Signature length must be 64 bytes or 128 character hexstring")
        r = int(signature[:64], 16)
        s = int(signature[64:], 16)
        return Signature(r, s, signature=signature, der_signature=der_signature, public_key=public_key)

    @staticmethod
    def create(tx_hash, private, use_rfc6979=True, k=None):
        """
        Sign a transaction hash and create a signature with provided private key.
        
        :param tx_hash: Transaction signature or transaction hash. If unhashed transaction or message is provided the double_sha256 hash of message will be calculated.
        :type tx_hash: bytes, str
        :param private: Private key as HDKey or Key object, or any other string accepted by HDKey object
        :type private: HDKey, Key, str, hexstring, bytes
        :param use_rfc6979: Use deterministic value for k nonce to derive k from tx_hash/message according to RFC6979 standard. Default is True, set to False to use random k
        :type use_rfc6979: bool
        :param k: Provide own k. Only use for testing or if you known what you are doing. Providing wrong value for k can result in leaking your private key!
        :type k: int
        
        :return Signature: 
        """
        if isinstance(tx_hash, bytes):
            tx_hash = to_hexstring(tx_hash)
        if len(tx_hash) > 64:
            tx_hash = to_hexstring(double_sha256(binascii.unhexlify(tx_hash)))
        if not isinstance(private, (Key, HDKey)):
            private = HDKey(private)
        pub_key = private.public()
        secret = private.secret

        if not k:
            if use_rfc6979 and USE_FASTECDSA:
                rfc6979 = RFC6979(tx_hash, secret, secp256k1_n, hashlib.sha256)
                k = rfc6979.gen_nonce()
            else:
                global rfc6979_warning_given
                if not USE_FASTECDSA and not rfc6979_warning_given:
                    _logger.warning("RFC6979 only supported when fastecdsa library is used")
                    rfc6979_warning_given = True
                k = random.SystemRandom().randint(1, secp256k1_n - 1)

        if USE_FASTECDSA:
            r, s = _ecdsa.sign(
                tx_hash,
                str(secret),
                str(k),
                str(secp256k1_p),
                str(secp256k1_a),
                str(secp256k1_b),
                str(secp256k1_n),
                str(secp256k1_Gx),
                str(secp256k1_Gy)
            )
            if int(s) > secp256k1_n / 2:
                s = secp256k1_n - int(s)
            return Signature(r, s, tx_hash, secret, public_key=pub_key, k=k)
        else:
            sk = ecdsa.SigningKey.from_string(private.private_byte, curve=ecdsa.SECP256k1)
            tx_hash_bytes = to_bytes(tx_hash)
            sig_der = sk.sign_digest(tx_hash_bytes, sigencode=ecdsa.util.sigencode_der, k=k)
            signature = convert_der_sig(sig_der)
            r = int(signature[:64], 16)
            s = int(signature[64:], 16)
            if s > secp256k1_n / 2:
                s = secp256k1_n - s
            return Signature(r, s, tx_hash, secret, public_key=pub_key, der_signature=sig_der, signature=signature, k=k)

    def __init__(self, r, s, tx_hash=None, secret=None, signature=None, der_signature=None, public_key=None, k=None):
        """
        Initialize Signature object with provided r and r value. 
        
        :param r: r value of signature
        :type r: int
        :param s: s value of signature
        :type s: int
        :param tx_hash: Transaction hash z to sign if known
        :type tx_hash: bytes, hexstring
        :param secret: Private key secret number
        :type secret: int
        :param signature: r and s value of signature as string
        :type signature: str, bytes
        :param der_signature: DER encoded signature
        :type der_signature: str, bytes
        :param public_key: Provide public key P if known
        :type public_key: HDKey, Key, str, hexstring, bytes
        :param k: k value used for signature
        :type k: int
        """

        self.r = int(r)
        self.s = int(s)
        self.x = None
        self.y = None
        if 1 > self.r >= secp256k1_n:
            raise BKeyError('Invalid Signature: r is not a positive integer smaller than the curve order')
        elif 1 > self.s >= secp256k1_n:
            raise BKeyError('Invalid Signature: s is not a positive integer smaller than the curve order')
        self._tx_hash = None
        self.tx_hash = tx_hash
        self.secret = None if not secret else int(secret)
        self._der_encoded = to_bytes(der_signature)
        self._signature = to_bytes(signature)
        self._public_key = None
        self.public_key = public_key
        self.k = k

    def __repr__(self):
        der_sig = '' if not self._der_encoded else to_hexstring(self._der_encoded)
        return "<Signature(r=%d, s=%d, signature=%s, der_signature=%s)>" % \
               (self.r, self.s, self.hex(), der_sig)

    @property
    def tx_hash(self):
        return self._tx_hash

    @tx_hash.setter
    def tx_hash(self, value):
        if value is not None:
            self._tx_hash = value
            if isinstance(value, bytes):
                self._tx_hash = to_hexstring(value)

    @property
    def public_key(self):
        """
        Return public key as HDKey object
        
        :return HDKey: 
        """
        return self._public_key

    @public_key.setter
    def public_key(self, value):
        if value is None:
            return
        if isinstance(value, bytes):
            value = HDKey(value)
        if value.is_private:
            value = value.public()
        self.x, self.y = value.public_point()

        if USE_FASTECDSA:
            if not fastecdsa_secp256k1.is_point_on_curve((self.x, self.y)):
                raise BKeyError('Invalid public key, point is not on secp256k1 curve')
        self._public_key = value

    def hex(self):
        """
        Signature r and s value as single hexstring

        :return hexstring:
        """
        return to_hexstring(self.bytes())

    def bytes(self):
        """
        Signature r and s value as single bytes string

        :return bytes:
        """

        if not self._signature:
            self._signature = to_bytes('%064x%064x' % (self.r, self.s))
        return self._signature

    def as_der_encoded(self):
        """
        DER encoded signature in bytes
        
        :return bytes: 
        """
        if not self._der_encoded:
            self._der_encoded = der_encode_sig(self.r, self.s)
        return self._der_encoded

    def verify(self, tx_hash=None, public_key=None):
        """
        Verify this signature. Provide tx_hash or public_key if not already known
        
        :param tx_hash: Transaction hash
        :type tx_hash: bytes, hexstring
        :param public_key: Public key P
        :type public_key: HDKey, Key, str, hexstring, bytes
                
        :return bool: 
        """
        if tx_hash is not None:
            self.tx_hash = to_hexstring(tx_hash)
        if public_key is not None:
            self.public_key = public_key

        if not self.tx_hash or not self.public_key:
            raise BKeyError("Please provide tx_hash and public_key to verify signature")

        if USE_FASTECDSA:
            return _ecdsa.verify(
                str(self.r),
                str(self.s),
                self.tx_hash,
                str(self.x),
                str(self.y),
                str(secp256k1_p),
                str(secp256k1_a),
                str(secp256k1_b),
                str(secp256k1_n),
                str(secp256k1_Gx),
                str(secp256k1_Gy)
            )
        else:
            transaction_to_sign = to_bytes(self.tx_hash)
            signature = self.bytes()
            if len(transaction_to_sign) != 32:
                transaction_to_sign = double_sha256(transaction_to_sign)
            ver_key = ecdsa.VerifyingKey.from_string(self.public_key.public_uncompressed_byte[1:],
                                                     curve=ecdsa.SECP256k1)
            try:
                if len(signature) > 64 and signature.startswith(b'\x30'):
                    try:
                        signature = convert_der_sig(signature[:-1], as_hex=False)
                    except Exception:
                        pass
                ver_key.verify_digest(signature, transaction_to_sign)
            except ecdsa.keys.BadSignatureError:
                return False
            except ecdsa.keys.BadDigestError as e:
                _logger.info("Bad Digest %s (error %s)" % (binascii.hexlify(signature), e))
                return False
            return True


def sign(tx_hash, private, use_rfc6979=True, k=None):
    """
    Sign transaction hash or message with secret private key. Creates a signature object.
    
    Sign a transaction hash with a private key and show DER encoded signature
    >>> sk = HDKey()
    >>> tx_hash = 'c77545c8084b6178366d4e9a06cf99a28d7b5ff94ba8bd76bbbce66ba8cdef70'
    >>> signature = sign(tx_hash, sk)
    >>> to_hexstring(signature.as_der_encoded())
    3044022040aa86a597ecd19aa60c1f18390543cc5c38049a18a8515aed095a4b15e1d8ea02202226efba29871477ab925e75356fda036f06d293d02fc9b0f9d49e09d8149e9d

    :param tx_hash: Transaction signature or transaction hash. If unhashed transaction or message is provided the double_sha256 hash of message will be calculated.
    :type tx_hash: bytes, str
    :param private: Private key as HDKey or Key object, or any other string accepted by HDKey object
    :type private: HDKey, Key, str, hexstring, bytes
    :param use_rfc6979: Use deterministic value for k nonce to derive k from tx_hash/message according to RFC6979 standard. Default is True, set to False to use random k
    :type use_rfc6979: bool
    :param k: Provide own k. Only use for testing or if you known what you are doing. Providing wrong value for k can result in leaking your private key!
    :type k: int
        
    :return Signature: 
    """
    return Signature.create(tx_hash, private, use_rfc6979, k)


def verify(tx_hash, signature, public_key=None):
    """
    Verify provided signature with tx_hash message. If provided signature is no Signature object a new object will
    be created for verification.

    :param tx_hash: Transaction hash
    :type tx_hash: bytes, hexstring
    :param signature: signature as hexstring or bytes
    :type signature: str, bytes
    :param public_key: Public key P. If not provided it will be derived from provided Signature object or raise an error if not available
    :type public_key: HDKey, Key, str, hexstring, bytes

    :return bool: 
    """
    if not isinstance(signature, Signature):
        if not public_key:
            raise BKeyError("No public key provided, cannot verify")
        signature = Signature.from_str(signature, public_key=public_key)
    return signature.verify(tx_hash, public_key)


def ec_point(m):
    """
    Method for elliptic curve multiplication on the secp256k1 curve. Multiply Generator point G with m

    :param m: A point on the elliptic curve
    :type m: int

    :return Point: Point multiplied by generator G
    """
    m = int(m)
    if USE_FASTECDSA:
        return fastecdsa_keys.get_public_key(m, fastecdsa_secp256k1)
    else:
        point = secp256k1_generator
        point *= m
        return point


def mod_sqrt(a):
    """
    Compute the square root of 'a' using the secp256k1 'bitcoin' curve

    Used to calculate y-coordinate if only x-coordinate from public key point is known.
    Formula: y ** 2 == x ** 3 + 7
    
    :param a: Number to calculate square root
    :type a: int
    
    :return int: 
    """

    # k = (secp256k1_p - 3) // 4
    k = 28948022309329048855892746252171976963317496166410141009864396001977208667915
    return pow(a, k + 1, secp256k1_p)
