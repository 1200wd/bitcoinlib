# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    MAIN - Load configs, initialize logging and database
#    © 2017 - 2019 January - 1200 Web Development <http://1200wd.com/>
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
import functools
import logging
from logging.handlers import RotatingFileHandler
from bitcoinlib.config.opcodes import *


# General defaults
PY3 = sys.version_info[0] == 3
TYPE_TEXT = str
if not PY3:
    TYPE_TEXT = (str, unicode)

# File locations
DEFAULT_DOCDIR = os.path.join(os.path.expanduser("~"), '.bitcoinlib/')
DEFAULT_DATABASEDIR = os.path.join(DEFAULT_DOCDIR, 'database/')
DEFAULT_LOGDIR = os.path.join(DEFAULT_DOCDIR, 'log/')
DEFAULT_SETTINGSDIR = os.path.join(DEFAULT_DOCDIR, 'config/')
CURRENT_INSTALLDIR = os.path.dirname(__file__)
CURRENT_INSTALLDIR_DATA = os.path.join(os.path.dirname(__file__), 'data')
DEFAULT_DATABASEFILE = 'bitcoinlib.sqlite'
DEFAULT_DATABASE = DEFAULT_DATABASEDIR + DEFAULT_DATABASEFILE
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
WORDLIST_DIR = os.path.join(os.path.dirname(__file__), 'wordlist')

# Networks
DEFAULT_NETWORK = 'bitcoin'


if not os.path.exists(DEFAULT_DOCDIR):
    os.makedirs(DEFAULT_DOCDIR)
if not os.path.exists(DEFAULT_LOGDIR):
    os.makedirs(DEFAULT_LOGDIR)
if not os.path.exists(DEFAULT_SETTINGSDIR):
    os.makedirs(DEFAULT_SETTINGSDIR)
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


# Copy data and settings to default settings directory if install.log is not found
def _initialize_lib():
    instlogfile = os.path.join(DEFAULT_LOGDIR, 'install.log')
    if os.path.isfile(instlogfile):
        return

    with open(instlogfile, 'w') as f:
        install_message = "BitcoinLib installed, check further logs in bitcoinlib.log\n\n" \
                          "If you remove this file all settings will be copied again from the library. " \
                          "This might be usefull after an update\n"
        f.write(install_message)

    # Copy data and settings file
    from shutil import copyfile
    src_files = os.listdir(CURRENT_INSTALLDIR_DATA)
    for file_name in src_files:
        full_file_name = os.path.join(CURRENT_INSTALLDIR_DATA, file_name)
        if os.path.isfile(full_file_name):
            copyfile(full_file_name, os.path.join(DEFAULT_SETTINGSDIR, file_name))


_initialize_lib()

# Initialize logging to bitcoinlib.log
logfile = os.path.join(DEFAULT_LOGDIR, 'bitcoinlib.log')
handler = RotatingFileHandler(logfile, maxBytes=100 * 1024 * 1024, backupCount=2)
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s',
                              datefmt='%Y/%m/%d %H:%M:%S')
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logging.info('WELCOME TO BITCOINLIB - CRYPTOCURRENCY LIBRARY')
logging.info('Logger name: %s' % logging.__name__)

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def script_type_default(witness_type=None, multisig=False, locking_script=False):
    """
    Determine default script type for provided witness type and key type combination used in this library.

    :param witness_type: Type of wallet: standard or segwit
    :type witness_type: str
    :param multisig: Multisig key or not, default is False
    :type multisig: bool
    :param locking_script: Limit search to locking_script. Specify False for locking scripts and True for unlocking scripts
    :type locking_script: bool

    :return str: Default script type
    """

    if not witness_type:
        return None
    if witness_type == 'legacy' and not multisig:
        return 'p2pkh' if locking_script else 'sig_pubkey'
    elif witness_type == 'legacy' and multisig:
        return 'p2sh' if locking_script else 'p2sh_multisig'
    elif witness_type == 'segwit' and not multisig:
        return 'p2wpkh' if locking_script else 'sig_pubkey'
    elif witness_type == 'segwit' and multisig:
        return 'p2wsh' if locking_script else 'p2sh_multisig'
    elif witness_type == 'p2sh-segwit' and not multisig:
        return 'p2sh' if locking_script else 'p2sh_p2wpkh'
    elif witness_type == 'p2sh-segwit' and multisig:
        return 'p2sh' if locking_script else 'p2sh_p2wsh'
    else:
        raise ValueError("Wallet and key type combination not supported: %s / %s" % (witness_type, multisig))


def get_encoding_from_witness(witness_type=None):
    """
    Derive address encoding (base58 or bech32) from transaction witness type

    :param witness_type: Witness type: legacy, p2sh-segwit or segwit
    :type witness_type: str

    :return str:
    """

    if witness_type == 'segwit':
        return 'bech32'
    elif witness_type in [None, 'legacy', 'p2sh-segwit']:
        return 'base58'
    else:
        raise ValueError("Unknown witness type %s" % witness_type)


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        logging.warning("Call to deprecated function {}.".format(func.__name__))
        return func(*args, **kwargs)
    return new_func
