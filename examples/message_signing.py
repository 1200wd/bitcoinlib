# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Sign Bitcoin Messages Examples
#
#    © 2025 December - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.keys import HDKey, signed_message_parse, verify_message
from bitcoinlib.wallets import wallet_create_or_open

#
# === Sign and verify a message with a wallet ===
#

message = "This is a example of a signed message by a Bitcoinlib wallet"
w = wallet_create_or_open('message-signing-wallet')
sig = w.sign_message(message)
signed_message = sig.as_signed_message(message)
print(signed_message)

# This prints a signed message such as:
#
# -----BEGIN BITCOIN SIGNED MESSAGE-----
# This is a example of a signed message by a Bitcoinlib wallet
# -----BEGIN SIGNATURE-----
# bc1q065ed8cnxf9rr2v0qhatr2guruulr0jpgjycfu
# J4YKfaKqHDJCidfWXYTRC191QYZ3slu8VzgFyUb6m7QJn7Yn2sif7Od1slvnhBV6pLqj2cnISyahVCIrrHQNe0I=
# -----END BITCOIN SIGNED MESSAGE-----
#
# You can check if is valid with a Bitcoin node, online on some websites (https://checkmsg.org) or with Bitcoinlib:
#

message, signature, address, network = signed_message_parse(signed_message)
print(f"Signature verified by verify_message method: {verify_message(message, signature, address, network)}")

print(f"Signature verified by Bitcoinlib Wallet: {w.verify_message(message, sig)}")


#
# === Sign a message with a private key, and verify with public key ===
#

message = "Message to sign with a private Key"
print(f"\n\nSign this message with a private key: {message}")
priv_key = HDKey()
sig = priv_key.sign_message(message)

pub_key = priv_key.public()
print(f"Verified with Public Key: {pub_key.verify_message(message, sig)}")


#
# === Sign a message with a private key, and verify with only an address ===
#

message = "Message to sign with a private Key, verify with only an address"
print(f"\n\nSign this message with a private key (2): {message}")
priv_key = HDKey()
sig = priv_key.sign_message(message)

addr = priv_key.address()
print(f"Base64 encoded signature: {sig.as_base64()}")
print(f"Address from private key: {addr}")
print(f"Verified with address: {verify_message(message, sig.as_base64(), addr)}")
