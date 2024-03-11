# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Bip38 encrypted private keys
#
#    © 2024 March - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.keys import *

#
# Example #1 - BIP38 key - no EC multiplication
#
private_wif = "L3QtG7mpcV1AiGCuRCi34HgwTtWDPWNe6m8Wi58S1LzavAsu3v1x"
password = "bitcoinlib"
expected_encrypted_wif = "6PYRg5u7XPXoL9v8nXbBJkzjcMtCqSDM1p9MJttpXb42W1DNt33iX8tosj"
k = HDKey(private_wif, witness_type='legacy')
encrypted_wif = k.encrypt(password=password)
assert(encrypted_wif == expected_encrypted_wif)
print("Encrypted WIF: %s" % encrypted_wif)

k2 = HDKey(encrypted_wif, password=password, witness_type='legacy')
assert(k2.wif_key() == private_wif)
print("Decrypted WIF: %s" % k2.wif_key())


#
# Example #2 - EC multiplied BIP38 key encryption - not lot and sequence
# from https://bip38.readthedocs.io/en/v0.3.0/index.html
#
passphrase = "meherett"
owner_salt = "75ed1cdeb254cb38"
seed = "99241d58245c883896f80843d2846672d7312e6195ca1a6c"
compressed = False
expected_intermediate_password = "passphraseondJwvQGEWFNrNJRPi4G5XAL5SU777GwTNtqmDXqA3CGP7HXfH6AdBxxc5WUKC"
expected_encrypted_wif = "6PfP7T3iQ5jLJLsH5DneySLLF5bhd879DHW87Pxzwtwvn2ggcncxsNKN5c"
expected_confirmation_code = "cfrm38V5NZfTZKRaRDTvFAMkNKqKAxTxdDjDdb5RpFfXrVRw7Nov5m2iP3K1Eg5QQRxs52kgapy"
expected_private_key = "5Jh21edvnWUXFjRz8mDVN3CSPp1CyTuUSFBKZeWYU726R6MW3ux"

intermediate_password = bip38_intermediate_password(passphrase, owner_salt=owner_salt)
assert(intermediate_password == expected_intermediate_password)
print("\nIntermediate Password: %s" % intermediate_password)

res = bip38_create_new_encrypted_wif(intermediate_password, compressed=compressed, seed=seed)
assert(res['encrypted_wif'] == expected_encrypted_wif)
print("Encrypted WIF: %s" % res['encrypted_wif'])
assert(res['confirmation_code'] == expected_confirmation_code)
print("Confirmation Code: %s" % res['confirmation_code'])

k = HDKey(res['encrypted_wif'], password=passphrase, compressed=compressed, witness_type='legacy')
assert(k.wif_key() == expected_private_key)
print("Private WIF: %s" % k.wif_key())

#
# Example #2 - EC multiplied BIP38 key encryption - with lot and sequence
# from https://bip38.readthedocs.io/en/v0.3.0/index.html
#
passphrase = "meherett"
owner_salt = "75ed1cdeb254cb38"
seed = "99241d58245c883896f80843d2846672d7312e6195ca1a6c"
compressed = True
lot = 369861
sequence = 1
expected_intermediate_password = "passphraseb7ruSNDGP7cmnFHQpmos7TeAy26AFN4GyRTBqq6hiaFbQzQBvirD9oHsafQvzd"
expected_encrypted_wif = "6PoEPBnJjm8UAiSGWQEKKNq9V2GMHqKkTcUqUFzsaX7wgjpQWR2qWPdnpt"
expected_confirmation_code = "cfrm38VWx5xH1JFm5EVE3mzQvDPFkz7SqNiaFxhyUfp3Fjc2wdYmK7dGEWoW6irDPSrwoaxB5zS"
expected_private_key = "KzFbTBirbEEtEPgWL3xhohUcrg6yUmJupAGrid7vBP9F2Vh8GTUB"

intermediate_password = bip38_intermediate_password(passphrase, lot=lot, sequence=sequence, owner_salt=owner_salt)
assert(intermediate_password == expected_intermediate_password)
print("\nIntermediate Password: %s" % intermediate_password)

res = bip38_create_new_encrypted_wif(intermediate_password, compressed=compressed, seed=seed)
assert(res['encrypted_wif'] == expected_encrypted_wif)
print("Encrypted WIF: %s" % res['encrypted_wif'])
assert(res['confirmation_code'] == expected_confirmation_code)
print("Confirmation Code: %s" % res['confirmation_code'])

k = HDKey(res['encrypted_wif'], password=passphrase, compressed=compressed, witness_type='legacy')
assert(k.wif_key() == expected_private_key)
print("Private WIF: %s" % k.wif_key())
