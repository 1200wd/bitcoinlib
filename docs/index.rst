.. Bitcoinlib documentation master file, created by
   sphinx-quickstart on Sat Apr  8 10:06:16 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Bitcoinlib's documentation!
======================================

Bitcoin and other Crypto Currency Library for Python.

Includes a fully functional wallet, with multi signature, multi currency and multiple accounts. Use this
library to create and manage transactions, addresses/keys, wallets, mnemonic password phrases and blocks with
simple and straightforward Python code.

You can use this library at a high level and create and manage wallets on the command line or at a low level
and create your own custom made transactions, scripts, keys or wallets.

The BitcoinLib connects to various service providers automatically to update wallets, transactions and
blockchain information.


Wallet
------

This Bitcoin Library contains a wallet implementation using SQLAlchemy and SQLite3, MySQL or PostgreSQL to
import, create and manage keys in a Hierarchical Deterministic way.

Example: Create wallet and generate new address (key) to receive bitcoins

.. code-block:: pycon

   >>> from bitcoinlib.wallets import Wallet
   >>> w = Wallet.create('Wallet1')
   >>> key1 = w.get_key()
   >>> key1.address
   '1Fo7STj6LdRhUuD1AiEsHpH65pXzraGJ9j'

Now send a small transaction to your wallet and use the scan() method to update transactions and UTXO's

.. code-block:: pycon

    >>> w.scan()
    >>> w.info()  # Shows wallet information, keys, transactions and UTXO's

When your wallet received a payment and has unspent transaction outputs, you can send bitcoins easily.
If successful a transaction ID is returned

.. code-block:: pycon

    >>> t = w.send_to('1PWXhWvUH3bcDWn6Fdq3xhMRPfxRXTjAi1', '0.001 BTC')
    'b7feea5e7c79d4f6f343b5ca28fa2a1fcacfe9a2b7f44f3d2fd8d6c2d82c4078'
    >>> t.info  # Shows transaction information and send results



Segregated Witness Wallet
-------------------------

Easily create and manage Segwit wallets. Both native Segwit with base32/bech32 addresses and P2SH nested Segwit
wallets with traditional addresses are available.

Create a native single key P2WPKH wallet:

.. code-block:: pycon

    >>> from bitcoinlib.wallets import Wallet
    >>> w = Wallet.create('segwit_p2wpkh', witness_type='segwit')
    >>> w.get_key().address
    bc1q84y2quplejutvu0h4gw9hy59fppu3thg0u2xz3

Or create a P2SH nested single key P2SH_P2WPKH wallet:

.. code-block:: pycon

    >>> from bitcoinlib.wallets import Wallet
    >>> w = Wallet.create('segwit_p2sh_p2wpkh', witness_type='p2sh-segwit')
    >>> w.get_key().address
    36ESSWgR4WxXJSc4ysDSJvecyY6FJkhUbp


Wallet from passphrase with accounts and multiple currencies
------------------------------------------------------------

The following code creates a wallet with two bitcoin and one litecoin account from a Mnemonic passphrase.
The complete wallet can be recovered from the passphrase which is the masterkey.

.. code-block:: python

    from bitcoinlib.wallets import Wallet, wallet_delete
    from bitcoinlib.mnemonic import Mnemonic

    passphrase = Mnemonic().generate()
    print(passphrase)
    w = Wallet.create("Wallet2", keys=passphrase, network='bitcoin')
    account_btc2 = w.new_account('Account BTC 2')
    account_ltc1 = w.new_account('Account LTC', network='litecoin')
    w.get_key()
    w.get_key(account_btc2.account_id)
    w.get_key(account_ltc1.account_id)
    w.info()


Multi Signature Wallets
-----------------------

Create a Multisig wallet with 2 cosigners which both need to sign a transaction.

.. code-block:: python

    from bitcoinlib.wallets import Wallet
    from bitcoinlib.keys import HDKey

    NETWORK = 'testnet'
    k1 = HDKey('tprv8ZgxMBicQKsPd1Q44tfDiZC98iYouKRC2CzjT3HGt1yYw2zuX2awTotzGAZQEAU9bi2M5MCj8iedP9MREPjUgpDEBwBgGi2C8eK'
               '5zNYeiX8', network=NETWORK)
    k2 = HDKey('tprv8ZgxMBicQKsPeUbMS6kswJc11zgVEXUnUZuGo3bF6bBrAg1ieFfUdPc9UHqbD5HcXizThrcKike1c4z6xHrz6MWGwy8L6YKVbgJ'
               'MeQHdWDp', network=NETWORK)
    w1 = Wallet.create('multisig_2of2_cosigner1', sigs_required=2,
                         keys=[k1, k2.public_master(multisig=True)], network=NETWORK)
    w2 = Wallet.create('multisig_2of2_cosigner2',  sigs_required=2,
                         keys=[k1.public_master(multisig=True), k2], network=NETWORK)
    print("Deposit testnet bitcoin to this address to create transaction: ", w1.get_key().address)

Create a transaction in the first wallet

.. code-block:: python

    w1.utxos_update()
    t = w1.sweep('mwCwTceJvYV27KXBc3NJZys6CjsgsoeHmf', min_confirms=0)
    t.info()

And then import the transaction in the second wallet, sign it and push it to the network

.. code-block:: python

    w2.get_key()
    t2 = w2.transaction_import(t)
    t2.sign()
    t2.send()
    t2.info()


Command Line Tool
-----------------

With the command line tool you can create and manage wallet without any Python programming.

To create a new Bitcoin wallet

.. code-block:: bash

    $ clw newwallet
    Command Line Wallet for BitcoinLib

    Wallet newwallet does not exist, create new wallet [yN]? y

    CREATE wallet 'newwallet' (bitcoin network)

    Your mnemonic private key sentence is: force humble chair kiss season ready elbow cool awake divorce famous tunnel

    Please write down on paper and backup. With this key you can restore your wallet and all keys

You can use the command line wallet 'clw' to create simple or multisig wallets for various networks,
manage public and private keys and managing transactions.

For the full command line wallet documentation please read

http://bitcoinlib.readthedocs.io/en/latest/_static/manuals.command-line-wallet.html


Service providers
-----------------

Communicates with pools of bitcoin service providers to retreive transaction, address, blockchain information.
To push a transaction to the network. To determine optimal service fee for a transaction. Or to update your
wallet's balance.

Example: Get estimated transactionfee in Sathosis per Kb for confirmation within 5 blocks

.. code-block:: pycon

   >>> from bitcoinlib.services.services import Service
   >>> Service().estimatefee(5)
   138964


Other Databases
---------------

Bitcoinlib uses the SQLite database by default but other databases are supported as well.
See http://bitcoinlib.readthedocs.io/en/latest/_static/manuals.databases.html for instructions on how to use
MySQL or PostgreSQL.


More examples
-------------
For more examples see https://github.com/1200wd/bitcoinlib/tree/master/examples


.. toctree::
   :caption: Manuals
   :maxdepth: 4

   Installation and Settings <source/_static/manuals.install>
   source/_static/manuals.command-line-wallet
   Add Service Provider <source/_static/manuals.add-provider>
   Bitcoind Node <source/_static/manuals.setup-bitcoind-connection>
   Databases <source/_static/manuals.databases>
   Encrypted Database <source/_static/manuals.sqlcipher>
   Security & Privacy <source/_static/manuals.security>
   source/_static/manuals.caching


.. toctree::
   :caption: Classes
   :maxdepth: 1

   Key <source/bitcoinlib.keys>
   Transaction <source/bitcoinlib.transactions>
   Wallet <source/bitcoinlib.wallets>
   Mnemonic <source/bitcoinlib.mnemonic>
   Network <source/bitcoinlib.networks>
   Block <source/bitcoinlib.blocks>
   Value <source/bitcoinlib.values>
   Service <source/bitcoinlib.services.services>
   Service providers <source/bitcoinlib.services>
   Config <source/bitcoinlib.config>
   Database <source/bitcoinlib.db>
   Cache <source/bitcoinlib.db_cache>

.. toctree::
   :caption: Reference
   :maxdepth: 1

   source/_static/classes-overview
   Modules <source/modules>
   Encoding <source/bitcoinlib.encoding>
   Tools <source/bitcoinlib.tools>
   source/_static/script-types-overview


Disclaimer
----------

This library is still in development, please use at your own risk and test sufficiently before using it in a
production environment.


Schematic overview
------------------

.. image:: _static/classes-overview.jpg
.. image:: _static/classes-overview-detailed.jpg


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
