# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Using Bitcoin Core wallets with Bitcoinlib
#
#    Method 2 - ...
#
#    © 2024 April - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.wallets import *
from bitcoinlib.services.bitcoind import BitcoindClient

#
# Settings and Initialization
#

pkwif = 'cTAyLb37Sr4XQPzWCiwihJxdFpkLKeJBFeSnd5hwNiW8aqrbsZCd'

w = wallet_create_or_open("wallet_bitcoincore2", keys=pkwif, network='testnet', witness_type='segwit',
                          key_path=KEY_PATH_BITCOINCORE)
w.providers=['bitcoind']
w.get_key()
w.scan(scan_gap_limit=1)
w.info()

# TODO
# FIXME
