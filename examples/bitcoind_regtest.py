# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Bitcoind regtest network example
#
#    © 2023 December - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.services.bitcoind import *
from bitcoinlib.wallets import wallet_create_or_open
from bitcoinlib.services.services import Service
from pprint import pprint

bdc = BitcoindClient(base_url='http://rpcuser:pwd@localhost:18444')

walletname = 'regtesttestwallet'
walletbcl = 'regtestwallet'

print("Current blockheight is %d" % bdc.proxy.getblockcount())

print("Open or create a new wallet")
wallets = bdc.proxy.listwallets()
if walletname not in wallets:
    wallet = bdc.proxy.createwallet(walletname)

address = bdc.proxy.getnewaddress()
print("Mine 50 blocks and generate regtest coins to address %s" % address)
bdc.proxy.generatetoaddress(50, address)

print("Current blockheight is %d" % bdc.proxy.getblockcount())
print("Current balance is %d" % bdc.proxy.getbalance())

w = wallet_create_or_open(walletname, network='regtest')
address2 = w.get_key().address
print("\nSend 10 rBTC to address %s" % address2)
bdc.proxy.settxfee(0.00002500)
txid = bdc.proxy.sendtoaddress(address2, 10)
print("Resulting txid: %s" % txid)
tx = bdc.proxy.gettransaction(txid)
pprint(tx)


print("\n\nConnect to bitcoind regtest with Service class and retrieve new transaction and utxo info")
srv = Service(network='regtest', providers=['bitcoind'], cache_uri='')
print("Blockcount %d" % srv.blockcount())
b = srv.getblock(500)
pprint(b.as_dict())
b.transactions[0].info()

t = srv.gettransaction(txid)
t.info()

utxos = srv.getutxos(address)
print(srv.getbalance(address))
for utxo in utxos:
    print(utxo['txid'], utxo['value'], utxo['confirmations'], utxo['block_height'])