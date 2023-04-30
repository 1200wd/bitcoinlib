# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Encryption and Security
#    © 2023 April - 1200 Web Development <http://1200wd.com/>
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
from unittest import mock, TestCase, main
from sqlalchemy.sql import text
from bitcoinlib.db import *
from bitcoinlib.wallets import Wallet


DATABASEFILE_UNITTESTS = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib.unittest_security.sqlite')
DATABASEFILE_CACHE_TMP = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib_cache_security.tmp.sqlite')


class TestSecurity(TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        if os.path.isfile(DATABASEFILE_CACHE_TMP):
            os.remove(DATABASEFILE_CACHE_TMP)

    @mock.patch.dict(os.environ, {"FROBNICATION_COLOUR": "ROUGE"})
    def test_security_wallet_field_encryption(self):
        pk = 'xprv9s21ZrQH143K2HrtPWvqgD8mUhMrrfE1ZME43baM8ti3hWgJwWX1wjHc25y2x11seT5G3KeHFY28MyTRxceeW22kMDAWsMDn7' \
             'rcWnEMFP3t'
        pk_enc_hex = 'cbfe0c6aa900cdd080cd28855e21e563d65fa3de4ad99a320037ccb7ce633d2c2889bb90b20e5dae2b0005405819d' \
                     '3239d21e4ffc39e980fcb6bbbb7db1718247ed3b53a3caeffd930c071cd3a059cc063bd0a71503671e98906dbe857' \
                     '17f1ffea8e20844309f6fb6b281349a2b3915af3d12dc4c90c3b68f6666eb665682d'

        wallet = Wallet.create('wlt-private-key-encryption-test', keys=pk, db_uri=DATABASEFILE_UNITTESTS)
        wallet.new_key()
        self.assertEqual(wallet.main_key.wif, pk)

        db_query = text('SELECT wif FROM keys WHERE id=%d' % wallet._dbwallet.main_key_id)
        encrypted_main_key = wallet._session.execute(db_query).fetchone()[0]
        print(encrypted_main_key)
        self.assertEqual(encrypted_main_key.hex(), pk_enc_hex)


if __name__ == '__main__':
    main()
