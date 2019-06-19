# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    CONFIG - Configuration settings
#    © 2019 March - 1200 Web Development <http://1200wd.com/>
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

import os
import sys
import locale


# General defaults
PY3 = sys.version_info[0] == 3
TYPE_TEXT = str
if not PY3:
    TYPE_TEXT = (str, unicode)
LOGLEVEL = 'WARNING'
if PY3:
    import configparser
else:
    import ConfigParser as configparser


# File locations
BCL_INSTALL_DIR = os.path.dirname(os.path.dirname(__file__))
BCL_DATABASE_DIR = ''
DEFAULT_DATABASE = None
BCL_LOG_DIR = ''
BCL_CONFIG_DIR = ''
BCL_DATA_DIR = ''
BCL_WORDLIST_DIR = ''
BCL_CONFIG_FILE = ''


# Services
TIMEOUT_REQUESTS = 5

# Transactions
SCRIPT_TYPES_LOCKING = {
    # Locking scripts / scriptPubKey (Output)
    'p2pkh': ['OP_DUP', 'OP_HASH160', 'hash-20', 'OP_EQUALVERIFY', 'OP_CHECKSIG'],
    'p2sh': ['OP_HASH160', 'hash-20', 'OP_EQUAL'],
    'p2wpkh': ['OP_0', 'hash-20'],
    'p2wsh': ['OP_0', 'hash-32'],
    'multisig': ['op_m', 'multisig', 'op_n', 'OP_CHECKMULTISIG'],
    'p2pk': ['public_key', 'OP_CHECKSIG'],
    'nulldata': ['OP_RETURN', 'return_data'],
}
SCRIPT_TYPES_UNLOCKING = {
    # Unlocking scripts / scriptSig (Input)
    'sig_pubkey': ['signature', 'SIGHASH_ALL', 'public_key'],
    'p2sh_multisig': ['OP_0', 'multisig', 'redeemscript'],
    'p2sh_p2wpkh': ['OP_0', 'OP_HASH160', 'redeemscript', 'OP_EQUAL'],
    'p2sh_p2wsh': ['OP_0', 'push_size', 'redeemscript'],
    'locktime_cltv': ['locktime_cltv', 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP'],
    'locktime_csv': ['locktime_csv', 'OP_CHECKSEQUENCEVERIFY', 'OP_DROP'],
    'signature': ['signature']
}

SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
SIGHASH_ANYONECANPAY = 80

SEQUENCE_LOCKTIME_DISABLE_FLAG = (1 << 31)  # To enable sequence time locks
SEQUENCE_LOCKTIME_TYPE_FLAG = (1 << 22)  # If set use timestamp based lock otherwise use block height
SEQUENCE_LOCKTIME_GRANULARITY = 9
SEQUENCE_LOCKTIME_MASK = 0x0000FFFF
SEQUENCE_ENABLE_LOCKTIME = 0xFFFFFFFE
SEQUENCE_REPLACE_BY_FEE = 0xFFFFFFFD

SIGNATURE_VERSION_STANDARD = 0
SIGNATURE_VERSION_SEGWIT = 1

# Mnemonics
DEFAULT_LANGUAGE = 'english'

# Networks
DEFAULT_NETWORK = 'bitcoin'


if os.name == 'nt' and locale.getpreferredencoding() != 'UTF-8':
    # TODO: Find a better windows hack
    import _locale
    _locale._getdefaultlocale = (lambda *args: ['en_US', 'utf8'])
elif locale.getpreferredencoding() != 'UTF-8':
    raise EnvironmentError("Locale is currently set to '%s'. "
                           "This library needs the locale set to UTF-8 to function properly" %
                           locale.getpreferredencoding())

# Keys / Addresses
SUPPORTED_ADDRESS_ENCODINGS = ['base58', 'bech32']
ENCODING_BECH32_PREFIXES = ['bc', 'tb', 'ltc', 'tltc', 'tdash', 'tdash', 'blt']
DEFAULT_WITNESS_TYPE = 'legacy'

# Wallets
WALLET_KEY_STRUCTURES = [
    {
        'purpose': None,
        'script_type': 'p2pkh',
        'witness_type': 'legacy',
        'multisig': False,
        'encoding': 'base58',
        'description': 'Single key wallet with no hierarchical deterministic key structure',
        'key_path': ['m']
    },
    {
        'purpose': 44,
        'script_type': 'p2pkh',
        'witness_type': 'legacy',
        'multisig': False,
        'encoding': 'base58',
        'description': 'Legacy wallet using pay-to-public-key-hash scripts',
        'key_path': ["m", "purpose'", "coin_type'",  "account'", "change", "address_index"]
    },
    {
        'purpose': 45,
        'script_type': 'p2sh',
        'witness_type': 'legacy',
        'multisig': True,
        'encoding': 'base58',
        'description': 'Legacy multisig wallet using pay-to-script-hash scripts',
        'key_path': ["m", "purpose'", "cosigner_index", "change", "address_index"]
    },
    {
        'purpose': 48,
        'script_type': 'p2sh-p2wsh',
        'witness_type': 'p2sh-segwit',
        'multisig': True,
        'encoding': 'base58',
        'description': 'Segwit multisig wallet using pay-to-wallet-script-hash scripts nested in p2sh scripts',
        'key_path': ["m", "purpose'", "coin_type'", "account'", "script_type'", "change", "address_index"]
    },
    {
        'purpose': 48,
        'script_type': 'p2wsh',
        'witness_type': 'segwit',
        'multisig': True,
        'encoding': 'bech32',
        'description': 'Segwit multisig wallet using native segwit pay-to-wallet-script-hash scripts',
        'key_path': ["m", "purpose'", "coin_type'", "account'", "script_type'", "change", "address_index"]
    },
    {
        'purpose': 49,
        'script_type': 'p2sh-p2wpkh',
        'witness_type': 'p2sh-segwit',
        'multisig': False,
        'encoding': 'base58',
        'description': 'Segwit wallet using pay-to-wallet-public-key-hash scripts nested in p2sh scripts',
        'key_path': ["m", "purpose'", "coin_type'", "account'", "change", "address_index"]
    },
    {
        'purpose': 84,
        'script_type': 'p2wpkh',
        'witness_type': 'segwit',
        'multisig': False,
        'encoding': 'bech32',
        'description': 'Segwit multisig wallet using native segwit pay-to-wallet-public-key-hash scripts',
        'key_path': ["m", "purpose'", "coin_type'", "account'", "change", "address_index"]
    },
]


def read_config():
    config = configparser.ConfigParser()

    def config_get(section, var, fallback):
        if os.environ.get("BCL_DEFAULT_CONFIG"):
            return fallback
        try:
            if PY3:
                val = config.get(section, var, fallback=fallback)
            else:
                val = config.get(section, var)
            return val
        except Exception:
            return fallback

    global BCL_INSTALL_DIR, BCL_DATABASE_DIR, DEFAULT_DATABASE, BCL_LOG_DIR, BCL_CONFIG_DIR, BCL_CONFIG_FILE
    global BCL_DATA_DIR, BCL_WORDLIST_DIR
    global TIMEOUT_REQUESTS, DEFAULT_LANGUAGE, DEFAULT_NETWORK, LOGLEVEL, DEFAULT_WITNESS_TYPE

    BCL_CONFIG_FILE = os.path.join(BCL_INSTALL_DIR, 'config.ini')
    data = config.read(BCL_CONFIG_FILE)
    if not data:
        BCL_CONFIG_FILE = os.path.join(os.path.expanduser("~"), '.bitcoinlib/config/config.ini')
        data = config.read(BCL_CONFIG_FILE)
    if not data:
        BCL_CONFIG_FILE = os.path.join(os.path.expanduser("~"), '.bitcoinlib/config.ini')
        data = config.read(BCL_CONFIG_FILE)

    BCL_DATABASE_DIR = config_get('locations', 'database_dir', '.bitcoinlib/database')
    if not os.path.isabs(BCL_DATABASE_DIR):
        BCL_DATABASE_DIR = os.path.join(os.path.expanduser("~"), BCL_DATABASE_DIR)
    if not os.path.exists(BCL_DATABASE_DIR):
        os.makedirs(BCL_DATABASE_DIR)
    default_databasefile = config_get('locations', 'default_databasefile', fallback='bitcoinlib.sqlite')
    DEFAULT_DATABASE = os.path.join(BCL_DATABASE_DIR, default_databasefile)

    BCL_LOG_DIR = config_get('locations', 'log_dir', fallback='.bitcoinlib/log')
    if not os.path.isabs(BCL_LOG_DIR):
        BCL_LOG_DIR = os.path.join(os.path.expanduser("~"), BCL_LOG_DIR)
    if not os.path.exists(BCL_LOG_DIR):
        os.makedirs(BCL_LOG_DIR)

    BCL_CONFIG_DIR = config_get('locations', 'config_dir', fallback='.bitcoinlib/config')
    if not os.path.isabs(BCL_CONFIG_DIR):
        BCL_CONFIG_DIR = os.path.join(os.path.expanduser("~"), BCL_CONFIG_DIR)
    if not os.path.exists(BCL_CONFIG_DIR):
        os.makedirs(BCL_CONFIG_DIR)

    BCL_DATA_DIR = config_get('locations', 'data_dir', fallback='data')
    if not os.path.isabs(BCL_DATA_DIR):
        BCL_DATA_DIR = os.path.join(BCL_INSTALL_DIR, BCL_DATA_DIR)

    BCL_WORDLIST_DIR = config_get('locations', 'wordlist_dir', fallback='wordlist')
    if not os.path.isabs(BCL_WORDLIST_DIR):
        BCL_WORDLIST_DIR = os.path.join(BCL_INSTALL_DIR, BCL_WORDLIST_DIR)

    TIMEOUT_REQUESTS = config_get('common', 'timeout_requests', fallback=TIMEOUT_REQUESTS)
    DEFAULT_LANGUAGE = config_get('common', 'default_language', fallback=DEFAULT_LANGUAGE)
    DEFAULT_NETWORK = config_get('common', 'default_network', fallback=DEFAULT_NETWORK)
    DEFAULT_WITNESS_TYPE = config_get('common', 'default_witness_type', fallback=DEFAULT_WITNESS_TYPE)

    LOGLEVEL = config_get('logs', 'loglevel', fallback=LOGLEVEL)

    if not data:
        return False
    return True


# Copy data and settings to default settings directory if install.log is not found
def initialize_lib():
    global BCL_LOG_DIR, BCL_DATA_DIR, BCL_CONFIG_DIR
    instlogfile = os.path.join(BCL_LOG_DIR, 'install.log')
    if os.path.isfile(instlogfile):
        return

    with open(instlogfile, 'w') as f:
        install_message = "BitcoinLib installed, check further logs in bitcoinlib.log\n\n" \
                          "If you remove this file all settings will be copied again from the library. " \
                          "This might be usefull after an update\n"
        f.write(install_message)

    # Copy data and settings file
    from shutil import copyfile
    src_files = os.listdir(BCL_DATA_DIR)
    for file_name in src_files:
        full_file_name = os.path.join(BCL_DATA_DIR, file_name)
        if os.path.isfile(full_file_name):
            copyfile(full_file_name, os.path.join(BCL_CONFIG_DIR, file_name))


# Initialize library
read_config()
version_file = open(os.path.join(BCL_INSTALL_DIR, 'config/VERSION'))
BITCOINLIB_VERSION = version_file.read().strip()

initialize_lib()
