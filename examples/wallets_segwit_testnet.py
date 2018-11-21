# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Segregated Witness Wallets
#
#    © 2018 October - 1200 Web Development <http://1200wd.com/>
#
#
# Create 4 different Segregated Witness wallets of which 2 Native segwit wallets and 2 wallets with P2SH embeded
# segwit scripts so every wallet can send payments to them.
#
# These four wallet types will be created:
# * P2WPKH - Pay-to-wallet-public-key-hash, Native SegWit single key
# * P2WSH - Pay-to-wallet-script-hash, Native SegWit multisig/script
# * P2SH-P2WPKH - P2WPKH nested in a P2SH script
# * P2SH-P2WSH - P2WSH nested in P2SH script
#
# If you deposit at least 0.001 TBTC test bitcoins to the first wallet, several transactions will be created for every
# kind of segwit wallet
#

from bitcoinlib.wallets import wallet_create_or_open, wallet_create_or_open_multisig
from bitcoinlib.keys import HDKey
from time import sleep


wif = 'tprv8ZgxMBicQKsPdpenF8SX1WMsr6eaS3rZgqhqVu1LJ3wkAp1NhREnFrsvzK4A7ERrHhxqjzZpoESRjwpgrrhjC1cWALzZRxoycCNz8jBNWre'
wif2 = 'tprv8ZgxMBicQKsPdktmSG4hGs6kq3dmTMmiDtLZwaipsCYxqbhtqWH69kNGZvNufnemLTCP3gbypLf1koKfAEujo5cnWPKBg3YbpZa63J9Cqtj'
cowif2 = HDKey(wif2).account_multisig_key()

#
# CREATE WALLETS
#

# Segwit P2SH-P2WPKH Wallet
w1 = wallet_create_or_open('segwit_testnet_p2sh_p2wpkh', keys=wif, witness_type='p2sh-segwit', network='testnet')
w1_key = w1.get_key()

# Segwit Native P2WPKH Wallet
w2 = wallet_create_or_open('segwit_testnet_p2wpkh', keys=wif, witness_type='segwit', network='testnet')
w2_key = w2.get_key()

# Segwit Native P2WSH Wallet
w3 = wallet_create_or_open_multisig('segwit_testnet_p2wsh', keys=[wif, cowif2.public()], witness_type='segwit',
                                    network='testnet')
w3_key = w3.get_key()

# Segwit P2SH-P2WSH Wallet
w4 = wallet_create_or_open_multisig('segwit_testnet_p2sh_p2wsh', keys=[wif, cowif2.public()],
                                    witness_type='p2sh-segwit', network='testnet')
w4_key = w4.get_key()


#
# SEND TRANSACTIONS
#

w1.utxos_update()
if not w1.utxos():
    print("No UTXO'S found, please make a test-bitcoin deposit to %s" % w1_key.address)
else:
    print("Sending transaction from wallet #1 to wallet #2:")
    t = w1.send_to(w2_key.address, 20000, fee=5000)
    t.info()

    while True:
        w2.utxos_update()
        print("waiting for tx broadcast")
        sleep(1)
        if w2.utxos():
            print("Sending transaction from wallet #2 to wallet #3:")
            t2 = w2.send_to(w3_key.address, 15000, fee=5000)
            t2.info()
            break

    while True:
        w3.utxos_update()
        print("waiting for tx broadcast")
        sleep(1)
        if w3.utxos():
            print("Sending transaction from wallet #3 to wallet #4:")
            t3 = w3.send_to(w4_key.address, 10000, fee=5000)
            t3.sign(cowif2.subkey_for_path('0/0'))
            t3.send()
            t3.info()
            break

    while True:
        w4.utxos_update()
        print("waiting for tx broadcast")
        sleep(1)
        if w4.utxos():
            print("Sending transaction from wallet #4 to wallet #1:")
            t4 = w4.send_to(w1_key.address, 5000, fee=5000)
            t4.sign(cowif2.subkey_for_path('0/0'))
            t4.send()
            t4.info()
            break
