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
from random import shuffle
from bitcoinlib.db import DEFAULT_DATABASEDIR
from bitcoinlib.wallets import HDWallet, list_wallets, delete_wallet, WalletError
from bitcoinlib.keys import HDKey
from bitcoinlib.networks import Network

DATABASEFILE_UNITTESTS = DEFAULT_DATABASEDIR + 'bitcoinlib.unittest.sqlite'
DATABASEFILE_UNITTESTS_2 = DEFAULT_DATABASEDIR + 'bitcoinlib.unittest2.sqlite'


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
        self.wallet.import_key(pk_hex, network='litecoin')
        addresses_ltc_in_wallet = self.wallet.addresslist(network='litecoin', depth=0)
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

    def test_wallet_bitcoinlib_testnet_send_utxos_updated(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        w = HDWallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet',
            databasefile=DATABASEFILE_UNITTESTS)

        w.new_key()
        w.updateutxos()
        self.assertEqual(len(w.getutxos()), 1)
        w.send_to('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 50000000)
        self.assertEqual(w.getutxos(), [])

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
        self.assertRaisesRegex(WalletError, 'Not enough unspent transaction outputs found', w.send_to,
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
        w.info()
        self.assertEqual(w.sweep('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo'),
                         'succesfull_test_sendrawtransaction')


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
        wl.updateutxos()  # In bitcoinlib_test network this generates new UTXO's
        t = wl.transaction_create([('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 100000)])
        t = wl.transaction_sign(t)
        self.assertTrue(t.verify())
        self.assertEqual(wl.transaction_send(t), 'succesfull_test_sendrawtransaction')

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
        msw1.updateutxos()
        msw2.updateutxos()
        utxos = msw1.getutxos()
        output_arr = [('21KnydRNSmqAf8Py74mMiwRXYHGxW27zyDu', utxos[0]['value'] - 50000)]
        input_arr = [(utxos[0]['tx_hash'], utxos[0]['output_n'], utxos[0]['key_id'], utxos[0]['value'])]
        t = msw1.transaction_create(output_arr, input_arr, transaction_fee=50000)
        t = msw1.transaction_sign(t)
        t2 = msw2.transaction_import(t.raw())
        t2 = msw2.transaction_sign(t2)
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
        msw1.updateutxos()
        msw2.updateutxos()
        utxos = msw1.getutxos()
        output_arr = [('21KnydRNSmqAf8Py74mMiwRXYHGxW27zyDu', utxos[0]['value'] - 50000)]
        input_arr = [(utxos[0]['tx_hash'], utxos[0]['output_n'], utxos[0]['key_id'], utxos[0]['value'])]
        t = msw1.transaction_create(output_arr, input_arr, transaction_fee=50000)
        t = msw1.transaction_sign(t)
        t2 = msw2.transaction_import(t.raw())
        t2 = msw2.transaction_sign(t2)
        self.assertEqual(msw2.transaction_send(t2), 'succesfull_test_sendrawtransaction')

    @staticmethod
    def _multisig_test(sigs_required, number_of_sigs, network):
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
                wallet_name, key_list, sigs_required=sigs_required, network=network, sort_keys=False,
                databasefile=DATABASEFILE_UNITTESTS)
            wallet_keys[wallet_id] = wallet_dict[wallet_id].new_key()
            wallet_dict[wallet_id].updateutxos()

        # Create transaction in one random wallet
        wallet_ids = [i for i in range(0, number_of_sigs)]
        shuffle(wallet_ids)
        transaction_fee = 50000
        wallet_id = wallet_ids.pop()
        wlt = wallet_dict[wallet_id]
        utxos = wlt.getutxos()
        output_arr = [(random_output_address, utxos[0]['value'] - transaction_fee)]
        input_arr = [(utxos[0]['tx_hash'], utxos[0]['output_n'], utxos[0]['key_id'], utxos[0]['value'])]
        t = wlt.transaction_create(output_arr, input_arr, transaction_fee=transaction_fee)
        t = wlt.transaction_sign(t)
        n_signs = 1

        # Sign transaction with other wallets until required number of signatures is reached
        while wallet_ids and n_signs < sigs_required:
            wallet_id = wallet_ids.pop()
            t = wallet_dict[wallet_id].transaction_import(t.raw())
            t = wallet_dict[wallet_id].transaction_sign(t)
            n_signs += 1
        return t

    def test_wallet_multisig_2of3(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        t = self._multisig_test(2, 3, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    def test_wallet_multisig_3of5(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        t = self._multisig_test(3, 5, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    # Disable for now takes about 46 seconds because it needs to create 9 * 9 wallets and lots of keys
    # def test_wallet_multisig_5of9(self):
    #     if os.path.isfile(DATABASEFILE_UNITTESTS):
    #         os.remove(DATABASEFILE_UNITTESTS)
    #     t = self._multisig_test(5, 9, 'bitcoinlib_test')
    #     self.assertTrue(t.verify())

    # TODO: other networks test + sorted keys
