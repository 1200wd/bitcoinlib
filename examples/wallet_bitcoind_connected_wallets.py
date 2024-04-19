# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Using Bitcoin Core wallets with Bitcoinlib
#
#    Method 1 - Create wallet in Bitcoin Core and use the same wallet in Bitcoinlib using the bitcoin node to
#    receive and send bitcoin transactions.
#
#    © 2024 April - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.wallets import *
from bitcoinlib.services.bitcoind import BitcoindClient

#
# Settings and Initialization
#

# Call bitcoin-cli dumpwallet and look for extended private masterkey at top off the export. Then copy the
# bitcoin core node masterseed here:
pkwif = 'tprv8ZgxMBicQKsPe2iVrERVdAgjcqHhxvZcWeS2Va6nvgddpDH1r33A4aTtdYYkoFDY6CCf5fogwLYmAdQQNxkk7W3ygwFd6hquJVLmmpbJRp2'
enable_verify_wallet = False

# Put connection string with format http://bitcoinlib:password@localhost:18332)
# to Bitcoin Core node in the following file:
bitcoind_url = open(os.path.join(os.path.expanduser('~'), ".bitcoinlib/.bitcoind_connection_string")).read()
bcc = BitcoindClient(base_url=bitcoind_url)
lastblock = bcc.proxy.getblockcount()
print("Connected to bitcoind, last block: " + str(lastblock))

#
# Create a copy of the Bitcoin Core Wallet in Bitcoinlib
#
w = wallet_create_or_open('wallet_bitcoincore', pkwif, network='testnet', witness_type='segwit',
                          key_path=KEY_PATH_BITCOINCORE)
addr = bcc.proxy.getnewaddress()
addrinfo = bcc.proxy.getaddressinfo(addr)
bcl_addr = w.key_for_path(addrinfo['hdkeypath']).address

# Verify if we are using the same wallet
if enable_verify_wallet and addr == bcl_addr:
    print("Address %s with path %s, is identical in Bitcoin core and Bitcoinlib" % (addr, addrinfo['hdkeypath']))
elif not addr == bcl_addr:
    print ("Address %s with path %s, is NOT identical in Bitcoin core and Bitcoinlib" % (addr, addrinfo['hdkeypath']))
    raise ValueError("Wallets not identical in Bitcoin core and Bitcoinlib")

#
# Using wallets
#

# Now pick an address from your wallet and send some testnet coins to it, for example by using another wallet or a
# testnet faucet.
w.providers = ['bitcoind']
w.scan()
# w.info()

if not w.balance():
    print("No testnet coins available")
else:
    print("Found testnet coins. Wallet balance: %d" % w.balance())
    # Send some coins to our own wallet
    t = w.send_to(w.get_key().address, 1000, fee=200, broadcast=True)
    t.info()

# If you now run bitcoin-cli listunspent 0, you should see the 1 or 2 new utxo's for this transaction.
