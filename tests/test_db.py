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
from bitcoinlib.db import *
from bitcoinlib.db_cache import *
from bitcoinlib.wallets import Wallet, WalletError, WalletTransaction
from bitcoinlib.transactions import Input, Output
from bitcoinlib.services.services import Service
try:
    import mysql.connector
    import psycopg
    from psycopg import sql
except ImportError as e:
    print("Could not import all modules. Error: %s" % e)


DATABASE_NAME = 'bitcoinlib_tmp'
DATABASE_CACHE_NAME = 'bitcoinlib_cache_tmp'

def database_init(dbname=DATABASE_NAME):
    session.close_all_sessions()
    if os.getenv('UNITTEST_DATABASE') == 'postgresql':
        con = psycopg.connect(user='postgres', host='localhost', password='postgres', autocommit=True)
        cur = con.cursor()
        try:
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(dbname)))
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
        except Exception as e:
            print("Error exception %s" % str(e))
            pass
        cur.close()
        con.close()
        return 'postgresql+psycopg://postgres:postgres@localhost:5432/' + dbname
    elif os.getenv('UNITTEST_DATABASE') == 'mysql':
        con = mysql.connector.connect(user='root', host='localhost', password='root')
        cur = con.cursor()
        cur.execute("DROP DATABASE IF EXISTS {}".format(dbname))
        cur.execute("CREATE DATABASE {}".format(dbname))
        con.commit()
        cur.close()
        con.close()
        return 'mysql://root:root@localhost:3306/' + dbname
    else:
        dburi = os.path.join(str(BCL_DATABASE_DIR), '%s.sqlite' % dbname)
        if os.path.isfile(dburi):
            try:
                os.remove(dburi)
            except PermissionError:
                db_obj = Db(dburi)
                db_obj.drop_db(True)
                db_obj.session.close()
                db_obj.engine.dispose()
        return dburi

class TestDb(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init(DATABASE_NAME)
        cls.database_cache_uri = database_init(DATABASE_CACHE_NAME)

    def test_database_create_drop(self):
        dbtmp = Db(self.database_uri)
        Wallet.create("tmpwallet", db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Wallet with name 'tmpwallet' already exists",
                                Wallet.create, 'tmpwallet', db_uri=self.database_uri)
        dbtmp.drop_db(yes_i_am_sure=True)
        Wallet.create("tmpwallet", db_uri=self.database_uri)

    def test_database_cache_create_drop(self):
        if os.getenv('UNITTEST_DATABASE') == 'mysql':
            self.skipTest('MySQL does not allow indexing on LargeBinary fields, so caching is not possible')
        dbtmp = DbCache(self.database_cache_uri)
        srv = Service(cache_uri=self.database_cache_uri, exclude_providers=['bitaps', 'bitgo'])
        t = srv.gettransaction('68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13')
        if t:
            self.assertGreaterEqual(srv.results_cache_n, 0)
            srv.gettransaction('68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13')
            self.assertGreaterEqual(srv.results_cache_n, 1)
            dbtmp.drop_db()
            self.assertRaisesRegex(Exception, "", srv.gettransaction,
                                   '68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13')

    def test_database_transaction_integers(self):
        db = Db(self.database_uri)
        w = Wallet.create('StrangeTransactions', account_id=0x7fffffff, db_uri=db.db_uri)
        inp = Input('68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13', 0x7fffffff,
                    value=0xffffffff, index_n=0x7fffffff, sequence=0xffffffff)
        outp = Output(0xffffffff, '37jKPSmbEGwgfacCr2nayn1wTaqMAbA94Z', output_n=0xffffffff)
        wt = WalletTransaction(w, 0x7fffffff, locktime=0xffffffff, fee=0xffffffff, confirmations=0x7fffffff,
                               input_total= 2100000000001000, block_height=0x7fffffff, version=0x7fffffff,
                               output_total=2100000000000000, size=0x07fffffff, inputs=[inp], outputs=[outp])
        self.assertTrue(wt.store())


if __name__ == '__main__':
    unittest.main()
