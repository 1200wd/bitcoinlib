# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Service Class
#    © 2017 March - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.services.services import *


class TestService(unittest.TestCase):

    def test_transaction_bitcoin_testnet_get_raw(self):
        tx_id = 'd3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955'
        raw_tx = '0100000001a3919372c9807d92507289d71bdd38f10682a49c47e50dc0136996b43d8aa54e010000006a47304402201f6e' \
                 '18f4532e14f328bc820cb78c53c57c91b1da9949fecb8cf42318b791fb38022045e78c9e55df1cf3db74bfd52ff2add2b5' \
                 '9ba63e068680f0023e6a80ac9f51f401210239a18d586c34e51238a7c9a27a342abfb35e3e4aa5ac6559889db1dab2816e' \
                 '9dfeffffff023ef59804000000001976a914af8e14a2cecd715c363b3a72b55b59a31e2acac988ac90940d000000000019' \
                 '76a914f0d34949650af161e7cb3f0325a1a8833075165088acb7740f00'
        self.assertEqual(raw_tx, Service(network='testnet').getrawtransaction(tx_id))

    def test_transaction_bitcoin_get_raw(self):
        tx_id = 'b7feea5e7c79d4f6f343b5ca28fa2a1fcacfe9a2b7f44f3d2fd8d6c2d82c4078'
        raw_tx = '01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff5d0342fe06244d69' \
                 '6e656420627920416e74506f6f6c20626a31312f4542312f4144362f432058d192b6fabe6d6defcf958e3cf9814240e00f' \
                 'a5e36e8cc319cd8141e20890607ccb1954e64843d804000000000000003914000057190200ffffffff013b33b158000000' \
                 '001976a914338c84849423992471bffb1a54a8d9b1d69dc28a88ac00000000'
        self.assertEqual(raw_tx, Service().getrawtransaction(tx_id))

    def test_transaction_bitcoin_decode_raw(self):
        raw_tx = '101000000010000000000000000000000000000000000000000000000000000000000000000ffffffff5d0342fe06244d69' \
                 '6e656420627920416e74506f6f6c20626a31312f4542312f4144362f432058d192b6fabe6d6defcf958e3cf9814240e00f' \
                 'a5e36e8cc319cd8141e20890607ccb1954e64843d804000000000000003914000057190200ffffffff013b33b158000000' \
                 '001976a914338c84849423992471bffb1a54a8d9b1d69dc28a88ac00000000'
        self.assertTrue(Service().decoderawtransaction(raw_tx))

    def test_get_balance(self):
        srv = Service(min_providers=5)
        srv.getbalance('15gHNr4TCKmhHDEG31L2XFNvpnEcnPSQvd')
        prev = None
        for sb in srv.results:
            balance = list(sb.values())[0]
            if prev is not None and balance != prev:
                self.fail('Different address balance from service providers: %d != %d' % (balance, prev))
            else:
                prev = balance
