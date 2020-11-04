# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Database
#    © 2019 December - 1200 Web Development <http://1200wd.com/>
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
from tests.db_0_5 import Db as DbInitOld
from bitcoinlib.db import *
from bitcoinlib.wallets import Wallet, WalletError


DATABASEFILE_UNITTESTS = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib.unittest.sqlite')
DATABASEFILE_TMP = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib.tmp.sqlite')


class TestDb(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_TMP):
            os.remove(DATABASEFILE_TMP)

    def test_database_upgrade(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        dbold = DbInitOld(DATABASEFILE_UNITTESTS)

        # self.assertFalse('latest_txid' in dbold.engine.execute("SELECT * FROM keys").keys())
        # self.assertFalse('address' in dbold.engine.execute("SELECT * FROM transaction_inputs").keys())
        # version_db = dbold.session.query(DbConfig.value).filter_by(variable='version').scalar()
        # self.assertEqual(version_db, '0.4.10')

    def test_database_create_drop(self):
        dbtmp = Db(DATABASEFILE_TMP)
        self.assertEqual(dbtmp.o.path, DATABASEFILE_TMP)
        Wallet.create("tmpwallet", db_uri=DATABASEFILE_TMP)
        self.assertRaisesRegexp(WalletError, "Wallet with name 'tmpwallet' already exists",
                                Wallet.create, 'tmpwallet', db_uri=DATABASEFILE_TMP)
        dbtmp.drop_db(yes_i_am_sure=True)
        Wallet.create("tmpwallet", db_uri=DATABASEFILE_TMP)


if __name__ == '__main__':
    unittest.main()
