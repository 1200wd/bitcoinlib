# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Wallet Class
#    © 2016 - 2019 February - 1200 Web Development <http://1200wd.com/>
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
from random import shuffle
from sqlalchemy.orm import close_all_sessions
from bitcoinlib.wallets import *
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey, BKeyError
from tests.test_custom import CustomAssertions


DATABASEFILE_UNITTESTS = DEFAULT_DATABASEDIR + 'bitcoinlib.unittest.sqlite'
DATABASEFILE_UNITTESTS_2 = DEFAULT_DATABASEDIR + 'bitcoinlib.unittest2.sqlite'


def db_remove(db=DATABASEFILE_UNITTESTS):
    close_all_sessions()
    if os.path.isfile(db):
        os.remove(db)


class TestWalletCreate(unittest.TestCase):

    wallet = None

    @classmethod
    def setUpClass(cls):
        db_remove()
        cls.wallet = HDWallet.create(
            name='test_wallet_create',
            databasefile=DATABASEFILE_UNITTESTS)

    def test_wallet_create(self):
        self.assertTrue(isinstance(self.wallet, HDWallet))

    def test_wallet_info(self):
        self.assertIsNot(self.wallet.info(), "")

    def test_wallet_key_info(self):
        self.assertIsNot(self.wallet.main_key.as_dict(), "")

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
        wlt = HDWallet.create("wallet-passphrase", keys=passphrase, network='testnet',
                              databasefile=DATABASEFILE_UNITTESTS)
        key0 = wlt.get_key()
        self.assertEqual(key0.address, "mqDeXXaFnWKNWhLmAae7zHhZDW4PMsLHPp")

    def test_wallet_create_with_passphrase_litecoin(self):
        passphrase = "always reward element perfect chunk father margin slab pond suffer episode deposit"
        wlt = HDWallet.create("wallet-passphrase-litecoin", keys=passphrase, network='litecoin',
                              databasefile=DATABASEFILE_UNITTESTS)
        keys = wlt.get_key(number_of_keys=5)
        self.assertEqual(keys[4].address, "Li5nEi62nAKWjv6fpixEpoLzN1pYFK621g")


class TestWalletImport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_remove()

    def test_wallet_import(self):
        keystr = 'tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePy' \
                 'A7irEvBoe4aAn52'
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
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
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
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
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
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
        pubwal = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_import_public_wallet',
            keys=pubkey,
            network='testnet',
            account_id=0)
        newkey = pubwal.new_key()
        self.assertEqual(newkey.address, u'myitDjbzYpUTShv9CyXRJKXtM4uRgSqa3A')

    def test_wallet_import_litecoin(self):
        accountkey = 'Ltpv71G8qDifUiNet6mn25D7GPAVLZeaFRWzDABxx5xNeigVpFEviHK1ZggPS1kbtegB3U2i8w6ToNfM5sdvEQPW' \
                     'tov4KWyQ5NxWUd3oDWXQb4C'
        wallet_import = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_litecoin',
            keys=accountkey,
            network='litecoin')
        newkey = wallet_import.new_key()
        self.assertEqual(wallet_import.main_key.wif, accountkey)
        self.assertEqual(newkey.address, u'LZj8MnR6tRgLNKUBSfd2pD2czA4F9G5oGk')
        self.assertEqual(newkey.path, "m/44'/2'/0'/0/1")

    def test_wallet_import_key_network_error(self):
        w = HDWallet.create(
            name='Wallet Error',
            databasefile=DATABASEFILE_UNITTESTS)
        self.assertRaisesRegexp(WalletError,
                                "Network litecoin not available in this wallet, please create an account "
                                "for this network first.",
                                w.import_key, 'T43gB4F6k1Ly3YWbMuddq13xLb56hevUDP3RthKArr7FPHjQiXpp', 
                                network='litecoin')
        
    def test_wallet_import_hdwif(self):
        # p2wpkh
        wif = \
            'zpub6s7HTSrGmNUWSgfbDMhYbXVuxA14yNnycS25v6ogicEauzUrRUkuCLQUWbJXP1NyXNqGmwpU6hZw7vr22a4yspwH8XQFjjwRmxC' \
            'KkXdDAXN'
        w = HDWallet.create("wif_import_p2wpkh", wif, databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.get_key().address, "bc1qruvyu8f2tg06zhysytdsc3qlngnpfzn0juwssx")
        self.assertEqual(w.get_key_change().address, "bc1qg6h45txt82x87uvv3ndm82xsf3wjknq8j7sufh")

        # p2sh_p2wpkh
        wif = \
            'ypub6YMgBd4GfQjtxUf8ExorFUQEpBfUYTDz7E1tvfNgDqZeDEUuNNVXSNfsebis2cyeqWYXx6yaBBEQV7sJW3NGoXw5wsp9kkEsB2D' \
            'qiVquYLE'
        w = HDWallet.create("wif_import_p2sh_p2wpkh", wif, databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.get_key().address, "3EFDqEWcrzyidoCXhxaUDB28pVtgX3YuiR")
        self.assertEqual(w.get_key_change().address, "33Un3fDSdT2hsuqyuHiCci1GyUbiyZEWHW")

        # p2wsh
        wif1 = \
            'Zpub74arK1zZNbJYvbMz6wwu2vvcSyB421ePA2p65AD1vaUA5ApzbPLwe3yRDHFgEoBZiLbTzdBPJyPMMaTNsmGkv76t2uD2d9ACqpv' \
            'vBa5zbv9'
        wif2 = \
            'Zpub74JTMKMB9cTWwE9Hs4UVaHvddqPtR51D99x2B5EGyXyxEg3PW77vfmD15RZ86TVdwwwuUaCueBtvaL921mgyKe9Ya6LHCaMXnEp' \
            '1PMw4vDy'
        w = HDWallet.create("wif_import_p2wsh", [wif1, wif2], databasefile=DATABASEFILE_UNITTESTS)
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
        w = HDWallet.create("wif_import_p2sh_p2wsh", [wif1, wif2, wif3], sigs_required=2,
                            databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.get_key().address, "3BeYQTUgrGPQMHDJcch6mF7G7sRrNYkRhP")
        self.assertEqual(w.get_key_change().address, "3PFD1qkgbaeeDnX38Smerb5vAPBkDVkhcm")


class TestWalletExport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_remove()

    def test_wallet_export_hdwifs(self):
        # p2wpkh
        p = 'garage million cheese nephew original subject pass reward month practice advance decide'
        w = HDWallet.create("wif_import_p2wpkh", p, network='bitcoin', witness_type='segwit',
                            databasefile=DATABASEFILE_UNITTESTS)
        wif = 'zpub6s7HTSrGmNUWSgfbDMhYbXVuxA14yNnycS25v6ogicEauzUrRUkuCLQUWbJXP1NyXNqGmwpU6hZw7vr22a4yspwH8XQFjjwRmx' \
              'CKkXdDAXN'
        # self.assertEqual(w.account(0).key().wif_public(script_type=w.script_type), wif)
        self.assertEqual(w.wif(is_private=False), wif)

        # # p2sh_p2wpkh
        p = 'cluster census trash van rack skill feed inflict mixture vocal crew sea'
        w = HDWallet.create("wif_import_p2sh_p2wpkh", p, network='bitcoin', witness_type='p2sh-segwit',
                            databasefile=DATABASEFILE_UNITTESTS)
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
        w = HDWallet.create("wif_import_p2wsh", [p1, p2], witness_type='segwit', network='bitcoin',
                            databasefile=DATABASEFILE_UNITTESTS)
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
        w = HDWallet.create("wif_import_p2sh_p2wsh", [p1, p2, p3], sigs_required=2, witness_type='p2sh-segwit',
                            network='bitcoin', databasefile=DATABASEFILE_UNITTESTS)
        for wif in w.wif(is_private=False):
            self.assertIn(wif, wifs)


class TestWalletKeys(unittest.TestCase):

    wallet = None

    @classmethod
    def setUpClass(cls):
        db_remove()
        cls.private_wif = 'xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzF9ySUHZw5qJkk5LCALAhXS' \
                           'XoCmCSnStRvgwLBtcbGsg1PeKT2en'
        cls.wallet = HDWallet.create(
            keys=cls.private_wif,
            name='test_wallet_keys',
            databasefile=DATABASEFILE_UNITTESTS)
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
        db_remove()
        wk = 'xprv9s21ZrQH143K3tCgu8uhkA2fw9F9opbvoNNzh5wcuEvNHbCU6Kg3c6dam2a6cw4UYeDxAsgBorAqXp2nsoYS84DqYMwkzxZ15' \
             'ujRHzmBMxE'
        w = HDWallet.create('test_wallet_keys_single_key', wk, scheme='single', databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.new_key(), w.new_key())

    def test_wallet_create_uncompressed_masterkey(self):
        wlt = wallet_create_or_open('uncompressed_test', keys='68vBWcBndYGLpd4KmeNTk1gS1A71zyDX6uVQKCxq6umYKyYUav5',
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

    def test_wallet_single_key_segwit(self):
        wlt = wallet_create_or_open('single_key_segwit', scheme='single', network='litecoin_testnet',
                                    witness_type='segwit', databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(wlt.addresslist()[0][:5], 'tltc1')

    def test_wallet_single_key_main_key(self):
        w = HDWallet.create('multisig_with_single_key', [HDKey().public_master_multisig(), HDKey(key_type='single')],
                            sigs_required=2, databasefile=DATABASEFILE_UNITTESTS)
        w.new_key()
        self.assertEqual(len(w.keys_addresses()), 1)


class TestWalletElectrum(unittest.TestCase):

    wallet = None

    @classmethod
    def setUpClass(cls):
        db_remove()
        cls.pk = 'xprv9s21ZrQH143K2fuscnMTwUadsPqEbYdFQVJ1uWPawUYi7C485NHhCiotGy6Kz3Cz7ReVr65oXNwhREZ8ePrz8p7zy' \
                 'Hra82D1EGS7cQQmreK'
        cls.wallet = HDWallet.create(
            keys=cls.pk,
            name='test_wallet_electrum',
            databasefile=DATABASEFILE_UNITTESTS)
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
        wlt = HDWallet.create('wallet_electrum_p2pkh', phrase, network='bitcoin', witness_type='segwit',
                              databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(wlt.get_key().address, 'bc1qjz5l6mej6ptqlggfvdlys8pfukwqp8xnu0mn5u')
        self.assertEqual(wlt.get_key_change().address, 'bc1qz4tr569wfs2fuekgcjtdlz0eufk7rfs8gnu5j9')

    def test_wallet_electrum_p2sh_p2wsh(self):
        phrase1 = 'magnet voice math okay castle recall arrange music high sustain require crowd'
        phrase2 = 'wink tornado honey delay nest sing series timber album region suit spawn'
        wlt = HDWallet.create('wallet_electrum_p2sh_p2wsh', [phrase1, phrase2], network='bitcoin',
                              witness_type='p2sh-segwit', databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(wlt.get_key().address, '3ArRVGXfqcjw68XzUZr4iCCemrPoFZxm7s')
        self.assertEqual(wlt.get_key_change().address, '3FZEUFf59C3psUUiKB8TFbjsFUGWD73QPY')


class TestWalletMultiCurrency(unittest.TestCase):

    wallet = None

    @classmethod
    def setUpClass(cls):
        db_remove()
        cls.pk = 'xprv9s21ZrQH143K4478MENLXpSXSvJSRYsjD2G3sY7s5sxAGubyujDmt9Qzfd1me5s1HokWGGKW9Uft8eB9dqryybAcFZ5JAs' \
                 'rg84jAVYwKJ8c'
        cls.wallet = HDWallet.create(
            keys=cls.pk, network='dash',
            name='test_wallet_multicurrency',
            databasefile=DATABASEFILE_UNITTESTS)

        cls.wallet.new_account(network='litecoin')
        cls.wallet.new_account(network='bitcoin')
        cls.wallet.new_account(network='testnet')
        cls.wallet.new_account(network='dash')
        cls.wallet.new_key()
        cls.wallet.new_key()
        cls.wallet.new_key(network='bitcoin')

    def test_wallet_multiple_networks_defined(self):
        networks_expected = sorted(['litecoin', 'bitcoin', 'dash', 'testnet'])
        networks_wlt = sorted([x.name for x in self.wallet.networks()])
        self.assertListEqual(networks_wlt, networks_expected,
                             msg="Not all network are defined correctly for this wallet")

    def test_wallet_multiple_networks_default_addresses(self):
        addresses_expected = ['XqTpf6NYrrckvsauJKfHFBzZaD9wRHjQtv', 'Xamqfy4y21pXMUP8x8TeTPWCNzsKrhSfau',
                              'XugknDhBtJFvfErjaobizCa8KAEDVU7bCJ', 'Xj6tV9Jc3qJ2AszpNxvEq7KVQKUMcfmBqH',
                              'XgkpZbqaRsRb2e2BC1QsWxTDEfW6JVpP6r']
        self.assertListEqual(self.wallet.addresslist(network='dash'), addresses_expected)

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
        pk_dashtest = 'YXsfembHRwpatrAVUGY8MBUuKwhUDf9EEWeZwGoEfE5appg5rLjSfZ1GwoaNB5DgUZ2aVuU1ezmg7zDefubuWkZ17et5o' \
                      'KoMgKnjvAZ6a4Yn2QZg'
        error_str = "Network bitcoinlib_test not available in this wallet, please create an account for this network " \
                    "first."
        self.assertRaisesRegexp(WalletError, error_str, self.wallet.import_key, pk_dashtest)


class TestWalletMultiNetworksMultiAccount(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_remove()

    def test_wallet_multi_networks_send_transaction(self):
        pk = 'tobacco defy swarm leaf flat pyramid velvet pen minor twist maximum extend'
        wallet = HDWallet.create(
            keys=pk, network='bitcoin',
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
        self.assertEqual(wallet.balance(network='bitcoinlib_test'), 600000000)
        self.assertEqual(wallet.balance(network='bitcoinlib_test', account_id=1), 600000000)
        self.assertEqual(wallet.balance(network='testnet'), 1500000)
        ltct_addresses = ['mhHhSx66jdXdUPu2A8pXsCBkX1UvHmSkUJ', 'mrdtENj75WUfrJcZuRdV821tVzKA4VtCBf',
                          'mmWFgfG43tnP2SJ8u8UDN66Xm63okpUctk']
        self.assertListEqual(wallet.addresslist(network='testnet'), ltct_addresses)
        
        t = wallet.send_to('21EsLrvFQdYWXoJjGX8LSEGWHFJDzSs2F35', 10000000, account_id=1,
                           network='bitcoinlib_test', fee=1000, offline=False)
        self.assertIsNone(t.error)
        self.assertTrue(t.verified)
        self.assertEqual(wallet.balance(network='bitcoinlib_test', account_id=1), 589999000)
        self.assertEqual(len(wallet.transactions(account_id=0, network='bitcoinlib_test')), 6)
        self.assertEqual(len(wallet.transactions(account_id=1, network='bitcoinlib_test')), 8)
        del wallet

    def test_wallet_multi_networks_account_bip44_code_error(self):
        wlt = HDWallet.create("wallet-bip44-code-error", network='testnet', databasefile=DATABASEFILE_UNITTESTS)
        error_str = "Can not create new account for network litecoin_testnet with same BIP44 cointype"
        self.assertRaisesRegexp(WalletError, error_str, wlt.new_account, network='litecoin_testnet')

    def test_wallet_get_account_defaults(self):
        w = wallet_create_or_open("test_wallet_get_account_defaults", witness_type='segwit',
                                  databasefile=DATABASEFILE_UNITTESTS)
        w.get_key(network='litecoin', account_id=100)
        network, account_id, account_key = w._get_account_defaults(network='litecoin')
        self.assertEqual(network, 'litecoin')
        self.assertEqual(account_id, 100)
        self.assertIn('account', account_key.name)

    def test_wallet_update_attributes(self):
        w = HDWallet.create('test_wallet_set_attributes', databasefile=DATABASEFILE_UNITTESTS)
        w.new_account(network='litecoin', account_id=1200)
        owner = 'Satoshi'
        w.owner = owner
        w.default_network_set('litecoin')
        w.default_account_id = 1200
        del w

        w2 = HDWallet('test_wallet_set_attributes', databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w2.owner, owner)
        self.assertEqual(w2.network.name, 'litecoin')
        nk = w2.new_key()
        self.assertEqual(nk.path, "m/44'/2'/1200'/0/1")


class TestWalletBitcoinlibTestnet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_remove()

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

        w.utxos_update()
        self.assertEqual(len(w.utxos()), 2)
        t = w.send_to('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 10000)
        self.assertTrue(t.pushed)

    def test_wallet_bitcoinlib_testnet_sendto_no_funds_txfee(self):
        w = HDWallet.create(
            network='bitcoinlib_test',
            name='test_wallet_bitcoinlib_testnet_sendto_no_funds_txfee',
            databasefile=DATABASEFILE_UNITTESTS)
        w.new_key()
        w.utxos_update()
        balance = w.balance()
        self.assertFalse(w.send_to('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', balance))

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

    @classmethod
    def setUpClass(cls):
        db_remove()

    def test_wallet_multisig_2_wallets_private_master_plus_account_public(self):
        db_remove()
        pk1 = 'tprv8ZgxMBicQKsPdPVdNSEeAhagkU6tUDhUQi8DcCTmJyNLUyU7svTFzXQdkYqNJDEtQ3S2wAspz3K56CMcmMsZ9eXZ2nkNq' \
              'gVxJhMHq3bGJ1X'
        pk1_acc_pub = 'tpubDCZUk9HLxh5gdB9eC8FUxPB1AbZtsSnbvyrAAzsC8x3tiYDgbzyxcngU99rG333jegHG5vJhs11AHcSVkbwrU' \
                      'bYEsPK8vA7E6yFB9qbsTYi'
        w1 = HDWallet.create(name='test_wallet_create_1', keys=pk1, databasefile=DATABASEFILE_UNITTESTS)
        w2 = HDWallet.create(name='test_wallet_create_2', keys=pk1_acc_pub, databasefile=DATABASEFILE_UNITTESTS)
        wk1 = w1.new_key()
        wk2 = w2.new_key()
        self.assertTrue(wk1.is_private)
        self.assertFalse(wk2.is_private)
        self.assertEqual(wk1.address, wk2.address)

    def test_wallet_multisig_create_2_cosigner_wallets(self):
        db_remove()
        pk_wif1 = 'tprv8ZgxMBicQKsPdvHCP6VxtFgowj2k7nBJnuRiVWE4DReDFojkLjyqdT8mtR6XJK9dRBcaa3RwvqiKFjsEQVhKfQmHZCCY' \
                  'f4jRTWvJuVuK67n'
        pk_wif2 = 'tprv8ZgxMBicQKsPdkJVWDkqQQAMVYB2usfVs3VS2tBEsFAzjC84M3TaLMkHyJWjydnJH835KHvksS92ecuwwWFEdLAAccwZ' \
                  'KjhcA63NUyvDixB'
        pk1 = HDKey(pk_wif1, network='testnet')
        pk2 = HDKey(pk_wif2, network='testnet')
        wl1 = HDWallet.create('multisig_test_wallet1',
                              [pk_wif1, pk2.subkey_for_path("m/45'").wif_public()],
                              sigs_required=2, network='testnet', databasefile=DATABASEFILE_UNITTESTS)
        wl2 = HDWallet.create('multisig_test_wallet2',
                              [pk1.subkey_for_path("m/45'").wif_public(), pk_wif2],
                              sigs_required=2, network='testnet', databasefile=DATABASEFILE_UNITTESTS)
        wl1_key = wl1.new_key()
        wl2_key = wl2.new_key(cosigner_id=wl1.cosigner_id)
        self.assertEqual(wl1_key.address, wl2_key.address)

    def test_wallet_multisig_bitcoinlib_testnet_transaction_send(self):
        db_remove()

        key_list = [
            'Pdke4WfXvALPdbrKEfBU9z9BNuRNbv1gRr66BEiZHKcRXDSZQ3gV',
            'PhUTR4ZkZu9Xkzn3ee3xMU1TxbNx6ENJvUjX4wBaZDyTCMrn1zuE',
            'PdnZFcwpxUSAcFE6MHB78weVAguwzSTUMBqswkqie7Uxfxsd77Zs'
        ]

        # Create wallet and generate key
        wl = HDWallet.create('multisig_test_simple', key_list, sigs_required=2, network='bitcoinlib_test',
                             databasefile=DATABASEFILE_UNITTESTS)
        wl.new_key()

        # Sign, verify and send transaction
        wl.utxos_update()  # In bitcoinlib_test network this generates new UTXO's
        t = wl.transaction_create([('21DBmFUMQMP7A6KeENXgZQ4wJdSCeGc2zFo', 100000)])
        t.sign()
        self.assertTrue(t.verify())
        t.send()
        self.assertIsNone(t.error)

    def test_wallet_multisig_bitcoin_transaction_send_offline(self):
        db_remove()
        pk2 = HDKey('e2cbed99ad03c500f2110f1a3c90e0562a3da4ba0cff0e74028b532c3d69d29d')
        key_list = [
            HDKey('e9e5095d3e26643cc4d996efc6cb9a8d8eb55119fdec9fa28a684ba297528067'),
            pk2.public_master(multisig=True).public(),
            HDKey('86b77aee5cfc3a55eb0b1099752479d82cb6ebaa8f1c4e9ef46ca0d1dc3847e6').public_master(
                multisig=True).public(),
        ]
        wl = HDWallet.create('multisig_test_bitcoin_send', key_list, sigs_required=2,
                             databasefile=DATABASEFILE_UNITTESTS)
        wl.utxo_add(wl.get_key().address, 200000, '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5', 0)
        t = wl.transaction_create([('3CuJb6XrBNddS79vr27SwqgR4oephY6xiJ', 100000)])
        t.sign(pk2.subkey_for_path("m/45'/2/0/0"))
        t.send(offline=True)
        self.assertTrue(t.verify())
        self.assertIsNone(t.error)

    def test_wallet_multisig_bitcoin_transaction_send_no_subkey_for_path(self):
        db_remove()
        pk2 = HDKey('e2cbed99ad03c500f2110f1a3c90e0562a3da4ba0cff0e74028b532c3d69d29d')
        key_list = [
            HDKey('e9e5095d3e26643cc4d996efc6cb9a8d8eb55119fdec9fa28a684ba297528067'),
            pk2.public_master(multisig=True),
            HDKey('86b77aee5cfc3a55eb0b1099752479d82cb6ebaa8f1c4e9ef46ca0d1dc3847e6').public_master(multisig=True),
        ]
        wl = HDWallet.create('multisig_test_bitcoin_send', key_list, sigs_required=2,
                             databasefile=DATABASEFILE_UNITTESTS)
        wl.utxo_add(wl.get_key().address, 200000, '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5', 0)
        t = wl.transaction_create([('3CuJb6XrBNddS79vr27SwqgR4oephY6xiJ', 100000)])
        t.sign(pk2)
        t.send(offline=True)
        self.assertTrue(t.verify())
        self.assertIsNone(t.error)

    def test_wallet_multisig_litecoin_transaction_send_offline(self):
        db_remove()
        NETWORK = 'litecoin_legacy'
        pk2 = HDKey('e2cbed99ad03c500f2110f1a3c90e0562a3da4ba0cff0e74028b532c3d69d29d', network=NETWORK)
        key_list = [
            HDKey('e9e5095d3e26643cc4d996efc6cb9a8d8eb55119fdec9fa28a684ba297528067', network=NETWORK),
            pk2.public_master(multisig=True),
            HDKey('86b77aee5cfc3a55eb0b1099752479d82cb6ebaa8f1c4e9ef46ca0d1dc3847e6',
                  network=NETWORK).public_master(multisig=True),
        ]
        wl = HDWallet.create('multisig_test_bitcoin_send', key_list, sigs_required=2, network=NETWORK,
                             databasefile=DATABASEFILE_UNITTESTS)
        wl.get_key(number_of_keys=2)
        wl.utxo_add(wl.get_key().address, 200000, '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5', 0)
        t = wl.transaction_create([('3DrP2R8XmHswUyeK9GeYgHJxvyxTfMNkid', 100000)])
        t.sign(pk2.subkey_for_path("m/45'/2/0/0"))
        t.send(offline=True)
        self.assertTrue(t.verify())
        self.assertIsNone(t.error)

    def test_wallet_multisig_2of2(self):
        """
        Create 2 cosigner wallets with 1 own private key a public key from other cosigner
        Then create and sign transaction if first wallet, import and sign it in second wallet
        and verify created transaction.

        """
        db_remove()

        keys = [
            HDKey('YXscyqNJ5YK411nwB4wzazXjJn9L9iLAR1zEMFcpLipDA25rZregBGgwXmprsvQLeQAsuTvemtbCWR1AHaPv2qmvkartoiFUU6'
                  'qu1uafT2FETtXT', network='bitcoinlib_test'),
            HDKey('YXscyqNJ5YK411nwB4EyGbNZo9eQSUWb64vAFKHt7E2LYnbmoNz8Gyjs6xc7iYAudcnkgf127NPnaanuUgyRngAiwYBcXKGsSJ'
                  'wadGhxByT2MnLd', network='bitcoinlib_test')]

        msw1 = HDWallet.create('msw1', [keys[0], keys[1].subkey_for_path("m/45'").wif_public()],
                               network='bitcoinlib_test', sort_keys=False, sigs_required=2,
                               databasefile=DATABASEFILE_UNITTESTS)
        msw2 = HDWallet.create('msw2', [keys[0].subkey_for_path("m/45'").wif_public(), keys[1]],
                               network='bitcoinlib_test', sort_keys=False, sigs_required=2,
                               databasefile=DATABASEFILE_UNITTESTS)
        msw1.new_key()
        msw2.new_key(cosigner_id=0)
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
        db_remove()
        db_remove(DATABASEFILE_UNITTESTS_2)

        keys = [
            HDKey('YXscyqNJ5YK411nwB4wzazXjJn9L9iLAR1zEMFcpLipDA25rZregBGgwXmprsvQLeQAsuTvemtbCWR1AHaPv2qmvkartoiFUU6'
                  'qu1uafT2FETtXT', network='bitcoinlib_test'),
            HDKey('YXscyqNJ5YK411nwB4EyGbNZo9eQSUWb64vAFKHt7E2LYnbmoNz8Gyjs6xc7iYAudcnkgf127NPnaanuUgyRngAiwYBcXKGsSJ'
                  'wadGhxByT2MnLd', network='bitcoinlib_test')]

        msw1 = HDWallet.create('msw1', [keys[0], keys[1].public_master(multisig=True)], network='bitcoinlib_test',
                               sort_keys=False, sigs_required=2, databasefile=DATABASEFILE_UNITTESTS)
        msw2 = HDWallet.create('msw2', [keys[0].public_master(multisig=True), keys[1]], network='bitcoinlib_test',
                               sort_keys=False, sigs_required=2, databasefile=DATABASEFILE_UNITTESTS_2)
        msw1.new_key()
        msw2.new_key(cosigner_id=msw1.cosigner_id)
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
        random_output_address = HDKey(network=network).address()

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
                    key_list.append(key_dict[key_id].public_master(multisig=True, as_private=True))
            wallet_dict[wallet_id] = HDWallet.create(
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
        db_remove()
        t = self._multisig_test(2, 3, False, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    def test_wallet_multisig_2of3_sorted(self):
        db_remove()
        t = self._multisig_test(2, 3, True, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    def test_wallet_multisig_3of5(self):
        db_remove()
        t = self._multisig_test(3, 5, False, 'bitcoinlib_test')
        self.assertTrue(t.verify())

    # Disable for now takes about 46 seconds because it needs to create 9 * 9 wallets and lots of keys
    # def test_wallet_multisig_5of9(self):
    #     if os.path.isfile(DATABASEFILE_UNITTESTS):
    #         os.remove(DATABASEFILE_UNITTESTS)
    #     t = self._multisig_test(5, 9, 'bitcoinlib_test')
    #     self.assertTrue(t.verify())

    def test_wallet_multisig_2of2_with_single_key(self):
        db_remove()
        keys = [HDKey(network='bitcoinlib_test'), HDKey(network='bitcoinlib_test', key_type='single')]
        key_list = [keys[0], keys[1].public()]

        wl = HDWallet.create('multisig_expk2', key_list, sigs_required=2, network='bitcoinlib_test',
                             databasefile=DATABASEFILE_UNITTESTS, sort_keys=False)
        wl.new_key()
        wl.new_key()
        wl.new_key_change()
        wl.utxos_update()
        self.assertEqual(wl.public_master()[1].wif, keys[1].wif())
        key_names = [k.name for k in wl.keys(is_active=False)]
        self.assertListEqual(key_names, ['Multisig Key 5/6', 'Multisig Key 8/6', 'Multisig Key 11/6'])

        t = wl.transaction_create([(HDKey(network='bitcoinlib_test').address(), 6400000)], min_confirms=0)
        t.sign(keys[1])
        t.send()
        self.assertIsNone(t.error)

    def test_wallet_multisig_sorted_keys(self):
        db_remove()
        key1 = HDKey()
        key2 = HDKey()
        key3 = HDKey()
        w1 = HDWallet.create('w1', [key1, key2.public_master(multisig=True), key3.public_master(multisig=True)],
                             sigs_required=2, databasefile=DATABASEFILE_UNITTESTS)
        w2 = HDWallet.create('w2', [key1.public_master(multisig=True), key2, key3.public_master(multisig=True)],
                             sigs_required=2, databasefile=DATABASEFILE_UNITTESTS)
        w3 = HDWallet.create('w3', [key1.public_master(multisig=True), key2.public_master(multisig=True), key3],
                             sigs_required=2, databasefile=DATABASEFILE_UNITTESTS)
        for _ in range(5):
            cosigner_id = random.randint(0, 2)
            address1 = w1.new_key(cosigner_id=cosigner_id).address
            address2 = w2.new_key(cosigner_id=cosigner_id).address
            address3 = w3.new_key(cosigner_id=cosigner_id).address
            self.assertTrue((address1 == address2 == address3),
                            'Different addressed generated: %s %s %s' % (address1, address2, address3))

    def test_wallet_multisig_sign_with_external_single_key(self):
        db_remove()
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
        wallet = HDWallet.create('Multisig-2-of-3-example', key_list, sigs_required=2, network=network,
                                 databasefile=DATABASEFILE_UNITTESTS)
        wallet.new_key()
        wallet.utxos_update()
        wt = wallet.send_to('21A6yyUPRL9hZZo1Rw4qP5G6h9idVVLUncE', 10000000)
        self.assertFalse(wt.verify())
        wt.sign(hdkey)
        self.assertTrue(wt.verify())

    def test_wallet_multisig_reopen_wallet(self):

        def _open_all_wallets():
            wl1 = wallet_create_or_open(
                'multisigmulticur1_tst', sigs_required=2, network=network,
                databasefile=DATABASEFILE_UNITTESTS, sort_keys=False,
                keys=[pk1, pk2.public_master(), pk3.public_master()])
            wl2 = wallet_create_or_open(
                'multisigmulticur2_tst', sigs_required=2, network=network,
                databasefile=DATABASEFILE_UNITTESTS, sort_keys=False,
                keys=[pk1.public_master(), pk2, pk3.public_master()])
            wl3 = wallet_create_or_open(
                'multisigmulticur3_tst', sigs_required=2, network=network,
                databasefile=DATABASEFILE_UNITTESTS, sort_keys=False,
                keys=[pk1.public_master(), pk2.public_master(), pk3])
            return wl1, wl2, wl3

        db_remove()
        network = 'litecoin'
        phrase1 = 'shop cloth bench traffic vintage security hour engage omit almost episode fragile'
        phrase2 = 'exclude twice mention orchard grit ignore display shine cheap exercise same apart'
        phrase3 = 'citizen obscure tribe index little welcome deer wine exile possible pizza adjust'
        pk1 = HDKey.from_passphrase(phrase1, multisig=True, network=network)
        pk2 = HDKey.from_passphrase(phrase2, multisig=True, network=network)
        pk3 = HDKey.from_passphrase(phrase3, multisig=True, network=network)
        wallets = _open_all_wallets()
        for wlt in wallets:
            self.assertEqual(wlt.get_key(cosigner_id=1).address, 'MQVt7KeRHGe35b9ziZo16T5y4fQPg6Up7q')
        del wallets
        wallets2 = _open_all_wallets()
        for wlt in wallets2:
            self.assertEqual(wlt.get_key(cosigner_id=1).address, 'MQVt7KeRHGe35b9ziZo16T5y4fQPg6Up7q')

    def test_wallet_multisig_network_mixups(self):
        db_remove()
        network = 'litecoin_testnet'
        phrase1 = 'shop cloth bench traffic vintage security hour engage omit almost episode fragile'
        phrase2 = 'exclude twice mention orchard grit ignore display shine cheap exercise same apart'
        phrase3 = 'citizen obscure tribe index little welcome deer wine exile possible pizza adjust'
        pk2 = HDKey.from_passphrase(phrase2, multisig=True, network=network)
        pk3 = HDKey.from_passphrase(phrase3, multisig=True, network=network)
        wlt = wallet_create_or_open(
            'multisig_network_mixups', sigs_required=2, network=network, databasefile=DATABASEFILE_UNITTESTS,
            keys=[phrase1, pk2.public_master(), pk3.public_master()],
            sort_keys=False)
        self.assertEqual(wlt.get_key().address, 'QjecchURWzhzUzLkhJ8Xijnm29Z9PscSqD')
        self.assertEqual(wlt.get_key().network.name, network)


class TestWalletKeyImport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_remove()

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
        with HDWallet.create('Multisig-2-of-3-example', key_list, sigs_required=2,
                             databasefile=DATABASEFILE_UNITTESTS) as wlt:
            wlt.new_key()
            wlt.utxos_update()
            wt = wlt.send_to('21A6yyUPRL9hZZo1Rw4qP5G6h9idVVLUncE', 10000000)
            wt.sign(hdkey)
            wt.send()
            self.assertIsNone(wt.error)

    def test_wallet_import_private_for_known_public(self):
        hdkey = HDKey(
            'xprv9s21ZrQH143K2noEZoqGHnaDDLjrnFpis8jm7NWDhkWuNNCqMupGSy7PMYtGL9jvdTY7Nx3GZ6UZ9C52nebwbYXK73imaPUK24'
            'dZJtGZhGd')
        with HDWallet.create('public-private', hdkey.public_master().public(), databasefile=DATABASEFILE_UNITTESTS) \
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
                                   databasefile=DATABASEFILE_UNITTESTS) as wlt:
            self.assertFalse(wlt.cosigner[2].main_key.is_private)
            wlt.import_key(prk3)
            self.assertTrue(wlt.cosigner[2].main_key.is_private)

    def test_wallet_import_private_for_known_public_p2sh_segwit(self):
        pk1 = HDKey('YXscyqNJ5YK411nwB3VjLYgjht3dqfKxyLdGSqNMGKhYdcK4Gh1CRSJyxS2So8KXSQrxtysS1jAmHtLnxRKa47xEiAx6hP'
                    'vrj8tuEzyeR8TQNu5e')
        pk2 = HDKey('YXscyqNJ5YK411nwB4Jo3JCQ1GZNetf4BrLJjZiqdWKVzoXwPtyJ5xyNdZjuEWtqCeSZGtmg7SuQerERwniHLYL3aVcnyS'
                    'ciEAxk7gLgDkoZC5Lq')
        w = HDWallet.create('segwit-p2sh-p2wsh-import',
                            [pk1, pk2.public_master(witness_type='p2sh-segwit', multisig=True)],
                            witness_type='p2sh-segwit', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        w.get_key()
        w.utxos_update()
        t = w.sweep('23CvEnQKsTVGgqCZzW6ewXPSJH9msFPsBt3')
        self.assertEqual(len(t.inputs[0].signatures), 1)
        self.assertFalse(t.verify())

        w.import_key(pk2)
        wc0 = w.cosigner[0]
        self.assertEqual(len(wc0.keys(is_private=False)), 0)
        t2 = w.send_to('23CvEnQKsTVGgqCZzW6ewXPSJH9msFPsBt3', 1000000)
        self.assertEqual(len(t2.inputs[0].signatures), 2)
        self.assertTrue(t2.verify())
        t3 = w.sweep('23CvEnQKsTVGgqCZzW6ewXPSJH9msFPsBt3')
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
        w = HDWallet.create('mswlt', [p1, pubk2], databasefile=DATABASEFILE_UNITTESTS, witness_type=witness_type)
        wk = w.new_key()
        self.assertEqual(wk.address, 'bc1qr7r7zpr5gqnz0zs39ve7c0g54gwe7h7322lt3kae6gh8tzc5epts0j9rhm')
        self.assertFalse(w.public_master()[1].is_private)
        self.assertEqual(w.public_master()[1].wif, wif2)
        w.import_key(p2)
        self.assertTrue(w.public_master()[1].is_private)
        self.assertEqual(w.public_master()[1].wif, 'ZprvArYK8TRL84162ECqZEwt8NsCRdN43ZVVPYTfPsKw5YfiRGWtx3AC3eXvTuk'
                                                   'CqUsKCLKQNGDV11hHi3FUQbcD9wc9g8ro64kK6H2MP4jaM7K')
        w.transactions_update()
        tx_hashes = sorted([t['tx_hash'] for t in w.transactions()])
        tx_hashes_expected = ['53b35eca3f2e767db02e4acc6c224d7a45f32158c8063f53c3d3660ab12d53ba',
                              'b6c4f286e8883927c26ce91e6cc89c7a8dd88223c111635e8e53f78c4573712a']
        self.assertListEqual(tx_hashes, tx_hashes_expected)


class TestWalletTransactions(unittest.TestCase, CustomAssertions):

    wallet = None

    @classmethod
    def setUpClass(cls):
        db_remove()
        account_key = 'tpubDCmJWqxWch7LYDhSuE1jEJMbAkbkDm3DotWKZ69oZfNMzuw7U5DwEaTVZHGPzt5j9BJDoxqVkPHt2EpUF66FrZhpfq' \
                      'ZY6DFj6x61Wwbrg8Q'
        cls.wallet = wallet_create_or_open('utxo-test', keys=account_key, network='testnet',
                                           databasefile=DATABASEFILE_UNITTESTS)
        cls.wallet.new_key()
        cls.wallet.utxos_update()

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
        wlt = wallet_create_or_open('offline-create-transaction', keys=hdkey, network='testnet',
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
        t = wlt.transaction_create([('n2S9Czehjvdmpwd2YqekxuUC1Tz5ZdK3YN', 1000)], fee=5000)
        t.sign()
        self.assertTrue(t.verify())
        del wlt

    def test_wallet_scan(self):
        account_key = 'tpubDCmJWqxWch7LYDhSuE1jEJMbAkbkDm3DotWKZ69oZfNMzuw7U5DwEaTVZHGPzt5j9BJDoxqVkPHt2EpUF66FrZhpfq' \
                      'ZY6DFj6x61Wwbrg8Q'
        self.wallet = wallet_create_or_open('scan-test', keys=account_key, network='testnet',
                                            databasefile=DATABASEFILE_UNITTESTS)
        self.wallet.scan(scan_gap_limit=10)
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
        del wlt

    def test_wallet_balance_update(self):
        wlt = HDWallet.create('test-balance-update', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        to_key = wlt.get_key()
        wlt.utxos_update()
        self.assertEqual(wlt.balance(), 200000000)

        t = wlt.send_to(to_key.address, 9000)
        self.assertEqual(wlt.balance(), 200000000 - t.fee)
        del wlt

    def test_wallet_balance_update_multi_network(self):
        passphrase = "always reward element perfect chunk father margin slab pond suffer episode deposit"
        wlt = HDWallet.create("wallet-passphrase", keys=passphrase, network='testnet',
                              databasefile=DATABASEFILE_UNITTESTS)
        wlt.get_key()
        wlt.new_account(network='bitcoinlib_test')
        wlt.get_key(network='bitcoinlib_test')
        wlt.utxos_update()
        self.assertEqual(wlt.balance(), 900)
        self.assertEqual(wlt.balance(network='testnet'), 900)
        self.assertEqual(wlt.balance(network='bitcoinlib_test'), 400000000)
        del wlt

    def test_wallet_add_dust_to_fee(self):
        # Send bitcoinlib test transaction and check if dust resume amount is added to fee
        wlt = HDWallet.create('bcltestwlt', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 99992000)
        self.assertEqual(t.fee, 8000)
        del wlt

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
        del wlt

    def test_wallet_transaction_import(self):
        wlt = HDWallet.create('bcltestwlt3', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 50000000, offline=True)
        t2 = wlt.transaction_import(t)
        self.assertDictEqualExt(t.as_dict(), t2.as_dict())
        del wlt

    def test_wallet_transaction_import_raw(self):
        wlt = HDWallet.create('bcltestwlt4', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        to_key = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(to_key.address, 50000000, offline=True)
        t2 = wlt.transaction_import_raw(t.raw())
        self.assertDictEqualExt(t.as_dict(), t2.as_dict())
        del wlt

    def test_wallet_transaction_fee_limits(self):
        wlt = HDWallet.create('bcltestwlt5', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        to_key = wlt.get_key()
        wlt.utxos_update()
        self.assertRaisesRegexp(WalletError, 'Fee per kB of 682 is lower then minimal network fee of 1000',
                                wlt.send_to, to_key.address, 50000000, fee=150)
        self.assertRaisesRegexp(WalletError, 'Fee per kB of 1365333 is higher then maximum network fee of 1000000',
                                wlt.send_to, to_key.address, 50000000, fee=300000)

    def test_wallet_transaction_fee_zero_problem(self):
        wlt = HDWallet.create(name='bcltestwlt6', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)
        nk = wlt.get_key()
        wlt.utxos_update()
        t = wlt.send_to(nk.address, 100000000)
        self.assertTrue(t.pushed)
        self.assertNotEqual(t.fee, 0)

    def test_wallet_transactions_estimate_size(self):
        prev_tx_hash = '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5'

        for witness_type in ['legacy', 'p2sh-segwit', 'segwit']:
            wallet_delete_if_exists('wallet_estimate_size', force=True, databasefile=DATABASEFILE_UNITTESTS)
            wl3 = HDWallet.create('wallet_estimate_size', witness_type=witness_type,
                                  databasefile=DATABASEFILE_UNITTESTS)
            wl3.utxo_add(wl3.get_key().address, 110000, prev_tx_hash, 0)
            to_address = wl3.get_key_change().address
            t = wl3.transaction_create([(to_address, 90000)], fee=10000)
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

            wallet_delete_if_exists('wallet_estimate_size_multisig', force=True, databasefile=DATABASEFILE_UNITTESTS)
            wl3 = HDWallet.create('wallet_estimate_size_multisig', [p1, p2.public_master(), p3.public_master()],
                                  sigs_required=2, databasefile=DATABASEFILE_UNITTESTS)
            wl3.utxo_add(wl3.get_key().address, 110000, prev_tx_hash, 0)
            to_address = wl3.get_key_change().address
            t = wl3.transaction_create([(to_address, 90000)], fee=10000)
            t.estimate_size()
            size1 = t.size
            t.sign(p2)
            t.estimate_size()
            size2 = t.size
            self.assertAlmostEqual(size1, size2, delta=3)
            self.assertAlmostEqual(len(t.raw()), size2, delta=3)


class TestWalletDash(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_remove()

    def test_wallet_create_with_passphrase_dash(self):
        passphrase = "always reward element perfect chunk father margin slab pond suffer episode deposit"
        wlt = HDWallet.create("wallet-passphrase-litecoin", keys=passphrase, network='dash',
                              databasefile=DATABASEFILE_UNITTESTS)
        keys = wlt.get_key(number_of_keys=5)
        self.assertEqual(keys[4].address, "XhxXcRvTm4yZZzbH4MYz2udkdHWEMMf9GM")

    def test_wallet_import_dash(self):
        accountkey = 'xprv9yQgG6Z38AXWuhkxScDCkLzThWWZgDKHKinMHUAPTH1uihrBWQw99sWBsN2HMpzeTze1YEYb8acT1x7sHKhXX8AbT' \
                     'GNf8tdbycySUi2fRaa'
        wallet = HDWallet.create(
            databasefile=DATABASEFILE_UNITTESTS,
            name='test_wallet_import_dash',
            keys=accountkey,
            network='dash')
        newkey = wallet.get_key()
        self.assertEqual(wallet.main_key.wif, accountkey)
        self.assertEqual(newkey.address, u'XtVa6s1rqo9BNXir1tb6KEXsj5NGogp1QB')
        self.assertEqual(newkey.path, "M/0/0")

    def test_wallet_multisig_dash(self):
        network = 'dash'
        pk1 = HDKey(network=network)
        pk2 = HDKey(network=network)
        wl1 = HDWallet.create('multisig_test_wallet1', [pk1, pk2.public_master(multisig=True)], sigs_required=2,
                              databasefile=DATABASEFILE_UNITTESTS)
        wl2 = HDWallet.create('multisig_test_wallet2', [pk1.public_master(multisig=True), pk2], sigs_required=2,
                              databasefile=DATABASEFILE_UNITTESTS)
        wl1_key = wl1.new_key()
        wl2_key = wl2.new_key(cosigner_id=wl1.cosigner_id)
        self.assertEqual(wl1_key.address, wl2_key.address)

    def test_wallet_import_private_for_known_public_multisig_dash(self):
        network = 'dash'
        pk1 = HDKey(network=network)
        pk2 = HDKey(network=network)
        pk3 = HDKey(network=network)
        with wallet_create_or_open("mstest_dash", [pk1.public_master(multisig=True), pk2.public_master(multisig=True),
                                                   pk3.public_master(multisig=True)], 2, network=network,
                                   sort_keys=False, databasefile=DATABASEFILE_UNITTESTS) as wlt:
            self.assertFalse(wlt.cosigner[1].main_key.is_private)
            wlt.import_key(pk2)
            self.assertTrue(wlt.cosigner[1].main_key.is_private)


class TestWalletSegwit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_remove()

    def test_wallet_segwit_create_p2pkh(self):
        phrase = 'depth child sheriff attack when purpose velvet stay problem lock myself praise'
        wlt = wallet_create_or_open('thetestwallet-bech32', keys=phrase, network='bitcoin', witness_type='segwit',
                                    databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(wlt.get_key().address, 'bc1q0xjnzddk8t4rnujmya8zgvxuct5s04my0fde3e')

    def test_wallet_segwit_create_pswsh(self):
        phrase1 = 'exclude twice mention orchard grit ignore display shine cheap exercise same apart'
        phrase2 = 'shop cloth bench traffic vintage security hour engage omit almost episode fragile'
        pk1 = HDKey.from_passphrase(phrase1, witness_type='segwit', multisig=True)
        pk2 = HDKey.from_passphrase(phrase2, witness_type='segwit', multisig=True)
        w = HDWallet.create('multisig-segwit', [pk1, pk2.public_master()], sigs_required=1, witness_type='segwit',
                            databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.get_key().address, 'bc1qfjhmzzt9l6dmm0xx3tc6qrtff8dve7j7qrcyp88tllszm97r84aqxel5jk')

    def test_wallet_segwit_create_p2sh_p2wsh(self):
        phrase1 = 'exclude twice mention orchard grit ignore display shine cheap exercise same apart'
        phrase2 = 'shop cloth bench traffic vintage security hour engage omit almost episode fragile'
        pk1 = HDKey.from_passphrase(phrase1)
        pk2 = HDKey.from_passphrase(phrase2)
        w = HDWallet.create('segwit-p2sh-p2wsh', [pk1, pk2.public_master(witness_type='p2sh-segwit', multisig=True)],
                            sigs_required=2, witness_type='p2sh-segwit', databasefile=DATABASEFILE_UNITTESTS)
        nk = w.get_key()
        self.assertEqual(nk.address, '3JFyRjKWYFz5BMFHLZvT7EZQJ85gLFvtkT')
        self.assertEqual(nk.key_type, 'multisig')
        self.assertEqual(nk.path, "m/48'/0'/0'/1'/0/0")

    def test_wallet_segwit_create_p2sh_p2wpkh(self):
        phrase = 'fun brick apology sport museum vague once gospel walnut jump spawn hedgehog'
        w = wallet_create_or_open('segwit-p2sh-p2wpkh', phrase, purpose=49, witness_type='p2sh-segwit',
                                  network='bitcoin', databasefile=DATABASEFILE_UNITTESTS)

        k1 = w.get_key()
        address = '3Disr2CmERuYuuMkkfGrjRUHqDENQvtNep'
        self.assertEqual(Address(b'\x00\x14' + k1.key().hash160(), script_type='p2sh').address, address)
        self.assertEqual(Address(k1.key().public_byte, script_type='p2sh_p2wpkh').address, address)
        self.assertEqual(k1.address, address)

    def test_wallet_segwit_p2wpkh_send(self):
        w = HDWallet.create('segwit_p2wpkh_send', witness_type='segwit', network='bitcoinlib_test',
                            databasefile=DATABASEFILE_UNITTESTS)
        w.get_key()
        w.utxos_update()
        t = w.send_to('blt1q7ywlg3lsyntsmp74jh65pnkntk3csagdwpz78k', 10000)
        self.assertEqual(t.witness_type, 'segwit')
        self.assertEqual(t.inputs[0].script_type, 'sig_pubkey')
        self.assertEqual(t.inputs[0].witness_type, 'segwit')
        self.assertTrue(t.verified)
        self.assertTrue(t.pushed)

    def test_wallet_segwit_p2wsh_send(self):
        w = HDWallet.create('segwit_p2wsh_send', witness_type='segwit', network='bitcoinlib_test',
                            keys=[HDKey(network='bitcoinlib_test'), HDKey(network='bitcoinlib_test')], sigs_required=2,
                            databasefile=DATABASEFILE_UNITTESTS)
        w.get_key()
        w.utxos_update()
        t = w.send_to('blt1q7r60he62p52u6h9zyxl6ew4dmmshpmk5sluaax48j9c7zyxu6m0smrjqxa', 10000)
        self.assertEqual(t.witness_type, 'segwit')
        self.assertEqual(t.inputs[0].script_type, 'p2sh_multisig')
        self.assertEqual(t.inputs[0].witness_type, 'segwit')
        self.assertTrue(t.verified)
        self.assertTrue(t.pushed)

    def test_wallet_segwit_p2sh_p2wpkh_send(self):
        w = HDWallet.create('segwit_p2sh_p2wpkh_send', witness_type='p2sh-segwit', network='bitcoinlib_test',
                            databasefile=DATABASEFILE_UNITTESTS)
        w.get_key()
        w.utxos_update()
        t = w.send_to('blt1q7ywlg3lsyntsmp74jh65pnkntk3csagdwpz78k', 10000)
        self.assertEqual(t.witness_type, 'segwit')
        self.assertEqual(t.inputs[0].script_type, 'sig_pubkey')
        self.assertEqual(t.inputs[0].witness_type, 'p2sh-segwit')
        self.assertTrue(t.verified)
        self.assertTrue(t.pushed)

    def test_wallet_segwit_p2sh_p2wsh_send(self):
        w = HDWallet.create('segwit_p2sh_p2wsh_send', witness_type='p2sh-segwit', network='bitcoinlib_test',
                            keys=[HDKey(network='bitcoinlib_test'), HDKey(network='bitcoinlib_test'),
                                  HDKey(network='bitcoinlib_test')], sigs_required=2,
                            databasefile=DATABASEFILE_UNITTESTS)
        w.get_key()
        w.utxos_update()
        t = w.send_to('blt1q7ywlg3lsyntsmp74jh65pnkntk3csagdwpz78k', 10000)
        self.assertEqual(t.witness_type, 'segwit')
        self.assertEqual(t.inputs[0].script_type, 'p2sh_multisig')
        self.assertEqual(t.inputs[0].witness_type, 'p2sh-segwit')
        self.assertTrue(t.verified)
        self.assertTrue(t.pushed)

    def test_wallet_segwit_uncompressed_error(self):
        k = HDKey(compressed=False)
        self.assertRaisesRegexp(BKeyError, 'Uncompressed keys are non-standard', wallet_create_or_open,
                                'segwit_uncompressed_error', k, witness_type='segwit', network='bitcoinlib_test',
                                databasefile=DATABASEFILE_UNITTESTS)

    def test_wallet_segwit_bitcoin_send(self):
        # Create several SegWit wallet and create transaction to send to each other. Uses utxo_add() method to create
        # test UTXO's

        prev_tx_hash = '46fcfdbdc3573756916a0ced8bbc5418063abccd2c272f17bf266f77549b62d5'

        # === Segwit P2WSH to P2WSH ===
        pk2 = HDKey()
        key_list = [
            HDKey(),
            pk2.public_master(witness_type='segwit', multisig=True),
            HDKey().public_master(witness_type='segwit', multisig=True),
        ]

        wl1 = HDWallet.create('segwit_bitcoin_p2wsh_send', key_list, sigs_required=2, witness_type='segwit',
                              databasefile=DATABASEFILE_UNITTESTS)
        wl1.utxo_add(wl1.get_key().address, 10000000, prev_tx_hash, 0)
        to_address = wl1.get_key_change().address
        t = wl1.transaction_create([(to_address, 100000)], fee=10000)

        t.sign(pk2.subkey_for_path("m/48'/0'/0'/2'/0/0"))
        self.assertTrue(t.verify())
        self.assertEqual(t.outputs[0].address, to_address)
        self.assertFalse(t.error)

        # === Segwit P2WPKH to P2WSH ===
        wl2 = HDWallet.create('segwit_bitcoin_p2wpkh_send', witness_type='segwit', databasefile=DATABASEFILE_UNITTESTS)
        wl2.utxo_add(wl2.get_key().address, 200000, prev_tx_hash, 0)
        to_address = wl1.get_key_change().address
        t = wl2.transaction_create([(to_address, 100000)], fee=10000)
        t.sign()
        self.assertTrue(t.verify())
        self.assertEqual(t.outputs[0].address, to_address)
        self.assertFalse(t.error)

        # === Segwit P2SH-P2WPKH to P2WPK ===
        wl3 = HDWallet.create('segwit_bitcoin_p2sh_p2wpkh_send', witness_type='p2sh-segwit',
                              databasefile=DATABASEFILE_UNITTESTS)
        wl3.utxo_add(wl3.get_key().address, 110000, prev_tx_hash, 0)
        t = wl3.transaction_create([(to_address, 100000)], fee=10000)
        t.sign()
        self.assertTrue(t.verify())
        self.assertEqual(t.outputs[0].address, to_address)
        self.assertFalse(t.error)

    def test_wallet_segwit_litecoin_multi_accounts(self):
        phrase = 'rug rebuild group coin artwork degree basic humor flight away praise able'
        w = HDWallet.create('segwit_wallet_litecoin_p2wpkh', keys=phrase, network='litecoin',
                            databasefile=DATABASEFILE_UNITTESTS, witness_type='segwit')
        self.assertEqual(w.get_key().address, "ltc1qsrzxzg39jyt8knsw5hlqmpwmuc8ejxvp9hfch8")
        self.assertEqual(w.get_key_change().address, "ltc1q9n6zknsw2hhq7dkyvczars8vl8zta5yusjjem5")
        acc2 = w.new_account()
        btc_acc = w.new_account(network='bitcoin')
        self.assertEqual(w.get_key(acc2.account_id).address, "ltc1quya06p0ywk55rvf6jjpvxwmd66n2axu8qhnned")
        self.assertEqual(w.get_key(btc_acc.account_id, network='bitcoin').address,
                         "bc1qnxntu52qfppmt2l2wezrn8rtsqy092q3utxhgd")

        phrase = 'rug rebuild group coin artwork degree basic humor flight away praise able'

        w = HDWallet.create('segwit_wallet_litecoin_p2sh_p2wpkh', keys=phrase, network='litecoin',
                            databasefile=DATABASEFILE_UNITTESTS, witness_type='p2sh-segwit')
        self.assertEqual(w.get_key().address, "MW1V5XPPW1YYQ5BGL5mSWEZNZSyD4XQPgh")
        self.assertEqual(w.get_key_change().address, "MWQoYMDTNvwZPNNypLMzkQ7JNSCtvS554j")

    def test_wallet_segwit_litecoin_sweep(self):
        phrase = 'wagon tunnel garage blast eager jaguar shop bring lake dumb chalk emerge'
        w = wallet_create_or_open('ltcsw', phrase, network='litecoin', witness_type='segwit',
                                  databasefile=DATABASEFILE_UNITTESTS)
        w.utxo_add('ltc1qu8dum66gd6dfr2cchgenf87qqxgenyme2kyhn8', 28471723,
                   '21da13be453624cf46b3d883f39602ce74d04efa7a186037898b6d7bcfd405ee', 10, 99)
        t = w.sweep('MLqham8sXULvktmNMuDQdrBbHRdytVZ1QK', offline=True)
        self.assertTrue(t.verified)

    def test_wallet_segwit_litecoin_multisig(self):
        p1 = 'only sing document speed outer gauge stand govern way column material odor'
        p2 = 'oyster pelican debate mass scene title pipe lock recipe flavor razor accident'
        w = wallet_create_or_open('ltcswms', [p1, p2], network='litecoin', witness_type='segwit',
                                  databasefile=DATABASEFILE_UNITTESTS)
        w.get_key(number_of_keys=2)
        w.utxo_add('ltc1qkewaz7lxn75y6wppvqlsfhrnq5p5mksmlp26n8xsef0556cdfzqq2uhdrt', 2100000000000001,
                   '21da13be453624cf46b3d883f39602ce74d04efa7a186037898b6d7bcfd405ee', 0, 15)

        t = w.sweep('ltc1q9h8xvtrge5ttcwzy3xtz7l8kj4dewgh6hgqfjdhtq6lwr4k3527qd8tyzs', offline=True)
        self.assertTrue(t.verified)

    def test_wallet_segwit_multisig_multiple_inputs(self):
        main_key = HDKey(network='bitcoinlib_test')
        cosigner = HDKey(network='bitcoinlib_test')
        w = wallet_create_or_open('test_wallet_segwit_multisig_multiple_inputs',
                                  [main_key, cosigner.public_master(witness_type='segwit', multisig=True)],
                                  witness_type='segwit', network='bitcoinlib_test', databasefile=DATABASEFILE_UNITTESTS)

        w.get_key(number_of_keys=2)
        w.utxos_update()
        to = w.get_key_change()
        t = w.sweep(to.address, offline=True)
        t.sign(cosigner)
        self.assertTrue(t.verify())

    def test_wallet_segwit_multiple_account_paths(self):
        pk1 = HDKey(
            "ZprvAhadJRUYsNge9JCXTr7xphZaR6sW3HEeSQL7wgtEXceG5hoUViB9KQ4EX6hAdgziW7MorQAjyasWYirrCQrb3ySHaPBa8EiLTx"
            "t4LmqTyzp")
        pk2 = HDKey(
            "ZprvAhadJRUYsNgeBbjftwKvAhDEV1hrYBGY19wATHqnEt5jfWXxXChYP8Qfnw3w2zJZskNercma5S1fWYH7e7XwbTVPgbabvs1CfU"
            "zY2KQD2cB")
        w = HDWallet.create("account-test", keys=[pk1, pk2.public_master(multisig=True)], witness_type='segwit',
                            databasefile=DATABASEFILE_UNITTESTS)
        w.new_account()
        w.new_account()
        w.new_account(account_id=100)
        self.assertRaisesRegexp(WalletError, "Account with ID 100 already exists for this wallet",
                                w.new_account, 'test', 100)
        paths = ["m/48'/0'/0'/2'", "m/48'/0'/0'/2'/0/0", "m/48'/0'/0'/2'/1/0", "m/48'/0'/1'/2'", "m/48'/0'/1'/2'/0/0",
                 "m/48'/0'/1'/2'/1/0", "m/48'/0'/100'/2'", "m/48'/0'/100'/2'/0/0", "m/48'/0'/100'/2'/1/0"]
        self.assertListEqual(sorted(paths), sorted([k.path for k in w.keys()]))
        self.assertListEqual(w.accounts(), [0, 1, 100])

    def test_wallet_segwit_multiple_networks_accounts(self):
        pk1 = 'surround vacant shoot aunt acoustic liar barely you expand rug industry grain'
        pk2 = 'defy push try brush ceiling sugar film present goat settle praise toilet'
        wallet = HDWallet.create(keys=[pk1, pk2], network='bitcoin', name='test_wallet_multicurrency',
                                 witness_type='segwit', databasefile=DATABASEFILE_UNITTESTS, encoding='base58')
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
        self.assertEqual(wallet.keys(network='litecoin')[0].address, "MQNA8FYrN2fvD7SSYny3Ccvpapvsu9cVJH")
        self.assertEqual(wallet.keys(network='bitcoin')[0].address, "3L6XFzC6RPeXSFpZS8v4S86v4gsNmKFnFT")


class TestWalletKeyStructures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_remove()

    def test_wallet_path_expand(self):
        wlt = wallet_create_or_open('wallet_path_expand', network='bitcoin', databasefile=DATABASEFILE_UNITTESTS)
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
        self.assertRaisesRegexp(BKeyError, "Please provide value for 'address_index'",
                                wlt.path_expand, ['m', 45, "cosigner_index", 55, "address_index"])
        self.assertRaisesRegexp(BKeyError, "Variable bestaatnie not found in Key structure definitions in main.py",
                                wlt.path_expand, ['m', "bestaatnie'", "coin_type'", "1", 2, 3])

    def test_wallet_exotic_key_paths(self):
        w = HDWallet.create("simple_custom_keypath", key_path="m/change/address_index",
                            databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.new_key().path, "m/0/1")
        self.assertEqual(w.new_key_change().path, "m/1/0")
        self.assertEqual(w.wif()[:4], 'xpub')

        w = HDWallet.create(
            "strange_key_path", keys=[HDKey(), HDKey()], purpose=100,
            key_path="m/purpose'/cosigner_index/change/address_index",
            databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.new_key().path, "m/100'/0/0/0")
        self.assertEqual(w.new_key_change().path, "m/100'/0/1/0")

        wif1 = 'Zpub74CSuvLPQxWkdW7bivQAhomXZTzbE8quAakKRg1C3x7uDcCCeh7zPp1tZrtJrscihJRASZWjZQ7nPQj1SHTn8gkzAHPZL3dC' \
               'MbMQLFwMKVV'
        wif2 = 'Zpub75J84sqDUenYwh6eYwFnpXmfRMkfCwyEUBsN6fkGLQhh4nGmdxHw1io3AcUvAcK14RXosXfjG6Gfkz3NUHCa1JESGCf52ZWQ' \
               'd2CqDgo1rLa'
        w = HDWallet.create(
            "long_key_path", keys=[wif1, wif2], witness_type='segwit', cosigner_id=1,
            key_path="m/purpose'/coin_type'/account'/script_type'/cosigner_index/change/address_index",
            databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.new_key().path, "M/1/0/0")
        self.assertEqual(w.new_key_change().path, "M/1/1/0")
        self.assertEqual(w.public_master()[0].wif, wif1)
        self.assertEqual(w.public_master()[1].wif, wif2)


class TestWalletReadonlyAddress(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_remove()

    def test_wallet_readonly_create_and_import(self):
        k = '13A1W4jLPP75pzvn2qJ5KyyqG3qPSpb9jM'
        w = wallet_create_or_open('addrwlt', k, databasefile=DATABASEFILE_UNITTESTS)
        addr = Address.import_address('13CiNuEMKASJBvGdupqaoRs2MqDNhAqmce')
        w.import_key(addr)
        w.utxos_update()
        self.assertListEqual(w.addresslist(),
                             ['13A1W4jLPP75pzvn2qJ5KyyqG3qPSpb9jM', '13CiNuEMKASJBvGdupqaoRs2MqDNhAqmce'])
        # FIXME: Value should be greater then 10000000000, but some service providers do not return all utxo's
        self.assertGreater(w.balance(), 1000000)
        self.assertRaisesRegexp(WalletError, "No unspent", w.send_to, '1ApcyGtcX4DUmfGqPBPY1bvKEh2irLqnhp', 50000)

    def test_wallet_address_import_public_key(self):
        wif = 'xpub661MyMwAqRbcFCwFkcko75u2VEinbG1u5U4nq8AFJq4AbLPEvwcmhZGgGcnDcEBpcfAFEP8vVhbJJvX1ieGWdoaa5AnHfyB' \
              'DAY95TfYH6H6'
        address = '1EJiPa66sT4PCDCFnc7oRnpWebAogPqppr'
        w = HDWallet.create('test_wallet_address_import_public_key', address, databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.addresslist(), [address])
        self.assertIsNone(w.main_key.key_public)
        w.import_key(wif)
        self.assertEqual(w.main_key.key_public, '0225248feed626f2496276109329f1ce30225e7a3153fe24b5c56828b0773bae75')

    def test_wallet_address_import_public_key_segwit(self):
        address = 'bc1q84xq6lrzr09t3h2pw5ys5zee7rn3mxh5v65732'
        wif = 'zprvAWgYBBk7JR8Gj9CNFRBUq3DvNHDbZhH4L6AybFSTCH7DDW6boPyiQfTigAPhJma5wC4TP1o53Gz1XLh94xD3dVQUpsFDaCb2' \
              '9XmDQKBwKhz'
        w = HDWallet.create('test_wallet_address_import_public_key_segwit', address, databasefile=DATABASEFILE_UNITTESTS)
        self.assertEqual(w.addresslist(), [address])
        self.assertIsNone(w.main_key.wif)
        w.import_key(wif)
        self.assertEqual(w.main_key.wif, wif)

    def test_wallet_address_import_private_key(self):
        wif = 'xprv9s21ZrQH143K2irnebDnjwxHwCtJBoJ3iF9C2jkdkVXBiY46PQJX9kxCRMVcM1YXLERWUiUBoxQEUDqFAKbrTaL9FB4HfRY' \
              'jsGgCGpRPWTy'
        address = '1EJiPa66sT4PCDCFnc7oRnpWebAogPqppr'
        w = HDWallet.create('test_wallet_address_import_private_key', address, databasefile=DATABASEFILE_UNITTESTS)
        self.assertListEqual(w.addresslist(), [address])
        self.assertFalse(w.main_key.is_private)
        w.import_key(wif)
        self.assertTrue(w.main_key.is_private)
