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
import functools
import logging
from logging.handlers import RotatingFileHandler
from bitcoinlib.config.opcodes import *
from bitcoinlib.config.config import *


# Initialize logging to bitcoi`nlib.log
logfile = os.path.join(BCL_LOG_DIR, 'bitcoinlib.log')
handler = RotatingFileHandler(logfile, maxBytes=100 * 1024 * 1024, backupCount=2)
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s',
                              datefmt='%Y/%m/%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(LOGLEVEL)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(LOGLEVEL)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logging.info('WELCOME TO BITCOINLIB - CRYPTOCURRENCY LIBRARY')
logging.info('Logger name: %s' % logging.__name__)
logging.info('Read config from: %s' % BCL_CONFIG_FILE)
logging.info('Directory databases: %s' % BCL_DATABASE_DIR)
logging.info('Default database: %s' % DEFAULT_DATABASE)
logging.info('Directory logs: %s' % BCL_LOG_DIR)
logging.info('Directory for BCL configuration: %s' % BCL_CONFIG_DIR)
logging.info('Directory for BCL data files: %s' % BCL_DATA_DIR)
logging.info('Directory wordlists: %s' % BCL_WORDLIST_DIR)

logging.getLogger('sqlalchemy.engine').setLevel('WARNING')


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
