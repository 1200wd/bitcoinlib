# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Delete aged unconfirmed transactions from wallet
#
#    © 2024 June - 1200 Web Development <http://1200wd.com/>
#

from time import sleep
from bitcoinlib.wallets import *


# Create wallet and add utxo's
pkm = 'monitor orphan turtle stage december special'
wallet_delete_if_exists("wallet_remove_old_unconfirmed_transactions", force=True)
w = Wallet.create("wallet_remove_old_unconfirmed_transactions", keys=pkm, network='bitcoinlib_test')
w.get_keys(number_of_keys=4)
utxos = [
    {
        "address": "blt1q4dugy6d7qz7226mk6ast3nz23z7ctd80mymle3",
        "script": "",
        "confirmations": 2,
        "output_n": 1,
        "txid": "e6192f6dafa689ac8889b466d2dd3eb2bb55b76c7305b4a2a6a31de6c9991aeb",
        "value": 1829810
    },
    {
        "address": "blt1q82l3c2d37yjxe0r9a7qn9v7c9y7hnaxp398kc0",
        "script": "",
        "confirmations": 0,
        "output_n": 0,
        "txid": "5891c85595193d0565fe418d5c5192c1297eafbef36c28bcab2ac3341ee68e71",
        "value": 2389180
    },
    {
        "address": "blt1qdtez8t797m74ar8wuvedw50jmycefwstfk8ulz",
        "script": "",
        "confirmations": 100,
        "output_n": 0,
        "txid": "7e87a63a0233615a5719a782a0b1c85de521151d8648e7d7244155a2caf7dd47",
        "value": 99389180
    },
    {
        "address": "blt1qdtez8t797m74ar8wuvedw50jmycefwstfk8ulz",
        "script": "",
        "confirmations": 100,
        "output_n": 0,
        "txid": "a4ef4aef09839a681419b80d5b6228b0089af39a4483896c9ac106192ac1ec34",
        "value": 838180
    },
]
w.utxos_update(utxos=utxos)
w.send_to('blt1qvtaw9m9ut96ykt2n2kdra8jpv3m5z2s8krqwsv', 50000, broadcast=True)
w.info()

print("We now have a wallet with 5 utxo's, of which 3 are unconfirmed")
print(f"UTXO count: {len(w.utxos())}")

print("Try to remove unconfirmed utxo's which are more then 1 hour old (doesn't delete anything)")
w.transactions_remove_unconfirmed(1)
print(f"UTXO count: {len(w.utxos())}")

sleep(1)  # sleep a little to avoid glitches in the time-matrix
print("Remove all unconfirmed utxo's, and mark previous outputs a unspent again")
w.transactions_remove_unconfirmed(0)
print(f"UTXO count: {len(w.utxos())}")

w.info()