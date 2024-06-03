Python Bitcoin Library
======================

Bitcoin cryptocurrency Library writen in Python.

Allows you to create a fully functional Bitcoin wallet with a single line of code.
Use this library to create and manage transactions, addresses/keys, wallets, mnemonic password phrases
and blocks with simple and straightforward Python code.

You can use this library at a high level and create and manage wallets from the command line or at a low level
and create your own custom made transactions, scripts, keys or wallets.

The BitcoinLib connects to various service providers automatically to update wallets, transaction and
blockchain information. You can also connect to a local
`Bitcoin <https://bitcoinlib.readthedocs.io/en/latest/source/_static/manuals.setup-bitcoind-connection.html>`_ or
`Bcoin node <https://bitcoinlib.readthedocs.io/en/latest/source/_static/manuals.setup-bcoin.html>`_.


.. image:: https://github.com/1200wd/bitcoinlib/actions/workflows/unittests.yaml/badge.svg
    :target: https://github.com/1200wd/bitcoinlib/actions/workflows/unittests.yaml
    :alt: Unittests
.. image:: https://img.shields.io/pypi/v/bitcoinlib.svg
    :target: https://pypi.org/pypi/bitcoinlib/
    :alt: PyPi
.. image:: https://readthedocs.org/projects/bitcoinlib/badge/?version=latest
    :target: http://bitcoinlib.readthedocs.io/en/latest/?badge=latest
    :alt: RTD
.. image:: https://coveralls.io/repos/github/1200wd/bitcoinlib/badge.svg?branch=installation-documentation-update
    :target: https://coveralls.io/github/1200wd/bitcoinlib?branch=master
    :alt: Coveralls


Install
-------

Install required packages on Ubuntu or related Linux systems:

.. code-block:: bash

    $ sudo apt install build-essential python3-dev libgmp3-dev

Then install using pip

.. code-block:: bash

    $ pip install bitcoinlib

Check out the `more detailed installation instructions <https://bitcoinlib.readthedocs.io/en/latest/source/_static/manuals.install.html>`_ to read how to install on other systems or for
troubleshooting.

If you are using docker you can check some Dockerfiles to create images in the
`docker <https://github.com/1200wd/bitcoinlib/tree/master/docker>`_ directory.

Documentation
-------------

Read the full documentation at: http://bitcoinlib.readthedocs.io/


Example
-------

The bitcoin library contains a wallet implementation using SQLAlchemy and SQLite3 to import, create and manage
keys in a Hierarchical Deterministic way.

Example: Create wallet and generate new address (key) to receive bitcoins

.. code-block:: pycon

   >>> from bitcoinlib.wallets import Wallet
   >>> w = Wallet.create('Wallet1')
   >>> w.get_key().address
   'bc1qk25wwkvz3am9smmm3372xct5s7cwf0hmnq8szj'

Now send a small transaction to your wallet and use the scan() method to update transactions and UTXO's

.. code-block:: pycon

    >>> w.scan()
    >>> w.info()  # Shows wallet information, keys, transactions and UTXO's

When your wallet received a payment and has unspent transaction outputs, you can send bitcoins easily.
If successful a transaction ID is returned

.. code-block:: pycon

    >>> t = w.send_to('bc1qemtr8ywkzg483g8m34ukz2l4pl3730776vzq54', '0.001 BTC', offline=False)
    'b7feea5e7c79d4f6f343b5ca28fa2a1fcacfe9a2b7f44f3d2fd8d6c2d82c4078'
    >>> t.info  # Shows transaction information and send results


More examples
-------------

You can find many more examples in the `documentation <https://bitcoinlib.readthedocs.io/en/latest/>`_
for instance about the `Wallet.create() <https://bitcoinlib.readthedocs.io/en/latest/source/bitcoinlib.wallets.html#bitcoinlib.wallets.Wallet.create>`_ method.

There are many working examples on how to create wallets, specific transactions, encrypted databases, parse the
blockchain, connect to specific service providers in the `examples directory <https://github.com/1200wd/bitcoinlib/tree/master/examples>`_ in the source code of this library.

Some more specific examples can be found on the `Coineva website <https://coineva.com/category/bitcoinlib.html>`_.

Contact
-------

If you have any questions, encounter a problem or want to share an idea, please use `Github Discussions
<https://github.com/1200wd/bitcoinlib/discussions>`_


Implements the following Bitcoin Improvement Proposals
------------------------------------------------------
- Hierarchical Deterministic Wallets (BIP0032)
- Passphrase-protected private key (BIP0038)
- Mnemonic code for generating deterministic keys (BIP0039)
- Purpose Field for Deterministic Wallets (BIP0043)
- Multi-Account Hierarchy for Deterministic Wallets (BIP0044)
- Structure for Deterministic P2SH Multisignature Wallets (BIP0045)
- Bech32/base32 address format for native v0-16 witness outputs (BIP0173)
- Native and P2SH nested Segregated Witness transactions (BIP0141 and BIP0143)
- Bech32m format for v1+ witness addresses (BIP0350)
- and many more...


Future / Roadmap
----------------

- Fully support timelocks
- Support Taproot and Schnorr signatures
- Support advanced scripts
- Support for Trezor wallet or other hardware wallets
- Allow to scan full blockchain
- Integrate simple SPV client


Disclaimer
----------

This library is still in development, please use at your own risk and test sufficiently before using it in a
production environment.
