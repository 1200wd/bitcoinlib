# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Mnemonic Wallets
#
#    © 2018 February - 1200 Web Development <http://1200wd.com/>
#

import os
from pprint import pprint
from bitcoinlib.wallets import HDWallet, DEFAULT_DATABASEDIR
from bitcoinlib.mnemonic import Mnemonic
try:
    input = raw_input
except NameError:
    pass

#
# Create Wallets
#

# First recreate database to avoid already exist errors
test_databasefile = 'bitcoinlib.test.sqlite'
test_database = DEFAULT_DATABASEDIR + test_databasefile
if os.path.isfile(test_database):
    os.remove(test_database)

print("\n=== Create a simple Mnemonic wallet ===")
passphrase = Mnemonic().generate()
print("Your private key passphrase is:", passphrase)
password = input("Enter password to protect passphrase: ")
wlt = HDWallet.create('mnwlttest1', key=passphrase, password=password, network='bitcoinlib_test',
                      databasefile=test_database)
wlt.get_key()
wlt.utxos_update()  # Create some test UTXOs
wlt.info()
to_key = wlt.get_key()
print("\n- Create transaction (send to own wallet)")
t = wlt.send_to(to_key.address, 50000000)
t.info()

print("\n- Successfully send, updated wallet info:")
wlt.info()
