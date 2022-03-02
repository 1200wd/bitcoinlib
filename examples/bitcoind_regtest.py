# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Bitcoind regtest network example
#
#    © 2022 Februari - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.services.bitcoind import *
from pprint import pprint

bdc = BitcoindClient(base_url='http://rpcuser:pwd@localhost:18444')

print("Current blockheight is %d" % bdc.proxy.getblockcount())
address = bdc.proxy.getnewaddress()
print("Mine 50 blocks and generate regtest coins to address %s" % address)
bdc.proxy.generatetoaddress(50, address)
print("Current blockheight is %d" % bdc.proxy.getblockcount())

address2 = bdc.proxy.getnewaddress()
print("Send 10 rBTC to address %s" % address2)
bdc.proxy.settxfee(0.00002500)
txid = bdc.proxy.sendtoaddress(address2, 10)
print("Resulting txid: %s" % txid)
tx = bdc.proxy.gettransaction(txid)
pprint(tx)
