.. Bitcoinlib documentation master file, created by
   sphinx-quickstart on Sat Apr  8 10:06:16 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Bitcoinlib's documentation!
======================================

Bitcoin and other Cryptocurrencies Library for Python. Includes a fully functional
wallet, Mnemonic key generation and management and connection
with various service providers to receive and send blockchain and transaction information.


Wallet
------

The bitcoinlibrary contains a wallet implementation using sqlalchemy and sqllite3 to import, create and manage
keys in a Hierarchical Deterministic Way.

Example: Create wallet and generate new key to receive bitcoins

.. code-block:: python

   >>> from bitcoinlib.wallets import HDWallet
   >>> w = HDWallet.create('Wallet1')
   >>> w
   <HDWallet (id=1, name=Wallet1, network=bitcoin)>
   >>> key1 = w.new_key()
   >>> key1
   <HDWalletKey (name=Key 0, wif=xprvA4B..etc..6HZKGW7Kozc, path=m/44'/0'/0'/0/0)>
   >>> key1.address
   '1Fo7STj6LdRhUuD1AiEsHpH65pXzraGJ9j'


When your wallet received a payment and has unspent transaction outputs, you can send bitcoins easily.
If succesfull a transaction ID is returned

.. code-block:: python

   >>> w.send_to('12ooWd8Xag7hsgP9PBPnmyGe36VeUrpMSH', 100000)
   'b7feea5e7c79d4f6f343b5ca28fa2a1fcacfe9a2b7f44f3d2fd8d6c2d82c4078'


Mnemonic Keys
-------------

Allows you to use easy to remember passphrases consisting of a number of words to store private keys (BIP0039).
You can password protect this passphrase (BIP0038), and use the HD Wallet structure to generate a almost infinite
number of new private keys and bitcoin addresses (BIP0043 and BIP0044).

Example: Generate a list of words passphrase and derive a private key seed

.. code-block:: python

   >>> from bitcoinlib.mnemonic import Mnemonic
   >>> words = Mnemonic().generate()
   >>> words
   protect dumb smart toddler journey spawn same dry season ecology scissors more
   >>> Mnemonic().to_seed(words)
   ..very long and ugly byte string which can be used as private key


Service providers
-----------------

Communicates with pools of bitcoin service providers to retreive transaction, address, blockchain information.
To push a transaction to the network. To determine optimal service fee for a transaction. Or to update your
wallet's balance.

Example: Get estimated transactionfee in sathosis per Kb for confirmation within 5 blocks

.. code-block:: python

   >>> from bitcoinlib.services.services import Service
   >>> Service().estimatefee(5)
   138964



.. toctree::
   :caption: Manuals
   :maxdepth: 1

   _static/manuals.install
   _static/manuals.command-line-wallet
   _static/manuals.add-provider



.. toctree::
   :caption: Reference
   :maxdepth: 1

   source/modules
   source/bitcoinlib.config
   source/bitcoinlib.db
   source/bitcoinlib.encoding
   source/bitcoinlib.keys
   source/bitcoinlib.mnemonic
   source/bitcoinlib.networks
   source/bitcoinlib.services
   source/bitcoinlib.transactions
   source/bitcoinlib.wallets


Disclaimer
----------

This library is still in development, please use at your own risk and test sufficiently before using it in a
production environment. Support for Litecoin and Dash is just for read only wallet, not for creating or
sending transactions.


Schematic overview
------------------

.. image:: _static/classes-overview.jpg
.. image:: _static/classes-overview-detailed.jpg


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
