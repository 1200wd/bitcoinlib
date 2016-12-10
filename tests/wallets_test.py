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
import os

from bitcoinlib.db import DEFAULT_DATABASEDIR
from bitcoinlib.wallets import HDWallet

DATABASEFILE_UNITTESTS = DEFAULT_DATABASEDIR + 'bitcoinlib.unittest.sqlite'


class TestEncodingMethods(unittest.TestCase):

    def setUp(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        self.wallet = HDWallet.create(
            name='test_wallet_create',
            databasefile=DATABASEFILE_UNITTESTS)

    def test_wallet_create(self):
        self.assertTrue(isinstance(self.wallet, HDWallet))

    def test_wallet_create_account(self):
        new_account = self.wallet.new_account(account_id=100)
        self.assertEqual(new_account.depth, 3)
        self.assertEqual(new_account.key_wif[:4], 'xprv')
        self.assertEqual(new_account.path, "m/44'/0'/100'")

    def test_wallet_create_key(self):
        new_key = self.wallet.new_key(account_id=100)
        self.assertEqual(new_key.depth, 5)
        self.assertEqual(new_key.key_wif[:4], 'xprv')
        self.assertEqual(new_key.path, "m/44'/0'/100'/0/0")

    def test_wallet_import(self):
        keystr = 'tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePy' \
                 'A7irEvBoe4aAn52'
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_import',
            key=keystr)
        self.assertEqual(wallet_import.main_key.key_wif, keystr)
        self.assertEqual(wallet_import.main_key.address, u'n3UKaXBRDhTVpkvgRH7eARZFsYE989bHjw')
        self.assertEqual(wallet_import.main_key.path, 'm')

    def test_wallet_import_account(self):
        accountkey = 'tprv8h4wEmfC2aSYN5wABvg9Wucyc4itsK2QSEmKpRyDESvqJAEiFZ18Qmz3xt9oWHBWLoq9Ks36NAkRKyHDYP6KYqYkH' \
                     'GZpdAqnj61cAgACmUY'
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_import_account',
            key=accountkey,
            account_id=99)
        self.assertEqual(wallet_import.main_key.key_wif, accountkey)
        self.assertEqual(wallet_import.main_key.address, u'mtvLfcWMQPHVjjoKPR2Pyr42tB3BAfXQ4R')
        self.assertEqual(wallet_import.main_key.path, "m/44'/0'/99'")

    def test_wallet_import_account_new_keys(self):
        accountkey = 'tprv8h4wEmfC2aSYN5wABvg9Wucyc4itsK2QSEmKpRyDESvqJAEiFZ18Qmz3xt9oWHBWLoq9Ks36NAkRKyHDYP6KYqYkH' \
                     'GZpdAqnj61cAgACmUY'
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_import_account_new_key',
            key=accountkey,
            network='testnet',
            account_id=99)
        newkey = wallet_import.new_key(account_id=99)
        newkey_change = wallet_import.new_key(account_id=99, change=1, name='change')
        wallet_import.info(detail=3)
        self.assertEqual(wallet_import.main_key.key_wif, accountkey)
        self.assertEqual(newkey.address, u'mweZrbny4fmpCmQw9hJH7EVfkuWX8te9jc')
        self.assertEqual(newkey.path, "m/44'/0'/99'/0/0")
        self.assertEqual(newkey_change.address, u'mrq34rE7e6E5mfhYeS7s2JinUX78e7r5cZ')
        self.assertEqual(newkey_change.path, "m/44'/0'/99'/1/0")
