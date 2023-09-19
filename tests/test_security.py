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
from unittest import TestCase, main
from sqlalchemy.sql import text
from bitcoinlib.db import BCL_DATABASE_DIR
from bitcoinlib.wallets import Wallet
from bitcoinlib.config.config import DATABASE_ENCRYPTION_ENABLED

DATABASEFILE_UNITTESTS_ENCRYPTED = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib.unittest_security.sqlite')
# DATABASEFILE_UNITTESTS_ENCRYPTED = 'postgresql://postgres:postgres@localhost:5432/bitcoinlib_security'


class TestSecurity(TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_UNITTESTS_ENCRYPTED):
            os.remove(DATABASEFILE_UNITTESTS_ENCRYPTED)

    def test_security_wallet_field_encryption(self):
        pk = 'xprv9s21ZrQH143K2HrtPWvqgD8mUhMrrfE1ZME43baM8ti3hWgJwWX1wjHc25y2x11seT5G3KeHFY28MyTRxceeW22kMDAWsMDn7' \
             'rcWnEMFP3t'
        pk_wif_enc_hex = \
            'cbfe0c6aa900cdd080cd28855e21e563d65fa3de4ad99a320037ccb7ce633d2c2889bb90b20e5dae2b0005405819d' \
            '3239d21e4ffc39e980fcb6bbbb7db1718247ed3b53a3caeffd930c071cd3a059cc063bd0a71503671e98906dbe857' \
            '17f1ffea8e20844309f6fb6b281349a2b3915af3d12dc4c90c3b68f6666eb665682d'
        pk_enc_hex = 'f8777f10a435d5e3fdbb64cfdcb929626ce38c7103e772921ad1fc21c5e69e474423a998523bf53565ab45711a14086c'

        if not DATABASE_ENCRYPTION_ENABLED:
            self.skipTest("Database encryption not enabled, skip this test")
        self.assertEqual(os.environ.get('DB_FIELD_ENCRYPTION_KEY'),
                         '11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff')

        wallet = Wallet.create('wlt-private-key-encryption-test', keys=pk, db_uri=DATABASEFILE_UNITTESTS_ENCRYPTED)
        wallet.new_key()
        self.assertEqual(wallet.main_key.wif, pk)

        db_query = text('SELECT wif, private FROM keys WHERE id=%d' % wallet._dbwallet.main_key_id)
        encrypted_main_key_wif = wallet._session.execute(db_query).fetchone()[0]
        encrypted_main_key_private = wallet._session.execute(db_query).fetchone()[1]
        self.assertIn(type(encrypted_main_key_wif), (bytes, memoryview), "Encryption of database private key failed!")
        self.assertEqual(encrypted_main_key_wif.hex(), pk_wif_enc_hex)
        self.assertEqual(encrypted_main_key_private.hex(), pk_enc_hex)


if __name__ == '__main__':
    main()
