# -*- coding: utf-8 -*-
#
#    bitcoinlib - Main
#    © 2016 December - 1200 Web Development <http://1200wd.com/>
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


DEFAULT_DOCDIR = os.path.join(os.path.expanduser("~"), '.bitcoinlib/')
DEFAULT_DATABASEDIR = DEFAULT_DOCDIR
DEFAULT_LOGDIR = DEFAULT_DOCDIR
DEFAULT_SETTINGSDIR = DEFAULT_DOCDIR
# -> Or put files in a seperate directory:
# DEFAULT_DATABASEDIR = os.path.join(DEFAULT_DOCDIR, 'database')
# DEFAULT_LOGDIR = os.path.join(DEFAULT_DOCDIR, 'log')
# DEFAULT_SETTINGSDIR = os.path.join(DEFAULT_DOCDIR, 'config')
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


def initialize_lib():
    instlogfile = os.path.join(DEFAULT_LOGDIR, 'install.log')
    if os.path.isfile(instlogfile):
        return

    with open(instlogfile, 'w') as f:
        f.write('Bitcoinlibrary installed, check further logs in bitcoinlib.log')

    # Copy data and settings file to DOCDIR
    from shutil import copyfile
    src_files = os.listdir(CURRENT_INSTALLDIR_DATA)
    for file_name in src_files:
        full_file_name = os.path.join(CURRENT_INSTALLDIR_DATA, file_name)
        if os.path.isfile(full_file_name):
            copyfile(full_file_name, os.path.join(DEFAULT_SETTINGSDIR, file_name))


initialize_lib()

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S',
    filename=os.path.join(DEFAULT_LOGDIR, 'bitcoinlib.log'),
    level=logging.DEBUG)
logging.info('WELCOME TO BITCOINLIB - CRYPTOCURRENCY LIBRARY')
logging.info('Logger name: %s' % logging.__name__)

