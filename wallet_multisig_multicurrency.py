# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    Multisig 2-of-3 wallet with Mnemonic passphrase keys
#
#    © 2017 September - 1200 Web Development <http://1200wd.com/>
#

from pprint import pprint
from random import randint
from bitcoinlib.wallets import *
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey

WALLET_NAME = "Multisig-Multicurrency"
NETWORK = 'testnet'
KEY_STRENGHT = 128

hdkey_paper1 = HDKey(network=NETWORK, key_type='single')
hdkey_paper2 = HDKey(network=NETWORK, key_type='single')

key_list = [
    HDKey(network=NETWORK),
    hdkey_paper1.public(),
    hdkey_paper2.public(),
]

wallet_delete_if_exists(WALLET_NAME)
wallet = HDWallet.create_multisig(WALLET_NAME, key_list, 2, network=NETWORK)

wallet.get_key()
wallet.new_key()

wallet.new_key(network='litecoin')

wallet.info()
