# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    Multisig 3-of-5 wallet with Mnemonic passphrase keys
#
#    © 2017 November - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.wallets import wallet_exists, HDWallet, wallet_delete
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey

WALLET_NAME = "Multisig-3of5"
NETWORK = 'testnet'
KEY_STRENGHT = 256

wallet_delete(WALLET_NAME)
if not wallet_exists(WALLET_NAME):
    # This wallets key list, use tools/mnemonic_key_create.py to create your own.
    #
    # Mnemonic passphrases for this keys are:
    # Key 1 - hockey brain fresh cluster autumn mansion faith output physical galaxy type disagree
    # Key 2 - vicious escape useless stomach display roast just box gain slight legend trophy
    # Key 3 - zone grocery puzzle mention boil shallow lend nominee fossil novel turtle alter
    # Key 4 - flight property catch give sorry try thumb animal news fly scatter cross
    # Key 5 - canyon hood clever sweet retreat gift poem frog oval pulp siege clinic
    #

    key_list = [
        # 1. Private key for this wallet (cosigner
        'tprv8ZgxMBicQKsPegNrj4zihq6PaWmhA6cXeMbATKSgAowEJGEtcEUfqNWXpeqAYorNkSKwCUux1ZUvXk7BXCiY1y5XbEXhrUuVvttbAbbKg67',
        # 2. Public account key for cosigner 2 wallet
        'tpubDCghbgppUNrHwwTLo2ihuxmVXHhirEukpHvjWB1bPoa3AkSZCnCAVhStpByYzRMmdMui1sbx1zdh4ZYk5p4Dgi177P5rJw6hnDsVNYoPjvp',
        # 3. Public account key for cosigner 3 wallet
        'tpubDD9mSFkkofjdejUE1Z6SJib5AuMEP9zbSMUVTEm9tbKmLsFDA6eVTMXz4z2pfKfU5DRhxgz473sFbtGKuE1X4fDnp6j5TkXWPf8X6pDbDm9',
        # 4. Public key from paper backup in vault
        HDKey('tpubD6NzVbkrYhZ4XJGZ3MKgSmq5b5DSF3dSW3zszZLEmDmUKsAksRc75ykFsoGnwRjkwv2kdooE4quQ6HndPcxbfFnc4KyA9vDbZ'
              'aSGawWmC4N', key_type='single', network=NETWORK),
        # 5. Public key with trusted 3rd party
        HDKey('tpubD6NzVbkrYhZ4YTEdHBuKCfRLxkpqYmdBmy5NwMnAngKaSXdvP5cJGr2GgP1r4pHj4499SGsnfC5ZpXeMWic4XLKBcvruN6Qcy'
              'i6ftdKFKYp', key_type='single', network=NETWORK)
    ]

    wallet3o5 = HDWallet.create_multisig(WALLET_NAME, key_list, 3, sort_keys=True)
    print(wallet3o5.network)
    wallet3o5.new_key()

    print("\n\nA multisig wallet with 1 key has been created on this system")
    wallet3o5.info()
else:
    wallet3o5 = HDWallet(WALLET_NAME)

wallet3o5.utxos_update()
wallet3o5.info()
utxos = wallet3o5.utxos()
if utxos:
    print("\nNew unspent outputs found!")
    print("Now a new transaction will be created to sweep this wallet and send bitcoins to a testnet faucet")
    send_to_address = '3GfnZJnpJ9Em85wnVJtiPapBcVzZkJDquD'
    res = wallet3o5.sweep(send_to_address, min_confirms=0)
    # The sweep, send or send_to methods of the Wallets class returns either a transaction ID upon successful send
    # or a dictionary with a transaction object and the reason for rejection
    assert 'transaction' in res
    print("Now copy-and-paste the raw transaction hex to your Other PC and sign it there with a second signature:")
    print("t2 = wallet.transaction_import('%s')" % res['transaction'].raw_hex())
    print("t2 = wallet.transaction_sign(t2)")
    print("wallet.transaction_send(t2)")
else:
    print("Please send funds to %s, so we can create a transaction" % wallet3o5.get_key().address)
    print("Restart this program when funds are send...")
