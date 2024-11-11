Command Line Wallet
===================

Manage Bitcoin wallets from commandline

The Command Line wallet Script can be found in the tools directory. If you call the script without
arguments it will show all available wallets.

Specify a wallet name or wallet ID to show more information about a wallet. If you specify a wallet
which doesn't exist the script will ask you if you want to create a new wallet.


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


Encrypt private key fields
--------------------------

Bitcoinlib has build in functionality to encrypt private key fields in the database. If you provide a password in
the runtime environment the data is encrypted at low level in the database module. You can provide a 32 byte key
in the DB_FIELD_ENCRYPTION_KEY variable or a password in the DB_FIELD_ENCRYPTION_PASSWORD variable.

.. code-block:: bash

    $ export DB_FIELD_ENCRYPTION_PASSWORD=iforgot
    $ clw new -w cryptwallet
    Command Line Wallet - BitcoinLib 0.6.14

    CREATE wallet 'cryptwallet' (bitcoin network)
    Passphrase: job giant vendor side oil embrace true cushion have matrix glimpse rack
    Please write down on paper and backup. With this key you can restore your wallet and all keys

    Type 'yes' if you understood and wrote down your key: yes
    ... wallet info ...

    $ clw -w cryptwallet -r
    Command Line Wallet - BitcoinLib 0.6.14

    Receive address: bc1q2cr0chgs6530mdpag2rfn7v9nt232nlpqcc4kc
    Install qr code module to show QR codes: pip install pyqrcode

If we now remove the password from the environment, we cannot open the wallet anymore:

.. code-block:: bash

    $ export DB_FIELD_ENCRYPTION_PASSWORD=
    $ clw -w cryptwallet -i
    Command Line Wallet - BitcoinLib 0.6.14

    ValueError: Data is encrypted please provide key in environment


Example: Multi-signature Bitcoinlib test wallet
-----------------------------------------------

First we generate 2 private keys to create a 2-of-2 multisig wallet:

.. code-block:: bash

    $ clw -g -n bitcoinlib_test -y
    Command Line Wallet - BitcoinLib 0.6.14

    Passphrase: marine kiwi great try know scan rigid indicate place gossip fault liquid
    Please write down on paper and backup. With this key you can restore your wallet and all keys

    Type 'yes' if you understood and wrote down your key: yes
    Private Master key, to create multisig wallet on this machine:
    BC19UtECk2r9PVQYhY4yboRf92XKEnKZf9hQEd1qBqCgQ98HkBeysLPqYewcWDUuaBRSSVXCShDfmhpbtgZ33sWeGPqfwoLwamzPEcnfwLoeqfQM
    Public Master key, to share with other cosigner multisig wallets:
    BC18rEEZrakM87qWbSSUv19vnRkEFL7ZtNtGx3exB886VbeFZp6aq9JLZucYAj1EtsHKUB2mkjvafCCGaeYeUVtdFcz5xTxTTgEPCE8fDC8LcahM
    Network: bitcoinlib_test

    $ clw -g -n bitcoinlib_test -y
    Command Line Wallet - BitcoinLib 0.6.14

    Passphrase: trumpet utility cotton couch hard shadow ivory alpha glance pear snow emerge
    Please write down on paper and backup. With this key you can restore your wallet and all keys
    Private Master key, to create multisig wallet on this machine:
    BC19UtECk2r9PVQYhaAa8kEgBMPWHC4fJVJD48zBMMb9gSpY9LQVvQ1HhzB3Xmkm2BpiH5SyWoboiewpbeexPLsw8QBfAqMbDfet6kLhedtfQF8r
    Public Master key, to share with other cosigner multisig wallets:
    BC18rEEvE8begagfJs7kdxx1yW9tFsz7879c9vQQ2mnGbF6WSeKuBEGtmxJYLEy8rpVV9wXffbBtnL1LPKZqujPtEKzHqQeERiRybKB3DRBBoSFH
    Network: bitcoinlib_test

The -g / --generate-key is used to generate a private key passphrase.
With -n / --network we specify the bitcoinlib_test network. This isn't actually a network but allows us to create and
verify transactions.
The -y / --yes options, skips the required user input.
We now use 1 private and 1 public key to create a wallet.

.. code-block:: bash

    $ clw new -w multisig-2-2 -n bitcoinlib_test -m 2 2 BC19UtECk2r9PVQYhY4yboRf92XKEnKZf9hQEd1qBqCgQ98HkBeysLPqYewcWDUuaBRSSVXCShDfmhpbtgZ33sWeGPqfwoLwamzPEcnfwLoeqfQM BC18rEEvE8begagfJs7kdxx1yW9tFsz7879c9vQQ2mnGbF6WSeKuBEGtmxJYLEy8rpVV9wXffbBtnL1LPKZqujPtEKzHqQeERiRybKB3DRBBoSFH

    Command Line Wallet - BitcoinLib 0.6.14

    CREATE wallet 'ms22' (bitcoinlib_test network)
    Wallet info for ms22
    === WALLET ===
     ID                             22
     Name                           ms22
     Owner
     Scheme                         bip32
     Multisig                       True
     Multisig Wallet IDs            23, 24
     Cosigner ID                    1
     Witness type                   segwit
     Main network                   bitcoinlib_test
     Latest update                  None

    = Multisig Public Master Keys =
        0 183 BC18rEEvE8begagfJs7kdxx1yW9tFsz7879c9vQQ2mnGbF6WSeKuBEGtmxJYLEy8rpVV9wXffbBtnL1LPKZqujPtEKzHqQeERiRybKB3DRBBoSFH bip32  cosigner
        1 186 BC18rEEZrakM87qWbSSUv19vnRkEFL7ZtNtGx3exB886VbeFZp6aq9JLZucYAj1EtsHKUB2mkjvafCCGaeYeUVtdFcz5xTxTTgEPCE8fDC8LcahM bip32  main     *
    For main keys a private master key is available in this wallet to sign transactions. * cosigner key for this wallet

    - NETWORK: bitcoinlib_test -
    - - Keys

    - - Transactions Account 0 (0)

    = Balance Totals (includes unconfirmed) =

The multisig wallet has been created, you can view the wallet info by using the -i / --wallet-info option. Now we
generate a new receiving address with the -r / --receive option and update the unspent outputs with the
-x / --update-utxos option.

.. code-block:: bash

    $ clw -w ms22 -r
    Command Line Wallet - BitcoinLib 0.6.14

    Receive address: blt1qxu6z7evkrmz5s7sk63dr0u3h9xsf2j2vys88reg75cjvjuz4vf2srkxp7p
    Install qr code module to show QR codes: pip install pyqrcode

    $ clw -w ms22 -x
    Command Line Wallet - BitcoinLib 0.6.14

    Updating wallet utxo's
    $ clw -w ms22 -i
    Command Line Wallet - BitcoinLib 0.6.14

    Wallet info for ms22
    === WALLET ===
     ID                             22
     Name                           ms22
     Owner
     Scheme                         bip32
     Multisig                       True
     Multisig Wallet IDs            23, 24
     Cosigner ID                    1
     Witness type                   segwit
     Main network                   bitcoinlib_test
     Latest update                  None

    = Multisig Public Master Keys =
        0 183 BC18rEEvE8begagfJs7kdxx1yW9tFsz7879c9vQQ2mnGbF6WSeKuBEGtmxJYLEy8rpVV9wXffbBtnL1LPKZqujPtEKzHqQeERiRybKB3DRBBoSFH bip32  cosigner
        1 186 BC18rEEZrakM87qWbSSUv19vnRkEFL7ZtNtGx3exB886VbeFZp6aq9JLZucYAj1EtsHKUB2mkjvafCCGaeYeUVtdFcz5xTxTTgEPCE8fDC8LcahM bip32  main     *
    For main keys a private master key is available in this wallet to sign transactions. * cosigner key for this wallet

    - NETWORK: bitcoinlib_test -
    - - Keys
      193 m/48`/9999999`/0`/2`/0/0     blt1qxu6z7evkrmz5s7sk63dr0u3h9xsf2j2vys88reg75cjvjuz4vf2srkxp7p Multisig Key 185/192                   2.00000000 T

    - - Transactions Account 0 (2)
    7b020ae9c7f8ba84a5a5136ae32e6195af5a4f25316f790a1278e04f479ca77d blt1qxu6z7evkrmz5s7sk63dr0u3h9xsf2j2vys88reg75cjvjuz4vf2srkxp7p       10          1.00000000 T U
    5d0f176259ab4bc596363aa3653c44858ebeb2fd8361311966776192968e545d blt1qxu6z7evkrmz5s7sk63dr0u3h9xsf2j2vys88reg75cjvjuz4vf2srkxp7p       10          1.00000000 T U

    = Balance Totals (includes unconfirmed) =
    bitcoinlib_test      (Account 0)                  2.00000000 T

We now have some utxo's in our wallet so we can create a transaction

.. code-block:: bash

    $ clw -w ms22 -s blt1qxu6z7evkrmz5s7sk63dr0u3h9xsf2j2vys88reg75cjvjuz4vf2srkxp7p 0.1
    Connected to pydev debugger (build 233.13135.95)
    Command Line Wallet - BitcoinLib 0.6.14

    Transaction created
    Transaction 3b96f493d189667565271041abbc0efbd8631bb54d76decb90e144bb145fa613
    Date: None
    Network: bitcoinlib_test
    Version: 1
    Witness type: segwit
    Status: new
    Verified: False
    Inputs
    - blt1qxu6z7evkrmz5s7sk63dr0u3h9xsf2j2vys88reg75cjvjuz4vf2srkxp7p 1.00000000 TST 7b020ae9c7f8ba84a5a5136ae32e6195af5a4f25316f790a1278e04f479ca77d 0
      segwit p2sh_multisig; sigs: 1 (2-of-2) not validated
    Outputs
    - blt1qxu6z7evkrmz5s7sk63dr0u3h9xsf2j2vys88reg75cjvjuz4vf2srkxp7p 0.10000000 TST p2wsh U
    - blt1qe4tr993nftagprtapclxrm7ahrcvl4w0dnxfnhz2cx6pjaeg989syy9zge 0.89993601 TST p2wsh U
    Size: 192
    Vsize: 192
    Fee: 6399
    Confirmations: None
    Block: None
    Pushed to network: False
    Wallet: ms22

    Transaction created but not sent yet. Transaction dictionary for export:
    {<dictionary>}

Copy the contents of the dictionary and save it as 3b96f493d189667565271041abbc0efbd8631bb54d76decb90e144bb145fa613.tx

The transaction has been created, but cannot be verified because the wallet contains only 1 private key. So we need to
create another wallet with the other private key, in real life situations this would be on another (offline) machine.

Below we create a new wallet, generate a receive address and update the utxo's. Finally we can import the transaction
dictionary which we be signed once imported. And as you can see the transaction has been verified now!

.. code-block:: bash

    $ clw new -w multisig-2-2-signer2 -n bitcoinlib_test -m 2 2 BC18rEEZrakM87qWbSSUv19vnRkEFL7ZtNtGx3exB886VbeFZp6aq9JLZucYAj1EtsHKUB2mkjvafCCGaeYeUVtdFcz5xTxTTgEPCE8fDC8LcahM BC19UtECk2r9PVQYhaAa8kEgBMPWHC4fJVJD48zBMMb9gSpY9LQVvQ1HhzB3Xmkm2BpiH5SyWoboiewpbeexPLsw8QBfAqMbDfet6kLhedtfQF8r
    $ clw -w multisig-2-2-signer2 -r
    $ clw -w multisig-2-2-signer2 -x
    $ clw -w multisig-2-2-signer2 -a tx.tx
    Command Line Wallet - BitcoinLib 0.6.14

    Transaction 3b96f493d189667565271041abbc0efbd8631bb54d76decb90e144bb145fa613
    Date: None
    Network: bitcoinlib_test
    Version: 1
    Witness type: segwit
    Status: new
    Verified: True
    Inputs
    - blt1qxu6z7evkrmz5s7sk63dr0u3h9xsf2j2vys88reg75cjvjuz4vf2srkxp7p 1.00000000 TST 7b020ae9c7f8ba84a5a5136ae32e6195af5a4f25316f790a1278e04f479ca77d 0
      segwit p2sh_multisig; sigs: 2 (2-of-2) valid
    Outputs
    - blt1qxu6z7evkrmz5s7sk63dr0u3h9xsf2j2vys88reg75cjvjuz4vf2srkxp7p 0.10000000 TST p2wsh U
    - blt1qe4tr993nftagprtapclxrm7ahrcvl4w0dnxfnhz2cx6pjaeg989syy9zge 0.89993601 TST p2wsh U
    Size: 192
    Vsize: 192
    Fee: 6399
    Confirmations: None
    Block: None
    Pushed to network: False
    Wallet: multisig-2-2-signer2


    Signed transaction:
    {<dictionary>}


Options Overview
----------------

Command Line Wallet for BitcoinLib

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
  --quiet, -q           Quiet mode, no output written to console

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
                        Set this if wallet contains only public keys, more than one private key or if you would like to create keys for other cosigners.
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


Options overview: New Wallet
----------------------------

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
  --quiet, -q           Quiet mode, no output written to console


