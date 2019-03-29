# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    Create a multisig 2-of-3 wallet with Mnemonic passphrase keys, so wallet contains 3 keys and 2 signatures are
#    needed to sign a transaction / send a payment.
#
#    Transaction are created and signed with 1 signature on this PC, on the other offline PC the transaction is signed
#    with a second private key. The third key is a stored on a paper in case one of the others keys is lost.
#
#    © 2017 - 2018 November - 1200 Web Development <http://1200wd.com/>
#
# TODO: Outdated, need to update example

from __future__ import print_function

from pprint import pprint
from bitcoinlib.wallets import wallet_exists, HDWallet
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey

WALLET_NAME = "Multisig-2of3"
NETWORK = 'testnet'
KEY_STRENGTH = 128  # Remove this line to use the default 256 bit key strength
SIGNATURES_REQUIRED = 2
WITNESS_TYPE = 'segwit'  # Witness type can be legacy, p2sh-segwit or segwit

# from bitcoinlib.wallets import wallet_delete_if_exists
# wallet_delete_if_exists(WALLET_NAME, force=True)

if not wallet_exists(WALLET_NAME):
    # Define cosigners, format (name, key_type, [password], private|public)
    cosigners = [
        ('This PC', 'bip44', 'password', 'private'),
        ('Offline PC', 'bip44', '', 'public'),
        ('Paper backup', 'single', '', 'public'),
    ]

    print("We will generate 3 private keys, to sign and send a transaction 2 keys are needed:"
          "\n- With 1 private key a wallet on This PC is created"
          "\n- Use private key 2 to create a wallet on an Offline PC"
          "\n- Store key 3 on a Paper in a safe in case one of the PC's is not available anymore"
          "\nPLEASE NOTE: THIS IS AN EXAMPLE. In real life do not generate all private keys on a "
          "single instance"
          )
    key_list = []
    key_list_thispc = []
    for cosigner in cosigners:
        print("\n")
        words = Mnemonic().generate(KEY_STRENGTH)
        password = ''
        if cosigner[2] == 'password':
            password = input("Please give password for cosigner '%s': " % cosigner[0])
        seed = Mnemonic().to_seed(words, password)
        hdkey = HDKey.from_seed(seed, network=NETWORK, key_type=cosigner[1])
        if cosigner[1] == 'bip44':
            public_account = hdkey.account_multisig_key(witness_type=WITNESS_TYPE)
        else:
            public_account = hdkey
        print("Key for cosigner '%s' generated. Please store both passphrase and password carefully!" % cosigner[0])
        print("Passphrase: %s" % words)
        print("Password: %s" % ('*' * len(password)))
        print("Share this public key below with other cosigner")
        print("Public key: %s" % public_account.wif_public())

        if cosigner[3] == 'private':
            key_list.append(hdkey)
            key_list_thispc.append(hdkey)
        else:
            key_list.append(public_account)
            key_list_thispc.append(public_account.public())

    thispc_wallet = HDWallet.create_multisig(WALLET_NAME, key_list_thispc, SIGNATURES_REQUIRED, sort_keys=True,
                                             witness_type=WITNESS_TYPE, network=NETWORK)
    thispc_wallet.new_key()

    print("\n\nA multisig wallet has been created on this system")
    thispc_wallet.info()

    print("\n---> Please create a wallet on your Other PC like this:")
    print("from bitcoinlib.wallets import HDWallet")
    print("from bitcoinlib.keys import HDKey")
    print("")
    print("key_list = [")
    print("    '%s'," % key_list[0].account_multisig_key().wif_public())
    print("    '%s'," % key_list[1].wif())
    print("    HDKey('%s', key_type='single', witness_type='%s')" % (key_list[2].wif_public(), WITNESS_TYPE))
    print("]")
    print("wlt = HDWallet.create_multisig('%s', key_list, 2, sort_keys=True, witness_type='%s', network='%s')" %
          (WALLET_NAME, WITNESS_TYPE, NETWORK))
    print("wlt.new_key()")
    print("wlt.info()")
else:
    thispc_wallet = HDWallet(WALLET_NAME)
    thispc_wallet.utxos_update()
    thispc_wallet.info()
    utxos = thispc_wallet.utxos()
    if utxos:
        print("\nNew unspent outputs found!")
        print("Now a new transaction will be created to sweep this wallet and send bitcoins to a testnet faucet")
        send_to_address = 'n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi'
        res = thispc_wallet.sweep(send_to_address, min_confirms=0)

        assert 'transaction' in res
        print("Now copy-and-paste the raw transaction hex to your Other PC and sign it there with a second signature:")
        print("\nfrom bitcoinlib.wallets import HDWallet")
        print("")
        print("wlt = HDWallet('%s')" % WALLET_NAME)
        print("utxos = ", end='')
        pprint(utxos)
        print("")
        print("wlt.utxos_update(utxos=utxos)")
        print("t = wlt.transaction_import('%s')" % res['transaction'].raw_hex())
        print("t_signed = wlt.transaction_sign(t)")
        print("")
        print("# Push the following raw transaction to the blockchain network on any online PC:")
        print("print(t_signed.raw_hex())")
    else:
        print("\nPlease send funds to %s, so we can create a transaction" % thispc_wallet.get_key().address)
        print("\nRestart this program when funds are send...")
