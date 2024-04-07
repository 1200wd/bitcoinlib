# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Using Bitcoin Core wallets with Bitcoinlib
#
#    © 2024 April - 1200 Web Development <http://1200wd.com/>
#

import os
from bitcoinlib.wallets import wallet_create_or_open
from bitcoinlib.services.bitcoind import BitcoindClient

#
# Settings and Initialization
#

# Generate your own private key with: HDKey(network='testnet').wif_private()
pkwif = 'vprv9DMUxX4ShgxMKxHYfZ7Z35RxRLC9Av59MyJaMmCFRqfvUdUZdBB1awTDvTfDzZbtsPzZVCcpCunaELcuPsnLeLMg634hsxSSvwpTdfgCYMX'
# Put connection string with format http://bitcoinlib:password@localhost:18332)
# to Bitcoin Core node in the following file:
bitcoind_url = open(os.path.join(os.path.expanduser('~'), ".bitcoinlib/.bitcoind_connection_string")).read()
bcc = BitcoindClient(base_url=bitcoind_url)
lastblock = bcc.proxy.getblockcount()
print("Connected to bitcoind, last block: " + str(lastblock))

#
# Create Wallets
#




#
# Using wallets
#

