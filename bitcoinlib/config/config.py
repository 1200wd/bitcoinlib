# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    CONFIG - Configuration settings
#    © 2022 - 2023 May - 1200 Web Development <http://1200wd.com/>
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
import locale
import platform
import configparser
import enum
from .opcodes import *
from pathlib import Path
from datetime import datetime, timezone

# General defaults
TYPE_TEXT = str
TYPE_INT = int
LOGLEVEL = 'WARNING'


# File locations
BCL_CONFIG_FILE = ''
BCL_INSTALL_DIR = Path(__file__).parents[1]
BCL_DATA_DIR = ''
BCL_DATABASE_DIR = ''
DEFAULT_DATABASE = None
DEFAULT_DATABASE_CACHE = None
BCL_LOG_FILE = ''

# Main
ENABLE_BITCOINLIB_LOGGING = True
ALLOW_DATABASE_THREADS = None
DATABASE_ENCRYPTION_ENABLED = False
DB_FIELD_ENCRYPTION_KEY = None
DB_FIELD_ENCRYPTION_PASSWORD = None

# Services
TIMEOUT_REQUESTS = 5
MAX_TRANSACTIONS = 20
BLOCK_COUNT_CACHE_TIME = 3
SERVICE_MAX_ERRORS = 4  # Fail service request when more then max errors occur for <SERVICE_MAX_ERRORS> providers

# Transactions
SCRIPT_TYPES = {
    # <name>: (<type>, <script_commands>, <data-lengths>)
    'p2pkh': ('locking', [op.op_dup, op.op_hash160, 'data', op.op_equalverify, op.op_checksig], [20]),
    'p2pkh_drop': ('locking', ['data', op.op_drop, op.op_dup, op.op_hash160, 'data', op.op_equalverify, op.op_checksig],
                   [32, 20]),
    'p2sh': ('locking', [op.op_hash160, 'data', op.op_equal], [20]),
    'p2wpkh': ('locking', [op.op_0, 'data'], [20]),
    'p2wsh': ('locking', [op.op_0, 'data'], [32]),
    'p2tr': ('locking', ['op_n', 'data'], [32]),
    'multisig': ('locking', ['op_n', 'key', 'op_n', op.op_checkmultisig], []),
    'p2pk': ('locking', ['key', op.op_checksig], []),
    'locktime_cltv_script': ('locking', ['locktime_cltv', op.op_checklocktimeverify, op.op_drop, op.op_dup,
                                         op.op_hash160, 'data', op.op_equalverify, op.op_checksig], [20]),
    'nulldata': ('locking', [op.op_return, 'data'], [0]),
    'nulldata_1': ('locking', [op.op_return, op.op_0], []),
    'nulldata_2': ('locking', [op.op_return], []),
    'sig_pubkey': ('unlocking', ['signature', 'key'], []),
    # 'p2sh_multisig': ('unlocking', [op.op_0, 'signature', 'op_n', 'key', 'op_n', op.op_checkmultisig], []),
    'p2sh_multisig': ('unlocking', [op.op_0, 'signature', 'redeemscript'], []),
    'multisig_redeemscript': ('unlocking', ['op_n', 'key', 'op_n', op.op_checkmultisig], []),
    'p2tr_unlock': ('unlocking', ['data'], [64]),
    'p2sh_multisig_2?': ('unlocking', [op.op_0, 'signature', op.op_verify, 'redeemscript'], []),
    'p2sh_multisig_3?': ('unlocking', [op.op_0, 'signature', op.op_1add, 'redeemscript'], []),
    # 'p2sh_p2wpkh': ('unlocking', [op.op_0, op.op_hash160, 'redeemscript', op.op_equal], []),
    # 'p2sh_p2wsh': ('unlocking', [op.op_0, 'redeemscript'], []),
    'p2sh_p2wpkh': ('unlocking', [op.op_0, 'data'], [20]),
    'p2sh_p2wsh': ('unlocking', [op.op_0, 'data'], [32]),
    'signature': ('unlocking', ['signature'], []),
    'signature_multisig': ('unlocking', [op.op_0, 'signature'], []),
    'locktime_cltv': ('unlocking', ['locktime_cltv', op.op_checklocktimeverify, op.op_drop], []),
    'locktime_csv': ('unlocking', ['locktime_csv', op.op_checksequenceverify, op.op_drop], []),
    #
    # List of nonstandard scripts, use for blockchain parsing. Must begin with 'nonstandard'
    'nonstandard_0001': ('unlocking', [op.op_0], []),
}

SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
SIGHASH_ANYONECANPAY = 0x80

SEQUENCE_LOCKTIME_DISABLE_FLAG = (1 << 31)  # To enable sequence time locks
SEQUENCE_LOCKTIME_TYPE_FLAG = (1 << 22)  # If set use timestamp based lock otherwise use block height
SEQUENCE_LOCKTIME_GRANULARITY = 9
SEQUENCE_LOCKTIME_MASK = 0x0000FFFF
SEQUENCE_ENABLE_LOCKTIME = 0xFFFFFFFE
SEQUENCE_REPLACE_BY_FEE = 0xFFFFFFFD

SIGNATURE_VERSION_STANDARD = 0
SIGNATURE_VERSION_SEGWIT = 1

BUMPFEE_DEFAULT_MULTIPLIER = 5

# Mnemonics
DEFAULT_LANGUAGE = 'english'

# BIP38
BIP38_MAGIC_LOT_AND_SEQUENCE = b'\x2c\xe9\xb3\xe1\xff\x39\xe2\x51'
BIP38_MAGIC_NO_LOT_AND_SEQUENCE = b'\x2c\xe9\xb3\xe1\xff\x39\xe2\x53'
BIP38_MAGIC_LOT_AND_SEQUENCE_UNCOMPRESSED_FLAG = b'\x04'
BIP38_MAGIC_LOT_AND_SEQUENCE_COMPRESSED_FLAG = b'\x24'
BIP38_MAGIC_NO_LOT_AND_SEQUENCE_UNCOMPRESSED_FLAG = b'\x00'
BIP38_MAGIC_NO_LOT_AND_SEQUENCE_COMPRESSED_FLAG = b'\x20'
BIP38_NO_EC_MULTIPLIED_PRIVATE_KEY_PREFIX = b'\x01\x42'
BIP38_EC_MULTIPLIED_PRIVATE_KEY_PREFIX = b'\x01\x43'
BIP38_CONFIRMATION_CODE_PREFIX = b'\x64\x3b\xf6\xa8\x9a'

# Networks
DEFAULT_NETWORK = 'bitcoin'
NETWORK_DENOMINATORS = {  # source: https://en.bitcoin.it/wiki/Units, https://en.wikipedia.org/wiki/Metric_prefix
    0.00000000000001: 'µsat',
    0.00000000001: 'msat',
    0.000000001: 'n',
    0.00000001: 'sat',
    0.0000001: 'fin',
    0.000001: 'µ',
    0.001: 'm',
    0.01: 'c',
    0.1: 'd',
    1: '',
    10: 'da',
    100: 'h',
    1000: 'k',
    1000000: 'M',
    1000000000: 'G',
    1000000000000: 'T',
    1000000000000000: 'P',
    1000000000000000000: 'E',
    1000000000000000000000: 'Z',
    1000000000000000000000000: 'Y',
}

if os.name == 'nt' and locale.getpreferredencoding().lower() != 'utf-8':
    import _locale
    _locale._gdl_bak = _locale._getdefaultlocale
    _locale._getdefaultlocale = (lambda *args: (_locale._gdl_bak()[0], 'utf8'))
elif locale.getpreferredencoding().lower() != 'utf-8':
    raise EnvironmentError("Locale is currently set to '%s'. "
                           "This library needs the locale set to UTF-8 to function properly" %
                           locale.getpreferredencoding())

# Keys / Addresses
SUPPORTED_ADDRESS_ENCODINGS = ['base58', 'bech32']
ENCODING_BECH32_PREFIXES = ['bc', 'tb', 'ltc', 'tltc', 'blt']
DEFAULT_WITNESS_TYPE = 'segwit'
BECH32M_CONST = 0x2bc830a3
KEY_PATH_LEGACY = ["m", "purpose'", "coin_type'",  "account'", "change", "address_index"]
KEY_PATH_P2SH = ["m", "purpose'", "cosigner_index", "change", "address_index"]
KEY_PATH_P2WSH = ["m", "purpose'", "coin_type'", "account'", "script_type'", "change", "address_index"]
KEY_PATH_P2WPKH = ["m", "purpose'", "coin_type'", "account'", "change", "address_index"]
KEY_PATH_BITCOINCORE = ['m', "account'", "change'", "address_index'"]

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
        'key_path': KEY_PATH_LEGACY
    },
    {
        'purpose': 45,
        'script_type': 'p2sh',
        'witness_type': 'legacy',
        'multisig': True,
        'encoding': 'base58',
        'description': 'Legacy multisig wallet using pay-to-script-hash scripts',
        'key_path': KEY_PATH_P2SH
    },
    {
        'purpose': 48,
        'script_type': 'p2sh-p2wsh',
        'witness_type': 'p2sh-segwit',
        'multisig': True,
        'encoding': 'base58',
        'description': 'Segwit multisig wallet using pay-to-wallet-script-hash scripts nested in p2sh scripts',
        'key_path': KEY_PATH_P2WSH
    },
    {
        'purpose': 48,
        'script_type': 'p2wsh',
        'witness_type': 'segwit',
        'multisig': True,
        'encoding': 'bech32',
        'description': 'Segwit multisig wallet using native segwit pay-to-wallet-script-hash scripts',
        'key_path': KEY_PATH_P2WSH
    },
    {
        'purpose': 49,
        'script_type': 'p2sh-p2wpkh',
        'witness_type': 'p2sh-segwit',
        'multisig': False,
        'encoding': 'base58',
        'description': 'Segwit wallet using pay-to-wallet-public-key-hash scripts nested in p2sh scripts',
        'key_path': KEY_PATH_P2WPKH
    },
    {
        'purpose': 84,
        'script_type': 'p2wpkh',
        'witness_type': 'segwit',
        'multisig': False,
        'encoding': 'bech32',
        'description': 'Segwit multisig wallet using native segwit pay-to-wallet-public-key-hash scripts',
        'key_path': KEY_PATH_P2WPKH
    },
    # {
    #     'purpose': 86,
    #     'script_type': 'p2tr',
    #     'witness_type': 'segwit',
    #     'multisig': False,
    #     'encoding': 'bech32',
    #     'description': 'Taproot single key wallet using P2TR transactions',
    #     'key_path': ["m", "purpose'", "coin_type'", "account'", "change", "address_index"]
    # },
]

# CACHING
SERVICE_CACHING_ENABLED = True


def read_config():
    config = configparser.ConfigParser()

    def config_get(section, var, fallback, is_boolean=False):
        try:
            if is_boolean:
                val = config.getboolean(section, var, fallback=fallback)
            else:
                val = config.get(section, var, fallback=fallback)
            return val
        except Exception:
            return fallback

    global BCL_INSTALL_DIR, BCL_DATABASE_DIR, DEFAULT_DATABASE, BCL_DATA_DIR, BCL_CONFIG_FILE
    global ALLOW_DATABASE_THREADS, DEFAULT_DATABASE_CACHE
    global BCL_LOG_FILE, LOGLEVEL, ENABLE_BITCOINLIB_LOGGING
    global TIMEOUT_REQUESTS, DEFAULT_LANGUAGE, DEFAULT_NETWORK, DEFAULT_WITNESS_TYPE
    global SERVICE_CACHING_ENABLED, DATABASE_ENCRYPTION_ENABLED, DB_FIELD_ENCRYPTION_KEY, DB_FIELD_ENCRYPTION_PASSWORD
    global SERVICE_MAX_ERRORS, BLOCK_COUNT_CACHE_TIME, MAX_TRANSACTIONS

    # Read settings from Configuration file provided in OS environment~/.bitcoinlib/ directory
    config_file_name = os.environ.get('BCL_CONFIG_FILE')
    if not config_file_name:
        BCL_CONFIG_FILE = Path('~/.bitcoinlib/config.ini').expanduser()
    else:
        BCL_CONFIG_FILE = Path(config_file_name)
        if not BCL_CONFIG_FILE.is_absolute():
            BCL_CONFIG_FILE = Path(Path.home(), '.bitcoinlib', BCL_CONFIG_FILE)
        if not BCL_CONFIG_FILE.exists():
            BCL_CONFIG_FILE = Path(BCL_INSTALL_DIR, 'data', config_file_name)
        if not BCL_CONFIG_FILE.exists():
            raise IOError('Bitcoinlib configuration file not found: %s' % str(BCL_CONFIG_FILE))
    data = config.read(str(BCL_CONFIG_FILE))
    BCL_DATA_DIR = Path(config_get('locations', 'data_dir', fallback='~/.bitcoinlib')).expanduser()

    # Database settings
    BCL_DATABASE_DIR = Path(BCL_DATA_DIR, config_get('locations', 'database_dir', 'database'))
    BCL_DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    default_databasefile = DEFAULT_DATABASE = \
        config_get('locations', 'default_databasefile', fallback='bitcoinlib.sqlite')
    if not default_databasefile.startswith('postgresql') and not default_databasefile.startswith('mysql') and not default_databasefile.startswith('mariadb'):
        DEFAULT_DATABASE = str(Path(BCL_DATABASE_DIR, default_databasefile))
    default_databasefile_cache = DEFAULT_DATABASE_CACHE = \
        config_get('locations', 'default_databasefile_cache', fallback='bitcoinlib_cache.sqlite')
    if not default_databasefile_cache.startswith('postgresql') and not default_databasefile_cache.startswith('mysql') and not default_databasefile_cache.startswith('mariadb'):
        DEFAULT_DATABASE_CACHE = str(Path(BCL_DATABASE_DIR, default_databasefile_cache))
    ALLOW_DATABASE_THREADS = config_get("common", "allow_database_threads", fallback=True, is_boolean=True)
    SERVICE_CACHING_ENABLED = config_get('common', 'service_caching_enabled', fallback=True, is_boolean=True)
    DATABASE_ENCRYPTION_ENABLED = config_get('common', 'database_encryption_enabled', fallback=False, is_boolean=True)
    DB_FIELD_ENCRYPTION_KEY = os.environ.get('DB_FIELD_ENCRYPTION_KEY')
    DB_FIELD_ENCRYPTION_PASSWORD = os.environ.get('DB_FIELD_ENCRYPTION_PASSWORD')

    # Log settings
    ENABLE_BITCOINLIB_LOGGING = config_get("logs", "enable_bitcoinlib_logging", fallback=True, is_boolean=True)
    BCL_LOG_FILE = Path(BCL_DATA_DIR, config_get('logs', 'log_file', fallback='bitcoinlib.log'))
    BCL_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOGLEVEL = config_get('logs', 'loglevel', fallback=LOGLEVEL)

    # Service settings
    TIMEOUT_REQUESTS = int(config_get('common', 'timeout_requests', fallback=TIMEOUT_REQUESTS))
    SERVICE_MAX_ERRORS = int(config_get('common', 'service_max_errors', fallback=SERVICE_MAX_ERRORS))
    MAX_TRANSACTIONS = int(config_get('common', 'max_transactions', fallback=MAX_TRANSACTIONS))
    BLOCK_COUNT_CACHE_TIME = int(config_get('common', 'block_count_cache_time', fallback=BLOCK_COUNT_CACHE_TIME))

    # Other settings
    DEFAULT_LANGUAGE = config_get('common', 'default_language', fallback=DEFAULT_LANGUAGE)
    DEFAULT_NETWORK = config_get('common', 'default_network', fallback=DEFAULT_NETWORK)
    DEFAULT_WITNESS_TYPE = config_get('common', 'default_witness_type', fallback=DEFAULT_WITNESS_TYPE)

    if not data:
        return False
    return True


# Copy data and settings to default settings directory if install.log is not found
def initialize_lib():
    global BCL_INSTALL_DIR, BCL_DATA_DIR, BITCOINLIB_VERSION
    instlogfile = Path(BCL_DATA_DIR, 'install.log')
    if instlogfile.exists():
        return

    with instlogfile.open('w') as f:
        install_message = "BitcoinLib installed, check further logs in bitcoinlib.log\n\n" \
                          "If you remove this file all settings will be reset again to the default settings. " \
                          "This might be usefull after an update or when problems occur.\n\n" \
                          "Installation parameters. Include this parameters when reporting bugs and issues:\n" \
                          "Bitcoinlib version: %s\n" \
                          "Installation date : %s\n" \
                          "Python            : %s\n" \
                          "Compiler          : %s\n" \
                          "Build             : %s\n" \
                          "OS Version        : %s\n" \
                          "Platform          : %s\n" % \
                          (BITCOINLIB_VERSION, datetime.now().isoformat(), platform.python_version(),
                           platform.python_compiler(), platform.python_build(), platform.version(), platform.platform())
        f.write(install_message)

    # Copy data and settings file
    from shutil import copyfile
    for file in Path(BCL_INSTALL_DIR, 'data').iterdir():
        if file.suffix not in ['.ini', '.json']:
            continue
        copyfile(str(file), Path(BCL_DATA_DIR, file.name))


# Initialize library
read_config()
BITCOINLIB_VERSION = Path(BCL_INSTALL_DIR, 'config/VERSION').open().read().strip()
initialize_lib()
