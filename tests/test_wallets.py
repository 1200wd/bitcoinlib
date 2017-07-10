# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Wallet Class
#    © 2017 April - 1200 Web Development <http://1200wd.com/>
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

from bitcoinlib.db import DEFAULT_DATABASEDIR
from bitcoinlib.wallets import HDWallet, list_wallets, delete_wallet, WalletError

DATABASEFILE_UNITTESTS = DEFAULT_DATABASEDIR + 'bitcoinlib.unittest.sqlite'


class TestWalletCreate(unittest.TestCase):

    def setUp(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        self.wallet = HDWallet.create(
            name='test_wallet_create',
            databasefile=DATABASEFILE_UNITTESTS)

    def test_wallet_create(self):
        self.assertTrue(isinstance(self.wallet, HDWallet))

    def test_wallet_info(self):
        self.assertIsNot(self.wallet.info(), "")

    def test_wallet_key_info(self):
        self.assertIsNot(self.wallet.main_key.info(), "")

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

    def test_list_wallets(self):
        wallets = list_wallets(databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(wallets[0]['name'], 'test_wallet_create')

    def test_delete_wallet(self):
        HDWallet.create(
            name='wallet_to_remove',
            databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(delete_wallet('wallet_to_remove', databasefile=DATABASEFILE_UNITTESTS), 1)

    def test_delete_wallet_exception(self):
        self.assertRaisesRegexp(WalletError, '', delete_wallet, 'unknown_wallet', databasefile=DATABASEFILE_UNITTESTS)

    def test_wallet_duplicate_key_for_path(self):
        nkfp = self.wallet.key_for_path("m/44'/0'/100'/1200/1200")
        nkfp2 = self.wallet.key_for_path("m/44'/0'/100'/1200/1200")
        self.assertEqual(nkfp.key().wif(), nkfp2.key().wif())

    def test_wallet_key_for_path_normalized(self):
        nkfp = self.wallet.key_for_path("m/44h/0p/100H/1200/1201")
        nkfp2 = self.wallet.key_for_path("m/44'/0'/100'/1200/1201")
        self.assertEqual(nkfp.key().wif(), nkfp2.key().wif())


class TestWalletImport(unittest.TestCase):

    def setUp(self):
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

    def setUp(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
            self.private_wif = 'xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzF9ySUHZw5qJkk5LCALAhXS' \
                               'XoCmCSnStRvgwLBtcbGsg1PeKT2en'
        self.wallet = HDWallet.create(
            key=self.private_wif,
            name='test_wallet_keys',
            databasefile=DATABASEFILE_UNITTESTS)
        self.wallet.new_key()
        self.wallet.new_key_change()

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


class TestWalletElectrum(unittest.TestCase):

    def setUp(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        self.pk = 'xprv9s21ZrQH143K2fuscnMTwUadsPqEbYdFQVJ1uWPawUYi7C485NHhCiotGy6Kz3Cz7ReVr65oXNwhREZ8ePrz8p7zy' \
                  'Hra82D1EGS7cQQmreK'
        self.wallet = HDWallet.create(
            key=self.pk,
            name='test_wallet_electrum',
            databasefile=DATABASEFILE_UNITTESTS)
        workdir = os.path.dirname(__file__)
        with open('%s/%s' % (workdir, 'electrum_keys.json'), 'r') as f:
            self.el_keys = json.load(f)
        for i in range(20):
            self.wallet.key_for_path('m/0/%d' % i, name='-test- Receiving #%d' % i, enable_checks=False)
        for i in range(6):
            self.wallet.key_for_path('m/1/%d' % i, name='-test- Change #%d' % i, enable_checks=False)

    def test_electrum_keys(self):
        for key in self.wallet.keys():
            print(key.address)
            if key.name[:6] == '-test-' and key.path not in ['m/0', 'm/1']:
                self.assertIn(key.address, self.el_keys.keys(),
                              msg='Key %s (%s, %s) not found in Electrum wallet key export' %
                                  (key.name, key.path, key.address))


class TestWalletMultiCurrency(unittest.TestCase):

    def setUp(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        self.pk = 'dHHM83S1ptYryy3ZeV6Q8zQBT9NvqiSjUMJPwf6xg2CdaFLiHbyzsCSeP9FG1wzbsPVY9VtC85VsWoFvU9z1S4GzqwDBh' \
                  'CawMAogXrUh2KgVahL'
        self.wallet = HDWallet.create(
            key=self.pk,
            name='test_wallet_multicurrency',
            databasefile=DATABASEFILE_UNITTESTS)

        self.wallet.new_account(network='litecoin')
        self.wallet.new_account(network='bitcoin')
        self.wallet.new_account(network='testnet')
        self.wallet.new_account(network='dash')
        self.wallet.new_key()
        self.wallet.new_key()
        self.wallet.new_key(network='bitcoin')

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
        res = self.wallet.import_key(pk_hex, network='litecoin')
        addresses_ltc_in_wallet = self.wallet.addresslist(network='litecoin', depth=0, tree_index=res.tree_index)
        self.assertIn(address_ltc, addresses_ltc_in_wallet)

    def test_wallet_multiple_networks_import_error(self):
        pk_dashtest = 'DRKVrRjogj3bNiLD8V9398hVVqqxi5NzhNJBLX3bfc9UdX77NxaNeMksf3ybsXSUJLh44TC9FCDkQfxAEyX924VJgK' \
                      'J5xeeM2agqru6DGAXRyMSW'
        error_str = "Network dash_testnet not available in this wallet, please create an account for this network " \
                    "first."
        self.assertRaisesRegexp(WalletError, error_str, self.wallet.import_key, pk_dashtest)


class TestWalletBitcoinlibTestnet(unittest.TestCase):

    def test_wallet_bitcoinlib_testnet_sendto(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        w = HDWallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet',
            databasefile=DATABASEFILE_UNITTESTS)

        w.new_key()
        w.updateutxos()
        self.assertEqual(w.send_to('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 50000000),
                         'succesfull_test_sendrawtransaction')

    def test_wallet_bitcoinlib_testnet_sendto_no_funds_txfee(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        w = HDWallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet',
            databasefile=DATABASEFILE_UNITTESTS)
        w.new_key()
        w.updateutxos()
        balance = w.balance()
        self.assertRaisesRegexp(WalletError, 'Not enough unspent transaction outputs found', w.send_to,
                                '21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', balance),

    def test_wallet_bitcoinlib_testnet_sweep(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        w = HDWallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet',
            databasefile=DATABASEFILE_UNITTESTS)
        w.new_key()
        w.new_key()
        w.new_key()
        w.updateutxos()
        self.assertEqual(w.sweep('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo'),
                         'succesfull_test_sendrawtransaction')


class TestWalletMultisig(unittest.TestCase):

    def setUp(self):
        # Source: Example from
        #   http://www.soroushjp.com/2014/12/20/bitcoin-multisig-the-hard-way-understanding-raw-multisignature-bitcoin-transactions/
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        key1 = 'xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6TJG6MaYHtXdxCePfeN1JQAHic2UFxujpMrK62f3' \
               'Qn4HAeGN8nm'
        key2 = 'xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6Sr15fZW12RHSQBKKrND4VHeRvtX8BhdJ2QPcTbv' \
               'eYZrsBum5cv'
        key3 = 'xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6S9yUPYqYra2xVE9Yq6wRbGXDdNHpUoz2EQY6ECN' \
               'Kg98YTZZiGz'
        self.multisig_wallet = HDWallet.create('mcw', key=key1, databasefile=DATABASEFILE_UNITTESTS)
        self.keylist = [self.multisig_wallet.main_key, key2, key3]
        self.multisig_key_id = self.multisig_wallet.create_multisig(self.keylist, 2)

    def test_wallet_create_multisig(self):
        self.assertEqual(self.multisig_key_id, 7)

    def test_wallet_multisig_address(self):
        self.assertEqual(self.multisig_wallet.key(self.multisig_key_id).address, '347N1Thc213QqfYCz3PZkjoJpNv5b14kBd')
