# bitcoinlib
Bitcoin library with methods to generate, import, store and convert cryptograpic keys.

Implements the following Bitcoin Improvement Proposals
- Hierarchical Deterministic Wallets (BIP0032)
- Passphrase-protected private key (BIP0038)
- Mnemonic code for generating deterministic keys (BIP0039)
- Purpose Field for Deterministic Wallets (BIP0043)
- Multi-Account Hierarchy for Deterministic Wallets (BIP0044)

[![Build Status](https://travis-ci.org/1200wd/bitcoinlib.svg?branch=master)](https://travis-ci.org/1200wd/bitcoinlib)
[![PyPI](https://img.shields.io/pypi/v/bitcoinlib.svg)](https://pypi.python.org/pypi/bitcoinlib/)
[![Documentation Status](https://readthedocs.org/projects/bitcoinlib/badge/?version=latest)](http://bitcoinlib.readthedocs.io/en/latest/?badge=latest)


## Keys

Import or generate all kinds of keys for the bitcoin network, bitcoin testnet or litecoin. Convert from one format to
another. 

Generate new keys from an extended public or private key by using child key derivation.

```python
from bitcoinlib.keys import Key, HDKey
 
print("\n=== Import public key ===")
K = Key('025c0de3b9c8ab18dd04e3511243ec2952002dbfadc864b9628910169d9b9b00ec')
K.info()
 
print("\n=== Import Private Key ===")
k = Key('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX')
print("Private key     %s" % k.wif())
print("Private key hex %s " % k.private_hex())
print("Compressed      %s\n" % k.compressed())
 
print("\n=== Import Testnet Key ===")
k = Key('92Pg46rUhgTT7romnV7iGW6W1gbGdeezqdbJCzShkCsYNzyyNcc')
k.info()
 
print("\n==== Import uncompressed Private Key and Encrypt with BIP38 ===")
k = Key('5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR')
print("Private key     %s" % k.wif())
print("Encrypted pk    %s " % k.bip38_encrypt('TestingOneTwoThree'))
print("Is Compressed   %s\n" % k.compressed())
 
print("\n==== Import and Decrypt BIP38 Key ===")
k = Key('6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg', passphrase='TestingOneTwoThree')
print("Private key     %s" % k.wif())
print("Is Compressed   %s\n" % k.compressed())
 
print("\n==== Generate random HD Key on testnet ===")
hdk = HDKey(network='testnet')
print("Random BIP32 HD Key on testnet %s" % hdk.extended_wif())
 
print("\n==== Import HD Key from seed ===")
k = HDKey.from_seed('000102030405060708090a0b0c0d0e0f')
print("HD Key WIF for seed 000102030405060708090a0b0c0d0e0f:  %s" % k.extended_wif())
 
print("\n==== Generate random Litecoin key ===")
lk = HDKey(network='litecoin')
lk.info()
 
print("\n==== Derive path with Child Key derivation ===")
print("Derive path path 'm/0H/1':")
print("  Private Extended WIF: %s" % k.subkey_for_path('m/0H/1').extended_wif())
print("  Public Extended WIF : %s\n" % k.subkey_for_path('m/0H/1').extended_wif_public())
 
print("\n==== Test Child Key Derivation ===")
print("Use the 2 different methods to derive child keys. One through derivation from public parent, "
      "and one thought private parent. They should be the same.")
K = HDKey('xpub6ASuArnXKPbfEVRpCesNx4P939HDXENHkksgxsVG1yNp9958A33qYoPiTN9QrJmWFa2jNLdK84bWmyqTSPGtApP8P'
          '7nHUYwxHPhqmzUyeFG')
k = HDKey('xprv9wTYmMFdV23N21MM6dLNavSQV7Sj7meSPXx6AV5eTdqqGLjycVjb115Ec5LgRAXscPZgy5G4jQ9csyyZLN3PZLxoM'
          '1h3BoPuEJzsgeypdKj')
```


### Mnemonic Keys

Allows you to use easy to remember passphrases consisting of a number of words to store private keys (BIP0039).
You can password protect this passphrase (BIP0038), and use the HD Wallet structure to generate a almost infinite 
number of new private keys and bitcoin addresses (BIP0043 and BIP0044).

```python
from bitcoinlib.keys import HDKey
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.encoding import change_base
 
# Convert hexadecimal to mnemonic and back again to hex
print("\nConvert hexadecimal to mnemonic and back again to hex")
pk = '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
words = Mnemonic().to_mnemonic(pk)
print("Hex                %s" % pk)
print("Checksum bin       %s" % Mnemonic().checksum(pk))
print("Mnemonic           %s" % words)
print(Mnemonic().to_seed(words, 'test'))
print("Seed for HD Key    %s" % change_base(Mnemonic().to_seed(words, 'test'), 256, 16))
print("Back to Hex        %s" % Mnemonic().to_entropy(words))
 
# Generate a random Mnemonic HD Key
print("\nGenerate a random Mnemonic HD Key")
entsize = 128
words = Mnemonic('english').generate(entsize)
print("Your Mnemonic is   %s" % words)
print("  (An avarage of %d tries is needed to brute-force this password)" % ((2 ** entsize) // 2))
seed = change_base(Mnemonic().to_seed(words), 256, 16)
hdk = HDKey().from_seed(seed)
print("Seed for HD Key    %s" % change_base(seed, 256, 16))
print("HD Key WIF is      %s" % hdk)
 
# Generate a key from a Mnemonic sentence
print("\nGenerate a key from a Mnemonic sentence")
words = "type fossil omit food supply enlist move perfect direct grape clean diamond"
print("Your Mnemonic is   %s" % words)
seed = change_base(Mnemonic().to_seed(words), 256, 16)
hdk = HDKey().from_seed(seed)
print("Seed for HD Key    %s" % change_base(seed, 256, 16))
print("HD Key WIF is      %s" % hdk)
 
# Let's talk Spanish
print("\nGenerate a key from a Spanish Mnemonic sentence")
words = "laguna afirmar talón resto peldaño deuda guerra dorado catorce avance oasis barniz"
print("Your Mnemonic is   %s" % words)
seed = change_base(Mnemonic().to_seed(words), 256, 16)
hdk = HDKey().from_seed(seed)
print("Seed for HD Key    %s" % change_base(seed, 256, 16))
print("HD Key WIF is      %s" % hdk)
 
# Want some Chinese?
print("\nGenerate a key from a Chinese Mnemonic sentence")
words = "信 收 曉 捐 炭 祖 瘋 原 強 則 岩 蓄"
print("Your Mnemonic is   %s" % words)
seed = change_base(Mnemonic().to_seed(words), 256, 16)
hdk = HDKey().from_seed(seed)
print("Seed for HD Key    %s" % change_base(seed, 256, 16))
print("HD Key WIF is      %s" % hdk)
 
# Spanish Unicode mnemonic sentence
print("\nGenerate a key from a Spanish UNICODE Mnemonic sentence")
words = u"guion cruz envío papel otoño percha hazaña salir joya gorra íntimo actriz"
print("Your Mnemonic is   %s" % words)
seed = change_base(Mnemonic().to_seed(words, '1200 web development'), 256, 16)
hdk = HDKey().from_seed(seed)
print("Seed for HD Key    %s" % change_base(seed, 256, 16))
print("HD Key WIF is      %s" % hdk)
 
# And Japanese
print("\nGenerate a key from a Japanese UNICODE Mnemonic sentence")
words = "あじわう　ちしき　たわむれる　おくさま　しゃそう　うんこう　ひてい　みほん　たいほ　てのひら　りこう　わかれる　かいすいよく　こもん　ねもと"
print("Your Mnemonic is   %s" % words)
seed = change_base(Mnemonic().to_seed(words, '1200 web development'), 256, 16)
hdk = HDKey().from_seed(seed)
print("Seed for HD Key    %s" % change_base(seed, 256, 16))
print("HD Key WIF is      %s" % hdk)
```


### Wallet

This is a simple wallet implementation using sqlalchemy and sqllite3 to store keys in a Hierarchical Deterministic Way.

```python
from bitcoinlib.wallets import HDWallet
 
# -- Create New Wallet and Generate a some new Keys --
wallet = HDWallet.create(name='Personal', network='testnet')
wallet.new_account()
new_key1 = wallet.new_key()
new_key2 = wallet.new_key()
new_key3 = wallet.new_key()
new_key4 = wallet.new_key(change=1)
donations_account = wallet.new_account()
new_key5 = wallet.new_key(account_id=donations_account.account_id)
wallet.info(detail=3)
 
# -- Create New Wallet with Testnet master key and account ID 251 --
wallet_import = HDWallet.create(
    name='TestNetWallet',
    key='tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePy'
        'A7irEvBoe4aAn52',
    network='testnet',
    account_id=251)
wallet_import.new_account()
wallet_import.new_key("Faucet gift")
wallet_import.info(detail=3)
 
# -- Create New Wallet with account (depth=3) private key on bitcoin network and purpose 0 --
wallet_import2 = HDWallet.create(
    name='Company Wallet',
    key='xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjAN'
        'TtpgP4mLTj34bhnZX7UiM',
    network='bitcoin',
    account_id=2, purpose=0)
wallet_import2.info(detail=3)
```

## Installation

Install with pip

    pip install bitcoinlib
   

#### Package dependencies

Required Python Packages, are automatically installed upon installing bitcoinlib:
- ecdsa
- pbkdf2
- pycrypto
- scrypt
- sqlalchemy

#### Python development packages
    sudo apt install python-dev python3-dev

#### To install OpenSSL development package on Debian, Ubuntu or their derivatives:
    sudo apt install libssl-dev

#### To install OpenSSL development package on Fedora, CentOS or RHEL:
    sudo yum install openssl-devel


## References

- https://pypi.python.org/pypi/bitcoinlib/
- https://github.com/1200wd/bitcoinlib