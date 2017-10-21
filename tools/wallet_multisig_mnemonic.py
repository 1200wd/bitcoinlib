# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    Create a multisig 2-of-3 wallet with Mnemonic passphrase keys.
#    Use an online PC to create transaction and sign with the first key and then sign with a second key
#    on an Offline PC. The third key is a stored on a paper in case one of the others keys is lost.
#
#    © 2017 Oktober - 1200 Web Development <http://1200wd.com/>
#

from pprint import pprint
from random import randint
from bitcoinlib.wallets import *
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey

WALLET_NAME = "Multisig-2of3"
NETWORK = 'bitcoin'
KEY_STRENGHT = 128

# wallet_delete_if_exists(WALLET_NAME)
if not wallet_exists(WALLET_NAME):
    cosign_names = ['This PC', 'Offline PC', 'Paper backup']

    print("We will generate 3 private keys, to sign and send a transaction 2 keys are needed:"
          "\n- With 1 private key a wallet on This PC is created"
          "\n- Use private key 2 to create a wallet on an Offline PC"
          "\n- Store key 3 on a Paper in a safe in case one of the PC's is not available anymore"
          )
    key_list = []
    for cosigner in cosign_names:
        words = Mnemonic().generate(KEY_STRENGHT)
        print("\nKey for cosigner '%s' generated. Please store both passphrase and password carefully!" % cosigner)
        password = ''
        if cosigner != 'Paper backup':
            password = input("Enter password for this key (or enter for no password): ")
        seed = Mnemonic().to_seed(words, password)
        hdkey = HDKey.from_seed(seed, network=NETWORK)
        public_account_wif = hdkey.account_multisig_key().wif_public()
        print("Passphrase: %s" % words)
        print("Share this public key below with other cosigner")
        print("Public key: %s" % public_account_wif)
        key_list.append(hdkey)

    thispc_keylist = [
        HDKey(key_list[0].wif(), network=NETWORK),
        HDKey(key_list[1].account_multisig_key().wif_public(), network=NETWORK),
        HDKey(key_list[2].wif_public(), network=NETWORK, key_type='single')
    ]
    thispc_wallet = HDWallet.create_multisig(WALLET_NAME, thispc_keylist, 2, sort_keys=True,
                                             network=NETWORK, databasefile=test_database)
    thispc_wallet.new_key()

    print("\n\nA multisig wallet with 1 key has been created on this system")
    thispc_wallet.info()

    print("\n---> Please create a wallet on your Other PC like this:")
    print("from bitcoinlib.wallets import HDWallet")
    print("key_list = [")
    print("    '%s'," % key_list[0].account_multisig_key().wif_public())
    print("    '%s'," % key_list[1].wif())
    print("    HDKey('%s', key_type='single')" % key_list[2].wif_public())
    print("]")
    print("wallet = HDWallet.create_multisig('%s', key_list, 2, sort_keys=True, network='%s')" % (WALLET_NAME, NETWORK))
    print("wallet.new_key()")
    print("wallet.info()")
else:
    thispc_wallet = HDWallet(WALLET_NAME, databasefile=test_database)

thispc_wallet.utxos_update()
thispc_wallet.info()
utxos = thispc_wallet.utxos()
if utxos:
    print("\nNew unspent outputs found!")
    print("Now a new transaction will be created to sweep this wallet and send bitcoins to a testnet faucet")
    send_to_address = 'n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi'
    res = thispc_wallet.sweep(send_to_address, min_confirms=0)
    # The sweep, send or send_to methods of the Wallets class returns either a transaction ID upon successful send
    # or a dictionary with a transaction object and the reason for rejection
    assert 'transaction' in res
    print("Now copy-and-paste the raw transaction hex to your Other PC and sign it there with a second signature:")
    print("t2 = wallet.transaction_import('%s')" % res['transaction'].raw_hex())
    print("t2 = wallet.transaction_sign(t2)")
    print("wallet.transaction_send(t2)")
else:
    print("Please send funds to %s, so we can create a transaction" % thispc_wallet.get_key().address)
    print("Restart this program when funds are send...")
