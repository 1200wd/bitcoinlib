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


DEFAULT_DATABASEDIR = os.path.join(os.path.expanduser("~"), '.bitcoinlib/')
DEFAULT_LOGDIR = DEFAULT_DATABASEDIR
CURRENT_INSTALLDIR = os.path.dirname(__file__)
CURRENT_INSTALLDIR_DATA = os.path.join(CURRENT_INSTALLDIR, 'data/')
DEFAULT_DATABASEFILE = 'bitcoinlib.sqlite'
DEFAULT_DATABASE = DEFAULT_DATABASEDIR + DEFAULT_DATABASEFILE

if not os.path.exists(DEFAULT_LOGDIR):
    os.makedirs(DEFAULT_LOGDIR)

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S',
    filename=os.path.join(DEFAULT_LOGDIR, 'bitcoinlib.log'),
    level=logging.INFO)
logging.info('WELCOME TO BITCOINLIB - CRYPTOCURRENCY LIBRARY')
logging.info('Logger name: %s' % logging.__name__)

