# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Creating and using Multisignature Wallets
#
#    © 2017 September - 1200 Web Development <http://1200wd.com/>
#

import os
from pprint import pprint
from bitcoinlib.wallets import *

test_databasefile = 'bitcoinlib.test.sqlite'
test_database = DEFAULT_DATABASEDIR + test_databasefile
if os.path.isfile(test_database):
    os.remove(test_database)

#
# Create Multisignature Wallets using Bitcoinlib Testnet and Create a Transaction
#

# Create 3 wallets with one private keys each, and 2 public keys corresponding with other wallets
NETWORK = 'bitcoinlib_test'
pk1 = HDKey(network=NETWORK)
pk2 = HDKey(network=NETWORK)
pk3 = HDKey(network=NETWORK)
klist = [pk1, pk2.account_multisig_key().wif_public(), pk3.account_multisig_key().wif_public()]
wl1 = HDWallet.create_multisig('multisig_2of3_cosigner1', sigs_required=2, key_list=klist,
                               network=NETWORK, databasefile=test_database)
klist = [pk1.account_multisig_key().wif_public(), pk2, pk3.account_multisig_key().wif_public()]
wl2 = HDWallet.create_multisig('multisig_2of3_cosigner2',  sigs_required=2, key_list=klist,
                               network=NETWORK, databasefile=test_database)
klist = [pk1.account_multisig_key().wif_public(), pk2.account_multisig_key().wif_public(), pk3]
wl3 = HDWallet.create_multisig('multisig_2of3_cosigner3', sigs_required=2, key_list=klist,
                               network=NETWORK, databasefile=test_database)

# Generate a new key in each wallet, all these keys should be the same
nk1 = wl1.new_key()
nk2 = wl2.new_key()
nk3 = wl3.new_key()
assert nk1.wif == nk2.wif == nk3.wif
print("Created new multisig address: ", nk1.wif)

# Create a transaction
transaction_fee = 29348
wl1.utxos_update()  # On bitcoinlib testnet, this automatically creates an UTXO
utxo = wl1.utxos()[0]
output_arr = [('23Gd1mfrqgaYiPGkMm5n5UDRkCxruDAA8wo', utxo['value'] - transaction_fee)]
input_arr = [(utxo['tx_hash'], utxo['output_n'], utxo['key_id'], utxo['value'])]
t = wl1.transaction_create(output_arr, input_arr, transaction_fee=transaction_fee)

# Now sign transaction with first wallet, should not verify yet
t.sign()
pprint(t.dict())
print("Verified (False): ", t.verify())

# Import transaction (with first signature) in 3rd wallet and sign with wallet's private key
wl3.utxos_update()
t2 = wl3.transaction_import(t)
t2.sign()
print("Verified (True): ", t2.verify())


#
# Create Multisig 2-of-2 testnet wallet, and sweep all UTXO's
#

# Create 2 cosigner multisig wallets
NETWORK = 'testnet'
pk1 = HDKey('tprv8ZgxMBicQKsPd1Q44tfDiZC98iYouKRC2CzjT3HGt1yYw2zuX2awTotzGAZQEAU9bi2M5MCj8iedP9MREPjUgpDEBwBgGi2C8eK'
            '5zNYeiX8', network=NETWORK)
pk2 = HDKey('tprv8ZgxMBicQKsPeUbMS6kswJc11zgVEXUnUZuGo3bF6bBrAg1ieFfUdPc9UHqbD5HcXizThrcKike1c4z6xHrz6MWGwy8L6YKVbgJ'
            'MeQHdWDp', network=NETWORK)
wl1 = HDWallet.create_multisig('multisig_2of2_cosigner1', sigs_required=2,
                               key_list=[pk1, pk2.account_multisig_key().wif_public()],
                               network=NETWORK, databasefile=test_database)
wl2 = HDWallet.create_multisig('multisig_2of2_cosigner2',  sigs_required=2,
                               key_list=[pk1.account_multisig_key().wif_public(), pk2],
                               network=NETWORK, databasefile=test_database)
nk1 = wl1.new_key()
nk2 = wl2.new_key()

# Create a transaction
wl1.utxos_update()
utxos = wl1.utxos()
if not utxos:
    print("Deposit testnet bitcoin to this address to create transaction: ", nk1.address)
else:
    print("Utxo found, sweep address to testnet faucet address")
    res = wl1.sweep('mwCwTceJvYV27KXBc3NJZys6CjsgsoeHmf', min_confirms=0)
    assert 'transaction' in res
    wl2.utxos_update()
    t2 = wl2.transaction_import(res['transaction'])
    t2.sign()
    print("Verified (True): ", t2.verify())
    print("Push transaction result: ", t2.send())


#
# Multisig wallet using single keys for cosigner wallet instead of BIP32 type key structures
#

NETWORK = 'bitcoinlib_test'
pk1 = HDKey('YXscyqNJ5YK411nwB33KeVkhSVjwwUkSG9xG3hkaoQFEbTwNJSrNTfni3aSSYiKtPeUPrFLwDsqHwZjNXhYm2DLEkQoaoikHoK2emrHv'
            'mqSEZrKP', network=NETWORK)
pk2 = HDKey('YXscyqNJ5YK411nwB3kXiApMaJySYss8sMM9FYgXMtmQKmDTF9yiu7yBNKnVjE8WdVVvuhxLqS6kHvW2MPHKmYzbzEHQsDXXAZuu1rCs'
            'Hcp7rrJx', network=NETWORK, key_type='single')
wl1 = HDWallet.create_multisig('multisig_single_keys1', [pk1, pk2.public()],
                               sigs_required=2, network=NETWORK, databasefile=test_database)
wl2 = HDWallet.create_multisig('multisig_single_keys2', [pk1.account_multisig_key().wif_public(), pk2],
                               sigs_required=2, network=NETWORK, databasefile=test_database)

# Create multisig keys and update UTXO's
wl1.new_key()
wl2.new_key()
wl1.utxos_update()
wl2.utxos_update()

# Create transaction and sign with both wallets, return address should be the same
t = wl2.transaction_create([('23Gd1mfrqgaYiPGkMm5n5UDRkCxruDAA8wo', 5000000)])
t.sign()
t2 = wl1.transaction_import(t)
t2.sign()
print("%s == %s: %s" % (t.outputs[1].address, t2.outputs[1].address, t.outputs[1].address == t2.outputs[1].address))
print("Verified (True): ", t2.verify())
