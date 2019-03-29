# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    Create Multisig 3-of-5 wallet
#
#    © 2017 November - 1200 Web Development <http://1200wd.com/>
#
# TODO: Outdated, need to update example

from pprint import pprint
from bitcoinlib.wallets import wallet_exists, HDWallet, wallet_delete_if_exists
from bitcoinlib.keys import HDKey

WALLET_NAME = "Multisig_3of5"
NETWORK = 'testnet'
SIGS_N = 5
SIGS_REQUIRED = 3

# COSIGNER DICTIONARY
# Create keys with mnemonic_key_create.py on separate instances and insert public or private key in dict
#
cosigners = [
    {
        'name': 'Anita',
        'key_type': 'bip44',
        'key': 'tprv8ZgxMBicQKsPdLUgjM2gKV2srYdBKWN8AxbAgy5i2rzJKaePCtrfaoDt8GYuTHzhujLweL6u5yrepHxPt1TnFUpmkMEYVyvNRMJKHhjEQ6h'
    },
    {
        'name': 'Bart',
        'key_type': 'bip44',
        'key': 'tprv8ZgxMBicQKsPeneZumFrSynR5aYyDhf7KDky9KrbGaNGMajAti8cWRpXFTBWUZfajLN2XgFDkVqZ2y6kJasEXQb7nEd7sKqHu24yydWJEPw'
    },
    {
        'name': 'Chris',
        'key_type': 'bip44',
        'key': 'tprv8ZgxMBicQKsPdyq1mze34uejZpwac4Bu9ZhHPDZi5gMRCs4Ugnu851rQDZ3KVBmMmp2hjr92J2GS6rTDr3LsoFUCt1DeXEBw7KNqZ448AB6'
    },
    {
        'name': 'Daan',
        'key_type': 'bip44',
        'key': 'tpubDDqeUityd3vW7JbKsYpd4SDXEPWzBUqJmdYMRkuefbejHkVyNnrWHfwELYu1bbRnjLALYAUfs7Bg69moqpRyYnS31Z6DuYA9r2wZC5sLGAm'
    },
    {
        'name': 'Paper-Backup',
        'key_type': 'single',
        'key': 'tpubD6NzVbkrYhZ4XfKVKY9LUfXh4t3ZHMDw9Q2SUUDTCCXrzFGfLm6v5n4frZWNfc5fwkbc33C3FwvbwbxgrDGKNSL2WcLAhPcZXijrQvLvyYA'
    },
]

if not wallet_exists(WALLET_NAME):
    # This wallets key list, use tools/mnemonic_key_create.py to create your own.
    #

    cosigners_private = []
    key_list = []
    for cosigner in cosigners:
        if not cosigner['key']:
            raise ValueError("Please create private keys with mnemonic_key_create.py and add to COSIGNERS definitions")
        hdkey = HDKey(cosigner['key'], key_type=cosigner['key_type'])
        if hdkey.is_private:
            cosigners_private.append(cosigner['name'])
        cosigner['hdkey'] = hdkey
        key_list.append(hdkey)

    # YOU SHOULD ENABLE THIS CHECK FOR REAL WALLETS
    # if len(cosigners_private) > 1:
    #    raise ValueError("It is strongly advised to use not more then 1 private key per wallet.")

    if len(key_list) != SIGS_N:
        raise ValueError("Number of cosigners (%d) is different then expected. SIG_N=%d" % (len(key_list), SIGS_N))
    wallet3o5 = HDWallet.create_multisig(WALLET_NAME, key_list, SIGS_REQUIRED, sort_keys=True, network=NETWORK)
    wallet3o5.new_key()

    print("\n\nA multisig wallet with 1 key has been created on this system")
else:
    wallet3o5 = HDWallet(WALLET_NAME)

print("\nUpdating UTXO's...")
wallet3o5.utxos_update()
wallet3o5.info()
utxos = wallet3o5.utxos()

# Creating transactions just like in a normal wallet, then send raw transaction to other cosigners. They
# can sign the transaction with there on key and pass it on to the next signer or broadcast it to the network.
# You can use sign_raw.py to import and sign a raw transaction.

# Example
# if utxos:
#     print("\nNew unspent outputs found!")
#     print("Now a new transaction will be created to sweep this wallet and send bitcoins to a testnet faucet")
#     send_to_address = 'mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB'
#     res = wallet3o5.sweep(send_to_address, min_confirms=0)
#     if 'transaction' in res:
#         print("Now send the raw transaction hex to one of the other cosigners to sign using sign_raw.py")
#         print("Raw transaction: " % res['transaction'].raw_hex())
#     else:
#         print("Send transaction result:")
#         pprint(res)
# else:
#     print("Please send funds to %s, so we can create a transaction" % wallet3o5.get_key().address)
#     print("Restart this program when funds are send...")
