# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    MAIN - Load configs, initialize logging and database
#    © 2017 April - 1200 Web Development <http://1200wd.com/>
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
import logging
from logging.handlers import RotatingFileHandler


# Default file locations
DEFAULT_DOCDIR = os.path.join(os.path.expanduser("~"), '.bitcoinlib/')
DEFAULT_DATABASEDIR = os.path.join(DEFAULT_DOCDIR, 'database/')
DEFAULT_LOGDIR = os.path.join(DEFAULT_DOCDIR, 'log/')
DEFAULT_SETTINGSDIR = os.path.join(DEFAULT_DOCDIR, 'config/')
CURRENT_INSTALLDIR = os.path.dirname(__file__)
CURRENT_INSTALLDIR_DATA = os.path.join(os.path.dirname(__file__), 'data')
DEFAULT_DATABASEFILE = 'bitcoinlib.sqlite'
DEFAULT_DATABASE = DEFAULT_DATABASEDIR + DEFAULT_DATABASEFILE


if not os.path.exists(DEFAULT_DOCDIR):
    os.makedirs(DEFAULT_DOCDIR)
if not os.path.exists(DEFAULT_LOGDIR):
    os.makedirs(DEFAULT_LOGDIR)
if not os.path.exists(DEFAULT_SETTINGSDIR):
    os.makedirs(DEFAULT_SETTINGSDIR)


# Copy data and settings to default settings directory if install.log is not found
def initialize_lib():
    instlogfile = os.path.join(DEFAULT_LOGDIR, 'install.log')
    if os.path.isfile(instlogfile):
        return

    with open(instlogfile, 'w') as f:
        f.write('Bitcoinlibrary installed, check further logs in bitcoinlib.log\n')

    # Copy data and settings file
    from shutil import copyfile
    src_files = os.listdir(CURRENT_INSTALLDIR_DATA)
    for file_name in src_files:
        full_file_name = os.path.join(CURRENT_INSTALLDIR_DATA, file_name)
        if os.path.isfile(full_file_name):
            copyfile(full_file_name, os.path.join(DEFAULT_SETTINGSDIR, file_name))

initialize_lib()


# Initialize logging to bitcoinlib.log
logfile = os.path.join(DEFAULT_LOGDIR, 'bitcoinlib.log')
handler = RotatingFileHandler(logfile, maxBytes=100 * 1024 * 1024, backupCount=2)
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s',
                              datefmt='%Y/%m/%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logging.info('WELCOME TO BITCOINLIB - CRYPTOCURRENCY LIBRARY')
logging.info('Logger name: %s' % logging.__name__)

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
