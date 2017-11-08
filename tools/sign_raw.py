# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    Sign Multisig
#
#    © 2017 November - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.wallets import *

WALLET_NAME = "Multisig_3of5"

wlt = HDWallet(WALLET_NAME)

# If you want to sign on an offline PC, export utxo dictionary to offline PC
# utxos = {...}
# wlt.utxos_update(utxos=utxos)

wlt.utxos_update()
wlt.info()

# Paste your raw transaction here
raw_tx = ''

t = wlt.transaction_import(raw_tx)
t_signed = wlt.transaction_sign(t)

