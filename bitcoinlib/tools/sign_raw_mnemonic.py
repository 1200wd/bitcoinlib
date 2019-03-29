# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    Import and sign multisig transaction in cosigner wallet
#
#    © 2017 November - 1200 Web Development <http://1200wd.com/>
#
# TODO: Outdated, need to update example


from bitcoinlib.wallets import HDWallet
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey
try:
    input = raw_input
except NameError:
    pass

WALLET_NAME = "Multisig_3of5"

wlt = HDWallet(WALLET_NAME)

# If you want to sign on an offline PC, export utxo dictionary to offline PC
# utxos = {...}
# wlt.utxos_update(utxos=utxos)

wlt.utxos_update()
wlt.info()

# Paste your raw transaction here or enter in default input
raw_tx = ''
if not raw_tx:
    raw_tx = input("Paste raw transaction hex: ")

passphrase = input("Enter passphrase: ")
password = input("Enter password []:")
seed = Mnemonic().to_seed(passphrase, password)
hdkey = HDKey.from_seed(seed, network=wlt.network.network_name)

t = wlt.transaction_import_raw(raw_tx)
t.sign(hdkey)

print("Raw signed transaction: ")
print(t.raw_hex())
