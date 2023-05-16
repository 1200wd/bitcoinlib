# Encrypt private key fields in Key table in database using symmetric AES encryption.
# - Add database_encryption_enabled=True in .bitcoinlib/config.ini
# - Supply encryption key in DB_FIELD_ENCRYPTION_KEY environment variable
# - Key must be a 32 byte hexadecimal string
# - Only encrypts the private and wif field in the DbKey database, for full database encryption please use the
#   db_password argument in the Wallet class

import os

# Method #1 - Set environment variable in code
os.environ['DB_FIELD_ENCRYPTION_KEY'] = '11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff'

# Method #2 - Use hardware wallet, yubikey, file on separate physical device, etc. to store password

# Method #3 - Ask user for a password use the sha256 hash as encryption key
# import hashlib
# pwd = input("Password? ")
# os.environ['DB_FIELD_ENCRYPTION_KEY'] = hashlib.sha256(bytes(pwd, 'utf8')).hexdigest()

from bitcoinlib.wallets import wallet_create_or_open

wallet = wallet_create_or_open('wallet_private_keys_encrypted')
wallet.new_key()
wallet.info()
print(wallet.main_key.wif)

