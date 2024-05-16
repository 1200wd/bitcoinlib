# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Using Bitcoin Core wallets with Bitcoinlib
#
#    Method 2 - Create wallet in Bitcoin Core, export public keys to bitcoinlib and easily manage wallet from bitcoinlib.
#
#    © 2024 May - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.wallets import *
from bitcoinlib.services.bitcoind import BitcoindClient

#
# Settings and Initialization
#

# Create wallet in Bitcoin Core and export descriptors
# $ bitcoin-cli createwallet wallet_bitcoincore2
# $ bitcoin-cli -rpcwallet=wallet_bitcoincore2 listdescriptors

# Now copy the descriptor of the public master key, which looks like: wpkh([.../84h/1h/0h]
pkwif = 'tpubDDuQM8y9z4VQW5FS13BXGMxUwkUKEXc8KG5xzzbe6UsssrJDKJEygqbgMATnn6ZDwLXQ5PQipH989qWRTzFhPPZMiHxYYrG14X34vc24pD6'

# You can create the wallet and manage it from bitcoinlib
w = wallet_create_or_open("wallet_bitcoincore2", keys=pkwif, witness_type='segwit')
w.providers=['bitcoind']
w.scan(scan_gap_limit=1)
w.info()
