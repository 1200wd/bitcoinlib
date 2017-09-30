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

WALLET_NAME = "Multisig-2-of-3-example"
NETWORK = 'testnet'
KEY_STRENGHT = 32

test_databasefile = 'bitcoinlib.test.sqlite'
test_database = DEFAULT_DATABASEDIR + test_databasefile
# Uncomment to delete database and recreate wallet
# if os.path.isfile(test_database):
#     os.remove(test_database)

if not wallet_exists(WALLET_NAME, databasefile=test_database):
    cosign_names = ['This PC', 'Other PC', 'Paper backup']

    print("We will generate 3 private keys, to sign and send a transaction 2 keys are needed:"
          "\n- With 1 private key a wallet on This PC is created"
          "\n- Use private key 2 to create a wallet on an Other PC"
          "\n- Store key 3 on a Paper in a safe in case one of the PC's is not available anymore"
          "\nPLEASE NOTE: THIS IS AN EXAMPLE. In real life use a better key strenght, "
          "no passwords or better passwords if they are important and do not generate all private keys on a "
          "single instance"
          )
    key_list = []
    for cosigner in cosign_names:
        words = Mnemonic().generate(KEY_STRENGHT)
        password = '%s%d' % (cosigner.replace(' ', '-').lower(), randint(10, 99))
        seed = Mnemonic().to_seed(words, password)
        hdkey = HDKey.from_seed(seed, network=NETWORK)
        public_account_wif = hdkey.account_multisig_key().wif_public()
        print("\nKey for cosigner '%s' generated. Please store both passphrase and password carefully!" % cosigner)
        print("Passphrase: %s" % words)
        print("Password: %s" % password)
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

    otherpc_keylist = [
        key_list[0].account_multisig_key().wif_public(),
        key_list[1].wif(),
        key_list[2].wif_public()
    ]
    print("\n---> Please create a wallet on your Other PC like this:")
    print("from bitcoinlib.wallets import HDWallet")
    print("key_list = ", end='')
    pprint(otherpc_keylist)
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
