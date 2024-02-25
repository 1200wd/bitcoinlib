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
from bitcoinlib.keys import HDKey
from bitcoinlib.encoding import EncodingError


try:
    import mysql.connector
    import psycopg
    from psycopg import sql
except ImportError:
    pass  # Only necessary when mysql or postgres is used


if os.getenv('UNITTEST_DATABASE') == 'postgresql':
    con = psycopg.connect(user='postgres', host='localhost', password='postgres', autocommit=True)
    cur = con.cursor()
    cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier('bitcoinlib_security')))
    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier('bitcoinlib_security')))
    cur.close()
    con.close()
    DATABASEFILE_UNITTESTS_ENCRYPTED = 'postgresql+psycopg://postgres:postgres@localhost:5432/bitcoinlib_security'
elif os.getenv('UNITTEST_DATABASE') == 'mysql':
    con = mysql.connector.connect(user='root', host='localhost', password='root')
    cur = con.cursor()
    cur.execute("DROP DATABASE IF EXISTS {}".format('bitcoinlib_security'))
    cur.execute("CREATE DATABASE {}".format('bitcoinlib_security'))
    con.commit()
    cur.close()
    con.close()
    DATABASEFILE_UNITTESTS_ENCRYPTED = 'mysql://root:root@localhost:3306/bitcoinlib_security'
else:
    DATABASEFILE_UNITTESTS_ENCRYPTED = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib.unittest_security.sqlite')
    if os.path.isfile(DATABASEFILE_UNITTESTS_ENCRYPTED):
        os.remove(DATABASEFILE_UNITTESTS_ENCRYPTED)


class TestSecurity(TestCase):

    def test_security_wallet_field_encryption_key(self):
        pk = 'xprv9s21ZrQH143K2HrtPWvqgD8mUhMrrfE1ZME43baM8ti3hWgJwWX1wjHc25y2x11seT5G3KeHFY28MyTRxceeW22kMDAWsMDn7' \
             'rcWnEMFP3t'
        pk_wif_enc_hex = \
            'cbfe0c6aa900cdd080cd28855e21e563d65fa3de4ad99a320037ccb7ce633d2c2889bb90b20e5dae2b0005405819d' \
            '3239d21e4ffc39e980fcb6bbbb7db1718247ed3b53a3caeffd930c071cd3a059cc063bd0a71503671e98906dbe857' \
            '17f1ffea8e20844309f6fb6b281349a2b3915af3d12dc4c90c3b68f6666eb665682d'
        pk_enc_hex = 'f8777f10a435d5e3fdbb64cfdcb929626ce38c7103e772921ad1fc21c5e69e474423a998523bf53565ab45711a14086c'

        if not os.environ.get('DB_FIELD_ENCRYPTION_KEY'):
            self.skipTest("Database field encryption key not found in environment, skip this test")
        self.assertEqual(os.environ.get('DB_FIELD_ENCRYPTION_KEY'),
                         '11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff')

        wallet = Wallet.create('wlt-private-key-encryption-test', keys=pk, db_uri=DATABASEFILE_UNITTESTS_ENCRYPTED)
        wallet.new_key()
        self.assertEqual(wallet.main_key.wif, pk)

        if os.getenv('UNITTEST_DATABASE') == 'mysql':
            db_query = text("SELECT wif, private FROM `keys` WHERE id=%d" % wallet._dbwallet.main_key_id)
        else:
            db_query = text("SELECT wif, private FROM keys WHERE id=%d" % wallet._dbwallet.main_key_id)
        encrypted_main_key_wif = wallet.session.execute(db_query).fetchone()[0]
        encrypted_main_key_private = wallet.session.execute(db_query).fetchone()[1]
        self.assertIn(type(encrypted_main_key_wif), (bytes, memoryview), "Encryption of database private key failed!")
        self.assertEqual(encrypted_main_key_wif.hex(), pk_wif_enc_hex)
        self.assertEqual(encrypted_main_key_private.hex(), pk_enc_hex)

    def test_security_wallet_field_encryption_password(self):
        pk = ('zprvAWgYBBk7JR8GivM5h6vdbXRrYRC6CU9aFDsVp2gLZ82Tx74UGf7nnN4cToSvNsDnK19tkuyXjzBMDcYvuseYYE5Q4qQo9JaLuNGz'
              'hfcovSp')
        pk_wif_enc_hex = \
            ('92410397d5a80ce75cdb5b0fe1204fd2e1411752c75f7b32a8c6a5574570d8be97155bcc4a86b6d34b0e6c22dfe32d340cc90dae1'
             '5e54316a9db538ad8a274881c7a45a7be0a00d6e5deda2ea28d8fa0ffcf8783b1fb580df6f5c056e43b79a93859bd083fc1922c86'
             'c17a3f945bbad5fa699a9d1cb2fc9f240708a1eee90b')
        pk_enc_hex = '1ff6958f0edc774f16d09d9fb36baa912fb9034f0e354c354a0a91c21e58fe05ad7c8089642565bf4fffd357db108117'

        if not os.environ.get('DB_FIELD_ENCRYPTION_PASSWORD'):
            self.skipTest("Database field encryption password not found in environment, skip this test")
        self.assertEqual(os.environ.get('DB_FIELD_ENCRYPTION_PASSWORD'),
                         'verybadpassword')

        wallet = Wallet.create('wlt-private-key-encryption-test-pwd', keys=pk,
                               db_uri=DATABASEFILE_UNITTESTS_ENCRYPTED)
        wallet.new_key()
        self.assertEqual(wallet.main_key.wif, pk)

        if os.getenv('UNITTEST_DATABASE') == 'mysql':
            db_query = text("SELECT wif, private FROM `keys` WHERE id=%d" % wallet._dbwallet.main_key_id)
        else:
            db_query = text("SELECT wif, private FROM keys WHERE id=%d" % wallet._dbwallet.main_key_id)
        encrypted_main_key_wif = wallet.session.execute(db_query).fetchone()[0]
        encrypted_main_key_private = wallet.session.execute(db_query).fetchone()[1]
        self.assertIn(type(encrypted_main_key_wif), (bytes, memoryview), "Encryption of database private key failed!")
        self.assertEqual(encrypted_main_key_wif.hex(), pk_wif_enc_hex)
        self.assertEqual(encrypted_main_key_private.hex(), pk_enc_hex)
        self.assertNotEqual(encrypted_main_key_private, HDKey(pk).private_byte)

    def test_security_encrypted_db_incorrect_password(self):
        if not(os.environ.get('DB_FIELD_ENCRYPTION_PASSWORD') or os.environ.get('DB_FIELD_ENCRYPTION_KEY')):
            self.skipTest("This test only runs when no encryption keys are provided")
        db = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bitcoinlib_encrypted.db')
        self.assertRaisesRegex(EncodingError, "Could not decrypt value \(password incorrect\?\): MAC check failed",
                               Wallet, 'wlt-encryption-test', db_uri=db)

    def test_security_encrypted_db_no_password(self):
        if os.environ.get('DB_FIELD_ENCRYPTION_PASSWORD') or os.environ.get('DB_FIELD_ENCRYPTION_KEY'):
            self.skipTest("This test only runs when no encryption keys are provided")
        db = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bitcoinlib_encrypted.db')
        self.assertRaisesRegex(ValueError, "Data is encrypted please provide key in environment",
                               Wallet, 'wlt-encryption-test', db_uri=db)

if __name__ == '__main__':
    main()
