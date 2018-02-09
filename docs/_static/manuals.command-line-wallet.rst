Command Line Wallet
===================

Manage wallets from commandline. Allows you to

* Show wallets and wallet info
* Create single and multisig wallets
* Delete wallets
* Generate receive addresses
* Create and send transactions

The Command Line wallet Script can be found in the tools directory. If you call the script without
arguments it will show all available wallets.

Specify a wallet name or wallet ID to show more information about a wallet. If you specify a wallet
which doesn't exists the script will ask you if you want to create a new wallet.


Create wallet
-------------

To create a wallet just specify an unused wallet name:

.. code-block:: none

    $ python cli-wallet.py mywallet
    Command Line Wallet for BitcoinLib

    Wallet mywallet does not exist, create new wallet [yN]? y

    CREATE wallet 'mywallet' (bitcoin network)

    Your mnemonic private key sentence is: mutual run dynamic armed brown meadow height elbow citizen put industry work

    Please write down on paper and backup. With this key you can restore your wallet and all keys

    Type 'yes' if you understood and wrote down your key: yes
    Updating wallet


Generate / show receive addresses
---------------------------------

To show an unused address to receive funds use the -r or --receive option. If you want to show QR
codes on the commandline install the pyqrcode module.

.. code-block:: none

    $ python cli-wallet.py mywallet -r
    Command Line Wallet for BitcoinLib

    Receive address is 1JMKBiiDMdjTx6rfqGumALvcRMX6DQNeG1


Send funds / create transaction
-------------------------------

To send funds use the -t option followed by the address and amount. You can also repeat this to
send to multiple addresses.

A manual fee can be entered with the -f / --fee option.

The default behavior is to just show the transaction info and raw transaction. You can push this
to the network with a 3rd party. Use the -p / --push option to push the transaction to the
network.

.. code-block:: none

    $ python cli-wallet.py -d dbtest mywallet -t 1FpBBJ2E9w9nqxHUAtQME8X4wGeAKBsKwZ 10000


Restore wallet with passphrase
------------------------------

To restore or create a wallet with a passphrase use new wallet name and the --passphrase option.
If it's an old wallet you can recreate and scan it with the -s option. This will create new
addresses and update unspend outputs.

.. code-block:: none

    $ python cli-wallet.py mywallet --passphrase "mutual run dynamic armed brown meadow height elbow citizen put industry work"
    $ python cli-wallet.py mywallet -s


Options Overview
----------------

Command Line Wallet for BitcoinLib

usage: cli-wallet.py [-h] [--network NETWORK] [--database DATABASE]
                     [--wallet-remove] [--list-wallets] [--wallet-info]
                     [--passphrase [PASSPHRASE [PASSPHRASE ...]]]
                     [--passphrase-strength PASSPHRASE_STRENGTH]
                     [--create-multisig [CREATE_MULTISIG [CREATE_MULTISIG ...]]]
                     [--receive] [--scan]
                     [--create-transaction [CREATE_TRANSACTION [CREATE_TRANSACTION ...]]]
                     [--fee FEE] [--push]
                     [wallet_name]

BitcoinLib CLI

positional arguments:
  wallet_name           Name of wallet to create or open. Used to store your
                        all your wallet keys and will be printed on each paper
                        wallet

optional arguments:
  -h, --help            show this help message and exit
  --network NETWORK, -n NETWORK
                        Specify 'bitcoin', 'testnet' or other supported
                        network
  --database DATABASE, -d DATABASE
                        Name of specific database file to use
  --wallet-remove       Name or ID of wallet to remove, all keys and related
                        information will be deleted
  --list-wallets, -l    List all known wallets in bitcoinlib database
  --wallet-info, -i     Show wallet information
  --passphrase [PASSPHRASE [PASSPHRASE ...]]
                        Passphrase to recover or create a wallet
  --passphrase-strength PASSPHRASE_STRENGTH
                        Number of bits for passphrase key
  --create-multisig [CREATE_MULTISIG [CREATE_MULTISIG ...]], -m [CREATE_MULTISIG [CREATE_MULTISIG ...]]
                        Specificy number of signatures required followed by a
                        list of signatures. Example: -m 2 tprv8ZgxMBicQKsPd1Q4
                        4tfDiZC98iYouKRC2CzjT3HGt1yYw2zuX2awTotzGAZQEAU9bi2M5M
                        Cj8iedP9MREPjUgpDEBwBgGi2C8eK5zNYeiX8 tprv8ZgxMBicQKsP
                        eUbMS6kswJc11zgVEXUnUZuGo3bF6bBrAg1ieFfUdPc9UHqbD5HcXi
                        zThrcKike1c4z6xHrz6MWGwy8L6YKVbgJMeQHdWDp
  --receive, -r         Show unused address to receive funds
  --scan, -s            Scan and update wallet with all addresses,
                        transactions and balances

Send / Create transaction:
  --create-transaction [CREATE_TRANSACTION [CREATE_TRANSACTION ...]], -t [CREATE_TRANSACTION [CREATE_TRANSACTION ...]]
                        Create transaction. Specify address followed by amount
  --fee FEE, -f FEE     Transaction fee
  --push, -p            Push created transaction to the network
