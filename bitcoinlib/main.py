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
from logging.handlers import RotatingFileHandler


DEFAULT_DOCDIR = os.path.join(os.path.expanduser("~"), '.bitcoinlib/')
# DEFAULT_DATABASEDIR = DEFAULT_DOCDIR
# DEFAULT_LOGDIR = DEFAULT_DOCDIR
# DEFAULT_SETTINGSDIR = DEFAULT_DOCDIR
DEFAULT_DATABASEDIR = os.path.join(DEFAULT_DOCDIR, 'database/')
DEFAULT_LOGDIR = os.path.join(DEFAULT_DOCDIR, 'log/')
DEFAULT_SETTINGSDIR = os.path.join(DEFAULT_DOCDIR, 'config/')
CURRENT_INSTALLDIR = os.path.dirname(__file__)
CURRENT_INSTALLDIR_DATA = os.path.join(os.path.dirname(__file__), 'data')
DEFAULT_DATABASEFILE = 'bitcoinlib.sqlite'
DEFAULT_DATABASE = DEFAULT_DATABASEDIR + DEFAULT_DATABASEFILE

DEFAULT_NETWORK = 'bitcoin'


if not os.path.exists(DEFAULT_DOCDIR):
    os.makedirs(DEFAULT_DOCDIR)
if not os.path.exists(DEFAULT_LOGDIR):
    os.makedirs(DEFAULT_LOGDIR)
if not os.path.exists(DEFAULT_SETTINGSDIR):
    os.makedirs(DEFAULT_SETTINGSDIR)


def read_only_properties(*attrs):

    def class_rebuilder(cls):
        "The class decorator"

        class NewClass(cls):
            "This is the overwritten class"
            def __setattr__(self, name, value):
                if name not in attrs:
                    pass
                elif name not in self.__dict__:
                    pass
                else:
                    raise AttributeError("Can't modify {}".format(name))

                super().__setattr__(name, value)
        return NewClass
    return class_rebuilder


def initialize_lib():
    instlogfile = os.path.join(DEFAULT_LOGDIR, 'install.log')
    if os.path.isfile(instlogfile):
        return

    with open(instlogfile, 'w') as f:
        f.write('Bitcoinlibrary installed, check further logs in bitcoinlib.log\n')

    # Copy data and settings file to DOCDIR
    from shutil import copyfile
    src_files = os.listdir(CURRENT_INSTALLDIR_DATA)
    for file_name in src_files:
        full_file_name = os.path.join(CURRENT_INSTALLDIR_DATA, file_name)
        if os.path.isfile(full_file_name):
            copyfile(full_file_name, os.path.join(DEFAULT_SETTINGSDIR, file_name))


initialize_lib()

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
