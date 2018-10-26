# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Bitcoinlib Network Class
#    © 2018 August - 1200 Web Development <http://1200wd.com/>
#

import unittest
from bitcoinlib.networks import *


class TestNetworks(unittest.TestCase):

    def test_networks_prefix_wif_network_by_value(self):
        self.assertEqual(network_by_value('prefix_wif', '80'), ['bitcoin'])

    def test_networks_prefix_bech32_network_by_value(self):
        self.assertEqual(network_by_value('prefix_bech32', 'tb'), ['testnet'])

    def test_networks_prefix_bech32_network_by_value_sorted(self):
        self.assertEqual(network_by_value('prefix_bech32', 'ltc'), ['litecoin', 'litecoin_legacy'])

    def test_networks_prefix_hdkey_wif(self):
        network = Network('bitcoin')
        self.assertEqual(network.prefix_hdkey_private, b'\x04\x88\xad\xe4')

    def test_networks_print_value(self):
        network = Network('dash')
        self.assertEqual(network.print_value(10000), '0.00010000 DASH')


if __name__ == '__main__':
    unittest.main()
