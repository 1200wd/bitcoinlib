# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Wallet Class
#    © 2016 - 2024 February - 1200 Web Development <http://1200wd.com/>
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
import time
from random import shuffle

try:
    import mysql.connector
    import psycopg
    from psycopg import sql
except ImportError as e:
    print("Could not import all modules. Error: %s" % e)
    # from psycopg2cffi import compat  # Use for PyPy support
    # compat.register()
    pass  # Only necessary when mysql or postgres is used
from bitcoinlib.wallets import *
from bitcoinlib.encoding import USE_FASTECDSA
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey, BKeyError
from bitcoinlib.values import Value
from tests.test_custom import CustomAssertions

DATABASEFILE_UNITTESTS = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib.unittest.sqlite')
DATABASEFILE_UNITTESTS_2 = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib.unittest2.sqlite')
DATABASE_NAME = 'bitcoinlib_test'
DATABASE_NAME_2 = 'bitcoinlib2_test'

print("DATABASE USED: %s" % os.getenv('UNITTEST_DATABASE'))


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


class TestWalletCreate(unittest.TestCase):
    wallet = None
    database_uri = None

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()
        cls.wallet = Wallet.create(
            name='test_wallet_create', witness_type='legacy',
            db_uri=cls.database_uri)

    def test_wallet_create(self):
        self.assertTrue(isinstance(self.wallet, Wallet))

    def test_wallet_info(self):
        if os.name == 'nt':
            self.skipTest("Problems with Travis windows python encodings")
        self.assertIsNone(self.wallet.info())
        self.assertIn("<Wallet(name=\"test_wallet_create\", db_uri=", repr(self.wallet))

    def test_wallet_exists(self):
        self.assertTrue(wallet_exists(self.wallet.wallet_id, db_uri=self.database_uri))
        self.assertTrue(wallet_exists('test_wallet_create', db_uri=self.database_uri))

    def test_wallet_key_info(self):
        self.assertIsNone(self.wallet.main_key.key().info())
        self.assertTrue(self.wallet.main_key.as_dict())

    def test_wallet_create_account(self):
        new_account = self.wallet.new_account(account_id=100)
        self.assertEqual(new_account.depth, 3)
        self.assertEqual(new_account.wif[:4], 'xprv')
        self.assertEqual(new_account.path, "m/44'/0'/100'")

    def test_wallet_create_key(self):
        new_key = self.wallet.new_key(account_id=200)
        self.assertEqual(new_key.depth, 5)
        self.assertEqual(new_key.wif[:4], 'xprv')
        self.assertEqual(new_key.path, "m/44'/0'/200'/0/0")

    def test_wallets_list(self):
        wallets = wallets_list(db_uri=self.database_uri)
        wallet_names = [w['name'] for w in wallets]
        # self.assertEqual(wallets[0]['name'], 'test_wallet_create')
        self.assertIn('test_wallet_create', wallet_names)

    def test_delete_wallet(self):
        Wallet.create(
            name='wallet_to_remove',
            db_uri=self.database_uri)
        self.assertEqual(wallet_delete('wallet_to_remove', db_uri=self.database_uri), 1)

    def test_delete_wallet_no_private(self):
        key = ("BC19UtECk2r9PVQYhZo2RsN5SJVTmTt6NjCqGh6KH7FoVGhV9oV3f6UdyMtSzWPUBPw2S313ZJqCCNd6kTV9xbNQWzPBUVufnp"
               "sNKhh3vb3ut5bY")
        Wallet.create('delete_watch_only_wallet', keys=key, network='bitcoinlib_test', db_uri=self.database_uri)
        self.assertEqual(wallet_delete('delete_watch_only_wallet', db_uri=self.database_uri), 1)

    def test_wallet_empty(self):
        w = Wallet.create('empty_wallet_test', db_uri=self.database_uri)
        self.assertNotEqual(len(w.keys()), 1)
        master_key = w.public_master().key()
        w2 = Wallet.create('empty_wallet_test2', keys=master_key, db_uri=self.database_uri)
        w3 = Wallet.create('empty_wallet_test3', keys=master_key, db_uri=self.database_uri)
        wallet_empty('empty_wallet_test', db_uri=self.database_uri)
        wallet_empty('empty_wallet_test2', db_uri=self.database_uri)
        wallet_empty(w3.wallet_id, db_uri=self.database_uri)
        self.assertEqual(len(w.keys()), 1)
        self.assertEqual(len(w2.keys()), 1)
        self.assertEqual(len(w3.keys()), 1)
        # Test exceptions
        self.assertRaisesRegex(WalletError, "Wallet 'unknown_wallet_2' not found", wallet_empty, 'unknown_wallet_2',
                                db_uri=self.database_uri)

    def test_wallet_delete_not_empty(self):
        w = Wallet.create('unempty_wallet_test', network='bitcoinlib_test', db_uri=self.database_uri)
        w.utxos_update()
        self.assertRaisesRegex(WalletError, "still has unspent outputs. Use 'force=True' to delete this wallet",
                                wallet_delete, 'unempty_wallet_test', db_uri=self.database_uri)
        self.assertTrue(wallet_delete('unempty_wallet_test', db_uri=self.database_uri, force=True))

    def test_delete_wallet_exception(self):
        self.assertRaisesRegex(WalletError, '', wallet_delete, 'unknown_wallet', db_uri=self.database_uri)

    def test_wallet_unknown_error(self):
        self.assertRaisesRegex(WalletError, "Wallet 'test_wallet_create_errors10' not found",
                                Wallet, 'test_wallet_create_errors10', db_uri=self.database_uri)

    def test_wallet_duplicate_key_for_path(self):
        nkfp = self.wallet.key_for_path("m/44'/0'/100'/1200/1200")
        nkfp2 = self.wallet.key_for_path("m/44'/0'/100'/1200/1200")
        self.assertEqual(nkfp.key().wif(), nkfp2.key().wif())

    def test_wallet_key_for_path_normalized(self):
        nkfp = self.wallet.key_for_path("m/44h/0p/100H/1200/1201")
        nkfp2 = self.wallet.key_for_path("m/44'/0'/100'/1200/1201")
        self.assertEqual(nkfp.key().wif(), nkfp2.key().wif())

    def test_wallet_create_with_passphrase(self):
        passphrase = "always reward element perfect chunk father margin slab pond suffer episode deposit"
        wlt = Wallet.create("wallet-passphrase", keys=passphrase, network='testnet', witness_type='legacy',
                            db_uri=self.database_uri)
        key0 = wlt.get_key()
        self.assertEqual(key0.address, "mqDeXXaFnWKNWhLmAae7zHhZDW4PMsLHPp")

    def test_wallet_create_with_passphrase_litecoin(self):
        passphrase = "always reward element perfect chunk father margin slab pond suffer episode deposit"
        wlt = Wallet.create("wallet-passphrase-litecoin", keys=passphrase, network='litecoin',
                            witness_type='legacy', db_uri=self.database_uri)
        keys = wlt.get_keys(number_of_keys=5)
        self.assertEqual(keys[4].address, "Li5nEi62nAKWjv6fpixEpoLzN1pYFK621g")

    def test_wallet_create_change_name(self):
        wlt = Wallet.create('test_wallet_create_change_name', db_uri=self.database_uri)
        wlt.name = 'wallet_renamed'
        wlt2 = Wallet('wallet_renamed', db_uri=self.database_uri)
        self.assertEqual(wlt2.name, 'wallet_renamed')

    def test_wallet_create_errors(self):
        Wallet.create('test_wallet_create_errors', db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Wallet with name 'test_wallet_create_errors' already exists",
                                Wallet.create, 'test_wallet_create_errors', db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Only bip32 or single key scheme's are supported at the moment",
                                Wallet.create, 'test_wallet_create_errors2', scheme='raar',
                                db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Wallet name '123' invalid, please include letter characters",
                                Wallet.create, '123', db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Please enter wallet name",
                                Wallet.create, '', db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Witness type unknown not supported at the moment",
                                Wallet.create, '', witness_type='unknown', db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Multisig wallets should use bip32 scheme not single",
                                Wallet.create, 'test_wallet_create_errors_multisig', keys=[HDKey(), HDKey()],
                                scheme='single', db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Password protected multisig wallets not supported",
                                Wallet.create, 'test_wallet_create_errors_multisig2', keys=[HDKey(), HDKey()],
                                password='geheim', db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Number of keys required to sign is greater then number of keys provided",
                                Wallet.create, 'test_wallet_create_errors_multisig3', keys=[HDKey(), HDKey()],
                                sigs_required=3, db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError,
                                "Network from key \(litecoin\) is different then specified network \(bitcoin\)",
                                Wallet.create, 'test_wallet_create_errors_multisig4',
                                keys=[HDKey(), HDKey(network='litecoin')], db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Invalid key or address: zwqrC7h9pRj7SBhLRDG4FnkNBRQgene3y3",
                                Wallet.create, 'test_wallet_create_errors4', keys='zwqrC7h9pRj7SBhLRDG4FnkNBRQgene3y3',
                                db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Invalid key or address: zwqrC7h9pRj7SBhLRDG4FnkNBRQgene3y3",
                                Wallet.create, 'test_wallet_create_errors4', keys='zwqrC7h9pRj7SBhLRDG4FnkNBRQgene3y3',
                                db_uri=self.database_uri)
        k = HDKey(network='litecoin').wif_private()
        self.assertRaisesRegex(WalletError, "Invalid key or address",
                                Wallet.create, 'test_wallet_create_errors5', keys=k, network='bitcoin',
                                db_uri=self.database_uri)
        k = HDKey().subkey_for_path('m/1/2/3/4/5/6/7')
        self.assertRaisesRegex(WalletError, "Depth of provided public master key 7 does not correspond with key path",
                                Wallet.create, 'test_wallet_create_errors7', keys=k,
                                db_uri=self.database_uri)

    def test_wallet_rename_duplicate(self):
        Wallet.create('test_wallet_rename_duplicate1', db_uri=self.database_uri)
        w2 = Wallet.create('test_wallet_rename_duplicate2', db_uri=self.database_uri)

        def test_func():
            w2.name = 'test_wallet_rename_duplicate1'

        self.assertRaisesRegex(WalletError, "Wallet with name 'test_wallet_rename_duplicate1' already exists",
                                test_func)

    def test_wallet_as_dict_json(self):
        wallet = Wallet.create("test_wallet_as_dict_json", db_uri=self.database_uri, network='bitcoinlib_test')
        self.assertTrue(wallet.as_dict())
        self.assertTrue(wallet.as_json())

    def test_wallet_create_bip38(self):
        if not USING_MODULE_SCRYPT:
            self.skipTest('Need scrypt module to test BIP38 wallets')
        passphrase = "region kite swamp float card flag chalk click gadget share wage clever"
        k = HDKey().from_passphrase(passphrase, witness_type='legacy')
        ke = k.encrypt('hoihoi')
        w = wallet_create_or_open('kewallet', ke, password='hoihoi', network='bitcoin', witness_type='legacy',
                                  db_uri=self.database_uri)
        self.assertEqual(k.private_hex, w.main_key.key_private.hex())

    def test_wallet_create_bip38_segwit(self):
        if not USING_MODULE_SCRYPT:
            self.skipTest('Need scrypt module to test BIP38 wallets')
        passphrase = "region kite swamp float card flag chalk click gadget share wage clever"
        k = HDKey().from_passphrase(passphrase)
        ke = k.encrypt('hoihoi')
        w = wallet_create_or_open('kewallet', ke, password='hoihoi', network='bitcoin', db_uri=self.database_uri)
        self.assertEqual(k.private_hex, w.main_key.key_private.hex())

    @classmethod
    def tearDownClass(cls):
        del cls.database_uri
        del cls.wallet


class TestWalletImport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()

    def test_wallet_import(self):
        keystr = 'tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePy' \
                 'A7irEvBoe4aAn52'
        wallet_import = Wallet.create(
            db_uri=self.database_uri,
            name='test_wallet_import',
            network='testnet',
            keys=keystr)
        wallet_import.new_account(account_id=99)
        self.assertEqual(wallet_import.main_key.wif, keystr)
        self.assertEqual(wallet_import.main_key.address, u'n3UKaXBRDhTVpkvgRH7eARZFsYE989bHjw')
        self.assertEqual(wallet_import.main_key.path, 'm')

    def test_wallet_import_account(self):
        accountkey = 'tprv8h4wEmfC2aSckSCYa68t8MhL7F8p9xAy322B5d6ipzY5ZWGGwksJMoajMCqd73cP4EVRygPQubgJPu9duBzPn3QV' \
                     '8Y7KbKUnaMzx9nnsSvh'
        wallet_import = Wallet.create(
            db_uri=self.database_uri,
            name='test_wallet_import_account',
            keys=accountkey,
            network='testnet',
            account_id=99)
        self.assertEqual(wallet_import.main_key.wif, accountkey)
        self.assertEqual(wallet_import.main_key.address, u'mowRx2TNXTgRSUmepjqhx5C1TTigmHLGRh')
        self.assertEqual(wallet_import.main_key.path, "M")
        self.assertEqual(wallet_import.main_key.account_id, 99)
        self.assertEqual(wallet_import.default_account_id, 99)

    def test_wallet_import_account_new_keys(self):
        accountkey = 'tprv8h4wEmfC2aSckSCYa68t8MhL7F8p9xAy322B5d6ipzY5ZWGGwksJMoajMCqd73cP4EVRygPQubgJPu9duBzPn3QV' \
                     '8Y7KbKUnaMzx9nnsSvh'
        wallet_import = Wallet.create(
            db_uri=self.database_uri,
            name='test_wallet_import_account_new_key',
            keys=accountkey,
            network='testnet',
            account_id=99)
        newkey = wallet_import.new_key(account_id=99)
        newkey_change = wallet_import.new_key_change(account_id=99, name='change')
        self.assertEqual(wallet_import.main_key.wif, accountkey)
        self.assertEqual(newkey.address, u'mxdLD8SAGS9fe2EeCXALDHcdTTbppMHp8N')
        self.assertEqual(newkey.path, "M/0/1")
        self.assertEqual(newkey.account_id, 99)
        self.assertEqual(newkey_change.address, u'mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2')
        self.assertEqual(newkey_change.path, "M/1/0")
        self.assertEqual(newkey_change.account_id, 99)

    def test_wallet_import_public_wallet(self):
        pubkey = 'tpubDDkyPBhSAx8DFYxx5aLjvKH6B6Eq2eDK1YN76x1WeijE8eVUswpibGbv8zJjD6yLDHzVcqWzSp2fWVFhEW9XnBssFqMwt' \
                 '9SrsVeBeqfBbR3'
        pubwal = Wallet.create(
            db_uri=self.database_uri,
            name='test_wallet_import_public_wallet',
            keys=pubkey,
            network='testnet',
            account_id=0)
        newkey = pubwal.new_key()
        self.assertEqual(newkey.address, u'myitDjbzYpUTShv9CyXRJKXtM4uRgSqa3A')

    def test_wallet_import_litecoin(self):
        accountkey = 'Ltpv71G8qDifUiNet6mn25D7GPAVLZeaFRWzDABxx5xNeigVpFEviHK1ZggPS1kbtegB3U2i8w6ToNfM5sdvEQPW' \
                     'tov4KWyQ5NxWUd3oDWXQb4C'
        wallet_import = Wallet.create(
            db_uri=self.database_uri,
            name='test_wallet_litecoin',
            keys=accountkey,
            network='litecoin')
        newkey = wallet_import.new_key()
        self.assertEqual(wallet_import.main_key.wif, accountkey)
        self.assertEqual(newkey.address, u'LZj8MnR6tRgLNKUBSfd2pD2czA4F9G5oGk')
        self.assertEqual(newkey.path, "m/44'/2'/0'/0/1")

    def test_wallet_import_key_network_error(self):
        w = Wallet.create(
            name='Wallet Error',
            db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError,
                                "Network litecoin not available in this wallet, please create an account "
                                "for this network first.",
                                w.import_key, 'T43gB4F6k1Ly3YWbMuddq13xLb56hevUDP3RthKArr7FPHjQiXpp',
                                network='litecoin')

    def test_wallet_import_hdwif(self):
        # p2wpkh
        wif = \
            'zpub6s7HTSrGmNUWSgfbDMhYbXVuxA14yNnycS25v6ogicEauzUrRUkuCLQUWbJXP1NyXNqGmwpU6hZw7vr22a4yspwH8XQFjjwRmxC' \
            'KkXdDAXN'
        w = Wallet.create("wif_import_p2wpkh", wif, db_uri=self.database_uri)
        self.assertEqual(w.get_key().address, "bc1qruvyu8f2tg06zhysytdsc3qlngnpfzn0juwssx")
        self.assertEqual(w.get_key_change().address, "bc1qg6h45txt82x87uvv3ndm82xsf3wjknq8j7sufh")

        # p2sh_p2wpkh
        wif = \
            'ypub6YMgBd4GfQjtxUf8ExorFUQEpBfUYTDz7E1tvfNgDqZeDEUuNNVXSNfsebis2cyeqWYXx6yaBBEQV7sJW3NGoXw5wsp9kkEsB2D' \
            'qiVquYLE'
        w = Wallet.create("wif_import_p2sh_p2wpkh", wif, db_uri=self.database_uri)
        self.assertEqual(w.get_key().address, "3EFDqEWcrzyidoCXhxaUDB28pVtgX3YuiR")
        self.assertEqual(w.get_key_change().address, "33Un3fDSdT2hsuqyuHiCci1GyUbiyZEWHW")

        # p2wsh
        wif1 = \
            'Zpub74arK1zZNbJYvbMz6wwu2vvcSyB421ePA2p65AD1vaUA5ApzbPLwe3yRDHFgEoBZiLbTzdBPJyPMMaTNsmGkv76t2uD2d9ACqpv' \
            'vBa5zbv9'
        wif2 = \
            'Zpub74JTMKMB9cTWwE9Hs4UVaHvddqPtR51D99x2B5EGyXyxEg3PW77vfmD15RZ86TVdwwwuUaCueBtvaL921mgyKe9Ya6LHCaMXnEp' \
            '1PMw4vDy'
        w = Wallet.create("wif_import_p2wsh", [wif1, wif2], cosigner_id=0, db_uri=self.database_uri)
        self.assertEqual(w.get_key().address, "bc1qhk5pd2fh0uea8z2wkceuf8eqlxsnkxm0hlt6qvfv346evqnfyumqucpqew")
        self.assertEqual(w.get_key_change().address, "bc1qyn73qh408ry38twxnj4aqzuyv7j6euwhwt2qtzayg673vtw2a4rsn7jlek")

        # p2sh_p2wsh
        wif1 = \
            'Ypub6kLT3k6fGK3ifMJwLB8BxiG8MGv5gG7uQhymshYiw2Lp5B3yuQJfn8KB5dL3fZnraEErTXmXp2cSKbACmxcRQ7AbcRrsnhns7Zw' \
            'zQb4kGgF'
        wif2 = \
            'Ypub6jkwv4tzCZJNe6j1JHZgwUmj6yCi5iEBNHrP1RDFyR13RwRNB5foJWeinpcBTqfv2uUe7mWSwsF1am4cVLN99xrkADPWrDick3S' \
            'aP8nxY8N'
        wif3 = \
            'Ypub6jVwyh6yYiRoA5zAnGY1g88G5LdaxkHX65d2kSW97yTBAF1RQwAs3UGPz8bX7LvQfg8tc9MQz7eZ79qVigELqSJzfFbGmPak4PZ' \
            'rvW8fZXy'
        w = Wallet.create("wif_import_p2sh_p2wsh", [wif1, wif2, wif3], sigs_required=2, cosigner_id=0,
                          db_uri=self.database_uri)
        self.assertEqual(w.get_key().address, "3BeYQTUgrGPQMHDJcch6mF7G7sRrNYkRhP")
        self.assertEqual(w.get_key_change().address, "3PFD1qkgbaeeDnX38Smerb5vAPBkDVkhcm")

    def test_wallet_import_master_key(self):
        k = HDKey()
        w = Wallet.create('test_wallet_import_master_key', keys=k.public_master(),
                          db_uri=self.database_uri)
        self.assertFalse(w.main_key.is_private)
        self.assertRaisesRegex(WalletError, "Please supply a valid private BIP32 master key with key depth 0",
                                w.import_master_key, k.public())
        self.assertRaisesRegex(WalletError, "Network of Wallet class, main account key and the imported private "
                                             "key must use the same network",
                                w.import_master_key, HDKey(network='litecoin'))
        self.assertRaisesRegex(WalletError, "This key does not correspond to current public master key",
                                w.import_master_key, HDKey())
        w.import_master_key(k.wif_private())
        self.assertTrue(w.main_key.is_private)

        k2 = HDKey()
        w2 = Wallet.create('test_wallet_import_master_key2', keys=k2.subkey_for_path("m/32'"), scheme='single',
                           db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Main key is already a private key, cannot import key",
                                w2.import_master_key, k2)
        w2.main_key = None
        self.assertRaisesRegex(WalletError, "Main wallet key is not an WalletKey instance",
                                w2.import_master_key, k2)

        k3 = HDKey()
        w3 = Wallet.create('test_wallet_import_master_key3', keys=k3.subkey_for_path("m/32'").public(),
                           scheme='single', db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "Current main key is not a valid BIP32 public master key",
                                w3.import_master_key, k3)


class TestWalletExport(unittest.TestCase):
    database_uri = None

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()

    def test_wallet_export_hdwifs(self):
        # p2wpkh
        p = 'garage million cheese nephew original subject pass reward month practice advance decide'
        w = Wallet.create("wif_export_p2wpkh", p, network='bitcoin', witness_type='segwit',
                          db_uri=self.database_uri)
        wif = 'zpub6s7HTSrGmNUWSgfbDMhYbXVuxA14yNnycS25v6ogicEauzUrRUkuCLQUWbJXP1NyXNqGmwpU6hZw7vr22a4yspwH8XQFjjwRmx' \
              'CKkXdDAXN'
        self.assertEqual(w.account(0).key().wif_public(witness_type=w.witness_type), wif)
        self.assertEqual(w.wif(is_private=False), wif)

        # # p2sh_p2wpkh
        p = 'cluster census trash van rack skill feed inflict mixture vocal crew sea'
        w = Wallet.create("wif_export_p2sh_p2wpkh", p, network='bitcoin', witness_type='p2sh-segwit',
                          db_uri=self.database_uri)
        wif = 'ypub6YMgBd4GfQjtxUf8ExorFUQEpBfUYTDz7E1tvfNgDqZeDEUuNNVXSNfsebis2cyeqWYXx6yaBBEQV7sJW3NGoXw5wsp9kkEsB2' \
              'DqiVquYLE'
        self.assertEqual(w.wif(is_private=False), wif)

        # p2wsh
        p1 = 'cave display deposit habit surround erupt that melt grace upgrade pink remove'
        p2 = 'question game start distance ritual frozen hint teach decorate boat sure mad'
        wifs = [
            'Zpub74arK1zZNbJYvbMz6wwu2vvcSyB421ePA2p65AD1vaUA5ApzbPLwe3yRDHFgEoBZiLbTzdBPJyPMMaTNsmGkv76t2uD2d9ACqpvv'
            'Ba5zbv9',
            'Zpub74JTMKMB9cTWwE9Hs4UVaHvddqPtR51D99x2B5EGyXyxEg3PW77vfmD15RZ86TVdwwwuUaCueBtvaL921mgyKe9Ya6LHCaMXnEp1'
            'PMw4vDy']
        w = Wallet.create("wif_export_p2wsh", [p1, p2], witness_type='segwit', network='bitcoin', cosigner_id=0,
                          db_uri=self.database_uri)
        for wif in w.wif(is_private=False):
            self.assertIn(wif, wifs)

        # p2sh_p2wsh
        p1 = 'organ pave cube daring travel thrive average solid wolf type refuse camp'
        p2 = 'horror brown web jaguar man current glow step harvest zero flush super'
        p3 = 'valid circle lounge pipe alone stool system off until physical juice opera'
        wifs = [
            'Ypub6kLT3k6fGK3ifMJwLB8BxiG8MGv5gG7uQhymshYiw2Lp5B3yuQJfn8KB5dL3fZnraEErTXmXp2cSKbACmxcRQ7AbcRrsnhns7Zwz'
            'Qb4kGgF',
            'Ypub6jkwv4tzCZJNe6j1JHZgwUmj6yCi5iEBNHrP1RDFyR13RwRNB5foJWeinpcBTqfv2uUe7mWSwsF1am4cVLN99xrkADPWrDick3Sa'
            'P8nxY8N',
            'Ypub6jVwyh6yYiRoA5zAnGY1g88G5LdaxkHX65d2kSW97yTBAF1RQwAs3UGPz8bX7LvQfg8tc9MQz7eZ79qVigELqSJzfFbGmPak4PZr'
            'vW8fZXy']
        w = Wallet.create("wif_export_p2sh_p2wsh", [p1, p2, p3], sigs_required=2, witness_type='p2sh-segwit',
                          network='bitcoin', cosigner_id=0, db_uri=self.database_uri)
        for wif in w.wif(is_private=False):
            self.assertIn(wif, wifs)


class TestWalletKeys(unittest.TestCase):
    private_wif = None
    database_uri = None
    wallet = None

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()
        cls.private_wif = 'xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzF9ySUHZw5qJkk5LCALAhXS' \
                          'XoCmCSnStRvgwLBtcbGsg1PeKT2en'
        cls.wallet = Wallet.create(
            keys=cls.private_wif,
            name='test_wallet_keys',
            db_uri=cls.database_uri)
        cls.wallet.new_key()
        cls.wallet.new_key_change()

    def test_wallet_addresslist(self):
        expected_addresslist = ['1B8gTuj778tkrQV1e8qjcesoZt9Cif3VEp', '1LS8zYrkgGpvJdtMmUdU1iU4TUMQh6jjF1',
                                '1K7S5am1hLfugEFWR9ENfEBpUrMbFhqtoh', '1EByrVS1sc6TDihJRRRtMAnKTaAVSZAgtQ',
                                '1KyLsZS2JwWdfvDZ5g8vhbanqjbNwKUseK', '1J6jppU5mWf4ausGfHMumrKrztpDKq2MrD',
                                '12ypWFxJSKWknmvxdSeStWCyVDBi8YyXpn', '1A7wRpnstUiA33rxW1i33b5qqaTsS4YSNQ',
                                '13uQKuiWwWp15BsEijnpKZSuTuHVTpZMvP']
        self.assertListEqual(self.wallet.addresslist(depth=-1), expected_addresslist)

    def test_wallet_keys_method_masterkey(self):
        self.assertEqual(self.wallet.keys(name='test_wallet_keys', depth=0)[0].wif, self.private_wif)

    def test_wallet_keys_method_account(self):
        account_wif = 'xprv9z87HKmxfjVRRyEt7zBWCctmJvqcowfWwKUeJnLjNyykvq5sDGm1yo5qTWWAj1gXsRd2b8GayjujPz1arbKsS3tnwQ' \
                      'Fz8nMip3pFBYjPT1b'
        self.assertEqual(self.wallet.keys_accounts()[0].wif, account_wif)

    def test_wallet_keys_method_keys_addresses(self):
        address_wifs = [
            'xprvA3xQPpbB95TCpX9eL2kVLrJKt4KZmzePogQFmefPABpm7gLghfMW5sK2dbogzaLV3EgaaHeUZTBEJ7irBEJAj5E9vpQ5byYCkzcn'
            'RAwpG7X',
            'xprvA3xQPpbB95TCrKAaUwPCwXR2iyAyg3SVQntdFnSzAGX3Wcr6XzocH31fznmjwufTyFcWuAghfb3bwfmQCHDQtKckEewjPWX8qDU7'
            'bhoLVVS',
            'xprvA3ALLPsyMi2DUrZbSRegEhrdNNg1kwM6n6zh3cv9Qx9ZYoHwgk44TwympUPV3UuQ5YNjubBsF2QbBfJqujoiFDKLHnphCpLmBzeER'
            'yZeFRE'
        ]
        self.assertListEqual([k.wif for k in self.wallet.keys_addresses()], address_wifs)

    def test_wallet_keys_method_keys_payment(self):
        self.assertEqual(self.wallet.keys_address_payment()[0].address, '1J6jppU5mWf4ausGfHMumrKrztpDKq2MrD')

    def test_wallet_keys_method_keys_change(self):
        self.assertEqual(self.wallet.keys_address_change()[0].address, '13uQKuiWwWp15BsEijnpKZSuTuHVTpZMvP')

    def test_wallet_keys_single_key(self):
        # self.db_remove()
        wk = 'xprv9s21ZrQH143K3tCgu8uhkA2fw9F9opbvoNNzh5wcuEvNHbCU6Kg3c6dam2a6cw4UYeDxAsgBorAqXp2nsoYS84DqYMwkzxZ15' \
             'ujRHzmBMxE'
        w = Wallet.create('test_wallet_keys_single_key', wk, scheme='single', db_uri=self.database_uri)
        self.assertEqual(w.new_key(), w.new_key())
        self.assertRaisesRegex(WalletError,
                                "Single wallet has only one \(master\)key. Use get_key\(\) or main_key\(\) method",
                                w.get_keys)

    def test_wallet_create_uncompressed_masterkey(self):
        wlt = wallet_create_or_open('uncompressed_test', keys='68vBWcBndYGLpd4KmeNTk1gS1A71zyDX6uVQKCxq6umYKyYUav5',
                                    network='bitcoinlib_test', witness_type='legacy', db_uri=self.database_uri)
        wlt.get_key()
        wlt.utxos_update()
        self.assertIsNone(wlt.sweep('216xtQvbcG4o7Yz33n7VCGyaQhiytuvoqJY', broadcast=True).error)

    def test_wallet_create_invalid_key(self):
        # Test for issue #206
        key_correct = HDKey(witness_type='segwit', network='testnet')
        key_invalid = HDKey(witness_type='segwit', network='testnet')
        wallet_create_or_open('my-awesome-wallet55', keys=key_correct, witness_type='segwit', network='testnet',
                                  db_uri=self.database_uri)
        self.assertRaisesRegex(AssertionError, '', Wallet, 'my-awesome-wallet55', main_key_object=key_invalid,
                                db_uri=self.database_uri)

    def test_wallet_single_key(self):
        wlt = wallet_create_or_open('single_key', scheme='single', network='bitcoinlib_test',
                                    db_uri=self.database_uri)
        wlt.utxos_update()
        transaction = wlt.transaction_create([('21DQCyZTNRoAccG1TWz9YaffDUKzZf6JWii', 90000000)])
        transaction.sign()
        self.assertTrue(transaction.verify())

    def test_wallet_single_key_segwit(self):
        wlt = wallet_create_or_open('single_key_segwit', scheme='single', network='litecoin_testnet',
                                    witness_type='segwit', db_uri=self.database_uri)
        self.assertEqual(wlt.addresslist()[0][:5], 'tltc1')

    def test_wallet_single_key_main_key(self):
        w = Wallet.create('multisig_with_single_key', [HDKey().public_master_multisig(), HDKey(key_type='single')],
                          sigs_required=2, db_uri=self.database_uri)
        w.new_key()
        self.assertEqual(len(w.keys_addresses()), 1)

    def test_wallet_private_parts(self):
        # as_json and as_dict should contain no private keys in any form
        wif = 'xprv9s21ZrQH143K3uhe9xrPfYfhvFBMARCjWjrgDZFJn7Nk5Gd6fzscc4U6wnFbhA989AN3V6hmPWZfGDi1ZTastgT1FmzLy8Nf5fJpZjqA8k7'
        private_hex = 'ffbf97886300c36e747a71d227a3132b209109a9e5296659f5aa03356ca27e1f'
        secret = 115678290018782943471210007860528561263328164009987126706295777426273334361631
        k = HDKey(wif)
        w = wallet_create_or_open('wlttest', k, db_uri=self.database_uri)
        w_json = w.as_json()
        self.assertFalse(wif in w_json)
        self.assertFalse(private_hex in w_json)
        self.assertFalse(str(secret) in w_json)

        wmk_json = w.main_key.key().as_json()
        self.assertFalse(wif in wmk_json)
        self.assertFalse(private_hex in wmk_json)
        self.assertFalse(str(secret) in wmk_json)
        self.assertTrue(wif in w.main_key.key().as_json(include_private=True))

        self.assertFalse(wif in str(w.main_key.as_dict()))
        self.assertTrue(wif in str(w.main_key.as_dict(include_private=True)))

        w.utxo_add(w.main_key.address, 200000, '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5', 0, 1)
        t = w.sweep(w.get_key().address, fee=2000)
        t_json = t.as_json()
        self.assertFalse(wif in t_json)
        self.assertFalse(private_hex in t_json)
        self.assertFalse(str(secret) in t_json)

        wif2 = 'xprv9s21ZrQH143K3mEc645dz1wEo4F1Sy8mNKdXZxFWniS7ZNqSgo2CS7chiDxqvVHJbQeR7RsMPaUaeTL6nwD9ChnwJw4LHz' \
               'Ni2xTDTQ8t1Hn'
        private_hex2 = 'e68f716a02929e29c5b9b3d8a1a1b5424dc63ea03eb9b9990cf0ffaf396789fc'
        secret2 = 104285397059777051994770481926675935425657204513917549168323819901909731871228
        k2 = HDKey(wif2)

        wms = wallet_create_or_open('wlttest_ms', [k, k2], cosigner_id=0, db_uri=self.database_uri)
        w_json = wms.as_json()
        self.assertFalse('"xprv' in w_json)
        self.assertFalse(wif in w_json)
        self.assertFalse(private_hex in w_json)
        self.assertFalse(str(secret) in w_json)
        self.assertFalse(wif2 in w_json)
        self.assertFalse(private_hex2 in w_json)
        self.assertFalse(str(secret2) in w_json)

    def test_wallet_key_create_from_key(self):
        k1 = HDKey(network='testnet')
        k2 = HDKey(network='testnet')
        w1 = Wallet.create('network_mixup_test_wallet', network='litecoin', db_uri=self.database_uri)
        wk1 = WalletKey.from_key('key1', w1.wallet_id, w1.session, key=k1.address_obj)
        self.assertEqual(wk1.network.name, 'testnet')
        self.assertRaisesRegex(WalletError, "Specified network and key network should be the same",
                                WalletKey.from_key, 'key2', w1.wallet_id, w1.session, key=k2.address_obj,
                                network='bitcoin')
        w2 = Wallet.create('network_mixup_test_wallet2', network='litecoin', db_uri=self.database_uri)
        wk2 = WalletKey.from_key('key1', w2.wallet_id, w2.session, key=k1)
        self.assertEqual(wk2.network.name, 'testnet')
        self.assertRaisesRegex(WalletError, "Specified network and key network should be the same",
                                WalletKey.from_key, 'key2', w2.wallet_id, w2.session, key=k2,
                                network='bitcoin')
        wk3 = WalletKey.from_key('key3', w2.wallet_id, w2.session, key=k1)
        self.assertEqual(wk3.name, 'key1')
        wk4 = WalletKey.from_key('key4', w2.wallet_id, w2.session, key=k1.address_obj)
        self.assertEqual(wk4.name, 'key1')
        k = HDKey().public_master()
        w = Wallet.create('pmtest', network='litecoin', db_uri=self.database_uri)
        wk1 = WalletKey.from_key('key', w.wallet_id, w.session, key=k)
        self.assertEqual(wk1.path, 'M')
        # Test __repr__ method
        self.assertIn("<WalletKey(key_id=", repr(wk1))
        # Test change key name
        wk1.name = 'new_name'
        self.assertEqual(wk1.name, 'new_name')

    def test_wallet_key_exceptions(self):
        w = Wallet.create('test_wallet_key_not_found', db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, 'Key with id 1000000 not found', WalletKey, 1000000, w.session)
        self.assertRaisesRegex(BKeyError, "Specified key \['litecoin', 'litecoin_legacy'\] is from different "
                                           "network then specified: bitcoin",
                                WalletKey.from_key, '', w.wallet_id, w.session,
                                'T3Er8TQUMjkor8JBGm6aPqg1FA2L98MSK52htgNDeSJmfhLYTpgN')
        self.assertRaisesRegex(WalletError, "", w.get_key, cosigner_id=10)

    def test_wallet_key_public_leaks(self):
        w = wallet_create_or_open("wallet_private", network='testnet', db_uri=self.database_uri)
        wk = w.public_master()
        self.assertIsNone(wk._hdkey_object.private_hex)
        self.assertIsNone(wk._dbkey)

        w2 = wallet_create_or_open('wallet_public', network='testnet', keys=wk, db_uri=self.database_uri)
        self.assertFalse(w2.main_key.is_private)
        self.assertIsNone(w2.main_key.key_private)

    def test_wallet_key_derivation_bitcoin_core(self):
        pkwif = \
            "tprv8ZgxMBicQKsPdwXQbgq89TZiKB2jiPQqpG86D2TxkikdjuPSFBJX7kiuSqXUR3vjAajk84ekJAgDbNtm72DcNUqgrasvVyL4ugqg9M2jLNk"
        wallet_delete_if_exists('wallet_bitcoinnode_keytest', force=True)
        w = wallet_create_or_open('wallet_bitcoinnode_keytest', pkwif, network='testnet', witness_type='segwit',
                                  key_path=KEY_PATH_BITCOINCORE)
        expected_address = "tb1qet37ftfmj9qlnajf5370zymwdx0dxrg5s08406"
        self.assertEqual(w.get_key().address, expected_address)

        bitcoincore_legacy_keys = [
            ("cT6RRQfmAKws5DiXeMqDoKQkdkpDeTxjR6hQSUMbAEYrQLowE2dA", "tb1qqqa20559evephf7k5vdl4kmkkkwzwq4r3fdqjn",
             "m/0'/1'/33'"),
            ("cRoLN8YaDq3MTGJZh4c2eA5kNvFRaiTy1t6o2tbs2FdSF3aWjYoE", "tb1qqzckpfc338h67c3wvdfxy80xyl3duerr9lzzeh",
             "m/0'/0'/945'"),
            ("cNRJJBHoVYYgVaZg4cighgh8dTnGN35fFAbSAak9hbsRybi88uUU", "tb1qqrvr94pkh57n3gqxz9wdvcuqqjrf7syr9lcezn",
             "m/0'/0'/179'"),
            ("cRsyfCoRxb37FR55gsdePjGvc2yP2b9zmK7xAcZnrfBDYi6qLpZH", "tb1qqrnwa6047e9weadsjkw4yvmq2hpcnsez5fscvg",
             "m/0'/1'/114'"),
            ("cPGrz5DJChNGUhXNp7uLTN1QyL8uSvDCeaQXE8XGtDnGpiFkwP2t", "tb1qqywxch6yqg0n2n43p8mh2jj8xn45zu0jd6w5qr",
             "m/0'/0'/661'"),
            ("cN3ftZiCws7rpibSN4bgwxNFjrwKFv8vBAhsGfWS181wvrQdvyW4", "tb1qqxxnzft5dcarhdke6jpqjxrh5pnj3jx28rquef",
             "m/0'/0'/508'"),
            ("cV7oNGCZedJ5AB6C8no5CPAJFFCL8562CzHV2WbTAbic3nFWCKWa", "tb1qqxaf72y6jsdly92d5djp0xgghunrctu69ej4l3",
             "m/0'/0'/703'"),
            ("cPHpS6LfJBuuKCwx9zBsbiuriGF84Vz7tZVbDeQSJ5eB8nFbmXN7", "tb1qq8l2ue64setgk5jyepk8vycs0qydxy4496tx5m",
             "m/0'/0'/296'"),
            ("cSTyAscq5QdPKEnBxs5hLHgMkfd2a6xVwU8QTh8DJTKVZK6Q535Q", "tb1qqgplnyw697xsfvpccy4qtzyflzn9ke7s97l8pq",
             "m/0'/0'/335'"),
            ("cUTMrBYCya9gMsxm5aGquQGNkcyc4eduuuzY3v6NpVbWqG6ixonP", "tb1qqg8x4cdcrv83nl0zv8djzhea4kl2647zsxh36l",
             "m/0'/0'/589'"),
            ("cVzxpZERuRgwvAcWUr4U7EtMSyzEsBCziwxTofnCTQN2EVBGjM5y", "tb1qqg8fzfddxet3zq5h334jsvl8x92p04hkfj9nf9",
             "m/0'/0'/928'"),
            ("cVhPAPYdZH6wbegMiuxYcNpGuxpbrTX519n5zKVjv3EGhd9w3xDx", "tb1qq2pe4z4undtc6ry38peefsw98apxaq0w0tdyvg",
             "m/0'/0'/998'"),
            ("cPyj6ziaPWDMX1rQQ2AYgtGmCWZkqyM9tuTdwiDvuEmQ6ZkzX7NQ", "tb1qq2epkw3vph82pl4ykjpvnnjxnka2grk8uv5d6h",
             "m/0'/0'/232'"),
            ("cRgxMBzg7vLmHjpzZW7ZsFBMEhFGHZxTU8oLLMUX8EbxXjrkRzxi", "tb1qqtqk529kenvdgymmdkg070kkyfc56lf0x9rqqw",
             "m/0'/0'/375'"),
            ("cQpyG8EaGfCzq5ficwsSz73krYS1LjELg9pRiydE7K9suMmNZirm", "tb1qqt93cacv5u8e40k995qxdfmzupnjst4h44px48",
             "m/0'/0'/711'"),
            ("cNyweGkXaFJ24k91tjpSGqbpzVvwu2c63FVKtJjztBGmoKtjhjDP", "tb1qqt4uwz330sfxkh7ug9tgpc4083r7ky3vpg22w6",
             "m/0'/0'/320'"),
            ("cQzDqSPb8KUeZ48BBaQt8DuLrsP1oQUgJDnWpnBVXnhrJ7ap4vjh", "tb1qqv8qkr0g76s6m4mguxag56hf6pgtyvy2c78c77",
             "m/0'/0'/245'"),
            ("cSCv6ByFqi6FGSA3yeb2oKfvPzokeKNGWZ1q3tSkovnBkDGvxJBR", "tb1qqdj4ruf23szh4jmkjt4nzx83utp7dlhydn2532",
             "m/0'/0'/336'"),
            ("cSpXvuvzNxSBp3YwUnXTbj2qa6MBMAdcK2gZXFnG6DoXUUzJj5ga", "tb1qqdax64eywry5yjw7npll7r6jg5afe4kc3a2ysa",
             "m/0'/1'/185'"),
            ("cUE6aGgcGGCidEqHUEFamsbVitQU3wtFnMU75oz36vQj2WPRAXfc", "tb1qqwgfqwm20kryx8py0n6escew8xgjqp5whpnfx0",
             "m/0'/1'/54'"),
            ("cVdndV7n3C2ga1uXHEWuehKWnfJxidcGf5tAxEPZgSxkGgQ5qmgr", "tb1qqw3fj4v90yy0at0muk8p9pjf25tjzpgw9wgy0t",
             "m/0'/0'/302'"),
            ("cVHfUViBhR62SE3R5RBiQeTYHVFVVh4YGy9YtiGg7auMrro646Cq", "tb1qqw5gcq4rk63sxrpy2s2prtylmgkrfa2sezck6d",
             "m/0'/0'/716'"),
            ("cQGYzBYwfuyuSGeTP3iKvUxnayXuDMcXbtQ1EwjfyLUuCHnv2qR4", "tb1qq0cy7pae98rrf6688xz47ryl90kuxh4jp65ll6",
             "m/0'/0'/624'"),
            ("cNS1Ket4FxnKBa93cmgTU3psQqwGnEMGjUHeMeNHgbE2KeVDqZQd", "tb1qqs6pr5jyautze32ummxpnpwhsyzf2rvptxxm0n",
             "m/0'/1'/150'"),
            ("cMrbo3BTBYLGHry8oeXhMaWGU8GWXSLFFAyLoEWMTPeZxwxxLMRN", "tb1qqsuuw0rfrz83svvsuatg8q7j2ea5z3geahr32g",
             "m/0'/0'/157'"),
        ]

        for bc_key in bitcoincore_legacy_keys:
            k = w.key_for_path(bc_key[2])
            self.assertEqual(k.address, bc_key[1])
            self.assertEqual(k.key().wif_key(), bc_key[0])

    @classmethod
    def tearDownClass(cls):
        del cls.database_uri
        del cls.wallet


class TestWalletElectrum(unittest.TestCase):
    wallet = None

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()
        cls.pk = 'xprv9s21ZrQH143K2fuscnMTwUadsPqEbYdFQVJ1uWPawUYi7C485NHhCiotGy6Kz3Cz7ReVr65oXNwhREZ8ePrz8p7zy' \
                 'Hra82D1EGS7cQQmreK'
        cls.wallet = Wallet.create(
            keys=cls.pk,
            name='test_wallet_electrum',
            db_uri=cls.database_uri)
        cls.wallet.key_path = ["m", "change", "address_index"]
        workdir = os.path.dirname(__file__)
        with open('%s/%s' % (workdir, 'electrum_keys.json')) as f:
            cls.el_keys = json.load(f)
        for i in range(20):
            cls.wallet.key_for_path('m/0/%d' % i, name='-test- Receiving #%d' % i)
        for i in range(6):
            cls.wallet.key_for_path('m/1/%d' % i, name='-test- Change #%d' % i)

    def test_electrum_keys(self):
        for key in self.wallet.keys():
            if key.name[:6] == '-test-' and key.path not in ['m/0', 'm/1'] and key.path[3:] != 'm/4':
                self.assertIn(key.address, self.el_keys.keys(),
                              msg='Key %s (%s, %s) not found in Electrum wallet key export' %
                                  (key.name, key.path, key.address))

    def test_wallet_electrum_p2pkh(self):
        phrase = 'smart donor clever resource stool denial wink under oak sand limb wagon'
        wlt = Wallet.create('wallet_electrum_p2pkh', phrase, network='bitcoin', witness_type='segwit',
                            db_uri=self.database_uri)
        self.assertEqual(wlt.get_key().address, 'bc1qjz5l6mej6ptqlggfvdlys8pfukwqp8xnu0mn5u')
        self.assertEqual(wlt.get_key_change().address, 'bc1qz4tr569wfs2fuekgcjtdlz0eufk7rfs8gnu5j9')

    def test_wallet_electrum_p2sh_p2wsh(self):
        phrase1 = 'magnet voice math okay castle recall arrange music high sustain require crowd'
        phrase2 = 'wink tornado honey delay nest sing series timber album region suit spawn'
        wlt = Wallet.create('wallet_electrum_p2sh_p2wsh', [phrase1, phrase2], network='bitcoin', cosigner_id=0,
                            witness_type='p2sh-segwit', db_uri=self.database_uri)
        self.assertEqual(wlt.get_key().address, '3ArRVGXfqcjw68XzUZr4iCCemrPoFZxm7s')
        self.assertEqual(wlt.get_key_change().address, '3FZEUFf59C3psUUiKB8TFbjsFUGWD73QPY')

    @classmethod
    def tearDownClass(cls):
        del cls.wallet


class TestWalletMultiCurrency(unittest.TestCase):
    wallet = None

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()
        cls.pk = 'xprv9s21ZrQH143K4478MENLXpSXSvJSRYsjD2G3sY7s5sxAGubyujDmt9Qzfd1me5s1HokWGGKW9Uft8eB9dqryybAcFZ5JAs' \
                 'rg84jAVYwKJ8c'
        cls.wallet = Wallet.create(
            keys=cls.pk, network='dogecoin', witness_type='legacy',
            name='test_wallet_multicurrency',
            db_uri=cls.database_uri)

        cls.wallet.new_account(network='litecoin')
        cls.wallet.new_account(network='bitcoin')
        cls.wallet.new_account(network='testnet')
        cls.wallet.new_account(network='dogecoin')
        cls.wallet.new_key()
        cls.wallet.new_key()
        cls.wallet.new_key(network='bitcoin')

    def test_wallet_multiple_networks_defined(self):
        networks_expected = sorted(['litecoin', 'bitcoin', 'dogecoin', 'testnet'])
        networks_wlt = sorted([x.name for x in self.wallet.networks()])
        self.assertListEqual(networks_wlt, networks_expected,
                             msg="Not all network are defined correctly for this wallet")

    def test_wallet_multiple_networks_default_addresses(self):
        addresses_expected = ['D5RuWXkLEWavHvFBanskaP2LFKTYg6J6fU',
            'DHUXe7QJfCo1gewXHsLyBB98zd6quWyxEK',
            'DSaM5oJ7rRbrVcSYuTc5KE21paw9kWqLf7',
            'DToob5uhE3hCMaCZxYd4S5eunFgr5f8XhD',
            'DAPKhNHuidSyzhBypVdnc5fRY3pcvihLgs']
        self.assertListEqual(self.wallet.addresslist(network='dogecoin'), addresses_expected)

    def test_wallet_multiple_networks_import_key(self):
        pk_bitcoin = 'xprv9s21ZrQH143K3RBvuNbSwpAHxXuPNWMMPfpjuX6ciwo91HpYq6gDLjZuyrQCPpo4qBDXyvftN7MdX7SBVXeGgHs' \
                     'TijeHZLLgnukZP8dDkjC'
        res = self.wallet.import_key(pk_bitcoin, network='bitcoin')
        self.assertEqual(res.address, '1Hhyezo3XUC1BYpwLmp2AueWWw26xgXq7B')

    def test_wallet_multiple_networks_import_key_network(self):
        pk_hex = '770abe6f3854620edfb836ce88ce74c26da1a4b00502c98c368a9373d0c0fcd8'
        address_ltc = 'Lg2uMYnqu48REt4KaSYLPZiaxy5PKUkkdZ'
        self.wallet.import_key(pk_hex, network='litecoin')
        addresses_ltc_in_wallet = self.wallet.addresslist(network='litecoin')
        self.assertIn(address_ltc, addresses_ltc_in_wallet)

    def test_wallet_multiple_networks_import_error(self):
        pk_test = ('BC19UtECk2r9PVQYhZYzX3m4arsu6tCL5VMpKPbeGpZdpzd9FHweoSRreTFKo96FAEFsUWBrASfKussgoxTrNQfm'
                   'jWFrVraLbiHf4gCkUvwHEocA')
        error_str = "Network bitcoinlib_test not available in this wallet, please create an account for this network " \
                    "first."
        self.assertRaisesRegex(WalletError, error_str, self.wallet.import_key, pk_test)

    def test_wallet_multiple_networks_value(self):
        pk = 'vprv9DMUxX4ShgxMM1FFB24BgXE3fMYXKicceSdMUtfhyyUzKNkCvPeYrcoZpPezahBEzFc23yHTPj46eqx3jKuQpQFq5kbd2oxDysd' \
             'teSN16sH'
        wallet_delete_if_exists('test_wallet_multiple_networks_value', force=True, db_uri=self.database_uri)
        w = wallet_create_or_open('test_wallet_multiple_networks_value', keys=pk, db_uri=self.database_uri)
        w.new_account(network='bitcoin')
        w.new_account(network='bitcoinlib_test')
        w.utxos_update(networks='testnet')
        self.assertGreaterEqual(len(w.utxos(network='testnet')), 2)
        w.utxos_update(networks='bitcoinlib_test')
        self.assertEqual(len(w.utxos(network='bitcoinlib_test')), 4)
        t = w.send_to('blt1qctnl4yk3qepjy3uu36kved5ds6q9g8c6raan7l', '50 mTST', broadcast=True)
        self.assertTrue(t.pushed)
        t = w.send_to('tb1qhq6x777xpj32jm005qppxa6gyxt3qrc376ye6c', '0.1 mTBTC', fee=1000)
        self.assertFalse(t.pushed)
        self.assertTrue(t.verified)

    @classmethod
    def tearDownClass(cls):
        del cls.wallet


class TestWalletMultiNetworksMultiAccount(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()

    def test_wallet_multi_networks_send_transaction(self):
        pk = 'tobacco defy swarm leaf flat pyramid velvet pen minor twist maximum extend'
        wallet = Wallet.create(
            keys=pk, network='bitcoin',
            name='test_wallet_multi_network_multi_account', witness_type='legacy',
            db_uri=self.database_uri)

        wallet.new_key()
        acc = wallet.new_account('BCL test home', network='bitcoinlib_test')
        acc2 = wallet.new_account('BCL test office', network='bitcoinlib_test')
        wallet.new_key(account_id=acc2.account_id, network='bitcoinlib_test')
        wallet.new_key(account_id=acc.account_id, network='bitcoinlib_test')
        wallet.utxos_update(networks='bitcoinlib_test', account_id=1)
        wallet.new_key(account_id=acc.account_id, network='bitcoinlib_test')
        wallet.new_key(account_id=acc.account_id, network='bitcoinlib_test')
        wallet.get_keys(network='testnet', number_of_keys=2)
        wallet.get_key(network='testnet', change=1)
        self.assertEqual(wallet.balance(network='bitcoinlib_test', account_id=0), 0)
        self.assertEqual(wallet.balance(network='bitcoinlib_test', account_id=1), 600000000)
        self.assertEqual(wallet.balance(network='testnet'), 0)
        tbtc_addresses = ['mhHhSx66jdXdUPu2A8pXsCBkX1UvHmSkUJ', 'mrdtENj75WUfrJcZuRdV821tVzKA4VtCBf',
                          'mmWFgfG43tnP2SJ8u8UDN66Xm63okpUctk']
        self.assertListEqual(wallet.addresslist(network='testnet'), tbtc_addresses)

        t = wallet.send_to('21EsLrvFQdYWXoJjGX8LSEGWHFJDzSs2F35', 10000000, account_id=1,
                           network='bitcoinlib_test', fee=1000, broadcast=True)
        self.assertIsNone(t.error)
        self.assertTrue(t.verified)
        self.assertEqual(wallet.balance(network='bitcoinlib_test', account_id=1), 589999000)
        self.assertEqual(len(wallet.transactions(account_id=0, network='bitcoinlib_test')), 0)
        self.assertEqual(len(wallet.transactions(account_id=1, network='bitcoinlib_test')), 7)
        del wallet

    def test_wallet_multi_networks_account_bip44_code_error(self):
        wlt = Wallet.create("wallet-bip44-code-error", network='testnet', db_uri=self.database_uri)
        error_str = "Can not create new account for network litecoin_testnet with same BIP44 cointype"
        self.assertRaisesRegex(WalletError, error_str, wlt.new_account, network='litecoin_testnet')

    def test_wallet_get_account_defaults(self):
        w = wallet_create_or_open("test_wallet_get_account_defaults", witness_type='segwit',
                                  db_uri=self.database_uri)
        w.get_key(network='litecoin', account_id=100)
        network, account_id, account_key = w._get_account_defaults(network='litecoin')
        self.assertEqual(network, 'litecoin')
        self.assertEqual(account_id, 100)
        self.assertIn('account', account_key.name)

    def test_wallet_update_attributes(self):
        w = Wallet.create('test_wallet_set_attributes', witness_type='legacy', db_uri=self.database_uri)
        w.new_account(network='litecoin', account_id=1200)
        owner = 'Satoshi'
        w.owner = owner
        w.default_network_set('litecoin')
        w.default_account_id = 1200
        del w

        w2 = Wallet('test_wallet_set_attributes', db_uri=self.database_uri)
        self.assertEqual(w2.owner, owner)
        self.assertEqual(w2.network.name, 'litecoin')
        nk = w2.new_key()
        self.assertEqual(nk.path, "m/44'/2'/1200'/0/1")


class TestWalletBitcoinlibTestnet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()

    def test_wallet_bitcoinlib_testnet_sendto(self):
        w = Wallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet_sendto',
            db_uri=self.database_uri)

        w.new_key()
        w.utxos_update()
        self.assertIsNone(w.send_to('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 5000000, broadcast=True).error)
        self.assertIsNone(w.send_to('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', '10000 satTST', broadcast=True).error)
        self.assertIsNone(w.send_to('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', Value('40 mTST'), broadcast=True).error)

    def test_wallet_bitcoinlib_testnet_send_utxos_updated(self):
        w = Wallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet_send_utxos_updated',
            db_uri=self.database_uri)

        w.utxos_update()
        self.assertEqual(len(w.utxos()), 2)
        t = w.send_to('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 10000, broadcast=True)
        self.assertTrue(t.pushed)

    def test_wallet_bitcoinlib_testnet_sendto_no_funds_txfee(self):
        w = Wallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet_sendto_no_funds_txfee',
            db_uri=self.database_uri)
        w.new_key()
        w.utxos_update()
        balance = w.balance()
        self.assertRaisesRegex(WalletError, "Not enough unspent transaction outputs found",
                                w.send_to, '21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', balance, broadcast=True)

    def test_wallet_bitcoinlib_testnet_sweep(self):
        w = Wallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet_sweep',
            db_uri=self.database_uri)
        w.new_key()
        w.new_key()
        w.new_key()
        w.utxos_update()
        self.assertIsNone(w.sweep('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', broadcast=True).error)
        self.assertEqual(w.utxos(), [])
        self.assertRaisesRegex(WalletError, "Cannot sweep wallet, no UTXO's found",
                                w.sweep, '21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', broadcast=True)


class TestWalletMultisig(unittest.TestCase):
    database_uri = None
    database_uri_2 = None

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()
        cls.database_uri_2 = database_init(DATABASE_NAME_2)

    def test_wallet_multisig_2_wallets_private_master_plus_account_public(self):
        # self.db_remove()
        pk1 = 'tprv8ZgxMBicQKsPdPVdNSEeAhagkU6tUDhUQi8DcCTmJyNLUyU7svTFzXQdkYqNJDEtQ3S2wAspz3K56CMcmMsZ9eXZ2nkNq' \
              'gVxJhMHq3bGJ1X'
        pk1_acc_pub = 'tpubDCZUk9HLxh5gdB9eC8FUxPB1AbZtsSnbvyrAAzsC8x3tiYDgbzyxcngU99rG333jegHG5vJhs11AHcSVkbwrU' \
                      'bYEsPK8vA7E6yFB9qbsTYi'
        w1 = Wallet.create(name='test_wallet_create_1', keys=pk1, db_uri=self.database_uri)
        w2 = Wallet.create(name='test_wallet_create_2', keys=pk1_acc_pub, db_uri=self.database_uri)
        wk1 = w1.new_key()
        wk2 = w2.new_key()
        self.assertTrue(wk1.is_private)
        self.assertFalse(wk2.is_private)
        self.assertEqual(wk1.address, wk2.address)

    def test_wallet_multisig_create_2_cosigner_wallets(self):
        # self.db_remove()
        pk_wif1 = 'tprv8ZgxMBicQKsPdvHCP6VxtFgowj2k7nBJnuRiVWE4DReDFojkLjyqdT8mtR6XJK9dRBcaa3RwvqiKFjsEQVhKfQmHZCCY' \
                  'f4jRTWvJuVuK67n'
        pk_wif2 = 'tprv8ZgxMBicQKsPdkJVWDkqQQAMVYB2usfVs3VS2tBEsFAzjC84M3TaLMkHyJWjydnJH835KHvksS92ecuwwWFEdLAAccwZ' \
                  'KjhcA63NUyvDixB'
        pk1 = HDKey(pk_wif1, network='testnet')
        pk2 = HDKey(pk_wif2, network='testnet')
        wl1 = Wallet.create('multisig_test_wallet1',
                            [pk_wif1, pk2.subkey_for_path("m/45'").wif_public()],
                            sigs_required=2, network='testnet', db_uri=self.database_uri)
        wl2 = Wallet.create('multisig_test_wallet2',
                            [pk1.subkey_for_path("m/45'").wif_public(), pk_wif2],
                            sigs_required=2, network='testnet', db_uri=self.database_uri)
        wl1_key = wl1.new_key()
        wl2_key = wl2.new_key(cosigner_id=wl1.cosigner_id)
        self.assertEqual(wl1_key.address, wl2_key.address)
        self.assertRaisesRegex(WalletError, "Accounts are not supported for this wallet", wl1.account, 10)

    def test_wallet_multisig_bitcoinlib_testnet_transaction_send(self):
        # self.db_remove()

        key_list = [
            'Pdke4WfXvALPdbrKEfBU9z9BNuRNbv1gRr66BEiZHKcRXDSZQ3gV',
            'PhUTR4ZkZu9Xkzn3ee3xMU1TxbNx6ENJvUjX4wBaZDyTCMrn1zuE',
            'PdnZFcwpxUSAcFE6MHB78weVAguwzSTUMBqswkqie7Uxfxsd77Zs'
        ]

        # Create wallet and generate key
        wl = Wallet.create('multisig_test_simple', key_list, sigs_required=2, network='bitcoinlib_test',
                           cosigner_id=0, db_uri=self.database_uri)
        wl.new_key()

        # Sign, verify and send transaction
        wl.utxos_update()  # In bitcoinlib_test network this generates new UTXO's
        t = wl.transaction_create([('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 100000)])
        t.sign()
        self.assertTrue(t.verify())
        t.send()
        self.assertIsNone(t.error)

    def test_wallet_multisig_bitcoin_transaction_send_offline(self):
        # self.db_remove()
        pk2 = HDKey('e2cbed99ad03c500f2110f1a3c90e0562a3da4ba0cff0e74028b532c3d69d29d', witness_type='legacy')
        key_list = [
            HDKey('e9e5095d3e26643cc4d996efc6cb9a8d8eb55119fdec9fa28a684ba297528067', witness_type='legacy'),
            pk2.public_master(multisig=True).public(),
            HDKey('86b77aee5cfc3a55eb0b1099752479d82cb6ebaa8f1c4e9ef46ca0d1dc3847e6').public_master(
                multisig=True, witness_type='legacy').public(),
        ]
        wl = Wallet.create('multisig_test_bitcoin_send', key_list, sigs_required=2, witness_type='legacy',
                           db_uri=self.database_uri)
        wl.utxo_add(wl.get_key().address, 200000, '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5',
                    0, 1)
        t = wl.transaction_create([('3CuJb6XrBNddS79vr27SwqgR4oephY6xiJ', 100000)], fee=10000)
        t.sign(pk2.subkey_for_path("m/45'/2/0/0"))
        t.send(broadcast=False)
        self.assertTrue(t.verify())
        self.assertIsNone(t.error)
        self.assertEqual(t.export()[0][2], 'out')

    def test_wallet_multisig_bitcoin_transaction_send_no_subkey_for_path(self):
        # self.db_remove()
        pk2 = HDKey('e2cbed99ad03c500f2110f1a3c90e0562a3da4ba0cff0e74028b532c3d69d29d')
        key_list = [
            HDKey('e9e5095d3e26643cc4d996efc6cb9a8d8eb55119fdec9fa28a684ba297528067'),
            pk2.public_master(multisig=True),
            HDKey('86b77aee5cfc3a55eb0b1099752479d82cb6ebaa8f1c4e9ef46ca0d1dc3847e6').public_master(multisig=True),
        ]
        wl = Wallet.create('multisig_test_bitcoin_send2', key_list, sigs_required=2,
                           db_uri=self.database_uri)
        wl.utxo_add(wl.get_key().address, 200000, '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5',
                    0, 1)
        t = wl.transaction_create([('3CuJb6XrBNddS79vr27SwqgR4oephY6xiJ', 100000)], fee=10000)
        t.sign(pk2)
        t.send(broadcast=False)
        self.assertTrue(t.verify())
        self.assertIsNone(t.error)

    def test_wallet_multisig_bitcoin_transaction_send_fee_priority(self):
        # self.db_remove()
        pk2 = HDKey('e2cbed99ad03c500f2110f1a3c90e0562a3da4ba0cff0e74028b532c3d69d29d')
        key_list = [
            HDKey('e9e5095d3e26643cc4d996efc6cb9a8d8eb55119fdec9fa28a684ba297528067'),
            pk2.public_master(multisig=True),
            HDKey('86b77aee5cfc3a55eb0b1099752479d82cb6ebaa8f1c4e9ef46ca0d1dc3847e6').public_master(multisig=True),
        ]
        wl = Wallet.create('multisig_test_bitcoin_send3', key_list, sigs_required=2, db_uri=self.database_uri)
        wl.utxo_add(wl.get_key().address, 20000000, '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5',
                    0, 1)
        t = wl.sweep('3CuJb6XrBNddS79vr27SwqgR4oephY6xiJ', fee='low')
        t.sign(pk2)
        self.assertTrue(t.verify())

        t2 = wl.transaction_create([('3CuJb6XrBNddS79vr27SwqgR4oephY6xiJ', 100000)], fee='low')
        t2.sign(pk2)
        t2.send(broadcast=False)
        self.assertTrue(t2.verify())
        self.assertIsNone(t2.error)

    def test_wallet_multisig_litecoin_transaction_send_offline(self):
        # self.db_remove()
        network = 'litecoin_legacy'
        pk2 = HDKey('e2cbed99ad03c500f2110f1a3c90e0562a3da4ba0cff0e74028b532c3d69d29d', witness_type='legacy',
                    network=network)
        key_list = [
            HDKey('e9e5095d3e26643cc4d996efc6cb9a8d8eb55119fdec9fa28a684ba297528067', witness_type='legacy',
                  network=network),
            pk2.public_master(multisig=True),
            HDKey('86b77aee5cfc3a55eb0b1099752479d82cb6ebaa8f1c4e9ef46ca0d1dc3847e6',
                  witness_type='legacy', network=network).public_master(multisig=True),
        ]
        wl = Wallet.create('multisig_test_litecoin_send', key_list, sigs_required=2, network=network,
                           witness_type='legacy', db_uri=self.database_uri)
        wl.get_keys(number_of_keys=2)
        wl.utxo_add(wl.get_key().address, 200000, '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5',
                    0, 1)
        t = wl.transaction_create([('3DrP2R8XmHswUyeK9GeYgHJxvyxTfMNkid', 100000)], fee=10000)
        t.sign(pk2.subkey_for_path("m/45'/2/0/0"))
        t.send(broadcast=False)
        self.assertTrue(t.verify())
        self.assertIsNone(t.error)

    def test_wallet_multisig_2of2(self):
        """
        Create 2 cosigner wallets with 1 own private key a public key from other cosigner
        Then create and sign transaction if first wallet, import and sign it in second wallet
        and verify created transaction.

        """
        # self.db_remove()

        keys = [
            HDKey('BC12Se7KL1uS2bA6QQaWWrcA5kApD8UAM78dx91LrFvsvdvua3irnpQNjHUTCPJR7tZ72eGhMsy3mLPp5C'
                  'SJcmKPchBvaf72i1mNY6yhrmY4RFSr', network='bitcoinlib_test', witness_type='legacy'),
            HDKey('BC12Se7KL1uS2bA6QPiq4cdXWKfmQwuPPTXkRUJNBSLFZt9tPgLfgrRSfkVLRLYCYpgzsTmKybPHSX165w'
                  '42VBjw4Neub1KyPBfNpjFfgx9SyynF', network='bitcoinlib_test', witness_type='legacy')]

        msw1 = Wallet.create('msw1', [keys[0], keys[1].subkey_for_path("m/45'").wif_public()],
                             network='bitcoinlib_test', sort_keys=False, sigs_required=2,
                             db_uri=self.database_uri)
        msw2 = Wallet.create('msw2', [keys[0].subkey_for_path("m/45'").wif_public(), keys[1]],
                             network='bitcoinlib_test', sort_keys=False, sigs_required=2,
                             db_uri=self.database_uri)
        msw1.new_key()
        self.assertEqual(len(msw1.get_key().key()), 2)
        msw2.new_key(cosigner_id=0)
        msw1.utxos_update()
        msw2.utxos_update()
        utxos = msw1.utxos()
        output_arr = [('21KnydRNSmqAf8Py74mMiwRXYHGxW27zyDu', utxos[0]['value'] - 50000)]
        input_arr = [(utxos[0]['txid'], utxos[0]['output_n'], utxos[0]['key_id'], utxos[0]['value'])]
        t = msw1.transaction_create(output_arr, input_arr, fee=50000)
        t.sign()
        t2 = msw2.transaction_import(t)
        t2.sign()
        self.assertTrue(t2.verify())

    def test_wallet_multisig_2of2_different_database(self):
        """
        Same unittest as before (test_wallet_multisig_sign_2_different_wallets) but now with 2
        separate databases to check for database interference.

        """
        # self.db_remove()

        keys = [
            HDKey('BC12Se7KL1uS2bA6QQaWWrcA5kApD8UAM78dx91LrFvsvdvua3irnpQNjHUTCPJR7tZ72eGhMsy3mLPp5C'
                  'SJcmKPchBvaf72i1mNY6yhrmY4RFSr', network='bitcoinlib_test', witness_type='legacy'),
            HDKey('BC12Se7KL1uS2bA6QPiq4cdXWKfmQwuPPTXkRUJNBSLFZt9tPgLfgrRSfkVLRLYCYpgzsTmKybPHSX165w'
                  '42VBjw4Neub1KyPBfNpjFfgx9SyynF', network='bitcoinlib_test', witness_type='legacy')]

        msw1 = Wallet.create('msw-2-2-1', [keys[0], keys[1].public_master(multisig=True)], network='bitcoinlib_test',
                             sort_keys=False, sigs_required=2, db_uri=self.database_uri)
        msw2 = Wallet.create('msw-2-2-2', [keys[0].public_master(multisig=True), keys[1]], network='bitcoinlib_test',
                             sort_keys=False, sigs_required=2, db_uri=self.database_uri_2)
        msw1.new_key()
        msw2.new_key(cosigner_id=msw1.cosigner_id)
        msw1.utxos_update()
        msw2.utxos_update()
        utxos = msw1.utxos()
        output_arr = [('21KnydRNSmqAf8Py74mMiwRXYHGxW27zyDu', utxos[0]['value'] - 50000)]
        input_arr = [(utxos[0]['txid'], utxos[0]['output_n'], utxos[0]['key_id'], utxos[0]['value'])]
        t = msw1.transaction_create(output_arr, input_arr, fee=50000)
        t.sign()
        t2 = msw2.transaction_import(t)
        t2.sign()
        t2.send()
        self.assertIsNone(t2.error)

    @classmethod
    def _multisig_test(cls, sigs_required, number_of_sigs, sort_keys, network, witness_type='legacy'):
        # Create Keys
        key_dict = {}
        for key_id in range(number_of_sigs):
            key_dict[key_id] = HDKey(network=network, witness_type=witness_type)
        random_output_address = HDKey(network=network, witness_type=witness_type).address()

        # Create wallets with 1 private key each
        wallet_dict = {}
        wallet_keys = {}
        for wallet_id in range(number_of_sigs):
            wallet_name = 'multisig-%d-%d-%d-%s-%s-%s' % (wallet_id, sigs_required, number_of_sigs, witness_type,
                                                         network, int(sort_keys))
            key_list = []
            for key_id in key_dict:
                if key_id == wallet_id:
                    key_list.append(key_dict[key_id])
                else:
                    key_list.append(key_dict[key_id].public_master(multisig=True, as_private=True))
            wallet_dict[wallet_id] = Wallet.create(
                wallet_name, key_list, sigs_required=sigs_required, network=network, sort_keys=sort_keys, cosigner_id=0,
                witness_type=witness_type, db_uri=cls.database_uri)
            wallet_keys[wallet_id] = wallet_dict[wallet_id].new_key()
            wallet_dict[wallet_id].utxos_update()

        # Create transaction in one random wallet
        wallet_ids = [i for i in range(0, number_of_sigs)]
        shuffle(wallet_ids)
        fee = 50000
        wallet_id = wallet_ids.pop()
        wlt = wallet_dict[wallet_id]
        utxos = wlt.utxos()
        output_arr = [(random_output_address, utxos[0]['value'] - fee)]
        input_arr = [(utxos[0]['txid'], utxos[0]['output_n'], utxos[0]['key_id'], utxos[0]['value'])]
        t = wlt.transaction_create(output_arr, input_arr, fee=fee)
        t.sign()
        n_signs = 1

        # Sign transaction with other wallets until required number of signatures is reached
        while wallet_ids and n_signs < sigs_required:
            wallet_id = wallet_ids.pop()
            t = wallet_dict[wallet_id].transaction_import(t)
            t.sign()
            n_signs += 1
        wlt.session.close()
        return t

    def test_wallet_multisig_2of3(self):
        # self.db_remove()
        t = self._multisig_test(2, 3, False, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    def test_wallet_multisig_2of3_segwit(self):
        # self.db_remove()
        t = self._multisig_test(2, 3, False, 'bitcoinlib_test', 'segwit')
        self.assertTrue(t.verify())

    def test_wallet_multisig_2of3_sorted(self):
        # self.db_remove()
        t = self._multisig_test(2, 3, True, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    def test_wallet_multisig_3of5(self):
        # self.db_remove()
        t = self._multisig_test(3, 5, False, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    def test_wallet_multisig_3of5_segwit(self):
        # self.db_remove()
        t = self._multisig_test(3, 5, False, 'bitcoinlib_test', 'segwit')
        self.assertTrue(t.verify())

    def test_wallet_multisig_2of2_with_single_key(self):
        # self.db_remove()
        keys = [HDKey(network='bitcoinlib_test'), HDKey(network='bitcoinlib_test', key_type='single')]
        key_list = [keys[0], keys[1].public()]

        wl = Wallet.create('multisig_expk2', key_list, sigs_required=2, network='bitcoinlib_test',
                           db_uri=self.database_uri, sort_keys=False)
        k1 = wl.new_key()
        k2 = wl.new_key()
        k3 = wl.new_key_change()
        wl.utxos_update()
        self.assertEqual(wl.public_master()[1].wif, keys[1].wif(multisig=True))
        key_names = [k.name for k in wl.keys(is_active=False)]
        self.assertListEqual(key_names, [k1.name, k2.name, k3.name])

        t = wl.transaction_create([(HDKey(network='bitcoinlib_test').address(), 6400000)], min_confirms=0)
        t.sign(keys[1])
        t.send()
        self.assertIsNone(t.error)

    def test_wallet_multisig_sorted_keys(self):
        # self.db_remove()
        key1 = HDKey()
        key2 = HDKey()
        key3 = HDKey()
        w1 = Wallet.create('w1', [key1, key2.public_master(multisig=True), key3.public_master(multisig=True)],
                           sigs_required=2, db_uri=self.database_uri)
        w2 = Wallet.create('w2', [key1.public_master(multisig=True), key2, key3.public_master(multisig=True)],
                           sigs_required=2, db_uri=self.database_uri)
        w3 = Wallet.create('w3', [key1.public_master(multisig=True), key2.public_master(multisig=True), key3],
                           sigs_required=2, db_uri=self.database_uri)
        for _ in range(5):
            cosigner_id = random.randint(0, 2)
            address1 = w1.new_key(cosigner_id=cosigner_id).address
            address2 = w2.new_key(cosigner_id=cosigner_id).address
            address3 = w3.new_key(cosigner_id=cosigner_id).address
            self.assertTrue((address1 == address2 == address3),
                            'Different addressed generated: %s %s %s' % (address1, address2, address3))

    def test_wallet_multisig_sign_with_external_single_key(self):
        # self.db_remove()
        network = 'bitcoinlib_test'
        words = 'square innocent drama'
        seed = Mnemonic().to_seed(words, 'password')
        hdkey = HDKey.from_seed(seed, network=network)
        hdkey.key_type = 'single'

        key_list = [
            HDKey(network=network, multisig=True).public_master(),
            HDKey(network=network),
            hdkey.public()
        ]
        wallet = Wallet.create('test_wallet_multisig_sign_with_external_single_key',
                               key_list, sigs_required=2, network=network, db_uri=self.database_uri)
        wallet.new_key()
        wallet.utxos_update()
        wt = wallet.send_to('21A6yyUPRL9hZZo1Rw4qP5G6h9idVVLUncE', 10000000, broadcast=True)
        self.assertFalse(wt.verify())
        wt.sign(hdkey)
        self.assertTrue(wt.verify())

    def test_wallet_multisig_reopen_wallet(self):

        def _open_all_wallets():
            wl1 = wallet_create_or_open(
                'multisigmulticur1_tst', sigs_required=2, network=network,
                db_uri=self.database_uri, sort_keys=False, witness_type='segwit',
                keys=[pk1, pk2.public_master(), pk3.public_master()])
            wl2 = wallet_create_or_open(
                'multisigmulticur2_tst', sigs_required=2, network=network,
                db_uri=self.database_uri, sort_keys=False, witness_type='segwit',
                keys=[pk1.public_master(), pk2, pk3.public_master()])
            wl3 = wallet_create_or_open(
                'multisigmulticur3_tst', sigs_required=2, network=network,
                db_uri=self.database_uri, sort_keys=False, witness_type='segwit',
                keys=[pk1.public_master(), pk2.public_master(), pk3])
            return wl1, wl2, wl3

        # self.db_remove()
        network = 'litecoin'
        phrase1 = 'shop cloth bench traffic vintage security hour engage omit almost episode fragile'
        phrase2 = 'exclude twice mention orchard grit ignore display shine cheap exercise same apart'
        phrase3 = 'citizen obscure tribe index little welcome deer wine exile possible pizza adjust'
        pk1 = HDKey.from_passphrase(phrase1, multisig=True, network=network)
        pk2 = HDKey.from_passphrase(phrase2, multisig=True, network=network)
        pk3 = HDKey.from_passphrase(phrase3, multisig=True, network=network)
        wallets = _open_all_wallets()
        for wlt in wallets:
            self.assertEqual(wlt.get_key(cosigner_id=1).address,
                             'ltc1qmw3e97pgrwypr0378wjje984guu0jy3ye4n523lcymk3rctuef6q7t3sek')
        del wallets
        wallets2 = _open_all_wallets()
        for wlt in wallets2:
            self.assertEqual(wlt.get_key(cosigner_id=1).address,
                             'ltc1qmw3e97pgrwypr0378wjje984guu0jy3ye4n523lcymk3rctuef6q7t3sek')

    def test_wallet_multisig_network_mixups(self):
        # self.db_remove()
        network = 'litecoin_testnet'
        phrase1 = 'shop cloth bench traffic vintage security hour engage omit almost episode fragile'
        phrase2 = 'exclude twice mention orchard grit ignore display shine cheap exercise same apart'
        phrase3 = 'citizen obscure tribe index little welcome deer wine exile possible pizza adjust'
        pk2 = HDKey.from_passphrase(phrase2, multisig=True, network=network, witness_type='legacy')
        pk3 = HDKey.from_passphrase(phrase3, multisig=True, network=network, witness_type='legacy')
        wlt = wallet_create_or_open(
            'multisig_network_mixups', sigs_required=2, network=network, db_uri=self.database_uri,
            keys=[phrase1, pk2.public_master(), pk3.public_master()], witness_type='legacy',
            sort_keys=False)
        self.assertEqual(wlt.get_key().address, 'QjecchURWzhzUzLkhJ8Xijnm29Z9PscSqD')
        self.assertEqual(wlt.get_key().network.name, network)

    def test_wallet_multisig_info(self):
        w = Wallet.create('test_wallet_multisig_info', keys=[HDKey(network='bitcoinlib_test'),
                                                             HDKey(network='bitcoinlib_test')],
                          network='bitcoinlib_test', cosigner_id=0, db_uri=self.database_uri)
        w.utxos_update()
        self.assertIsNone(w.info(detail=6))

    def test_wallets_multisig_missing_private_and_cosigner(self):
        k0 = 'xprv9s21ZrQH143K459uwGGCU3Wj3v1LFFJ42tgyTsNnr6p2BS6FZ9jQ7fmZMMnqsWSi2BBgpX3hFbR4ode8Jx58ibSNeaBLFQ68Xs3' \
             'jwg4QFLh'
        k1 = 'xpub661MyMwAqRbcGcJB4UPQpR2mUQtdUVbjjNC84DEK9ptZ2XgAC54U1onrH6tEMueYbzGPCRRPoDx5npvCS4Xryz8toVVEQ4ZFfkU' \
             'cJobNZfn'
        k2 = 'xpub661MyMwAqRbcFD9fBAsKxxRPgikEvig5KYT1CEnAp7FcfcFeu2ZxdNcj6DDUxNreWgftXody6NqDHmFmh8tRZ4UNAecucovtW4M' \
             'bGjYRJFP'
        hdkey0 = HDKey(k0).public_master_multisig()
        hdkey1 = HDKey(k1, key_type='single')
        hdkey2 = HDKey(k2, key_type='single')
        self.assertRaisesRegex(WalletError,
                                "This wallet does not contain any private keys, please specify cosigner_id for "
                                "this wallet", wallet_create_or_open,
                                'test_wallets_multisig_missing_private_and_cosigner',
                                keys=[hdkey0, hdkey1, hdkey2], db_uri=self.database_uri)

    def test_wallets_multisig_with_single_key_cosigner(self):
        k0 = 'xprv9s21ZrQH143K459uwGGCU3Wj3v1LFFJ42tgyTsNnr6p2BS6FZ9jQ7fmZMMnqsWSi2BBgpX3hFbR4ode8Jx58ibSNeaBLFQ68Xs3' \
             'jwg4QFLh'  # cosigner 2
        k1 = 'xpub661MyMwAqRbcGcJB4UPQpR2mUQtdUVbjjNC84DEK9ptZ2XgAC54U1onrH6tEMueYbzGPCRRPoDx5npvCS4Xryz8toVVEQ4ZFfkU' \
             'cJobNZfn'  # cosigner 1
        k2 = 'xpub661MyMwAqRbcFD9fBAsKxxRPgikEvig5KYT1CEnAp7FcfcFeu2ZxdNcj6DDUxNreWgftXody6NqDHmFmh8tRZ4UNAecucovtW4M' \
             'bGjYRJFP'  # cosigner 0
        hdkey0 = HDKey(k0).public_master_multisig()
        hdkey1 = HDKey(k1, key_type='single')
        hdkey2 = HDKey(k2, key_type='single')

        w = wallet_create_or_open('test_wallets_multisig_with_single_key_cosigner0', keys=[hdkey0, hdkey1, hdkey2],
                                  cosigner_id=0, db_uri=self.database_uri)
        w.new_key(cosigner_id=2)
        w.new_key(cosigner_id=2)
        # Cosigner 0 use a single key wallet, so calling new_key() repeatedly has no effect
        w.new_key()
        w.new_key()
        self.assertEqual(len(w.addresslist()), 3)
        self.assertEqual(w.keys()[0].address, '39b2tosg9To6cQTrqnZLhuhW5auqCqXKsH')
        self.assertEqual(w.keys()[1].address, '3K2eBv2hm3SjhVRaJJK8Dt7wMb8mRTWcMH')
        self.assertEqual(w.keys()[2].address, '3PprnP2HcaivRGaUSBm9Z724NHvjibb4c7')

        w2 = wallet_create_or_open('test_wallets_multisig_with_single_key_cosigner2', keys=[hdkey0, hdkey1, hdkey2],
                                   cosigner_id=2, db_uri=self.database_uri)
        w2.new_key()
        w2.new_key()
        w2.new_key(cosigner_id=0)
        self.assertEqual(w2.keys()[0].address, '39b2tosg9To6cQTrqnZLhuhW5auqCqXKsH')
        self.assertEqual(w2.keys()[1].address, '3K2eBv2hm3SjhVRaJJK8Dt7wMb8mRTWcMH')
        self.assertEqual(w2.keys()[2].address, '3PprnP2HcaivRGaUSBm9Z724NHvjibb4c7')
        self.assertEqual(w2.keys()[0].path, "M/2/0/0")
        self.assertEqual(w2.keys()[1].path, "M/2/0/1")
        self.assertEqual(w2.keys()[2].path, "M/0/0/0")

        # Close wallet and reopen to test for database issues for example
        del w
        w = wallet_create_or_open('test_wallets_multisig_with_single_key_cosigner0',
                                  db_uri=self.database_uri)
        w.new_key(cosigner_id=2)
        self.assertEqual(w.keys()[3].address, '3Q9rnDniMa55jZFyzBDKihtXwZSM34zfEj')

    def test_wallets_multisig_huge(self):
        for witness_type in ['legacy', 'segwit']:
            network = 'bitcoinlib_test'
            n_keys = 15
            sigs_req = 10
            wallet_name = 'test_wallet_multisig_huge_%s' % witness_type
            key_list = [HDKey(witness_type=witness_type, network=network) for _ in range(0, n_keys)]
            pk_n = random.randint(0, n_keys - 1)
            key_list_cosigners = [k.public_master(multisig=True) for k in key_list if k is not key_list[pk_n]]
            key_list_wallet = [key_list[pk_n]] + key_list_cosigners

            w = Wallet.create(wallet_name, keys=key_list_wallet, sigs_required=sigs_req,
                              witness_type=witness_type, network=network, db_uri=self.database_uri)
            w.get_keys(number_of_keys=2)
            w.utxos_update()
            to_address = HDKey(network=network, witness_type=witness_type).address()
            t = w.sweep(to_address)

            key_pool = [i for i in range(0, n_keys - 1) if i != pk_n]
            while len(t.inputs[0].signatures) < sigs_req:
                co_id = random.choice(key_pool)
                t.sign(key_list[co_id])
                key_pool.remove(co_id)
            self.assertTrue(t.verify())

    def test_wallets_multisig_huge_error(self):
        network = 'bitcoinlib_test'
        n_keys = 16
        sigs_req = 10
        wallet_name = 'test_wallet_multisig_huge_error'
        key_list = [HDKey(network=network) for _ in range(0, n_keys)]
        pk_n = random.randint(0, n_keys - 1)
        key_list_cosigners = [k.public_master(multisig=True) for k in key_list if k is not key_list[pk_n]]
        key_list_wallet = [key_list[pk_n]] + key_list_cosigners
        self.assertRaisesRegex(WalletError, 'Redeemscripts with more then 15 keys are non-standard and could '
                                             'result in locked up funds',
                                Wallet.create, wallet_name, keys=key_list_wallet, sigs_required=sigs_req,
                                network=network, db_uri=self.database_uri)

    def test_wallet_multisig_replace_sig_bug(self):
        network = 'bitcoinlib_test'
        witness_type = 'legacy'
        wallet_name = 'test_wallet_multisig_sign_bug'
        sigs_req = 3
        pk_hex_list = [
            '842b1d54c9eceda72de8f4cfaa2daf1e90fe1707541e9038286849cd56ff0093',
            'bf19b9c9438bb1048a5dbc08600046f47129611d7ab61ca0ea96d914b8b0e231',
            '8d0d44f34565f38f48faa79bedf4f36788ae5df937140c784acae3cc3d6a26aa',
            'aa9e08e1a46b6a08556338748ce911c98efb4038dceb6d7bf8d3dd6d8072c482',
            '2631ab1a4745f657f7216c636fb8ac708a3f6b63a6cd5cf773bfc9a3ebe6e1ba',
            '97a66126f42fd3241cf256846e58cd7049d4d395f84b1811f73a3f5d33ff833e',
        ]
        key_list = [HDKey(pk, witness_type='legacy', network=network) for pk in pk_hex_list]
        key_list_cosigners = [k.public_master(multisig=True) for k in key_list if k is not key_list[0]]
        key_list_wallet = [key_list[0]] + key_list_cosigners
        w = wallet_create_or_open(wallet_name, keys=key_list_wallet, sigs_required=sigs_req, witness_type=witness_type,
                                  network=network, db_uri=self.database_uri)
        w.get_keys()
        w.utxos_update()
        to_address = HDKey(network=network, witness_type=witness_type).address()
        t = w.send_to(to_address, 1000000, broadcast=True)
        key_pool = [i for i in range(0, len(key_list) - 1) if i != 0]
        co_ids = [4, 2]
        while len(t.inputs[0].signatures) < sigs_req:
            co_id = co_ids.pop(0)
            t.sign(key_list[co_id])
            key_pool.remove(co_id)
        self.assertTrue(t.verify())

    def test_wallet_multisig_multinetwork(self):
        network1 = 'litecoin'
        network2 = 'bitcoinlib_test'
        p1 = 'only sing document speed outer gauge stand govern way column material odor'
        p2 = 'oyster pelican debate mass scene title pipe lock recipe flavor razor accident'
        k2 = HDKey.from_passphrase(p2, network=network1, multisig=True).public_master()
        w = wallet_create_or_open('ltcswms', [p1, k2], network=network1, witness_type='segwit',
                                  cosigner_id=0, db_uri=self.database_uri)
        self.assertEqual(len(w.get_keys(number_of_keys=2)), 2)
        w.utxo_add('ltc1qkewaz7lxn75y6wppvqlsfhrnq5p5mksmlp26n8xsef0556cdfzqq2uhdrt', 2100000000000001,
                   '21da13be453624cf46b3d883f39602ce74d04efa7a186037898b6d7bcfd405ee', 0, 15)
        t = w.sweep('ltc1q9h8xvtrge5ttcwzy3xtz7l8kj4dewgh6hgqfjdhtq6lwr4k3527qd8tyzs')
        self.assertFalse(t.verified)
        t.sign(p2)
        self.assertTrue(t.verified)
        self.assertRaisesRegex(WalletError, "Cannot create new keys for network bitcoinlib_test, "
                                            "no private masterkey found", w.new_key, network=network2)


class TestWalletKeyImport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()

    def test_wallet_key_import_and_sign_multisig(self):
        network = 'bitcoinlib_test'
        words = 'square innocent drama'
        seed = Mnemonic().to_seed(words, 'password')
        hdkey = HDKey.from_seed(seed, network=network)
        hdkey.key_type = 'single'

        key_list = [
            HDKey(network=network, multisig=True).public_master(),
            HDKey(network=network),
            hdkey.public()
        ]
        with Wallet.create('Multisig-2-of-3-example', key_list, sigs_required=2,
                           db_uri=self.database_uri) as wlt:
            wlt.new_key()
            wlt.utxos_update()
            wt = wlt.send_to('21A6yyUPRL9hZZo1Rw4qP5G6h9idVVLUncE', 10000000, broadcast=True)
            wt.sign(hdkey)
            wt.send()
            self.assertIsNone(wt.error)

    def test_wallet_import_private_for_known_public(self):
        hdkey = HDKey(
            'xprv9s21ZrQH143K2noEZoqGHnaDDLjrnFpis8jm7NWDhkWuNNCqMupGSy7PMYtGL9jvdTY7Nx3GZ6UZ9C52nebwbYXK73imaPUK24'
            'dZJtGZhGd')
        with Wallet.create('public-private', hdkey.public_master().public(), db_uri=self.database_uri) \
                as wlt:
            self.assertFalse(wlt.main_key.is_private)
            wlt.import_key(hdkey)
            self.assertTrue(wlt.main_key.is_private)
            self.assertListEqual([k.path for k in wlt.keys()], ["m/44'/0'/0'", "m/44'/0'/0'/0", "m/44'/0'/0'/0/0",
                                                                'm', "m/44'", "m/44'/0'"])
            self.assertEqual(wlt.new_account().address, '16m3JAtQjHbmEZd8uYTyKebvrxh2RsFHB')
            self.assertEqual(wlt.get_key().address, '1P8BTrsBn8DKGQq7nSWPiEiUDgiG8sW1kf')

    def test_wallet_import_private_for_known_public_multisig(self):
        puk1 = "Ltub2ULsQdDwsgJsxgNnetNNAz19RMhTzkZeG9sv8H3hyBuBkS4pMUJKcy3LsUETJfmS47mBg3mrxMuAYJqSf2jW3TyfP81WKHjc" \
               "LV46vPh5kfX"
        puk2 = "Ltub2UZgTKsUVf6jmMZ3cihnLdvqxCCuJmAj2B3GaVUuQ6DPeNqFdtFAMr4rfbEkLveguPAKoiNfVNbWFexxxnxBUaZwXSWAp2X7" \
               "kPMSdJ9rHRQ"
        puk3 = "Ltub2VcWC27VfGLB2PTwq3TQ5fsCAkyVE33WJ8QbBxPSQ8RWmsQmoWX1k1Fu4SfH2cVhKQCc5bPyUKEzEA35PeCmp5a9PCAWM26E" \
               "AjuPh58gq7C"
        prk3 = "Ltpv71G8qDifUiNetjnY73hftMUMUdvPuiPGomJAfwEiJXbGFpWsMZJoZxwusqLSrgiW5kmjUempoLywoM4QfqGZWci2qx1omPQF" \
               "iFEwaUv85GA"

        with wallet_create_or_open("mstest", [puk1, puk2, puk3], 2, network='litecoin', sort_keys=False,
                                   cosigner_id=0, db_uri=self.database_uri) as wlt:
            self.assertFalse(wlt.cosigner[2].main_key.is_private)
            wlt.import_key(prk3)
            self.assertTrue(wlt.cosigner[2].main_key.is_private)

    def test_wallet_import_private_for_known_public_p2sh_segwit(self):
        pk1 = HDKey('BC15gwSkKnLsWk3GmCxBwzdbij4fXUa5j6UB8bSYJt9a81aSUCVjg7tVJaEDpxRZ4X2dt3VKjuy8po1fbo6opZ6tCqxVAg'
                    'XgQKUBwWi6EGh2eLRC')
        pk2 = HDKey('BC15gwSkKnLsWk3GmCWRgmp2edaya3UgmQ4TqjiBfx2cuvMC5ASQwJ5N5wwKcMp627AucznuYvTzKnhYRERcPFnEAn1a7w'
                    'VKQy7FMLXzMq7N2nQq')
        w = Wallet.create('segwit-p2sh-p2wsh-import',
                          [pk1, pk2.public_master(witness_type='p2sh-segwit', multisig=True)],
                          witness_type='p2sh-segwit', network='bitcoinlib_test', db_uri=self.database_uri)
        w.get_key()
        w.utxos_update()
        t = w.sweep('23CvEnQKsTVGgqCZzW6ewXPSJH9msFPsBt3', broadcast=True)
        self.assertEqual(len(t.inputs[0].signatures), 1)
        self.assertFalse(t.verify())

        w.import_key(pk2)
        wc0 = w.cosigner[0]
        self.assertEqual(len(wc0.keys(is_private=False)), 0)
        t2 = w.send_to('23CvEnQKsTVGgqCZzW6ewXPSJH9msFPsBt3', 1000000, broadcast=True)
        self.assertEqual(len(t2.inputs[0].signatures), 2)
        self.assertTrue(t2.verify())
        t3 = w.sweep('23CvEnQKsTVGgqCZzW6ewXPSJH9msFPsBt3', min_confirms=0, broadcast=True)
        self.assertEqual(len(t3.inputs[0].signatures), 2)
        self.assertTrue(t3.verify())
        self.assertAlmostEqual(t3.outputs[0].value, 198981935, delta=100000)

    def test_wallet_import_private_for_known_public_segwit_passphrases(self):
        witness_type = 'segwit'
        p1 = 'scan display embark segment deputy lesson vanish second wonder erase crumble swing'
        p2 = 'private school road sight weapon where wreck glory lazy weapon silent print'
        wif1 = 'Zpub74zBTMSW6uSE3nFTJbxxvyF3P169wy9N3WzMzFBwWV56sj2NTsGEXAcj6HeLwAhsbs6Ca7Gx7JY1McV2CA1eANi2ubuQA34j' \
               'CxbEPR7eLPm'
        wif2 = 'Zpub75XfXxxDxRZPEiHJfGUtVWovyfCYT2DLkmPGCFjYdtChJ4r3VaUSbSrQKCVezZuZ6wiJ8UvuG3QPAJdKxB9iY9zUTZ9VLLMw' \
               'jTF9ghGRx1Q'
        k1 = HDKey.from_passphrase(p1)
        k2 = HDKey.from_passphrase(p2)
        pubk1 = k1.public_master_multisig(witness_type=witness_type)
        pubk2 = k2.public_master_multisig(witness_type=witness_type)
        self.assertEqual(pubk1.wif(), wif1)
        self.assertEqual(pubk2.wif(), wif2)
        w = Wallet.create('mswlt', [p1, pubk2], db_uri=self.database_uri, witness_type=witness_type)
        wk = w.new_key()
        self.assertEqual(wk.address, 'bc1qr7r7zpr5gqnz0zs39ve7c0g54gwe7h7322lt3kae6gh8tzc5epts0j9rhm')
        self.assertFalse(w.public_master(as_private=True)[1].is_private)
        self.assertEqual(w.public_master(as_private=True)[1].wif, wif2)
        w.import_key(p2)
        self.assertTrue(w.public_master(as_private=True)[1].is_private)
        self.assertEqual(w.public_master(as_private=True)[1].wif,
                         'ZprvArYK8TRL84162ECqZEwt8NsCRdN43ZVVPYTfPsKw5YfiRGWtx3AC3eXvTuk'
                         'CqUsKCLKQNGDV11hHi3FUQbcD9wc9g8ro64kK6H2MP4jaM7K')
        w.transactions_update()
        txids = sorted([t.txid for t in w.transactions()])
        txids_expected = ['53b35eca3f2e767db02e4acc6c224d7a45f32158c8063f53c3d3660ab12d53ba',
                          'b6c4f286e8883927c26ce91e6cc89c7a8dd88223c111635e8e53f78c4573712a']
        self.assertListEqual(txids, txids_expected)


class TestWalletTransactions(unittest.TestCase, CustomAssertions):
    wallet = None

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()
        account_key = 'tpubDCmJWqxWch7LYDhSuE1jEJMbAkbkDm3DotWKZ69oZfNMzuw7U5DwEaTVZHGPzt5j9BJDoxqVkPHt2EpUF66FrZhpfq' \
                      'ZY6DFj6x61Wwbrg8Q'
        cls.wallet = wallet_create_or_open('utxo-test', keys=account_key, network='testnet',
                                           db_uri=cls.database_uri)
        cls.wallet.new_key()
        cls.wallet.utxos_update()

    def test_wallet_import_utxos(self):
        total_value = sum([utxo['value'] for utxo in self.wallet.utxos()])
        self.assertEqual(total_value, 60000000)

    def test_wallet_transaction_export(self):
        txs = self.wallet.transactions_export()
        tx = [t for t in txs if t[1] == 'fb575942ef5ddc0d6afe10ccf73928faa81315a1f9be2d5b8a801daf7d251a6f'][0]
        self.assertEqual(tx[2], 'in')
        self.assertEqual(tx[3], [])
        self.assertEqual(tx[4], ['mwCvJviVTzjEKLZ1UW5jaepjWHUeoYrEe7'])
        self.assertEqual(tx[5], 10000000)

    def test_wallet_transactions_full(self):
        txs = self.wallet.transactions_full()
        self.assertGreaterEqual(len(txs), 3)
        for tx in txs:
            self.assertIsInstance(tx, WalletTransaction)

    def test_wallet_sweep_public_wallet(self):
        tx = self.wallet.sweep('mwCvJviVTzjEKLZ1UW5jaepjWHUeoYrEe7', fee_per_kb=50000, broadcast=True)
        prev_tx_list_check = [
            '4fffbf7c50009e5477ac06b9f1741890f7237191d1cf5489c7b4039df2ebd626',
            '9423919185b15c633d2fcd5095195b521a8970f01ca6413c43dbe5646e5b8e1e',
            'fb575942ef5ddc0d6afe10ccf73928faa81315a1f9be2d5b8a801daf7d251a6f']
        prev_tx_list = sorted([x.prev_txid.hex() for x in tx.inputs])
        self.assertListEqual(prev_tx_list, prev_tx_list_check)
        self.wallet.transactions_export()

    def test_wallet_offline_create_transaction(self):
        hdkey_wif = 'tprv8ZgxMBicQKsPf5exCdeBgnYjJt2LxDcQbv6u9HHymY3qh6EoTy8SGwou5xyvExL3iWfBsZWp3YUyo9gRmxQxrBS2FwGk' \
                    'qjcDhTcyVLhrXXZ'
        hdkey = HDKey(hdkey_wif)
        wlt = wallet_create_or_open('offline-create-transaction', keys=hdkey, network='testnet',
                                    db_uri=self.database_uri)
        self.assertEqual(wlt.wif(is_private=True), hdkey_wif)
        wlt.get_key()
        utxos = [{
            'address': 'n2S9Czehjvdmpwd2YqekxuUC1Tz5ZdK3YN',
            'script': '',
            'confirmations': 10,
            'output_n': 1,
            'txid': '9df91f89a3eb4259ce04af66ad4caf3c9a297feea5e0b3bc506898b6728c5003',
            'value': 8970937
        }]
        wlt.utxos_update(utxos=utxos)
        t = wlt.transaction_create([('n2S9Czehjvdmpwd2YqekxuUC1Tz5ZdK3YN', 1000)], fee=5000)
        t.sign()
        self.assertTrue(t.verify())
        del wlt

    def test_wallet_scan(self):
        account_key = 'tpubDCmJWqxWch7LYDhSuE1jEJMbAkbkDm3DotWKZ69oZfNMzuw7U5DwEaTVZHGPzt5j9BJDoxqVkPHt2EpUF66FrZhpfq' \
                      'ZY6DFj6x61Wwbrg8Q'
        wallet = wallet_create_or_open('scan-test', keys=account_key, network='testnet', db_uri=self.database_uri)
        wallet.scan(scan_gap_limit=1)
        self.assertEqual(len(wallet.keys()), 6)
        self.assertEqual(wallet.balance(), 60000000)
        self.assertEqual(len(wallet.transactions()), 3)
        self.assertEqual(len(wallet.transactions(as_dict=True)), 3)

    def test_wallet_scan_tx_order_same_block(self):
        # Check tx order in same block
        address = 'tb1qlh9x3jwhfqspp7u9w6l7zqxpmuvplzaczaele3'
        w = wallet_create_or_open('fix-multiple-tx-1-block', keys=address, db_uri=self.database_uri)
        w.scan()
        self.assertEqual(w.transactions()[0].txid, 'bae05e65c13a1b1635abf581a6250a458cbd672c914e2563b5bb175274f9c5a7')

    def test_wallet_scan_utxos(self):
        pk = 'tpubDDi7dF92m7UrWNuAmzR9mzETcCjFT9v6XZq2oXjvhH4Bzr4L13np7d6bBB5tZk1Kg3y2vB79ohpgsLiubcRA8RfA6L69nmZvSG26XfmC5Ao'
        w = wallet_create_or_open('kladkladklieder3', keys=pk, db_uri=self.database_uri)
        w.scan(scan_gap_limit=1)
        self.assertEqual(len(w.utxos()), 2)
        self.assertEqual(w.balance(), 2000)
        exp_tx_list = ['3c634d82d6a9e855f26266acefb7096afdad80cad007079028bc259dc2f642a4',
                       '5658a4bf4b47c20c92d593999be469e8b8726ffcb5cb348681f020eadf342c3f',
                       '7834f47064c7bfd5b68cef98a61f5c4c7a8a3c6985ef137c7b3447bb62fa2324',
                       '7a4b8da2b74c71c01e1752457da715bc96807da02ec5e05d3eb4ed1dcb0c4735',
                       'b71cedddf6381c8b6eba953d5b9454b9ca41e2abbdbd9498a6c90004f649abb4']
        tx_list = sorted(list(set([t.txid for t in w.transactions()])))
        self.assertListEqual(tx_list, exp_tx_list)

    def test_wallet_two_utxos_one_key(self):
        wlt = Wallet.create('double-utxo-test', network='bitcoinlib_test', db_uri=self.database_uri)
        key = wlt.new_key()
        wlt.utxos_update()
        utxos = wlt.utxos()

        inp1 = Input(prev_txid=utxos[0]['txid'], output_n=utxos[0]['output_n'], keys=key.key_public,
                     network='bitcoinlib_test', witness_type='legacy')
        inp2 = Input(prev_txid=utxos[1]['txid'], output_n=utxos[1]['output_n'], keys=key.key_public,
                     network='bitcoinlib_test', witness_type='legacy')
        out = Output(10000000, address=key.address, network='bitcoinlib_test')

        t = Transaction(inputs=[inp1, inp2], outputs=[out], network='testnet')
        t.sign(key.key_private)
        self.assertTrue(t.verify())
        del wlt

    def test_wallet_balance_update(self):
        wlt = Wallet.create('test-balance-update', network='bitcoinlib_test', db_uri=self.database_uri)
        to_key = wlt.get_key()
        wlt.utxos_update()
        self.assertEqual(wlt.balance(), 200000000)

        t = wlt.send_to(to_key.address, 9000, broadcast=True)
        self.assertEqual(wlt.balance(), 200000000 - t.fee)
        self.assertEqual(t.txid, wlt.transaction_spent(t.inputs[0].prev_txid, t.inputs[0].output_n))
        self.assertEqual(t.txid, wlt.transaction_spent(t.inputs[0].prev_txid.hex(), t.inputs[0].output_n_int))
        del wlt

    def test_wallet_balance_update_multi_network(self):
        k = "tpubDCutwJADa3iSbFtB2LgnaaqJgZ8FPXRRzcrMq7Tms41QNnTV291rpkps9vRwyss9zgDc7hS5V1aM1by8nFip5VjpGpz1oP54peKt" \
            "hJzfabX"
        wlt = Wallet.create("test_wallet_balance_update_multi_network", network='bitcoinlib_test',
                            witness_type='legacy', db_uri=self.database_uri)
        wlt.new_key()
        wlt.new_account(network='testnet')
        wlt.import_key(k)
        wlt.utxos_update()
        self.assertEqual(wlt.balance(), 400000000)
        self.assertEqual(wlt.balance(network='testnet'), 1800)
        self.assertEqual(wlt.balance(network='bitcoinlib_test'), 400000000)
        del wlt

    def test_wallet_balance_update_total(self):
        k = "tpubDCutwJADa3iSbFtB2LgnaaqJgZ8FPXRRzcrMq7Tms41QNnTV291rpkps9vRwyss9zgDc7hS5V1aM1by8nFip5VjpGpz1oP54peKt" \
            "hJzfabX"
        wlt = Wallet.create("test_wallet_balance_update_total", keys=k, network='testnet',
                            db_uri=self.database_uri)
        wlt.get_key()
        self.assertEqual(wlt.balance_update_from_serviceprovider(), 900)

    def test_wallet_add_dust_to_fee(self):
        # Send bitcoinlib test transaction and check if dust resume amount is added to fee
        wlt = Wallet.create('bcltestwlt', network='bitcoinlib_test', witness_type='legacy',
                            db_uri=self.database_uri)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 99992000, fee=7500, broadcast=True)
        self.assertEqual(t.fee, 8000)
        del wlt

    def test_wallet_transactions_send_update_utxos(self):
        # Send bitcoinlib test transaction and check if all utxo's are updated after send
        wlt = Wallet.create('bcltestwlt2', network='bitcoinlib_test', db_uri=self.database_uri)
        to_keys = wlt.get_keys(number_of_keys=5)
        wlt.utxos_update()
        self.assertEqual(wlt.balance(), 1000000000)
        t = wlt.send_to(to_keys[0].address, 550000000, broadcast=True)
        wlt._balance_update(min_confirms=0)
        self.assertEqual(wlt.balance(), 1000000000 - t.fee)
        self.assertEqual(len(wlt.utxos()), 6)
        del wlt

    def test_wallet_transaction_import(self):
        wlt = Wallet.create('bcltestwlt3', network='bitcoinlib_test', db_uri=self.database_uri)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 40000000)
        t2 = wlt.transaction_import(t)
        self.assertDictEqualExt(t.as_dict(), t2.as_dict())
        del wlt

    def test_wallet_transaction_import_raw(self):
        wlt = Wallet.create('bcltestwlt4', network='bitcoinlib_test', db_uri=self.database_uri)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 50000000)
        t2 = wlt.transaction_import_raw(t.raw())
        self.assertDictEqualExt(t.as_dict(), t2.as_dict(), ['spending_txid', 'spending_index_n'])
        del wlt

    def test_wallet_transaction_import_raw_locktime(self):
        wlt = Wallet.create('bcltestwlt4b', network='bitcoinlib_test', db_uri=self.database_uri)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 12312837)
        t.set_locktime_blocks(1000)
        t2 = wlt.transaction_import_raw(t.raw())
        self.assertDictEqualExt(t.as_dict(), t2.as_dict(), ['spending_txid', 'spending_index_n'])
        del wlt

    def test_wallet_transaction_import_raw_segwit_fee(self):
        wallet_delete_if_exists('bcltestwlt-size', force=True, db_uri=self.database_uri)
        pk = ('BC19UtECk2r9PVQYhZT9iJZvzK7jDgQXFQxRiguB28ESn53b8BjZjT4ZyQEStPD9yKAXBhTq6Wtb9zyPQiRU4chaTjEwvtpKW'
              'EdrMscH3ZqPTtdV')
        wlt = Wallet.create('bcltestwlt-size', keys=pk, network='bitcoinlib_test', witness_type='segwit',
                            db_uri=self.database_uri)
        wlt.utxos_update()
        t = wlt.send_to(wlt.get_key().address, 8237234)
        t2 = wlt.transaction_import_raw(t.raw())
        self.assertEqual(t.fee, t2.fee)
        self.assertEqual(t.size, t2.size)
        self.assertEqual(t.vsize, t2.vsize)
        self.assertEqual(t.fee_per_kb, t2.fee_per_kb)
        self.assertEqual(t.raw_hex(), t2.raw_hex())
        del wlt

    def test_wallet_transaction_load_segwit_size(self):
        pk = ('BC19UtECk2r9PVQYhZT9iJZvzK7jDgQXFQxRiguB28ESn53b8BjZjT4ZyQEStPD9yKAXBhTq6Wtb9zyPQiRU4chaTjEwvtpKW'
              'EdrMscH3ZqPTtdV')
        wlt = Wallet.create('bcltestwlt2-size', keys=pk, network='bitcoinlib_test', witness_type='segwit',
                            db_uri=self.database_uri)
        wlt.utxos_update()
        t = wlt.send_to(wlt.get_key().address, 50000000, broadcast=True)
        t.verify()
        self.assertTrue(t.verified)

        t2 = wlt.transaction(t.txid)
        t2.verify()
        self.assertTrue(t2.verified)
        self.assertEqual(t.vsize, t2.vsize)
        self.assertEqual(t.witness_data(), t2.witness_data())

    def test_wallet_transaction_import_dict(self):
        wlt = Wallet.create('bcltestwlt5', network='bitcoinlib_test', db_uri=self.database_uri)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 60000000)
        t2 = wlt.transaction_import(t.as_dict())
        self.assertDictEqualExt(t.as_dict(), t2.as_dict())
        del wlt

    def test_wallet_transaction_fee_limits(self):
        wlt = Wallet.create('bcltestwlt6', network='bitcoinlib_test', witness_type='legacy',
                            db_uri=self.database_uri)
        to_key = wlt.get_key()
        wlt.utxos_update()
        self.assertRaisesRegex(WalletError, 'Fee per kB of 660 is lower then minimal network fee of 1000',
                                wlt.send_to, to_key.address, 50000000, fee=150)
        self.assertRaisesRegex(WalletError, 'Fee per kB of 1321585 is higher then maximum network fee of 1000000',
                                wlt.send_to, to_key.address, 50000000, fee=300000)

    def test_wallet_transaction_fee_zero_problem(self):
        wlt = Wallet.create(name='bcltestwlt7', network='bitcoinlib_test', db_uri=self.database_uri)
        nk = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(nk.address, 100000000, broadcast=True)
        self.assertTrue(t.pushed)
        self.assertNotEqual(t.fee, 0)

    def test_wallet_transactions_estimate_size(self):
        prev_txid = '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5'

        for witness_type in ['legacy', 'p2sh-segwit', 'segwit']:
            wallet_delete_if_exists('wallet_estimate_size', force=True, db_uri=self.database_uri)
            wl3 = Wallet.create('wallet_estimate_size', witness_type=witness_type,
                                db_uri=self.database_uri)
            wl3.utxo_add(wl3.get_key().address, 110000, prev_txid, 0, 1)
            to_address = wl3.get_key_change().address
            t = wl3.transaction_create([(to_address, 90000)], fee=10000, random_output_order=False)
            t.estimate_size()
            size1 = t.size
            t.sign()
            t.estimate_size()
            size2 = t.size
            self.assertAlmostEqual(size1, size2, delta=2)
            self.assertAlmostEqual(len(t.raw()), size2, delta=2)

        for witness_type in ['legacy', 'p2sh-segwit', 'segwit']:
            p1 = HDKey(witness_type=witness_type, multisig=True)
            p2 = HDKey(witness_type=witness_type, multisig=True)
            p3 = HDKey(witness_type=witness_type, multisig=True)

            wallet_delete_if_exists('wallet_estimate_size_multisig', force=True, db_uri=self.database_uri)
            wl3 = Wallet.create('wallet_estimate_size_multisig', [p1, p2.public_master(), p3.public_master()],
                                sigs_required=2, db_uri=self.database_uri)
            wl3.utxo_add(wl3.get_key().address, 110000, prev_txid, 0, 1)
            to_address = wl3.get_key_change().address
            t = wl3.transaction_create([(to_address, 90000)], fee=10000, random_output_order=False)
            t.estimate_size()
            size1 = t.size
            t.sign(p2)
            t.estimate_size()
            size2 = t.size
            self.assertAlmostEqual(size1, size2, delta=6)
            self.assertAlmostEqual(len(t.raw()), size2, delta=6)

    def test_wallet_transaction_method(self):
        pk1 = HDKey(network='bitcoinlib_test')
        pk2 = HDKey(network='bitcoinlib_test')
        w = Wallet.create('wallet_transaction_tests', keys=[pk1, pk2], cosigner_id=0,
                          db_uri=self.database_uri)
        w.get_key()
        w.utxos_update()
        self.assertEqual(len(w.transactions()), 2)
        self.assertEqual(type(w.transactions(as_dict=True)[0]), dict)
        self.assertEqual(type(w.transactions()[0].as_dict()), dict)

    def test_wallet_transaction_from_txid(self):
        w = Wallet.create('testwltbcl', keys='dda84e87df25f32d73a7f7d008ed2b89fc00d9d07fde588d1b8af0af297023de',
                          witness_type='legacy', network='bitcoinlib_test', db_uri=self.database_uri)
        w.utxos_update()
        wts = w.transactions()
        txid = wts[0].txid
        self.assertEqual(txid, '86eebbefb1062b45b19bc1bbc3fbe044fadcf592dc4e64f1a13a58ac362123ef')
        wt0 = WalletTransaction.from_txid(w, txid)
        self.assertEqual(wt0.outputs[0].address, 'zwqrC7h9pRj7SBhLRDG4FnkNBRQgene3y1')
        # Test __repr__
        self.assertEqual(repr(wt0), '<WalletTransaction(input_count=0, output_count=1, status=confirmed, '
                                    'network=bitcoinlib_test)>')
        # Test info()
        wt0.info()
        # Unknown txid
        self.assertIsNone(WalletTransaction.from_txid(w, '112233'))

    def test_wallet_transaction_sign_with_hex(self):
        k = HDKey(network='bitcoinlib_test', witness_type='legacy')
        pmk = k.public_master()
        w = Wallet.create('wallet_tx_tests', keys=pmk, network='bitcoinlib_test', db_uri=self.database_uri)
        w.utxos_update()
        wt = w.transaction_create([(w.get_key(), 190000000)])
        sk = k.subkey_for_path("m/44'/9999999'/0'/0/0")
        wt.sign(sk.private_hex)
        self.assertTrue(wt.verified)

    def test_wallet_transaction_sign_with_wif(self):
        wif = ('BC19UtECk2r9PVQYhZuLSVjB6M7QPkAQSJN59RJKZQuuuPxaxNBEwmnfpWYvrQTrJZCANKoXBm7HKY78dVHjTkqoqA67aUf'
               'NSLZjuwNGDBMQD7uM')
        wif2 = ('BC19UtECk2r9PVQYhYJrXwB3We4E9Xc6uJngAEoqBrntN1gpGZwAWKRdcupdf2iKFLfY3pYRxHAi99EZ7dyYcKLZ2a7999'
                'Lu2NRSZzToFXib5kcE')
        w = wallet_create_or_open('test_wallet_transaction_sign_with_wif',
                                  keys=[wif, HDKey(wif2).public_master_multisig(witness_type='segwit')],
                                  witness_type='segwit', network='bitcoinlib_test',
                                  db_uri=self.database_uri)
        w.get_key()
        w.utxos_update()
        t = w.send_to('blt1q285vnphcs4r0t5dw06tmxl7aryj3jnx88duehv4p7eldsshrmygsmlq84z', 2000, fee=1000, broadcast=True)
        t.sign(wif2)
        self.assertIsNone(t.send())
        self.assertTrue(t.pushed)

    def test_wallet_transaction_restore_saved_tx(self):
        if not USE_FASTECDSA:
            self.skipTest("Need fastecdsa module with deterministic txid's to run this test")

        w = wallet_create_or_open('test_wallet_transaction_restore', network='bitcoinlib_test',
                                  db_uri=self.database_uri)
        wk = w.get_key()
        utxos = [{
            'address': wk.address,
            'script': '',
            'confirmations': 10,
            'output_n': 1,
            'txid': '9f5d4004c7cc5a31a735bddea6ff517e52f1cd700df208d2c39ddc536670f1fe',
            'value': 1956783097
        }]
        w.utxos_update(utxos=utxos)
        to = w.get_key_change()
        t = w.sweep(to.address, fee=10000)
        tx_id = t.store()
        del w
        wallet_empty('test_wallet_transaction_restore', db_uri=self.database_uri)
        w = wallet_create_or_open('test_wallet_transaction_restore', network='bitcoinlib_test',
                                  db_uri=self.database_uri)
        w.get_key()
        w.utxos_update(utxos=utxos)
        to = w.get_key_change()
        t2 = w.sweep(to.address, fee=10000)
        self.assertEqual(t.txid, t2.txid)
        self.assertEqual(t2.store(), tx_id)

    def test_wallet_transaction_send_keyid(self):
        w = Wallet.create('wallet_send_key_id', witness_type='segwit', network='bitcoinlib_test',
                          db_uri=self.database_uri)
        keys = w.get_keys(number_of_keys=2)
        w.utxos_update()
        t = w.send_to('blt1qtk5swtntg8gvtsyr3kkx3mjcs5ncav84exjvde', 150000000, input_key_id=keys[1].key_id,
                      broadcast=True)
        self.assertEqual(t.inputs[0].address, keys[1].address)
        self.assertTrue(t.verified)
        self.assertRaisesRegex(WalletError, "Not enough unspent transaction outputs found", w.send_to,
                                'blt1qtk5swtntg8gvtsyr3kkx3mjcs5ncav84exjvde', 250000000,
                                input_key_id=keys[0].key_id)

    def test_wallet_transactions_limit(self):
        address = '15yN7NPEpu82sHhB6TzCW5z5aXoamiKeGy'
        w = wallet_create_or_open('ftrtxtstwlt', address, db_uri=self.database_uri)
        w.transactions_update(limit=2)
        self.assertGreaterEqual(w.balance(), 1000)
        self.assertGreaterEqual(len(w.transactions()), 2)
        w.transactions_update(limit=2)
        self.assertGreaterEqual(len(w.transactions()), 4)

    def test_wallet_transactions_update_by_txids(self):
        address = '15yN7NPEpu82sHhB6TzCW5z5aXoamiKeGy'
        w = wallet_create_or_open('ftrtxtstwlt2', address, db_uri=self.database_uri)
        w.transactions_update_by_txids(['b246dad8980093fa55814b4739396fd6a7f5f28994f721f55d1a862d6c98e7ab'])
        txs = w.transactions()
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0].block_height, 368209)

    def test_wallet_transactions_sign_with_mnenomic(self):
        phr = 'battle alter frequent adult tuna follow always jar obtain until ice arrange'
        prv_key = HDKey.from_passphrase(phr, network='bitcoinlib_test')
        w = wallet_create_or_open('wlt-sign-with-mnemonic', keys=prv_key.public(), network='bitcoinlib_test',
                                  scheme='single', db_uri=self.database_uri)
        w.new_key()
        w.utxos_update()
        t = w.send_to('214bP4ZpdejMppADEnxSkzziPgEG6XGcxiJ', 100000)
        self.assertFalse(t.verified)
        t.sign(phr)
        t.verify()
        self.assertTrue(t.verified)

    def test_wallet_select_inputs(self):
        wlt = Wallet.create('bclwltsltinputs', network='bitcoinlib_test', db_uri=self.database_uri)
        wlt.get_key()
        wlt.utxos_update()
        self.assertEqual(wlt.select_inputs(150000000, max_utxos=1), [])
        self.assertEqual(len(wlt.select_inputs(150000000)), 2)

    def test_wallet_transaction_create_exceptions(self):
        wif = ('BC17qWy2RMw8AmwsqwTjmX2SwwSHBNA2c6KyGHs5Kghg3q6dPa4ajP1jwFBPCkoSeXWsPAiVD2iAcroVc6cJQmHrYatvi'
               'NCk5jDM83DkbPGFxbCK')
        wlt = Wallet.create('test_wallet_transaction_create_exceptions', keys=wif, db_uri=self.database_uri)
        wlt.utxos_update()
        self.assertRaisesRegex(WalletError, "Output array must be a list of tuples with address and amount. "
                                             "Use 'send_to' method to send to one address",
                                wlt.transaction_create, '217rBycQpv9rjhiLcg94vdZ7muMVLJ9yysJ')
        inps = wlt.select_inputs(150000000)
        self.assertRaisesRegex(WalletError, "Input array contains 2 UTXO's but max_utxos=1 parameter specified",
                                wlt.transaction_create, [('217rBycQpv9rjhiLcg94vdZ7muMVLJ9yysJ', 150000000)],
                                inps, max_utxos=1)
        wallet_empty('test_wallet_transaction_create_exceptions', db_uri=self.database_uri)
        self.assertRaisesRegex(WalletError, "UTXO",
                                wlt.transaction_create, [('217rBycQpv9rjhiLcg94vdZ7muMVLJ9yysJ', 150000000)],
                                inps)

    def test_wallet_transactions_sweep(self):
        w = wallet_create_or_open('test_wallet_sweep_check_fee', db_uri=self.database_uri)
        w.utxo_add(w.new_key().address, 5000,
                   'f31446151f06522eb321d5992f4f1c95123c8b9d082b92c391df83c6d0a35516', 0, 1)
        t = w.sweep('14pThTJoEnQxbJJVYLhzSKcs6EmZgShscX', fee=2000)
        self.assertEqual(5000, t.outputs[0].value + t.fee)
        self.assertRaisesRegex(WalletError, "Amount to send is smaller then dust amount: 1000",
                               w.sweep, to_address='14pThTJoEnQxbJJVYLhzSKcs6EmZgShscX', fee=4000)
        self.assertRaisesRegex(WalletError, "Amount to send is smaller then dust amount: -1000",
                               w.sweep, to_address='14pThTJoEnQxbJJVYLhzSKcs6EmZgShscX', fee=6000)

    def test_wallet_sweep_multiple_inputs_or_outputs(self):
        w = wallet_create_or_open('test_wallet_sweep_multiple_outputs', db_uri=self.database_uri)

        utxos = [
            {
                "address": w.new_key().address,
                "script": "",
                "confirmations": 10,
                "output_n": 1,
                "txid": "f31446151f06522eb321d5992f4f1c95123c8b9d082b92c391df83c6d0a35516",
                "value": 100000
            },
            {
                "address": w.new_key().address,
                "script": "",
                "confirmations": 10,
                "output_n": 1,
                "txid": "9df91f89a3eb4259ce04af66ad4caf3c9a297feea5e0b3bc506898b6728c5003",
                "value": 200000
            },
            {
                "address": w.new_key().address,
                "script": "",
                "confirmations": 10,
                "output_n": 0,
                "txid": "7c21f0fad4344774d231081a75d7ab77f5328f446ef13e17709f876bd643d4de",
                "value": 25000
            },
            {
                "address": w.new_key().address,
                "script": "",
                "confirmations": 10,
                "output_n": 1,
                "txid": "7c21f0fad4344774d231081a75d7ab77f5328f446ef13e17709f876bd643d4de",
                "value": 50000
            },
        ]
        w.utxos_update(utxos=utxos)

        t = w.sweep([('14pThTJoEnQxbJJVYLhzSKcs6EmZgShscX', 11000), ('1GSffHyTGyKvQWpKHc7Mjd8K2bmbt7g9Xx', 0)],
                    broadcast=False, fee=2000)
        self.assertIn(362000, [o.value for o in t.outputs])
        self.assertTrue(t.verified)

        input_key_ids = [u['key_id'] for u in w.utxos() if u['value'] in [50000, 25000, 100000]]
        t = w.sweep([('14pThTJoEnQxbJJVYLhzSKcs6EmZgShscX', 150000), ('1GSffHyTGyKvQWpKHc7Mjd8K2bmbt7g9Xx', 0)],
                    input_key_id=input_key_ids, fee=5000)
        self.assertIn(20000, [o.value for o in t.outputs])
        self.assertEqual(3, len(t.inputs))
        self.assertTrue(t.verified)

    def test_wallet_send_multiple_change_outputs(self):
        w = wallet_create_or_open('test_wallet_send_multiple_change_outputs', db_uri=self.database_uri)

        utxos = [
            {
                "address": w.new_key().address,
                "script": "",
                "confirmations": 1,
                "output_n": 0,
                "txid": "d82d131e5ac0edfa6a3e1781c05b2a7f846b60fe8868b9d53da33756d98bc4fd",
                "value": 250000
            },
            {
                "address": w.new_key().address,
                "script": "",
                "confirmations": 2,
                "output_n": 1,
                "txid": "08de8bcb017f3aa9568344d1b49b9e3a16a580427330f9cb68e1ce61cacb4a2f",
                "value": 75000
            },
            {
                "address": w.new_key().address,
                "script": "",
                "confirmations": 2,
                "output_n": 0,
                "txid": "08de8bcb017f3aa9568344d1b49b9e3a16a580427330f9cb68e1ce61cacb4a2f",
                "value": 25000
            },
        ]
        w.utxos_update(utxos=utxos)

        t = w.send_to('1D6kjUgadFdpvEL7hUUDsmqSemeUaN1iFi', 150000, number_of_change_outputs=2, fee=3000)
        self.assertEqual(3, len(t.outputs))
        self.assertEqual(247000, t.output_total)
        self.assertFalse([o.value for o in t.outputs if o.value < o.network.dust_amount])
        self.assertTrue(t.verified)
        self.assertEqual(1, len(t.inputs))

        t = w.send_to('1D6kjUgadFdpvEL7hUUDsmqSemeUaN1iFi', 80000, number_of_change_outputs=0, fee=1000)
        self.assertEqual(249000, sum([o.value for o in t.outputs]))
        self.assertGreaterEqual(len(t.outputs), 2)
        self.assertLessEqual(len(t.outputs), 5)
        self.assertFalse([o.value for o in t.outputs if o.value < o.network.dust_amount])
        self.assertTrue(t.verified)
        self.assertEqual(1, len(t.inputs))

    def test_wallet_transaction_save_and_load(self):
        w = wallet_create_or_open('wallet_transaction_save_and_load', network='bitcoinlib_test',
                                  db_uri=self.database_uri)
        w.utxos_update()
        t = w.send_to(w.get_key(), 50000001)
        self.assertTrue(t.verify())
        t.save()
        t2 = w.transaction_load(t.txid)
        self.assertTrue(t2.verify())
        self.assertEqual(t.txid, t2.txid)
        self.assertEqual(t.raw_hex(), t2.raw_hex())

    def test_wallet_transaction_save_and_load_filename(self):
        w = wallet_create_or_open('wallet_transaction_save_and_load_filename', network='bitcoinlib_test',
                                  db_uri=self.database_uri)
        w.utxos_update()
        t = w.send_to(w.get_key(), 44000001)
        self.assertTrue(t.verify())
        t.save('saved_tx.tx')
        t2 = w.transaction_load(filename='saved_tx.tx')
        self.assertTrue(t2.verify())
        self.assertEqual(t.txid, t2.txid)
        self.assertEqual(t.raw_hex(), t2.raw_hex())

    def test_wallet_avoid_forced_address_reuse(self):
        w = wallet_create_or_open('wallet_avoid_forced_address_reuse_test', network='bitcoinlib_test',
                                  db_uri=self.database_uri)
        k1 = w.get_key()
        w.utxos_update()
        k2 = w.new_key()
        w.sweep(k2.address, broadcast=True)

        # Send dust to used address
        w.send_to(k1, 400, min_confirms=0, broadcast=True)

        # Try to spend dust
        t = w.sweep('zz3nA9VNyXwwyKKALckuhQ5sYdxMuzCQuQ', min_confirms=0, broadcast=True)
        self.assertEqual(len(t.inputs), 1)

    def test_wallet_avoid_forced_address_reuse2(self):
        w = wallet_create_or_open('wallet_avoid_forced_address_reuse_test2', db_uri=self.database_uri)
        utxos = [
            {
                'address': w.new_key().address,
                'script': '',
                'confirmations': 5,
                'output_n': 0,
                'txid': '35b59b39d66e34dada7536df1dd95b831c367125f846ea2904c128e66aa29267',
                'value': 426
            },
            {
                'address': w.new_key().address,
                'script': '',
                'confirmations': 5,
                'output_n': 0,
                'txid': '458f44d469489ce06d2aab54347253dd82bee90b38756e4514e5a29b5f07213f',
                'value': 200000
            }
        ]
        w.utxos_update(utxos=utxos)
        self.assertRaisesRegex(WalletError, "", w.send_to, 'bc1qx76mfmrgvejprscpk8e76d90h94xdhhgnr3jfk', 200001,
                                fee=150)

    def test_wallet_transactions_delete(self):
        w = wallet_create_or_open('wallet_transactions_delete', network='bitcoinlib_test', db_uri=self.database_uri)
        w.utxos_update()
        w.transactions()[0].delete()
        self.assertEqual(len(w.transactions()), 1)

    def test_wallet_transaction_delete_reverse_latest(self):
        pkm = 'elephant dust deer company win final'
        expected_utxos = ['520208458b4f93ef7f1a4df447b6fedb50888aaa098ab501b32b1df3f88daa86',
                          'ea7bd8fe970ca6430cebbbf914ce2feeb369c3ae95edc117725dbe21519ccdab']
        expected_txid = '00c6f17bab32ac30979c284a36537f288ed85648810d5d479fcf2a526cdcd3f6'

        w = Wallet.create("remove_utxos_test", keys=pkm, network="bitcoinlib_test", db_uri=self.database_uri)
        w.utxos_update()
        self.assertEqual([], [False for u in w.utxos() if u['txid'] not in expected_utxos])

        w.get_key()
        t = w.send_to("blt1qad80unqvexkhm96rxysra2mczy74zlszjr4ty9", "0.5 TST", broadcast=True,
                      fee=4799, random_output_order=False)
        self.assertEqual(w.balance(), 199995201)
        if USE_FASTECDSA:
            self.assertEqual(t.txid, expected_txid)
        else:
            expected_txid = t.txid

        wlt_utxos = [u['txid'] for u in w.utxos()]
        self.assertEqual(wlt_utxos[2], expected_txid)
        wt = w.transaction(t.txid)
        wt.delete()
        self.assertEqual([], [False for u in w.utxos() if u['txid'] not in expected_utxos])

    def test_wallet_create_import_key(self):
        w = wallet_create_or_open("test_wallet_create_import_key_private", network='bitcoinlib_test',
                                  db_uri=self.database_uri)

        w.utxos_update()
        wk = w.public_master()
        w2 = wallet_create_or_open('test_wallet_create_import_key_public', network='bitcoinlib_test', keys=wk,
                                   db_uri=self.database_uri)
        w2.utxos_update()

        wt = w2.send_to('21HKMUVtSUETuWyDESrmCj6Vwvtuns8XG5k', 1000, fee=1000)
        wt.save()

        wt2 = Transaction.load(wt.txid)
        self.assertEqual(wt, wt2)

    def test_wallet_transactions_pagination(self):
        w = wallet_create_or_open("bclt_wallet_pagination_test", network='bitcoinlib_test', db_uri=self.database_uri)
        w.get_keys(number_of_keys=10)
        w.utxos_update()
        txs_all = w.transactions_full()
        txs_page = w.transactions_full(limit=2, offset=10)
        self.assertEqual(len(txs_all), 20)
        self.assertEqual(len(txs_page), 2)
        self.assertEqual(txs_all[10], txs_page[0])
        self.assertEqual(txs_all[11], txs_page[1])

    def test_wallet_merge_transactions(self):
        w = wallet_create_or_open('wallet_merge_transactions_tests', network='bitcoinlib_test',
                                  db_uri=self.database_uri)
        w.utxos_update()
        u = w.utxos()

        t1 = w.send_to(w.get_key(), 200000, input_key_id=u[0]['key_id'], broadcast=True)
        t2 = w.send_to(w.get_key(), 300000, input_key_id=u[1]['key_id'], broadcast=True)
        t = t1 + t2
        self.assertTrue(t.verified)
        self.assertEqual(t1.input_total + t2.input_total, t.input_total)
        self.assertEqual(t1.output_total + t2.output_total, t.output_total)
        self.assertEqual(t1.fee + t2.fee, t.fee)

    def test_wallet_transaction_replace_by_fee(self):
        w = wallet_create_or_open('wallet_transaction_rbf', network='bitcoinlib_test',
                                  db_uri=self.database_uri)
        w.utxos_update()
        address = w.get_key()
        t = w.send_to(address, 10000, fee=500, replace_by_fee=True)
        self.assertTrue(t.verify())
        t2 = w.send_to(address, 10000, fee=1000, replace_by_fee=True)
        self.assertTrue(t2.verify())
        self.assertTrue(t2.replace_by_fee)
        self.assertEqual(t2.inputs[0].sequence, SEQUENCE_REPLACE_BY_FEE)

    def test_wallet_anti_fee_sniping(self):
        w = wallet_create_or_open('antifeesnipingtestwallet', network='testnet', db_uri=self.database_uri)
        w.utxo_add(w.get_key().address, 1234567, os.urandom(32).hex(), 1)
        t = w.send_to('tb1qrjtz22q59e76mhumy0p586cqukatw5vcd0xvvz', 123456)
        block_height = Service(network='testnet', cache_uri='').blockcount()
        self.assertAlmostEqual(t.locktime, block_height+1, delta=3)

        w2 = wallet_create_or_open('antifeesnipingtestwallet2', network='testnet', anti_fee_sniping=True)
        w2.utxo_add(w2.get_key().address, 1234567, os.urandom(32).hex(), 1)
        t = w2.send_to('tb1qrjtz22q59e76mhumy0p586cqukatw5vcd0xvvz', 123456, locktime=1901070183)
        self.assertEqual(t.locktime, 1901070183)

        w3 = wallet_create_or_open('antifeesnipingtestwallet3', network='testnet', anti_fee_sniping=False)
        w3.utxo_add(w3.get_key().address, 1234567, os.urandom(32).hex(), 1)
        t = w3.send_to('tb1qrjtz22q59e76mhumy0p586cqukatw5vcd0xvvz', 123456)
        self.assertEqual(t.locktime, 0)

    @classmethod
    def tearDownClass(cls):
        del cls.wallet


class TestWalletSegwit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()

    def test_wallet_segwit_create_p2pkh(self):
        phrase = "review arch uniform illness hello animal device reform bicycle obscure cruise boat"
        wlt = wallet_create_or_open('thetestwallet-bech32', keys=phrase, network='bitcoin', witness_type='segwit',
                                    db_uri=self.database_uri)
        self.assertEqual(wlt.get_key().address, 'bc1ql22f3gqqphsejtqkqjqg9an03sjz4l6gztcm34')

    def test_wallet_segwit_create_pswsh(self):
        phrase1 = 'exclude twice mention orchard grit ignore display shine cheap exercise same apart'
        phrase2 = 'shop cloth bench traffic vintage security hour engage omit almost episode fragile'
        pk1 = HDKey.from_passphrase(phrase1, witness_type='segwit', multisig=True)
        pk2 = HDKey.from_passphrase(phrase2, witness_type='segwit', multisig=True)
        w = Wallet.create('multisig-segwit', [pk1, pk2.public_master()], sigs_required=1, witness_type='segwit',
                          db_uri=self.database_uri)
        self.assertEqual(w.get_key().address, 'bc1qfjhmzzt9l6dmm0xx3tc6qrtff8dve7j7qrcyp88tllszm97r84aqxel5jk')

    def test_wallet_segwit_create_p2sh_p2wsh(self):
        phrase1 = 'exclude twice mention orchard grit ignore display shine cheap exercise same apart'
        phrase2 = 'shop cloth bench traffic vintage security hour engage omit almost episode fragile'
        pk1 = HDKey.from_passphrase(phrase1)
        pk2 = HDKey.from_passphrase(phrase2)
        w = Wallet.create('segwit-p2sh-p2wsh', [pk1, pk2.public_master(witness_type='p2sh-segwit', multisig=True)],
                          sigs_required=2, witness_type='p2sh-segwit', db_uri=self.database_uri)
        nk = w.get_key()
        self.assertEqual(nk.address, '3JFyRjKWYFz5BMFHLZvT7EZQJ85gLFvtkT')
        self.assertEqual(nk.key_type, 'multisig')
        self.assertEqual(nk.path, "m/48'/0'/0'/1'/0/0")

    def test_wallet_segwit_create_p2sh_p2wpkh(self):
        phrase = 'fun brick apology sport museum vague once gospel walnut jump spawn hedgehog'
        w = wallet_create_or_open('segwit-p2sh-p2wpkh', phrase, purpose=49, witness_type='p2sh-segwit',
                                  network='bitcoin', db_uri=self.database_uri)

        k1 = w.get_key()
        address = '3Disr2CmERuYuuMkkfGrjRUHqDENQvtNep'
        self.assertEqual(Address(b'\x00\x14' + k1.key().hash160, script_type='p2sh').address, address)
        self.assertEqual(Address(k1.key().public_byte, script_type='p2sh_p2wpkh').address, address)
        self.assertEqual(k1.address, address)

    def test_wallet_segwit_p2wpkh_send(self):
        w = Wallet.create('segwit_p2wpkh_send', witness_type='segwit', network='bitcoinlib_test',
                          db_uri=self.database_uri)
        w.get_key()
        w.utxos_update()
        t = w.send_to('blt1q7ywlg3lsyntsmp74jh65pnkntk3csagdwpz78k', 10000, broadcast=True)
        self.assertEqual(t.witness_type, 'segwit')
        self.assertEqual(t.inputs[0].script_type, 'sig_pubkey')
        self.assertEqual(t.inputs[0].witness_type, 'segwit')
        self.assertTrue(t.verified)
        self.assertTrue(t.pushed)

    def test_wallet_segwit_p2wsh_send(self):
        w = Wallet.create('segwit_p2wsh_send', witness_type='segwit', network='bitcoinlib_test',
                          keys=[HDKey(network='bitcoinlib_test'), HDKey(network='bitcoinlib_test')], sigs_required=2,
                          cosigner_id=0, db_uri=self.database_uri)
        k = w.get_key()
        w.utxos_update()
        w.utxos_update(key_id=k.key_id)   # Test db updates after second request and only update single key
        t = w.send_to('blt1q7r60he62p52u6h9zyxl6ew4dmmshpmk5sluaax48j9c7zyxu6m0smrjqxa', 10000, broadcast=True)
        self.assertEqual(t.witness_type, 'segwit')
        self.assertEqual(t.inputs[0].script_type, 'p2sh_multisig')
        self.assertEqual(t.inputs[0].witness_type, 'segwit')
        self.assertTrue(t.verified)
        self.assertTrue(t.pushed)

    def test_wallet_segwit_p2sh_p2wpkh_send(self):
        w = Wallet.create('segwit_p2sh_p2wpkh_send', witness_type='p2sh-segwit', network='bitcoinlib_test',
                          db_uri=self.database_uri)
        w.get_key()
        w.utxos_update()
        t = w.send_to('blt1q7ywlg3lsyntsmp74jh65pnkntk3csagdwpz78k', 10000, broadcast=True)
        self.assertEqual(t.witness_type, 'segwit')
        self.assertEqual(t.inputs[0].script_type, 'sig_pubkey')
        self.assertEqual(t.inputs[0].witness_type, 'p2sh-segwit')
        self.assertTrue(t.verified)
        self.assertTrue(t.pushed)

    def test_wallet_segwit_p2sh_p2wsh_send(self):
        w = Wallet.create('segwit_p2sh_p2wsh_send', witness_type='p2sh-segwit', network='bitcoinlib_test',
                          keys=[HDKey(network='bitcoinlib_test'), HDKey(network='bitcoinlib_test'),
                                HDKey(network='bitcoinlib_test')], sigs_required=2, cosigner_id=0,
                          db_uri=self.database_uri)
        w.get_key()
        w.utxos_update()
        t = w.send_to('blt1q7ywlg3lsyntsmp74jh65pnkntk3csagdwpz78k', 10000, broadcast=True)
        self.assertEqual(t.witness_type, 'segwit')
        self.assertEqual(t.inputs[0].script_type, 'p2sh_multisig')
        self.assertEqual(t.inputs[0].witness_type, 'p2sh-segwit')
        self.assertTrue(t.verified)
        self.assertTrue(t.pushed)

    def test_wallet_segwit_uncompressed_error(self):
        k = HDKey(compressed=False, network='bitcoinlib_test')
        self.assertRaisesRegex(BKeyError, 'Uncompressed keys are non-standard', wallet_create_or_open,
                                'segwit_uncompressed_error', k, witness_type='segwit', network='bitcoinlib_test',
                                db_uri=self.database_uri)

    def test_wallet_segwit_bitcoin_send(self):
        # Create several SegWit wallet and create transaction to send to each other. Uses utxo_add() method to create
        # test UTXO's

        prev_txid = '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5'

        # === Segwit P2WSH to P2WSH ===
        pk2 = HDKey()
        key_list = [
            HDKey(),
            pk2.public_master(witness_type='segwit', multisig=True),
            HDKey().public_master(witness_type='segwit', multisig=True),
        ]

        wl1 = Wallet.create('segwit_bitcoin_p2wsh_send', key_list, sigs_required=2, witness_type='segwit',
                            db_uri=self.database_uri)
        wl1.utxo_add(wl1.get_key().address, 10000000, prev_txid, 0, 1)
        to_address = wl1.get_key_change().address
        t = wl1.transaction_create([(to_address, 100000)], fee=10000, random_output_order=False)

        t.sign(pk2.subkey_for_path("m/48'/0'/0'/2'/0/0"))
        self.assertTrue(t.verify())
        self.assertEqual(t.outputs[0].address, to_address)
        self.assertFalse(t.error)

        # === Segwit P2WPKH to P2WSH ===
        wl2 = Wallet.create('segwit_bitcoin_p2wpkh_send', witness_type='segwit', db_uri=self.database_uri)
        wl2.utxo_add(wl2.get_key().address, 200000, prev_txid, 0, 1)
        to_address = wl1.get_key_change().address
        t = wl2.transaction_create([(to_address, 100000)], fee=10000, random_output_order=False)
        t.sign()
        self.assertTrue(t.verify())
        self.assertEqual(t.outputs[0].address, to_address)
        self.assertFalse(t.error)

        # === Segwit P2SH-P2WPKH to P2WPK ===
        wl3 = Wallet.create('segwit_bitcoin_p2sh_p2wpkh_send', witness_type='p2sh-segwit',
                            db_uri=self.database_uri)
        wl3.utxo_add(wl3.get_key().address, 110000, prev_txid, 0, 1)
        t = wl3.transaction_create([(to_address, 100000)], fee=10000, random_output_order=False)
        t.sign()
        self.assertTrue(t.verify())
        self.assertEqual(t.outputs[0].address, to_address)
        self.assertFalse(t.error)

    def test_wallet_segwit_litecoin_multi_accounts(self):
        phrase = 'rug rebuild group coin artwork degree basic humor flight away praise able'
        w = Wallet.create('segwit_wallet_litecoin_p2wpkh', keys=phrase, network='litecoin',
                          db_uri=self.database_uri, witness_type='segwit')
        self.assertEqual(w.get_key().address, "ltc1qsrzxzg39jyt8knsw5hlqmpwmuc8ejxvp9hfch8")
        self.assertEqual(w.get_key_change().address, "ltc1q9n6zknsw2hhq7dkyvczars8vl8zta5yusjjem5")
        acc2 = w.new_account()
        btc_acc = w.new_account(network='bitcoin')
        self.assertEqual(w.get_key(acc2.account_id).address, "ltc1quya06p0ywk55rvf6jjpvxwmd66n2axu8qhnned")
        self.assertEqual(w.get_key(btc_acc.account_id, network='bitcoin').address,
                         "bc1qnxntu52qfppmt2l2wezrn8rtsqy092q3utxhgd")

        phrase = 'rug rebuild group coin artwork degree basic humor flight away praise able'

        w = Wallet.create('segwit_wallet_litecoin_p2sh_p2wpkh', keys=phrase, network='litecoin',
                          db_uri=self.database_uri, witness_type='p2sh-segwit')
        self.assertEqual(w.get_key().address, "MW1V5XPPW1YYQ5BGL5mSWEZNZSyD4XQPgh")
        self.assertEqual(w.get_key_change().address, "MWQoYMDTNvwZPNNypLMzkQ7JNSCtvS554j")

    def test_wallet_segwit_litecoin_sweep(self):
        phrase = 'wagon tunnel garage blast eager jaguar shop bring lake dumb chalk emerge'
        w = wallet_create_or_open('ltcsw', phrase, network='litecoin', witness_type='segwit',
                                  db_uri=self.database_uri)
        w.utxo_add('ltc1qu8dum66gd6dfr2cchgenf87qqxgenyme2kyhn8', 28471723,
                   '21da13be453624cf46b3d883f39602ce74d04efa7a186037898b6d7bcfd405ee', 10, 99)
        t = w.sweep('MLqham8sXULvktmNMuDQdrBbHRdytVZ1QK')
        self.assertTrue(t.verified)

    def test_wallet_segwit_litecoin_multisig(self):
        p1 = 'only sing document speed outer gauge stand govern way column material odor'
        p2 = 'oyster pelican debate mass scene title pipe lock recipe flavor razor accident'
        w = wallet_create_or_open('ltc_segwit_ms', [p1, p2], network='litecoin', witness_type='segwit',
                                  cosigner_id=0, db_uri=self.database_uri)
        w.get_keys(number_of_keys=2)
        w.utxo_add('ltc1qkewaz7lxn75y6wppvqlsfhrnq5p5mksmlp26n8xsef0556cdfzqq2uhdrt', 2100000000000001,
                   '21da13be453624cf46b3d883f39602ce74d04efa7a186037898b6d7bcfd405ee', 0, 15)

        t = w.sweep('ltc1q9h8xvtrge5ttcwzy3xtz7l8kj4dewgh6hgqfjdhtq6lwr4k3527qd8tyzs')
        self.assertTrue(t.verified)

    def test_wallet_segwit_multisig_multiple_inputs(self):
        main_key = HDKey(network='bitcoinlib_test')
        cosigner = HDKey(network='bitcoinlib_test')
        w = wallet_create_or_open('test_wallet_segwit_multisig_multiple_inputs',
                                  [main_key, cosigner.public_master(witness_type='segwit', multisig=True)],
                                  witness_type='segwit', network='bitcoinlib_test', db_uri=self.database_uri)

        w.get_keys(number_of_keys=2)
        w.utxos_update()
        to = w.get_key_change()
        t = w.sweep(to.address)
        t.sign(cosigner)
        self.assertTrue(t.verify())

    def test_wallet_segwit_multiple_account_paths(self):
        pk1 = HDKey(
            "ZprvAhadJRUYsNge9JCXTr7xphZaR6sW3HEeSQL7wgtEXceG5hoUViB9KQ4EX6hAdgziW7MorQAjyasWYirrCQrb3ySHaPBa8EiLTx"
            "t4LmqTyzp")
        pk2 = HDKey(
            "ZprvAhadJRUYsNgeBbjftwKvAhDEV1hrYBGY19wATHqnEt5jfWXxXChYP8Qfnw3w2zJZskNercma5S1fWYH7e7XwbTVPgbabvs1CfU"
            "zY2KQD2cB")
        w = Wallet.create("account-test", keys=[pk1, pk2.public_master(multisig=True)], witness_type='segwit',
                          db_uri=self.database_uri)
        w.new_account()
        w.new_account()
        w.new_account(account_id=100)
        self.assertRaisesRegex(WalletError, "Account with ID 100 already exists for this wallet",
                                w.new_account, 'test', 100)
        self.assertRaisesRegex(WalletError, "Account with ID 1001 not found in this wallet",
                                w.account, 1001)

        paths = ["m/48'/0'/0'/2'", "m/48'/0'/0'/2'/0/0", "m/48'/0'/0'/2'/1/0", "m/48'/0'/1'/2'", "m/48'/0'/1'/2'/0/0",
                 "m/48'/0'/1'/2'/1/0", "m/48'/0'/100'/2'", "m/48'/0'/100'/2'/0/0", "m/48'/0'/100'/2'/1/0"]
        self.assertListEqual(sorted(paths), sorted([k.path for k in w.keys()]))
        self.assertListEqual(w.accounts(), [0, 1, 100])

    def test_wallet_segwit_multiple_networks_accounts(self):
        pk1 = 'surround vacant shoot aunt acoustic liar barely you expand rug industry grain'
        pk2 = 'defy push try brush ceiling sugar film present goat settle praise toilet'
        wallet = Wallet.create(keys=[pk1, pk2], network='bitcoin', name='test_wallet_segwit_multicurrency',
                               witness_type='segwit', cosigner_id=0, encoding='base58',
                               db_uri=self.database_uri)
        wallet.new_account(network='litecoin')
        wallet.new_account(network='litecoin')
        wallet.new_account(network='bitcoin')
        wallet.new_account(network='testnet')
        wallet.new_key()
        wallet.new_key(network='litecoin')
        wallet.new_key(network='testnet')
        wallet.new_key(network='bitcoin')

        networks_expected = ['bitcoin', 'litecoin', 'testnet']
        self.assertListEqual(sorted([nw.name for nw in wallet.networks()]), networks_expected)
        self.assertListEqual([k.path for k in wallet.keys_accounts(network='litecoin')],
                             ["m/48'/2'/0'/2'", "m/48'/2'/1'/2'"])
        self.assertEqual(wallet.keys(network='litecoin')[0].address,
                         "ltc1qcu83hcdwy46dv85vmwnnfgzeu8d9arfy7kfyct52dxqcyvq2q6ds5kq2ah")
        self.assertEqual(wallet.keys(network='bitcoin')[0].address,
                         "bc1qd0f952amxkmqc9e60u4g8w4r5a3cx22lt5vqeeyljllacxq8ezusclkwa0")


class TestWalletKeyStructures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()

    def test_wallet_path_expand(self):
        wlt = wallet_create_or_open('wallet_path_expand', network='bitcoin', witness_type='legacy',
                                    db_uri=self.database_uri)
        self.assertListEqual(wlt.path_expand([8]), ['m', "44'", "0'", "0'", '0', '8'])
        self.assertListEqual(wlt.path_expand(['8']), ['m', "44'", "0'", "0'", '0', '8'])
        self.assertListEqual(wlt.path_expand(["99'", 1, 2]), ['m', "44'", "0'", "99'", '1', '2'])
        self.assertListEqual(wlt.path_expand(['m', "purpose'", "coin_type'", "1'", 2, 3]),
                             ['m', "44'", "0'", "1'", '2', '3'])
        self.assertListEqual(wlt.path_expand(['m', "purpose'", "coin_type'", "1", 2, 3]),
                             ['m', "44'", "0'", "1'", '2', '3'])
        self.assertListEqual(wlt.path_expand(['m', "purpose", "coin_type'", "1", 2, 3]),
                             ['m', "44'", "0'", "1'", '2', '3'])
        self.assertListEqual(wlt.path_expand([100], -2), ['m', "44'", "0'", "100'"])
        self.assertRaisesRegex(BKeyError, "Please provide value for 'address_index'",
                                wlt.path_expand, ['m', 45, "cosigner_index", 55, "address_index"])
        self.assertRaisesRegex(BKeyError, "Variable bestaatnie not found in Key structure definitions in main.py",
                                wlt.path_expand, ['m', "bestaatnie'", "coin_type'", "1", 2, 3])

    def test_wallet_exotic_key_paths(self):
        w = Wallet.create("simple_custom_keypath", key_path="m/change/address_index", witness_type='legacy',
                          db_uri=self.database_uri)
        self.assertEqual(w.new_key().path, "m/0/1")
        self.assertEqual(w.new_key_change().path, "m/1/0")
        self.assertEqual(w.wif()[:4], 'xpub')

        w = Wallet.create(
            "strange_key_path", keys=[HDKey(), HDKey()], purpose=100, cosigner_id=0,
            key_path="m/purpose'/cosigner_index/change/address_index", witness_type='legacy',
            db_uri=self.database_uri)
        self.assertEqual(w.new_key().path, "m/100'/0/0/0")
        self.assertEqual(w.new_key_change().path, "m/100'/0/1/0")

        wif1 = 'Zpub74CSuvLPQxWkdW7bivQAhomXZTzbE8quAakKRg1C3x7uDcCCeh7zPp1tZrtJrscihJRASZWjZQ7nPQj1SHTn8gkzAHPZL3dC' \
               'MbMQLFwMKVV'
        wif2 = 'Zpub75J84sqDUenYwh6eYwFnpXmfRMkfCwyEUBsN6fkGLQhh4nGmdxHw1io3AcUvAcK14RXosXfjG6Gfkz3NUHCa1JESGCf52ZWQ' \
               'd2CqDgo1rLa'
        w = Wallet.create(
            "long_key_path", keys=[wif1, wif2], witness_type='segwit', cosigner_id=1,
            key_path="m/purpose'/coin_type'/account'/script_type'/cosigner_index/change/address_index",
            db_uri=self.database_uri)
        self.assertEqual(w.new_key().path, "M/1/0/0")
        self.assertEqual(w.new_key_change().path, "M/1/1/0")
        self.assertEqual(w.public_master()[0].wif, wif1)
        self.assertEqual(w.public_master()[1].wif, wif2)

    def test_wallet_normalize_path(self):
        self.assertEqual(normalize_path("m/48h/0p/100H/1200'/1234555"), "m/48'/0'/100'/1200'/1234555")
        self.assertRaisesRegex(WalletError, 'Could not parse path. Index is empty.', normalize_path,
                                "m/44h/0p/100H//1201")

    def test_wallet_accounts(self):
        w = Wallet.create('test_litecoin_accounts', network='litecoin', account_id=1111, db_uri=self.database_uri)
        w.new_account(account_id=2222)
        w.new_account(account_id=5555, network='testnet')
        self.assertListEqual(w.accounts(), [1111, 2222])
        self.assertListEqual(w.accounts(network='testnet'), [5555])


class TestWalletReadonlyAddress(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()

    def test_wallet_readonly_create_and_import(self):
        k = '13A1W4jLPP75pzvn2qJ5KyyqG3qPSpb9jM'
        w = wallet_create_or_open('addrwlt', k, db_uri=self.database_uri)
        addr = Address.parse('12yuSkjKmHzXCFn39PK1XP3XyeoVw9LJdN')
        w.import_key(addr)
        self.assertEqual(len(w.accounts()), 1)
        w.utxos_update()
        self.assertListEqual(w.addresslist(),
                             ['13A1W4jLPP75pzvn2qJ5KyyqG3qPSpb9jM', '12yuSkjKmHzXCFn39PK1XP3XyeoVw9LJdN'])
        self.assertGreaterEqual(w.balance(), 4532991)
        self.assertRaisesRegex(WalletError, "No unspent", w.send_to, '1ApcyGtcX4DUmfGqPBPY1bvKEh2irLqnhp', 50000)
        self.assertEqual(w.utxo_last('13A1W4jLPP75pzvn2qJ5KyyqG3qPSpb9jM'),
                         '22965c151d850b5c7d98561e5432459141b1321a299cdcac1764f540eef56451')

    def test_wallet_address_import_public_key(self):
        wif = 'xpub661MyMwAqRbcFCwFkcko75u2VEinbG1u5U4nq8AFJq4AbLPEvwcmhZGgGcnDcEBpcfAFEP8vVhbJJvX1ieGWdoaa5AnHfyB' \
              'DAY95TfYH6H6'
        address = '1EJiPa66sT4PCDCFnc7oRnpWebAogPqppr'
        w = Wallet.create('test_wallet_address_import_public_key', address, db_uri=self.database_uri)
        self.assertEqual(w.addresslist(), [address])
        self.assertIsNone(w.main_key.key_public)
        w.import_key(wif)
        self.assertEqual(w.main_key.key_public.hex(),
                         '0225248feed626f2496276109329f1ce30225e7a3153fe24b5c56828b0773bae75')

    def test_wallet_address_import_public_key_segwit(self):
        address = 'bc1q84xq6lrzr09t3h2pw5ys5zee7rn3mxh5v65732'
        wif = 'zprvAWgYBBk7JR8Gj9CNFRBUq3DvNHDbZhH4L6AybFSTCH7DDW6boPyiQfTigAPhJma5wC4TP1o53Gz1XLh94xD3dVQUpsFDaCb2' \
              '9XmDQKBwKhz'
        w = Wallet.create('test_wallet_address_import_public_key_segwit', address, db_uri=self.database_uri)
        self.assertEqual(w.addresslist(), [address])
        self.assertIsNone(w.main_key.wif)
        w.import_key(wif)
        self.assertEqual(w.main_key.wif, wif)

    def test_wallet_address_import_private_key(self):
        wif = 'xprv9s21ZrQH143K2irnebDnjwxHwCtJBoJ3iF9C2jkdkVXBiY46PQJX9kxCRMVcM1YXLERWUiUBoxQEUDqFAKbrTaL9FB4HfRY' \
              'jsGgCGpRPWTy'
        address = '1EJiPa66sT4PCDCFnc7oRnpWebAogPqppr'
        w = Wallet.create('test_wallet_address_import_private_key', address, db_uri=self.database_uri)
        self.assertListEqual(w.addresslist(), [address])
        self.assertFalse(w.main_key.is_private)
        w.import_key(wif)
        self.assertTrue(w.main_key.is_private)


class TestWalletMixedWitnessTypes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_uri = database_init()

    def test_wallet_mixed_witness_types_address(self):
        pk = 'a9b723d90282710036e06ec5b3d0c303817e486fa3e8bc117aec839deaedb961'
        wseg = Wallet.create(name='wallet_witness_type_segwit', keys=pk, db_uri=self.database_uri)
        wleg = Wallet.create(name='wallet_witness_type_legacy', keys=pk, witness_type='legacy',
                             db_uri=self.database_uri)
        wp2sh = Wallet.create(name='wallet_witness_type_p2sh', keys=pk, witness_type='p2sh-segwit',
                              db_uri=self.database_uri)
        self.assertEqual(wseg.get_key(witness_type='legacy').address, wleg.get_key().address)
        self.assertEqual(wseg.get_key(witness_type='p2sh-segwit').address, wp2sh.get_key().address)
        self.assertEqual(wleg.get_key(witness_type='segwit').address, wseg.get_key().address)
        wmix_legkey = wseg.new_account(witness_type='legacy').address
        self.assertEqual(wmix_legkey, '18nM5LxmzaEcf4rv9pK7FLiAtfmH1VgVWD')
        self.assertEqual(wmix_legkey, wleg.new_account().address)
        self.assertEqual(wseg.new_key(witness_type='p2sh-segwit').address, wp2sh.new_key().address)
        self.assertEqual(wseg.new_key_change(witness_type='p2sh-segwit').address, wp2sh.new_key_change().address)
        self.assertEqual(wleg.get_key_change(witness_type='segwit').address,
                         wp2sh.get_key_change(witness_type='segwit').address)
        self.assertEqual(wleg.new_key_change(witness_type='p2sh-segwit', account_id=111).address,
                         wp2sh.new_key_change(account_id=111).address)

    def test_wallet_mixed_witness_types_masterkeys(self):
        pk = '5f5b1f7d8c023c4bf5deff1eefe7ee27c126879da7e65487cf9ff64bdc3a1518'
        wseg = Wallet.create(name='wallet_witness_types_masterkey_segwit', keys=pk, db_uri=self.database_uri)
        wleg = Wallet.create(name='wallet_witness_types_masterkey_legacy', keys=pk, witness_type='legacy',
                             db_uri=self.database_uri)
        wp2sh = Wallet.create(name='wallet_witness_types_masterkey_p2sh', keys=pk, witness_type='p2sh-segwit',
                              db_uri=self.database_uri)
        self.assertEqual(wseg.public_master().wif, wleg.public_master(witness_type='segwit').wif)
        self.assertEqual(wseg.public_master(witness_type='p2sh-segwit').wif,
                         wleg.public_master(witness_type='p2sh-segwit').wif)
        self.assertEqual(wp2sh.public_master().wif, wleg.public_master(witness_type='p2sh-segwit').wif)
        self.assertEqual(wleg.public_master().wif, wp2sh.public_master(witness_type='legacy').wif)

    def test_wallet_mixed_witness_types_send(self):
        w = Wallet.create(name='wallet_mixed_bcltest', network='bitcoinlib_test', db_uri=self.database_uri)
        seg_key = w.get_key()
        leg_key = w.new_key(witness_type='legacy')
        p2sh_key = w.new_key(witness_type='p2sh-segwit')
        self.assertEqual(seg_key.witness_type, 'segwit')
        self.assertEqual(leg_key.witness_type, 'legacy')
        self.assertEqual(p2sh_key.witness_type, 'p2sh-segwit')
        w.utxos_update()
        t = w.sweep('blt1qgk3zp30pnpggylp84enh0zpfpkdu63kv4xak4p', fee=30000)
        self.assertEqual(len(t.inputs), len(w.addresslist()) * 2)
        self.assertEqual(t.outputs[0].value, int(w.balance() - 30000))
        self.assertTrue(t.verified)
        t.send()
        self.assertIsNone(t.error)

    def test_wallet_mixed_witness_no_private_key(self):
        pub_master = ('zpub6qwhKTArtsgtCpVweSyJdVqmXTkmH3HXE2sc7RdhF5drnmcW2HXuFBqRPzVxhQkdaER3bSZeJbAbYxNGeShwUu'
                      'T49JfJqZLHNAsEUHD76AR')
        address = 'bc1qgf8fzfj65lcr5vae0sh77akurh4zc9s9m4uspm'
        w = Wallet.create('wallet_mix_no_private', keys=pub_master, db_uri=self.database_uri)
        self.assertEqual(address, w.get_key().address)
        self.assertRaisesRegex(WalletError, "This wallet has no private key, cannot use multiple witness types",
                                w.get_key, witness_type='legacy')

    def test_wallet_mixed_witness_type_create(self):
        w = Wallet.create('test_wallet_mixed_witness_type_create', network='testnet', db_uri=self.database_uri)
        w.get_key(witness_type='legacy')
        w.new_account('test-account', 101, witness_type='p2sh-segwit')
        w.get_key(account_id=101)
        kltc = w.get_key(network='litecoin')
        self.assertEqual(kltc.network, 'litecoin')
        self.assertListEqual(sorted(w.witness_types()), ['legacy', 'p2sh-segwit', 'segwit'])
        self.assertListEqual(sorted(w.witness_types(account_id=101)), ['p2sh-segwit', 'segwit'])
        self.assertListEqual(w.witness_types(network='litecoin'), ['segwit'])

    def test_wallet_mixed_witness_types_passphrase(self):
        p1 = 'advance upset milk quit sword tide pumpkin unit weekend denial tobacco alien'
        p2 = 'danger aspect north choose run bean short race prepare receive armed burst'
        w = Wallet.create('multiwitnessmultisigtest', keys=[p1, p2], cosigner_id=0, db_uri=self.database_uri)
        w.new_key()
        w.new_key(network='litecoin', witness_type='p2sh-segwit')
        w.new_key(witness_type='legacy')
        w.new_key(witness_type='p2sh-segwit')
        expected_addresslist = \
            ['39h96ozh8F8W2sVrc2EhEbFwwdRoLHJAfB', '3LdJC6MSmFqKrn2WrxRfhd8DYkYYr8FNDr',
             'MTSW4eC7xJiyp4YjwGZqpGmubsdm28Cdvc', 'bc1qgw8rg0057q9fmupx7ru6vtkxzy03gexc9ljycagj8z3hpzdfg7usvu56dp']
        self.assertListEqual(sorted(w.addresslist()), expected_addresslist)

    def test_wallet_transactions_add_input_from_wallet(self):
        w = wallet_create_or_open('add_input_from_wallet_test', network='bitcoinlib_test',
                                  db_uri=self.database_uri)
        w.utxos_update()
        t = WalletTransaction(w, network='bitcoinlib_test')
        t.add_input_from_wallet()
        t.add_output(100000, 'blt1q68x6ghc7anelyzm4v7hwl2g245e07agee8yfag')
        t.add_output(99000000, 'blt1qy0dlpnmfd8ldt5ns5kp0m4ery79wjaw5fz30t3', change=True)
        t.sign_and_update()
        self.assertTrue(t.verified)
        self.assertEqual(t.fee, 900000)
        self.assertEqual(len(t.outputs), 2)
        self.assertEqual(t.inputs[0].witness_type, 'segwit')

    def test_wallet_transactions_bumpfee(self):
        pkm = 'elephant dust deer company win final'
        wallet_delete_if_exists('bumpfeetest01', force=True)
        w = wallet_create_or_open('bumpfeetest01', keys=pkm, network='bitcoinlib_test', db_uri=self.database_uri)
        w.utxos_update()
        t = w.send_to('blt1qm89pcm4392vj93q9s2ft8saqzm4paruzj95a83', 99900000, fee=100000,
                      broadcast=True)
        self.assertEqual(w.balance(), 100000000)
        self.assertEqual(len(t.inputs), 1)
        self.assertEqual(len(t.outputs), 1)
        self.assertEqual(w.utxos()[0]['txid'], 'ea7bd8fe970ca6430cebbbf914ce2feeb369c3ae95edc117725dbe21519ccdab')
        t.bumpfee(broadcast=True)
        self.assertEqual(len(t.inputs), 2)
        self.assertEqual(len(t.outputs), 2)
        self.assertEqual(w.balance(), 99999325)

        w = wallet_create_or_open('bumpfeetest02', keys=pkm, network='bitcoinlib_test', db_uri=self.database_uri)
        w.utxos_update()
        t = w.send_to('blt1qm89pcm4392vj93q9s2ft8saqzm4paruzj95a83', 50000000, fee=100000,
                      broadcast=True)
        self.assertEqual(w.balance(), 149900000)
        self.assertEqual(len(t.inputs), 1)
        self.assertEqual(len(t.outputs), 2)
        t.bumpfee(fee=200000, broadcast=True)
        self.assertEqual(len(t.inputs), 1)
        self.assertEqual(len(t.outputs), 2)
        self.assertEqual(w.balance(), 149800000)

        w = wallet_create_or_open('bumpfeetest03', keys=pkm, network='bitcoinlib_test', db_uri=self.database_uri)
        w.utxos_update()
        t = w.send_to('blt1qm89pcm4392vj93q9s2ft8saqzm4paruzj95a83', 99900000, fee=50000,
                      broadcast=True)
        self.assertEqual(w.balance(), 100050000)
        self.assertEqual(len(t.inputs), 1)
        self.assertEqual(len(t.outputs), 2)
        t.bumpfee(extra_fee=50000, broadcast=True)
        self.assertEqual(len(t.inputs), 1)
        self.assertEqual(len(t.outputs), 1)
        self.assertEqual(w.balance(), 100000000)
        self.assertEqual(len(w.utxos()), 1)

        w = wallet_create_or_open('bumpfeetest04', keys=pkm, network='bitcoinlib_test', db_uri=self.database_uri)
        w.utxos_update()
        t = w.send_to('blt1qm89pcm4392vj93q9s2ft8saqzm4paruzj95a83', 199900000, fee=100000,
                      broadcast=True)
        self.assertRaisesRegex(TransactionError, "Not enough unspent inputs found for transaction", t.bumpfee)

    def test_wallet_transaction_remove_unconfirmed(self):
        pkm = 'monitor orphan turtle stage december special'
        w = wallet_create_or_open("wallet_remove_old_unconfirmed_transactions", keys=pkm, 
                                  network='bitcoinlib_test', db_uri=self.database_uri)
        w.get_keys(number_of_keys=4)
        utxos = [
            {
                "address": "blt1q4dugy6d7qz7226mk6ast3nz23z7ctd80mymle3",
                "script": "",
                "confirmations": 2,
                "output_n": 1,
                "txid": "e6192f6dafa689ac8889b466d2dd3eb2bb55b76c7305b4a2a6a31de6c9991aeb",
                "value": 1829810
            },
            {
                "address": "blt1q82l3c2d37yjxe0r9a7qn9v7c9y7hnaxp398kc0",
                "script": "",
                "confirmations": 0,
                "output_n": 0,
                "txid": "5891c85595193d0565fe418d5c5192c1297eafbef36c28bcab2ac3341ee68e71",
                "value": 2389180
            },
            {
                "address": "blt1qdtez8t797m74ar8wuvedw50jmycefwstfk8ulz",
                "script": "",
                "confirmations": 100,
                "output_n": 0,
                "txid": "7e87a63a0233615a5719a782a0b1c85de521151d8648e7d7244155a2caf7dd47",
                "value": 99389180
            },
            {
                "address": "blt1qdtez8t797m74ar8wuvedw50jmycefwstfk8ulz",
                "script": "",
                "confirmations": 100,
                "output_n": 0,
                "txid": "a4ef4aef09839a681419b80d5b6228b0089af39a4483896c9ac106192ac1ec34",
                "value": 838180
            },
        ]
        w.utxos_update(utxos=utxos)
        w.send_to('blt1qvtaw9m9ut96ykt2n2kdra8jpv3m5z2s8krqwsv', 50000, broadcast=True)
        self.assertEqual(len(w.utxos()), 5)
        self.assertEqual(w.balance(), 104441651)
        w.transactions_remove_unconfirmed(1)
        self.assertEqual(len(w.utxos()), 5)
        self.assertEqual(w.balance(), 104441651)
        time.sleep(3)
        w.transactions_remove_unconfirmed(0)
        self.assertEqual(len(w.utxos()), 3)
        self.assertEqual(w.balance(), 102057170)
