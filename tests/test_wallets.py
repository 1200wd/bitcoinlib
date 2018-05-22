# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Wallet Class
#    © 2018 May - 1200 Web Development <http://1200wd.com/>
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
import json
from random import shuffle
from bitcoinlib.db import DEFAULT_DATABASEDIR
from bitcoinlib.wallets import *
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey
from bitcoinlib.networks import Network
from tests.test_custom import CustomAssertions


DATABASEFILE_UNITTESTS = DEFAULT_DATABASEDIR + 'bitcoinlib.unittest.sqlite'
DATABASEFILE_UNITTESTS_2 = DEFAULT_DATABASEDIR + 'bitcoinlib.unittest2.sqlite'


class TestWalletCreate(unittest.TestCase):

    wallet = None

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        cls.wallet = HDWallet.create(
            name='test_wallet_create',
            databasefile=DATABASEFILE_UNITTESTS)

    @classmethod
    def tearDownClass(cls):
        cls.wallet._session.close_all()
        os.remove(DATABASEFILE_UNITTESTS)

    def test_wallet_create(self):
        self.assertTrue(isinstance(self.wallet, HDWallet))

    def test_wallet_info(self):
        self.assertIsNot(self.wallet.info(), "")

    def test_wallet_key_info(self):
        self.assertIsNot(self.wallet.main_key.dict(), "")

    def test_wallet_create_account(self):
        new_account = self.wallet.new_account(account_id=100)
        self.assertEqual(new_account.depth, 3)
        self.assertEqual(new_account.wif[:4], 'xprv')
        self.assertEqual(new_account.path, "m/44'/0'/100'")

    def test_wallet_create_key(self):
        new_key = self.wallet.new_key(account_id=100)
        self.assertEqual(new_key.depth, 5)
        self.assertEqual(new_key.wif[:4], 'xprv')
        self.assertEqual(new_key.path, "m/44'/0'/100'/0/0")

    def test_wallets_list(self):
        wallets = wallets_list(databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(wallets[0]['name'], 'test_wallet_create')

    def test_delete_wallet(self):
        HDWallet.create(
            name='wallet_to_remove',
            databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(wallet_delete('wallet_to_remove', databasefile=DATABASEFILE_UNITTESTS), 1)

    def test_delete_wallet_exception(self):
        self.assertRaisesRegexp(WalletError, '', wallet_delete, 'unknown_wallet', databasefile=DATABASEFILE_UNITTESTS)

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
        wlt = HDWallet.create("wallet-passphrase", key=passphrase, network='testnet',
                              databasefile=DATABASEFILE_UNITTESTS)
        key0 = wlt.get_key()
        self.assertEqual(key0.address, "mqDeXXaFnWKNWhLmAae7zHhZDW4PMsLHPp")


class TestWalletImport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)

    def test_wallet_import(self):
        keystr = 'tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePy' \
                 'A7irEvBoe4aAn52'
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_import',
            network='testnet',
            key=keystr)
        wallet_import.new_account(account_id=99)
        self.assertEqual(wallet_import.main_key.wif, keystr)
        self.assertEqual(wallet_import.main_key.address, u'n3UKaXBRDhTVpkvgRH7eARZFsYE989bHjw')
        self.assertEqual(wallet_import.main_key.path, 'm')

    def test_wallet_import_account(self):
        accountkey = 'tprv8h4wEmfC2aSckSCYa68t8MhL7F8p9xAy322B5d6ipzY5ZWGGwksJMoajMCqd73cP4EVRygPQubgJPu9duBzPn3QV' \
                     '8Y7KbKUnaMzx9nnsSvh'
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_import_account',
            key=accountkey,
            network='testnet',
            account_id=99)
        self.assertEqual(wallet_import.main_key.wif, accountkey)
        self.assertEqual(wallet_import.main_key.address, u'mowRx2TNXTgRSUmepjqhx5C1TTigmHLGRh')
        self.assertEqual(wallet_import.main_key.path, "m/44'/1'/99'")

    def test_wallet_import_account_new_keys(self):
        accountkey = 'tprv8h4wEmfC2aSckSCYa68t8MhL7F8p9xAy322B5d6ipzY5ZWGGwksJMoajMCqd73cP4EVRygPQubgJPu9duBzPn3QV' \
                     '8Y7KbKUnaMzx9nnsSvh'
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_import_account_new_key',
            key=accountkey,
            network='testnet',
            account_id=99)
        newkey = wallet_import.new_key(account_id=99)
        newkey_change = wallet_import.new_key_change(account_id=99, name='change')
        self.assertEqual(wallet_import.main_key.wif, accountkey)
        self.assertEqual(newkey.address, u'mfvFzusKPZzGBAhS69AWvziRPjamtRhYpZ')
        self.assertEqual(newkey.path, "m/44'/1'/99'/0/0")
        self.assertEqual(newkey_change.address, u'mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2')
        self.assertEqual(newkey_change.path, "m/44'/1'/99'/1/0")

    def test_wallet_import_public_wallet(self):
        pubkey = 'tpubDDkyPBhSAx8DFYxx5aLjvKH6B6Eq2eDK1YN76x1WeijE8eVUswpibGbv8zJjD6yLDHzVcqWzSp2fWVFhEW9XnBssFqMwt' \
                 '9SrsVeBeqfBbR3'
        pubwal = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_import_public_wallet',
            key=pubkey,
            network='testnet',
            account_id=0)
        newkey = pubwal.new_key()
        self.assertEqual(newkey.address, u'mweZrbny4fmpCmQw9hJH7EVfkuWX8te9jc')

    def test_wallet_import_litecoin(self):
        accountkey = 'Ltpv71G8qDifUiNet6mn25D7GPAVLZeaFRWzDABxx5xNeigVpFEviHK1ZggPS1kbtegB3U2i8w6ToNfM5sdvEQPW' \
                     'tov4KWyQ5NxWUd3oDWXQb4C'
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_litecoin',
            key=accountkey,
            network='litecoin')
        newkey = wallet_import.new_key()
        self.assertEqual(wallet_import.main_key.wif, accountkey)
        self.assertEqual(newkey.address, u'LPkJcpV1cmT8qLFmUApySBtxt7UWavoQmh')
        self.assertEqual(newkey.path, "m/44'/2'/0'/0/0")

    def test_wallet_import_key_network_error(self):
        w = HDWallet.create(
            name='Wallet Error',
            databasefile=DATABASEFILE_UNITTESTS)
        self.assertRaisesRegexp(WalletError,
                                "Network litecoin not available in this wallet, please create an account "
                                "for this network first.",
                                w.import_key, 'T43gB4F6k1Ly3YWbMuddq13xLb56hevUDP3RthKArr7FPHjQiXpp')


class TestWalletKeys(unittest.TestCase):

    wallet = None

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        cls.private_wif = 'xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzF9ySUHZw5qJkk5LCALAhXS' \
                           'XoCmCSnStRvgwLBtcbGsg1PeKT2en'
        cls.wallet = HDWallet.create(
            key=cls.private_wif,
            name='test_wallet_keys',
            databasefile=DATABASEFILE_UNITTESTS)
        cls.wallet.new_key()
        cls.wallet.new_key_change()

    @classmethod
    def tearDownClass(cls):
        cls.wallet._session.close_all()
        os.remove(DATABASEFILE_UNITTESTS)

    def test_wallet_addresslist(self):
        expected_addresslist = ['1B8gTuj778tkrQV1e8qjcesoZt9Cif3VEp', '1LS8zYrkgGpvJdtMmUdU1iU4TUMQh6jjF1',
                                '1K7S5am1hLfugEFWR9ENfEBpUrMbFhqtoh', '1EByrVS1sc6TDihJRRRtMAnKTaAVSZAgtQ',
                                '1KyLsZS2JwWdfvDZ5g8vhbanqjbNwKUseK', '1A7wRpnstUiA33rxW1i33b5qqaTsS4YSNQ',
                                '1J6jppU5mWf4ausGfHMumrKrztpDKq2MrD', '13uQKuiWwWp15BsEijnpKZSuTuHVTpZMvP']
        self.assertListEqual(self.wallet.addresslist(depth=None), expected_addresslist)

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
            'xprvA3ALLPsyMi2DUrZbSRegEhrdNNg1kwM6n6zh3cv9Qx9ZYoHwgk44TwympUPV3UuQ5YNjubBsF2QbBfJqujoiFDKLHnphCpLmBzeER'
            'yZeFRE'
        ]
        self.assertListEqual([k.wif for k in self.wallet.keys_addresses()], address_wifs)

    def test_wallet_keys_method_keys_payment(self):
        self.assertEqual(self.wallet.keys_address_payment()[0].address, '1J6jppU5mWf4ausGfHMumrKrztpDKq2MrD')

    def test_wallet_keys_method_keys_change(self):
        self.assertEqual(self.wallet.keys_address_change()[0].address, '13uQKuiWwWp15BsEijnpKZSuTuHVTpZMvP')

    def test_wallet_keys_single_key(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        wk = 'xprv9s21ZrQH143K3tCgu8uhkA2fw9F9opbvoNNzh5wcuEvNHbCU6Kg3c6dam2a6cw4UYeDxAsgBorAqXp2nsoYS84DqYMwkzxZ15' \
             'ujRHzmBMxE'
        w = HDWallet.create('test_wallet_keys_single_key', wk, scheme='single', databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.new_key(), w.new_key())

    def test_wallet_create_uncompressed_masterkey(self):
        wlt = wallet_create_or_open('uncompressed_test', key='68vBWcBndYGLpd4KmeNTk1gS1A71zyDX6uVQKCxq6umYKyYUav5',
                                    network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        wlt.get_key()
        wlt.utxos_update()
        self.assertIsNone(wlt.sweep('216xtQvbcG4o7Yz33n7VCGyaQhiytuvoqJY').error)

    def test_wallet_single_key(self):
        wlt = wallet_create_or_open('single_key', scheme='single', network='bitcoinlib_test',
                                    databasefile=DATABASEFILE_UNITTESTS)
        wlt.utxos_update()
        transaction = wlt.transaction_create([('21DQCyZTNRoAccG1TWz9YaffDUKzZf6JWii', 90000000)])
        transaction.sign()
        self.assertTrue(transaction.verify())


class TestWalletElectrum(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        cls.pk = 'xprv9s21ZrQH143K2fuscnMTwUadsPqEbYdFQVJ1uWPawUYi7C485NHhCiotGy6Kz3Cz7ReVr65oXNwhREZ8ePrz8p7zy' \
                  'Hra82D1EGS7cQQmreK'
        cls.wallet = HDWallet.create(
            key=cls.pk,
            name='test_wallet_electrum',
            databasefile=DATABASEFILE_UNITTESTS)
        workdir = os.path.dirname(__file__)
        with open('%s/%s' % (workdir, 'electrum_keys.json'), 'r') as f:
            cls.el_keys = json.load(f)
        for i in range(20):
            cls.wallet.key_for_path('m/0/%d' % i, name='-test- Receiving #%d' % i, enable_checks=False)
        for i in range(6):
            cls.wallet.key_for_path('m/1/%d' % i, name='-test- Change #%d' % i, enable_checks=False)

    @classmethod
    def tearDownClass(cls):
        cls.wallet._session.close_all()
        os.remove(DATABASEFILE_UNITTESTS)

    def test_electrum_keys(self):
        for key in self.wallet.keys():
            if key.name[:6] == '-test-' and key.path not in ['m/0', 'm/1']:
                self.assertIn(key.address, self.el_keys.keys(),
                              msg='Key %s (%s, %s) not found in Electrum wallet key export' %
                                  (key.name, key.path, key.address))


class TestWalletMultiCurrency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        cls.pk = 'dHHM83S1ptYryy3ZeV6Q8zQBT9NvqiSjUMJPwf6xg2CdaFLiHbyzsCSeP9FG1wzbsPVY9VtC85VsWoFvU9z1S4GzqwDBh' \
                  'CawMAogXrUh2KgVahL'
        cls.wallet = HDWallet.create(
            key=cls.pk,
            name='test_wallet_multicurrency',
            databasefile=DATABASEFILE_UNITTESTS)

        cls.wallet.new_account(network='litecoin')
        cls.wallet.new_account(network='bitcoin')
        cls.wallet.new_account(network='testnet')
        cls.wallet.new_account(network='dash')
        cls.wallet.new_key()
        cls.wallet.new_key()
        cls.wallet.new_key(network='bitcoin')

    @classmethod
    def tearDownClass(cls):
        cls.wallet._session.close_all()
        os.remove(DATABASEFILE_UNITTESTS)

    def test_wallet_multiple_networks_defined(self):
        networks_expected = sorted(['litecoin', 'bitcoin', 'dash', 'testnet'])
        networks_wlt = sorted([x['network_name'] for x in self.wallet.networks()])
        self.assertListEqual(networks_wlt, networks_expected,
                             msg="Not all network are defined correctly for this wallet")

    def test_wallet_multiple_networks_default_addresses(self):
        addresses_expected = ['XqTpf6NYrrckvsauJKfHFBzZaD9wRHjQtv', 'Xj6tV9Jc3qJ2AszpNxvEq7KVQKUMcfmBqH']
        self.assertListEqual(self.wallet.addresslist(network='dash'), addresses_expected)

    def test_wallet_multiple_networks_import_key(self):
        pk_bitcoin = 'xprv9s21ZrQH143K3RBvuNbSwpAHxXuPNWMMPfpjuX6ciwo91HpYq6gDLjZuyrQCPpo4qBDXyvftN7MdX7SBVXeGgHs' \
                     'TijeHZLLgnukZP8dDkjC'
        res = self.wallet.import_key(pk_bitcoin)
        self.assertEqual(res.address, '1Hhyezo3XUC1BYpwLmp2AueWWw26xgXq7B')

    def test_wallet_multiple_networks_import_key_network(self):
        pk_hex = '770abe6f3854620edfb836ce88ce74c26da1a4b00502c98c368a9373d0c0fcd8'
        address_ltc = 'Lg2uMYnqu48REt4KaSYLPZiaxy5PKUkkdZ'
        self.wallet.import_key(pk_hex, network='litecoin')
        addresses_ltc_in_wallet = self.wallet.addresslist(network='litecoin', depth=0)
        self.assertIn(address_ltc, addresses_ltc_in_wallet)

    def test_wallet_multiple_networks_import_error(self):
        pk_dashtest = 'DRKVrRjogj3bNiLD8V9398hVVqqxi5NzhNJBLX3bfc9UdX77NxaNeMksf3ybsXSUJLh44TC9FCDkQfxAEyX924VJgK' \
                      'J5xeeM2agqru6DGAXRyMSW'
        error_str = "Network dash_testnet not available in this wallet, please create an account for this network " \
                    "first."
        self.assertRaisesRegexp(WalletError, error_str, self.wallet.import_key, pk_dashtest)


class TestWalletMultiNetworksMultiAccount(unittest.TestCase):

    def test_wallet_multi_networks_send_transaction(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        pk = 'tobacco defy swarm leaf flat pyramid velvet pen minor twist maximum extend'
        wallet = HDWallet.create(
            key=pk, network='bitcoin',
            name='test_wallet_multi_network_multi_account',
            databasefile=DATABASEFILE_UNITTESTS)

        wallet.new_key()
        acc = wallet.new_account('BCL test home', network='bitcoinlib_test')
        acc2 = wallet.new_account('BCL test office', network='bitcoinlib_test')
        wallet.new_key(account_id=acc2.account_id, network='bitcoinlib_test')
        wallet.new_key(account_id=acc.account_id, network='bitcoinlib_test')
        wallet.utxos_update(networks='bitcoinlib_test')
        wallet.new_key(account_id=acc.account_id, network='bitcoinlib_test')
        wallet.new_key(account_id=acc.account_id, network='bitcoinlib_test')
        wallet.get_key(network='testnet', number_of_keys=2)
        wallet.get_key(network='testnet', change=1)
        wallet.utxos_update(networks='testnet')
        
        self.assertEqual(wallet.balance(network='bitcoinlib_test'), 200000000)
        self.assertEqual(wallet.balance(network='bitcoinlib_test', account_id=1), 200000000)
        self.assertEqual(wallet.balance(network='testnet'), 1500000)
        ltct_addresses = ['mhHhSx66jdXdUPu2A8pXsCBkX1UvHmSkUJ', 'mrdtENj75WUfrJcZuRdV821tVzKA4VtCBf',
                          'mmWFgfG43tnP2SJ8u8UDN66Xm63okpUctk']
        self.assertListEqual(wallet.addresslist(network='testnet'), ltct_addresses)
        
        t = wallet.send_to('21EsLrvFQdYWXoJjGX8LSEGWHFJDzSs2F35', 10000000, account_id=1,
                                network='bitcoinlib_test', fee=1000, offline=False)
        self.assertIsNone(t.error)
        self.assertTrue(t.verified)
        self.assertEqual(wallet.balance(network='bitcoinlib_test', account_id=1), 189999000)
        self.assertEqual(len(wallet.transactions(account_id=0, network='bitcoinlib_test')), 2)
        self.assertEqual(len(wallet.transactions(account_id=1, network='bitcoinlib_test')), 4)


class TestWalletBitcoinlibTestnet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)

    @classmethod
    def tearDownClass(cls):
        os.remove(DATABASEFILE_UNITTESTS)

    def test_wallet_bitcoinlib_testnet_sendto(self):
        w = HDWallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet_sendto',
            databasefile=DATABASEFILE_UNITTESTS)

        w.new_key()
        w.utxos_update()
        self.assertIsNone(w.send_to('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 5000000).error)

    def test_wallet_bitcoinlib_testnet_send_utxos_updated(self):
        w = HDWallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet_send_utxos_updated',
            databasefile=DATABASEFILE_UNITTESTS)

        w.new_key()
        w.utxos_update()
        self.assertEqual(len(w.utxos()), 2)
        w.send_to('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 1)

    def test_wallet_bitcoinlib_testnet_sendto_no_funds_txfee(self):
        w = HDWallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet_sendto_no_funds_txfee',
            databasefile=DATABASEFILE_UNITTESTS)
        w.new_key()
        w.utxos_update()
        balance = w.balance()
        self.assertRaisesRegexp(WalletError, 'Not enough unspent transaction outputs found',
                                w.send_to, '21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', balance)

    def test_wallet_bitcoinlib_testnet_sweep(self):
        w = HDWallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet_sweep',
            databasefile=DATABASEFILE_UNITTESTS)
        w.new_key()
        w.new_key()
        w.new_key()
        w.utxos_update()
        self.assertIsNone(w.sweep('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo').error)
        self.assertEqual(w.utxos(), [])


class TestWalletMultisig(unittest.TestCase):

    def test_wallet_multisig_2_wallets_private_master_plus_account_public(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        pk1 = 'tprv8ZgxMBicQKsPdPVdNSEeAhagkU6tUDhUQi8DcCTmJyNLUyU7svTFzXQdkYqNJDEtQ3S2wAspz3K56CMcmMsZ9eXZ2nkNq' \
              'gVxJhMHq3bGJ1X'
        pk1_acc_pub = 'tpubDCZUk9HLxh5gdB9eC8FUxPB1AbZtsSnbvyrAAzsC8x3tiYDgbzyxcngU99rG333jegHG5vJhs11AHcSVkbwrU' \
                      'bYEsPK8vA7E6yFB9qbsTYi'
        w1 = self.wallet = HDWallet.create(name='test_wallet_create_1', key=pk1, databasefile=DATABASEFILE_UNITTESTS)
        w2 = self.wallet = HDWallet.create(name='test_wallet_create_2', key=pk1_acc_pub,
                                           databasefile=DATABASEFILE_UNITTESTS)
        wk1 = w1.new_key()
        wk2 = w2.new_key()
        self.assertTrue(wk1.is_private)
        self.assertFalse(wk2.is_private)
        self.assertEqual(wk1.address, wk2.address)

    def test_wallet_multisig_create_2_cosigner_wallets(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        pk_wif1 = 'tprv8ZgxMBicQKsPdvHCP6VxtFgowj2k7nBJnuRiVWE4DReDFojkLjyqdT8mtR6XJK9dRBcaa3RwvqiKFjsEQVhKfQmHZCCY' \
                  'f4jRTWvJuVuK67n'
        pk_wif2 = 'tprv8ZgxMBicQKsPdkJVWDkqQQAMVYB2usfVs3VS2tBEsFAzjC84M3TaLMkHyJWjydnJH835KHvksS92ecuwwWFEdLAAccwZ' \
                  'KjhcA63NUyvDixB'
        pk1 = HDKey(pk_wif1, network='testnet')
        pk2 = HDKey(pk_wif2, network='testnet')
        wl1 = HDWallet.create_multisig('multisig_test_wallet1',
                                       [pk_wif1, pk2.subkey_for_path("m/45'/1'/0'").wif_public()],
                                       sigs_required=2, network='testnet', databasefile=DATABASEFILE_UNITTESTS)
        wl2 = HDWallet.create_multisig('multisig_test_wallet2',
                                       [pk1.subkey_for_path("m/45'/1'/0'").wif_public(), pk_wif2],
                                       sigs_required=2, network='testnet', databasefile=DATABASEFILE_UNITTESTS)
        wl1_key = wl1.new_key()
        wl2_key = wl2.new_key()
        self.assertEqual(wl1_key.address, wl2_key.address)

    def test_wallet_multisig_bitcoinlib_testnet_transaction_send(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)

        key_list = [
            'Pdke4WfXvALPdbrKEfBU9z9BNuRNbv1gRr66BEiZHKcRXDSZQ3gV',
            'PhUTR4ZkZu9Xkzn3ee3xMU1TxbNx6ENJvUjX4wBaZDyTCMrn1zuE',
            'PdnZFcwpxUSAcFE6MHB78weVAguwzSTUMBqswkqie7Uxfxsd77Zs'
        ]

        # Create wallet and generate key
        wl = HDWallet.create_multisig('multisig_test_simple', key_list, sigs_required=2, network='bitcoinlib_test',
                                      databasefile=DATABASEFILE_UNITTESTS)
        wl.new_key()

        # Sign, verify and send transaction
        wl.utxos_update()  # In bitcoinlib_test network this generates new UTXO's
        t = wl.transaction_create([('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 100000)])
        t.sign()
        self.assertTrue(t.verify())
        t.send()
        self.assertIsNone(t.error)

    def test_wallet_multisig_2of2(self):
        """
        Create 2 cosigner wallets with 1 own private key a public key from other cosigner
        Then create and sign transaction if first wallet, import and sign it in second wallet
        and verify created transaction.

        """
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)

        keys = [
            HDKey('YXscyqNJ5YK411nwB4wzazXjJn9L9iLAR1zEMFcpLipDA25rZregBGgwXmprsvQLeQAsuTvemtbCWR1AHaPv2qmvkartoiFUU6'
                  'qu1uafT2FETtXT', network='bitcoinlib_test'),
            HDKey('YXscyqNJ5YK411nwB4EyGbNZo9eQSUWb64vAFKHt7E2LYnbmoNz8Gyjs6xc7iYAudcnkgf127NPnaanuUgyRngAiwYBcXKGsSJ'
                  'wadGhxByT2MnLd', network='bitcoinlib_test')]

        msw1 = HDWallet.create_multisig('msw1', [keys[0], keys[1].subkey_for_path("m/45'/9999999'/0'").wif_public()],
                                        network='bitcoinlib_test', sort_keys=False, sigs_required=2,
                                        databasefile=DATABASEFILE_UNITTESTS)
        msw2 = HDWallet.create_multisig('msw2', [keys[0].subkey_for_path("m/45'/9999999'/0'").wif_public(), keys[1]],
                                        network='bitcoinlib_test', sort_keys=False, sigs_required=2,
                                        databasefile=DATABASEFILE_UNITTESTS)
        msw1.new_key()
        msw2.new_key()
        msw1.utxos_update()
        msw2.utxos_update()
        utxos = msw1.utxos()
        output_arr = [('21KnydRNSmqAf8Py74mMiwRXYHGxW27zyDu', utxos[0]['value'] - 50000)]
        input_arr = [(utxos[0]['tx_hash'], utxos[0]['output_n'], utxos[0]['key_id'], utxos[0]['value'])]
        t = msw1.transaction_create(output_arr, input_arr, fee=50000)
        t.sign()
        t2 = msw2.transaction_import(t)
        t2.sign()
        self.assertTrue(t2.verify())

    def test_wallet_multisig_2of2_different_database(self):
        """
        Same unittest as before (test_wallet_multisig_sign_2_different_wallets) but now with 2
        separate databases to check for database inteference.

        """
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        if os.path.isfile(DATABASEFILE_UNITTESTS_2):
            os.remove(DATABASEFILE_UNITTESTS_2)

        keys = [
            HDKey('YXscyqNJ5YK411nwB4wzazXjJn9L9iLAR1zEMFcpLipDA25rZregBGgwXmprsvQLeQAsuTvemtbCWR1AHaPv2qmvkartoiFUU6'
                  'qu1uafT2FETtXT', network='bitcoinlib_test'),
            HDKey('YXscyqNJ5YK411nwB4EyGbNZo9eQSUWb64vAFKHt7E2LYnbmoNz8Gyjs6xc7iYAudcnkgf127NPnaanuUgyRngAiwYBcXKGsSJ'
                  'wadGhxByT2MnLd', network='bitcoinlib_test')]

        msw1 = HDWallet.create_multisig('msw1', [keys[0], keys[1].subkey_for_path("m/45'/9999999'/0'").wif_public()],
                                        network='bitcoinlib_test', sort_keys=False, sigs_required=2,
                                        databasefile=DATABASEFILE_UNITTESTS)
        msw2 = HDWallet.create_multisig('msw2', [keys[0].subkey_for_path("m/45'/9999999'/0'").wif_public(), keys[1]],
                                        network='bitcoinlib_test', sort_keys=False, sigs_required=2,
                                        databasefile=DATABASEFILE_UNITTESTS_2)
        msw1.new_key()
        msw2.new_key()
        msw1.utxos_update()
        msw2.utxos_update()
        utxos = msw1.utxos()
        output_arr = [('21KnydRNSmqAf8Py74mMiwRXYHGxW27zyDu', utxos[0]['value'] - 50000)]
        input_arr = [(utxos[0]['tx_hash'], utxos[0]['output_n'], utxos[0]['key_id'], utxos[0]['value'])]
        t = msw1.transaction_create(output_arr, input_arr, fee=50000)
        t.sign()
        t2 = msw2.transaction_import(t)
        t2.sign()
        t2.send()
        self.assertIsNone(t2.error)

    @staticmethod
    def _multisig_test(sigs_required, number_of_sigs, sort_keys, network):
        # Create Keys
        key_dict = {}
        for key_id in range(number_of_sigs):
            key_dict[key_id] = HDKey(network=network)
        random_output_address = HDKey(network=network).key.address()

        # Create wallets with 1 private key each
        wallet_dict = {}
        wallet_keys = {}
        for wallet_id in range(number_of_sigs):
            wallet_name = 'multisig-%d' % wallet_id
            key_list = []
            for key_id in key_dict:
                if key_id == wallet_id:
                    key_list.append(key_dict[key_id])
                else:
                    key_list.append(key_dict[key_id].
                                    subkey_for_path(
                        "m/45'/%d'/0'" % Network(network).bip44_cointype).wif_public())
            wallet_dict[wallet_id] = HDWallet.create_multisig(
                wallet_name, key_list, sigs_required=sigs_required, network=network, sort_keys=sort_keys,
                databasefile=DATABASEFILE_UNITTESTS)
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
        input_arr = [(utxos[0]['tx_hash'], utxos[0]['output_n'], utxos[0]['key_id'], utxos[0]['value'])]
        t = wlt.transaction_create(output_arr, input_arr, fee=fee)
        t.sign()
        n_signs = 1

        # Sign transaction with other wallets until required number of signatures is reached
        while wallet_ids and n_signs < sigs_required:
            wallet_id = wallet_ids.pop()
            t = wallet_dict[wallet_id].transaction_import(t)
            t.sign()
            n_signs += 1
        wlt._session.close()
        return t

    def test_wallet_multisig_2of3(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        t = self._multisig_test(2, 3, False, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    def test_wallet_multisig_2of3_sorted(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        t = self._multisig_test(2, 3, True, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    def test_wallet_multisig_3of5(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        t = self._multisig_test(3, 5, False, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    # Disable for now takes about 46 seconds because it needs to create 9 * 9 wallets and lots of keys
    # def test_wallet_multisig_5of9(self):
    #     if os.path.isfile(DATABASEFILE_UNITTESTS):
    #         os.remove(DATABASEFILE_UNITTESTS)
    #     t = self._multisig_test(5, 9, 'bitcoinlib_test')
    #     self.assertTrue(t.verify())

    def test_wallet_multisig_2of2_with_single_key(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        keys = [
            HDKey(network='bitcoinlib_test'),
            HDKey(network='bitcoinlib_test', key_type='single')
        ]
        key_list = [keys[0], keys[1].public()]

        wl = HDWallet.create_multisig('multisig_expk2', key_list, sigs_required=2, network='bitcoinlib_test',
                                      databasefile=DATABASEFILE_UNITTESTS, sort_keys=False)
        wl.new_key()
        wl.new_key()
        wl.new_key_change()
        wl.utxos_update()
        key_names = [k.name for k in wl.keys(is_active=False)]
        self.assertListEqual(key_names, ['Multisig Key 8/7', 'Multisig Key 10/7', 'Multisig Key 12/7'])

        t = wl.transaction_create([(HDKey(network='bitcoinlib_test').key.address(), 6400000)], min_confirms=0)
        t.sign(keys[1])
        t.send()
        self.assertIsNone(t.error)

        key_names_active = [k.name for k in wl.keys(is_active=False)]
        self.assertEqual(key_names_active,
                         ['Multisig Key 8/7', 'Multisig Key 10/7', 'Multisig Key 12/7', 'Multisig Key 14/7'])

    def test_wallet_multisig_sorted_keys(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        key1 = HDKey()
        key2 = HDKey()
        key3 = HDKey()
        w1 = HDWallet.create_multisig(
            'w1', [key1, key2.account_multisig_key().public(), key3.account_multisig_key().public()],
            sigs_required=2, sort_keys=True, databasefile=DATABASEFILE_UNITTESTS)
        w2 = HDWallet.create_multisig(
            'w2', [key1.account_multisig_key().public(), key2, key3.account_multisig_key().public()],
            sigs_required=2, sort_keys=True, databasefile=DATABASEFILE_UNITTESTS)
        w3 = HDWallet.create_multisig(
            'w3', [key1.account_multisig_key().public(), key2.account_multisig_key().public(), key3],
            sigs_required=2,  sort_keys=True, databasefile=DATABASEFILE_UNITTESTS)
        for _ in range(10):
            address1 = w1.new_key().address
            address2 = w2.new_key().address
            address3 = w3.new_key().address
            self.assertTrue((address1 == address2 == address3),
                            'Different addressed generated: %s %s %s' % (address1, address2, address3))

    def test_wallet_multisig_sign_with_external_single_key(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        network = 'bitcoinlib_test'
        words = 'square innocent drama'
        seed = Mnemonic().to_seed(words, 'password')
        hdkey = HDKey.from_seed(seed, network=network)
        hdkey.key_type = 'single'

        key_list = [
            HDKey(network=network).account_multisig_key().public(),
            HDKey(network=network),
            hdkey.public()
        ]
        wallet = HDWallet.create_multisig('Multisig-2-of-3-example', key_list, 2, network=network,
                                          databasefile=DATABASEFILE_UNITTESTS)
        wallet.new_key()
        wallet.utxos_update()
        wt = wallet.send_to('n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi', 10000000)
        self.assertFalse(wt.verify())
        wt.sign(hdkey)
        self.assertTrue(wt.verify())

    def test_wallet_multisig_reopen_wallet(self):

        def _open_all_wallets():
            wl1 = wallet_create_or_open_multisig(
                'multisigmulticur1_tst', sigs_required=2, network=network,
                databasefile=DATABASEFILE_UNITTESTS,
                key_list=[pk1, pk2.account_multisig_key().wif_public(), pk3.account_multisig_key().wif_public()])
            wl2 = wallet_create_or_open_multisig(
                'multisigmulticur2_tst', sigs_required=2, network=network,
                databasefile=DATABASEFILE_UNITTESTS,
                key_list=[pk1.account_multisig_key().wif_public(), pk2, pk3.account_multisig_key().wif_public()])
            wl3 = wallet_create_or_open_multisig(
                'multisigmulticur3_tst', sigs_required=2, network=network,
                databasefile=DATABASEFILE_UNITTESTS,
                key_list=[pk1.account_multisig_key().wif_public(), pk2.account_multisig_key().wif_public(), pk3])
            return wl1, wl2, wl3

        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        network = 'litecoin'
        phrase1 = 'shop cloth bench traffic vintage security hour engage omit almost episode fragile'
        phrase2 = 'exclude twice mention orchard grit ignore display shine cheap exercise same apart'
        phrase3 = 'citizen obscure tribe index little welcome deer wine exile possible pizza adjust'
        pk1 = HDKey.from_passphrase(phrase1, network=network)
        pk2 = HDKey.from_passphrase(phrase2, network=network)
        pk3 = HDKey.from_passphrase(phrase3, network=network)
        wallets = _open_all_wallets()
        for wlt in wallets:
            self.assertEqual(wlt.get_key().address, '354bZpUpeaUEwsRn5Le5BymTvqPHf9jZkS')
        del wallets
        wallets2 = _open_all_wallets()
        for wlt in wallets2:
            self.assertEqual(wlt.get_key().address, '354bZpUpeaUEwsRn5Le5BymTvqPHf9jZkS')
            wlt._session.close_all()

    def test_wallet_multisig_network_mixups(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        network = 'litecoin_testnet'
        phrase1 = 'shop cloth bench traffic vintage security hour engage omit almost episode fragile'
        phrase2 = 'exclude twice mention orchard grit ignore display shine cheap exercise same apart'
        phrase3 = 'citizen obscure tribe index little welcome deer wine exile possible pizza adjust'
        pk2 = HDKey.from_passphrase(phrase2, network=network)
        pk3 = HDKey.from_passphrase(phrase3, network=network)
        wlt = wallet_create_or_open_multisig(
            'multisig_network_mixups', sigs_required=2, network=network, databasefile=DATABASEFILE_UNITTESTS,
            key_list=[phrase1, pk2.account_multisig_key().wif_public(), pk3.account_multisig_key().wif_public()])
        self.assertEqual(wlt.get_key().address, 'QeBprfDJNadgqJV4R5d7e9i6duVK8HFgAN')
        self.assertEqual(wlt.get_key().network.network_name, network)


class TestWalletKeyImport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)

    @classmethod
    def tearDownClass(cls):
        os.remove(DATABASEFILE_UNITTESTS)

    def test_wallet_key_import_and_sign_multisig(self):
        network = 'bitcoinlib_test'
        words = 'square innocent drama'
        seed = Mnemonic().to_seed(words, 'password')
        hdkey = HDKey.from_seed(seed, network=network)
        hdkey.key_type = 'single'

        key_list = [
            HDKey(network=network).account_multisig_key().public(),
            HDKey(network=network),
            hdkey.public()
        ]
        with HDWallet.create_multisig('Multisig-2-of-3-example', key_list, 2, sort_keys=True, network=network,
                                      databasefile=DATABASEFILE_UNITTESTS) as wlt:
            wlt.new_key()
            wlt.utxos_update()
            wt = wlt.send_to('n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi', 10000000)
            wt.sign(hdkey)
            wt.send()
            self.assertIsNone(wt.error)

    def test_wallet_import_private_for_known_public(self):
        hdkey = HDKey(
            'xprv9s21ZrQH143K2noEZoqGHnaDDLjrnFpis8jm7NWDhkWuNNCqMupGSy7PMYtGL9jvdTY7Nx3GZ6UZ9C52nebwbYXK73imaPUK24'
            'dZJtGZhGd')
        with HDWallet.create('public-private', hdkey.account_key().public(), databasefile=DATABASEFILE_UNITTESTS) \
                as wlt:
            wlt.import_key(hdkey)

            self.assertListEqual([k.path for k in wlt.keys()], ["m/44'/0'/0'", 'm', "m/44'", "m/44'/0'"])
            self.assertEqual(wlt.new_account().address, '16m3JAtQjHbmEZd8uYTyKebvrxh2RsFHB')
            self.assertEqual(wlt.new_key().address, '1P8BTrsBn8DKGQq7nSWPiEiUDgiG8sW1kf')

    def test_wallet_import_private_for_known_public_multisig(self):
        puk1 = "Ltub2ZjnfUYueMfDXPsdbY8AbXRRwuxfFfYTGtyzyToy1iafjxWr2ikBLQuqKbeGGHsQUzstcUaAJWXi1HmcE4Er3WYX49aduDnE" \
               "k1okyVP2iNB"
        puk2 = "Ltub2ZUMUHmKvoN3GjAw6PvmVczc4Sv9pbA98LqMso87cQ7p51JrG6vfhf5poJ2pMXQ78eeRxmuvyVRYWz2kNQKa9MM9sJMQpzo1" \
               "wH2V1D3Zcft"
        puk3 = "Ltub2ZtuHm8zDa1gKWq1472ByzgaWQhK1p2TK8xtMSXTVTsxgacofqMbr5fru23ifoXtdYa2nvWGsN4Hm1M6bRZwSHeUrnENL7Gu" \
               "af1DapFSc2J"
        prk2 = 'Ltpv71G8qDifUiNesWWsQZZVKVZNjBGHEfDExoAYkUp4SpU9aiWygzq11TgcCA9CJoGmMJjFatECSR9LGBpL5CxtmaHXpwGXFzrL' \
               'QJGENq739hW'
        with wallet_create_or_open_multisig("mstest", [puk1, puk2, puk3], 2, network='litecoin',
                                            databasefile=DATABASEFILE_UNITTESTS) as wlt:
            self.assertFalse(wlt.cosigner[1].main_key.is_private)
            wlt.import_key(prk2)
            self.assertTrue(wlt.cosigner[1].main_key.is_private)


class TestWalletTransactions(unittest.TestCase, CustomAssertions):

    wallet = None

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        account_key = 'tpubDCmJWqxWch7LYDhSuE1jEJMbAkbkDm3DotWKZ69oZfNMzuw7U5DwEaTVZHGPzt5j9BJDoxqVkPHt2EpUF66FrZhpfq' \
                      'ZY6DFj6x61Wwbrg8Q'
        cls.wallet = wallet_create_or_open('utxo-test', key=account_key, network='testnet',
                                           databasefile=DATABASEFILE_UNITTESTS)
        cls.wallet.new_key()
        cls.wallet.utxos_update()

    @classmethod
    def tearDownClass(cls):
        cls.wallet._session.close()
        os.remove(DATABASEFILE_UNITTESTS)

    def test_wallet_import_utxos(self):
        total_value = sum([utxo['value'] for utxo in self.wallet.utxos()])
        self.assertEqual(total_value, 60000000)

    def test_wallet_sweep_public_wallet(self):
        tx = self.wallet.sweep('mwCvJviVTzjEKLZ1UW5jaepjWHUeoYrEe7', fee_per_kb=50000)
        prev_tx_list_check = [
            '4fffbf7c50009e5477ac06b9f1741890f7237191d1cf5489c7b4039df2ebd626',
            '9423919185b15c633d2fcd5095195b521a8970f01ca6413c43dbe5646e5b8e1e',
            'fb575942ef5ddc0d6afe10ccf73928faa81315a1f9be2d5b8a801daf7d251a6f']
        prev_tx_list = sorted([to_hexstring(x.prev_hash) for x in tx.inputs])
        self.assertListEqual(prev_tx_list, prev_tx_list_check)

    def test_wallet_offline_create_transaction(self):
        hdkey_wif = 'tprv8ZgxMBicQKsPf5exCdeBgnYjJt2LxDcQbv6u9HHymY3qh6EoTy8SGwou5xyvExL3iWfBsZWp3YUyo9gRmxQxrBS2FwGk' \
                    'qjcDhTcyVLhrXXZ'
        hdkey = HDKey(hdkey_wif)
        wlt = wallet_create_or_open('offline-create-transaction', key=hdkey, network='testnet',
                                    databasefile=DATABASEFILE_UNITTESTS)
        wlt.get_key()
        utxos = [{
            'address': 'n2S9Czehjvdmpwd2YqekxuUC1Tz5ZdK3YN',
            'script': '',
            'confirmations': 10,
            'output_n': 1,
            'tx_hash': '9df91f89a3eb4259ce04af66ad4caf3c9a297feea5e0b3bc506898b6728c5003',
            'value': 8970937
        }]
        wlt.utxos_update(utxos=utxos)
        t = wlt.transaction_create([('n2S9Czehjvdmpwd2YqekxuUC1Tz5ZdK3YN', 100)], fee=5000)
        t.sign()
        self.assertTrue(t.verify())

    def test_wallet_scan(self):
        account_key = 'tpubDCmJWqxWch7LYDhSuE1jEJMbAkbkDm3DotWKZ69oZfNMzuw7U5DwEaTVZHGPzt5j9BJDoxqVkPHt2EpUF66FrZhpfq' \
                      'ZY6DFj6x61Wwbrg8Q'
        self.wallet = wallet_create_or_open('scan-test', key=account_key, network='testnet',
                                            databasefile=DATABASEFILE_UNITTESTS)
        self.wallet.scan()
        self.wallet.info()
        self.assertEqual(len(self.wallet.keys()), 25)
        self.assertEqual(len(self.wallet.keys(is_active=None)), 31)
        self.assertEqual(self.wallet.balance(), 60500000)

    def test_wallet_two_utxos_one_key(self):
        wlt = HDWallet.create('double-utxo-test', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        key = wlt.new_key()
        wlt.utxos_update()
        utxos = wlt.utxos()

        inp1 = Input(prev_hash=utxos[0]['tx_hash'], output_n=utxos[0]['output_n'], keys=key.key_public,
                     network='bitcoinlib_test')
        inp2 = Input(prev_hash=utxos[1]['tx_hash'], output_n=utxos[1]['output_n'], keys=key.key_public,
                     network='bitcoinlib_test')
        out = Output(10000000, address=key.address, network='bitcoinlib_test')

        t = Transaction(inputs=[inp1, inp2], outputs=[out], network='testnet')
        t.sign(key.key_private)
        self.assertTrue(t.verify())

    def test_wallet_balance_update(self):
        wlt = HDWallet.create('test-balance-update', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        to_key = wlt.get_key()
        wlt.utxos_update()
        self.assertEqual(wlt.balance(), 200000000)

        t = wlt.send_to(to_key.address, 9000)
        self.assertEqual(wlt.balance(), 200000000 - t.fee)

    def test_wallet_balance_update_multi_network(self):
        passphrase = "always reward element perfect chunk father margin slab pond suffer episode deposit"
        wlt = HDWallet.create("wallet-passphrase", key=passphrase, network='testnet',
                              databasefile=DATABASEFILE_UNITTESTS)
        wlt.get_key()
        wlt.new_account(network='bitcoinlib_test')
        wlt.get_key(network='bitcoinlib_test')
        wlt.utxos_update()
        self.assertEqual(wlt.balance(), 900)
        self.assertEqual(wlt.balance(network='testnet'), 900)
        self.assertEqual(wlt.balance(network='bitcoinlib_test'), 200000000)

    def test_wallet_add_dust_to_fee(self):
        # Send bitcoinlib test transaction and check if dust resume amount is added to fee
        wlt = HDWallet.create('bcltestwlt', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 99999500)
        self.assertEqual(t.fee, 500)

    def test_wallet_transactions_send_update_utxos(self):
        # Send bitcoinlib test transaction and check if all utxo's are updated after send
        wlt = HDWallet.create('bcltestwlt2', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        to_key = wlt.get_key(number_of_keys=5)
        wlt.utxos_update()
        self.assertEqual(wlt.balance(), 1000000000)
        t = wlt.send_to(to_key[0].address, 550000000)
        wlt._balance_update(min_confirms=0)
        self.assertEqual(wlt.balance(), 1000000000-t.fee)
        self.assertEqual(len(wlt.utxos()), 6)

    def test_wallet_transaction_import(self):
        wlt = HDWallet.create('bcltestwlt3', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 50000000, offline=True)
        t2 = wlt.transaction_import(t)
        t.fee_per_kb = None
        self.assertDictEqualExt(t.dict(), t2.dict())

    def test_wallet_transaction_import_raw(self):
        wlt = HDWallet.create('bcltestwlt4', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 50000000, offline=True)
        t2 = wlt.transaction_import_raw(t.raw())
        t.fee_per_kb = None
        self.assertDictEqualExt(t.dict(), t2.dict())
