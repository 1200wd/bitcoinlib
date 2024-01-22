Command Line Wallet
===================

Manage Bitcoin wallets from commandline

The Command Line wallet Script can be found in the tools directory. If you call the script without
arguments it will show all available wallets.

Specify a wallet name or wallet ID to show more information about a wallet. If you specify a wallet
which doesn't exists the script will ask you if you want to create a new wallet.


Create wallet
-------------

To create a wallet just specify an unused wallet name:

.. code-block:: none

    $ clw new -w mywallet
    CREATE wallet 'newwallet' (bitcoin network)
    Passphrase: sibling undo gift cat garage survey taxi index admit odor surface waste
    Please write down on paper and backup. With this key you can restore your wallet and all keys

    Type 'yes' if you understood and wrote down your key: yes
    Wallet info for newwallet
    === WALLET ===
     ID                             21
     Name                           newwallet
     Owner
     Scheme                         bip32
     Multisig                       False
     Witness type                   segwit
     Main network                   bitcoin
     Latest update                  None

    = Wallet Master Key =
     ID                             177
     Private                        True
     Depth                          0

    - NETWORK: bitcoin -
    - - Keys
      182 m/84'/0'/0'/0/0              bc1qza24j7snqlmx7603z8qplm4rzfkr0p0mneraqv    address index 0                        0.00000000 ₿

    - - Transactions Account 0 (0)

    = Balance Totals (includes unconfirmed) =



Generate / show receive addresses
---------------------------------

To show an unused address to receive funds use the -r or --receive option. If you want to show QR
codes on the commandline install the pyqrcode module.

.. code-block:: none

    $ clw -w mywallet -r
    Command Line Wallet for BitcoinLib

    Receive address is bc1qza24j7snqlmx7603z8qplm4rzfkr0p0mneraqv


Send funds / create transaction
-------------------------------

To send funds use the -t option followed by the address and amount. You can also repeat this to
send to multiple addresses.

A manual fee can be entered with the -f / --fee option.

The default behavior is to just show the transaction info and raw transaction. You can push this
to the network with a 3rd party. Use the -p / --push option to push the transaction to the
network.

.. code-block:: none

    $ clw -w mywallet -d dbtest -t bc1qza24j7snqlmx7603z8qplm4rzfkr0p0mneraqv 10000


Restore wallet with passphrase
------------------------------

To restore or create a wallet with a passphrase use new wallet name and the --passphrase option.
If it's an old wallet you can recreate and scan it with the -u / --update-transactions option. This will create new
addresses and update unspent outputs.

.. code-block:: none

    $ clw new -w mywallet --passphrase "mutual run dynamic armed brown meadow height elbow citizen put industry work"
    $ clw mywallet -ui

The -i / --wallet-info shows the contents of the updated wallet.

Options Overview
----------------

Command Line Wallet for BitcoinLib

.. code-block:: none

usage: clw.py [-h] [--list-wallets] [--generate-key] [--passphrase-strength PASSPHRASE_STRENGTH] [--database DATABASE] [--wallet_name [WALLET_NAME]] [--network NETWORK] [--witness-type WITNESS_TYPE] [--yes]
              [--quiet] [--wallet-remove] [--wallet-info] [--update-utxos] [--update-transactions] [--wallet-empty] [--receive] [--cosigner-id COSIGNER_ID] [--export-private]
              [--import-private IMPORT_PRIVATE] [--send ADDRESS AMOUNT] [--number-of-change-outputs NUMBER_OF_CHANGE_OUTPUTS] [--input-key-id INPUT_KEY_ID] [--sweep ADDRESS] [--fee FEE]
              [--fee-per-kb FEE_PER_KB] [--push] [--import-tx TRANSACTION] [--import-tx-file FILENAME_TRANSACTION]
              {new} ...

BitcoinLib command line wallet

positional arguments:
  {new}

options:
  -h, --help            show this help message and exit
  --list-wallets, -l    List all known wallets in database
  --generate-key, -g    Generate a new masterkey, and show passphrase, WIF and public account key. Can be used to create a new (multisig) wallet
  --passphrase-strength PASSPHRASE_STRENGTH
                        Number of bits for passphrase key. Default is 128, lower is not advised but can be used for testing. Set to 256 bits for more future-proof passphrases
  --database DATABASE, -d DATABASE
                        URI of the database to use
  --wallet_name [WALLET_NAME], -w [WALLET_NAME]
                        Name of wallet to create or open. Provide wallet name or number when running wallet actions
  --network NETWORK, -n NETWORK
                        Specify 'bitcoin', 'litecoin', 'testnet' or other supported network
  --witness-type WITNESS_TYPE, -j WITNESS_TYPE
                        Witness type of wallet: legacy, p2sh-segwit or segwit (default)
  --yes, -y             Non-interactive mode, does not prompt for confirmation
  --quiet, -q           Quiet mode, no output writen to console

Wallet Actions:
  --wallet-remove       Name or ID of wallet to remove, all keys and transactions will be deleted
  --wallet-info, -i     Show wallet information
  --update-utxos, -x    Update unspent transaction outputs (UTXO's) for this wallet
  --update-transactions, -u
                        Update all transactions and UTXO's for this wallet
  --wallet-empty, -z    Delete all keys and transactions from wallet, except for the masterkey(s). Use when updating fails or other errors occur. Please backup your database and masterkeys first. Update
                        empty wallet again to restore your wallet.
  --receive, -r         Show unused address to receive funds.
  --cosigner-id COSIGNER_ID, -o COSIGNER_ID
                        Set this if wallet contains only public keys, more then one private key or if you would like to create keys for other cosigners.
  --export-private, -e  Export private key for this wallet and exit
  --import-private IMPORT_PRIVATE, -v IMPORT_PRIVATE
                        Import private key in this wallet

Transactions:
  --send ADDRESS AMOUNT, -s ADDRESS AMOUNT
                        Create transaction to send amount to specified address. To send to multiple addresses, argument can be used multiple times.
  --number-of-change-outputs NUMBER_OF_CHANGE_OUTPUTS
                        Number of change outputs. Default is 1, increase for more privacy or to split funds
  --input-key-id INPUT_KEY_ID, -k INPUT_KEY_ID
                        Use to create transaction with 1 specific key ID
  --sweep ADDRESS       Sweep wallet, transfer all funds to specified address
  --fee FEE, -f FEE     Transaction fee
  --fee-per-kb FEE_PER_KB, -b FEE_PER_KB
                        Transaction fee in satoshi per kilobyte
  --push, -p            Push created transaction to the network
  --import-tx TRANSACTION
                        Import raw transaction hash or transaction dictionary in wallet and sign it with available key(s)
  --import-tx-file FILENAME_TRANSACTION, -a FILENAME_TRANSACTION
                        Import transaction dictionary or raw transaction string from specified filename and sign it with available key(s)


And create new wallet options:

.. code-block:: none

usage: clw.py new [-h] --wallet_name [WALLET_NAME] [--password PASSWORD] [--network NETWORK] [--passphrase PASSPHRASE] [--create-from-key KEY] [--create-multisig [. ...]] [--witness-type WITNESS_TYPE]
                  [--cosigner-id COSIGNER_ID] [--database DATABASE] [--receive] [--yes] [--quiet]

Create new wallet

options:
  -h, --help            show this help message and exit
  --wallet_name [WALLET_NAME], -w [WALLET_NAME]
                        Name of wallet to create or open. Provide wallet name or number when running wallet actions
  --password PASSWORD   Password for BIP38 encrypted key. Use to create a wallet with a protected key
  --network NETWORK, -n NETWORK
                        Specify 'bitcoin', 'litecoin', 'testnet' or other supported network
  --passphrase PASSPHRASE
                        Passphrase to recover or create a wallet. Usually 12 or 24 words
  --create-from-key KEY, -c KEY
                        Create a new wallet from specified key
  --create-multisig [. ...], -m [. ...]
                        [NUMBER_OF_SIGNATURES_REQUIRED, NUMBER_OF_SIGNATURES, KEY-1, KEY-2, ... KEY-N]Specify number of signatures followed by the number of signatures required and then a list of public or
                        private keys for this wallet. Private keys will be created if not provided in key list. Example, create a 2-of-2 multisig wallet and provide 1 key and create another key: -m 2 2
                        tprv8ZgxMBicQKsPd1Q44tfDiZC98iYouKRC2CzjT3HGt1yYw2zuX2awTotzGAZQEAU9bi2M5MCj8iedP9MREPjUgpDEBwBgGi2C8eK5zNYeiX8
                        tprv8ZgxMBicQKsPeUbMS6kswJc11zgVEXUnUZuGo3bF6bBrAg1ieFfUdPc9UHqbD5HcXizThrcKike1c4z6xHrz6MWGwy8L6YKVbgJMeQHdWDp
  --witness-type WITNESS_TYPE, -j WITNESS_TYPE
                        Witness type of wallet: legacy, p2sh-segwit or segwit (default)
  --cosigner-id COSIGNER_ID, -o COSIGNER_ID
                        Set this if wallet contains only public keys, more then one private key or if you would like to create keys for other cosigners.
  --database DATABASE, -d DATABASE
                        URI of the database to use
  --receive, -r         Show unused address to receive funds.
  --yes, -y             Non-interactive mode, does not prompt for confirmation
  --quiet, -q           Quit mode, no output writen to console.


