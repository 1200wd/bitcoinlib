# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Unit Tests for Wallet Class
#    © 2016 November - 1200 Web Development <http://1200wd.com/>
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

import unittest

from bitcoinlib.db import *
from bitcoinlib.wallets import HDWallet


class TestEncodingMethods(unittest.TestCase):

    def SetUp(self):
        import os
        DATABASEFILE = 'bitcoinlib.unittest.sqlite'
        if os.path.isfile(DATABASEDIR + DATABASEFILE):
            os.remove(DATABASEDIR + DATABASEFILE)
        Base.metadata.create_all(engine)

    def test_change_base_hex_bit(self):
        kstr = 'tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePy' \
               'A7irEvBoe4aAn52'
        wallet_import = HDWallet.create(
            name='TestNetWallet',
            key= kstr,
            network='testnet',
            account_id=251)
        wallet_import.new_account()
        wallet_import.new_key("Faucet gift")
        self.assertEqual(wallet_import.main_key(), kstr)