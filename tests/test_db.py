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
from sqlalchemy.exc import OperationalError
from tests.db_0_5 import Db as DbInitOld
from bitcoinlib.db import *
from bitcoinlib.db_cache import *
from bitcoinlib.wallets import Wallet, WalletError
from bitcoinlib.services.services import Service


DATABASEFILE_UNITTESTS = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib.unittest.sqlite')
DATABASEFILE_TMP = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib.tmp.sqlite')
DATABASEFILE_CACHE_TMP = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib_cache.tmp.sqlite')


class TestDb(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_TMP):
            os.remove(DATABASEFILE_TMP)
        if os.path.isfile(DATABASEFILE_CACHE_TMP):
            os.remove(DATABASEFILE_CACHE_TMP)

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
        Wallet.create("tmpwallet", db_uri=DATABASEFILE_TMP)
        self.assertRaisesRegexp(WalletError, "Wallet with name 'tmpwallet' already exists",
                                Wallet.create, 'tmpwallet', db_uri=DATABASEFILE_TMP)
        dbtmp.drop_db(yes_i_am_sure=True)
        Wallet.create("tmpwallet", db_uri=DATABASEFILE_TMP)

    def test_database_cache_create_drop(self):
        dbtmp = DbCache(DATABASEFILE_CACHE_TMP)
        srv = Service(cache_uri=DATABASEFILE_CACHE_TMP, exclude_providers=['bitaps', 'bitgo'])
        t = srv.gettransaction('68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13')
        if t:
            self.assertGreaterEqual(srv.results_cache_n, 0)
            srv.gettransaction('68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13')
            self.assertGreaterEqual(srv.results_cache_n, 1)
            dbtmp.drop_db()
            self.assertRaisesRegex(OperationalError, "", srv.gettransaction,
                                   '68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13')


if __name__ == '__main__':
    unittest.main()
