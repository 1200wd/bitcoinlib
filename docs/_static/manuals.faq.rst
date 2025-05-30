Frequently Asked Questions
==========================

Can I use Bitcoinlib on my system?
----------------------------------

BitcoinLib is platform independent and should run on your system.
Bitcoinlib is mainly developed on Ubuntu linux and runs unittests on every commit on Ubuntu and Windows.
Dockerfiles are available for Alpine, Kali and Fedora. You can find all dockerfiles on https://github.com/1200wd/bitcoinlib/tree/master/docker

I run into an error 'x' when installing Bitcoinlib
--------------------------------------------------

1. Check the `installation page <manuals.install.html>`_ and see if you have installed all the requirements.
2. Install the required packages one-by-one using pip install, and see if you get any specific errors.
3. Check for help in `Github Discussions <https://github.com/1200wd/bitcoinlib/discussions>`_.
4. See if you find any known `issue <https://github.com/1200wd/bitcoinlib/issues>`_.
5. If it doesn't work out, do not hesitate to ask your question in the github discussions or post an issue!

Does Bitcoinlib support 'x'-coin
--------------------------------

Bitcoinlib main focus is on Bitcoin. But besides Bitcoin it supports Litecoin and Dogecoin. For testing
it supports the Bitcoin testing networks: testnet3, testnet4, regtest and signet. For other coins the Litecoin testnet and Dogecoin testnet is supported.

Support for Dash, Bitcoin Cash and Bitcoin SV has been dropped. There are currently no plans to support other coins. Main problem with supporting new coins is the lack of service provides with a working and stable API.

My wallet transactions are not (correctly) updating!
----------------------------------------------------

Most likely cause is a problem with a specific service provider.

Please set log level to 'debug' and check the logs in bitcoinlib.log to see if you can pin down the specific error.
You could then disable the provider and post the `issue <https://github.com/1200wd/bitcoinlib/issues>`_.

To avoid these kinds of errors it is advised to run your local `Bcoin node <manuals.setup-bcoin.html>`_,
`Blockbook <manuals.setup-blockbook.html>`_ or `ElectrumX <manuals.setup-electrumx.html>`_ server.

With a local Bcoin node or Blockbook server you do not depend on external Service providers which increases reliability, security, speed and privacy.

Provider 'x' does not work
--------------------------

If you encounter errors when updating transactions, utxo's, blocks, etc there is probably a problem with a specific provider. You can check the logs in bitcoinlib.log and see which provider has problems. To solve this you can:

* Set priority = 0 for this provider to temporary disable it
* Remove the provider from the providers.json file in you local .bitcoinlib directory
* Use the exclude_provider option when you calling the Service class:

.. code-block:: python

    srv = Service(exclude_providers=['blocksmurfer'])

* Or use a specific provider, for instance your local Blockbook server:

.. code-block:: python

    srv = Service(providers=['blockbook'])


Can I use Bitcoinlib with another database besides SQLite?
----------------------------------------------------------

Yes, the library can also work with PostgreSQL or MySQL / MariaDB databases.
For more information see: `Databases <manuals.databases.html>`_.

I have imported a private key from another wallet but the address is different
------------------------------------------------------------------------------

If you have imported a private key from another wallet in Bitcoinlib and the address in Bitcoinlib does not match, then this is probably because the wallets use different key paths or keys at different levels.

* Check if the level and type of the key it the same? Is it a masterkey (level 0), a master public key (level 3), or a key of an address (level 5)
* Does the wallet uses the same key paths? Bitcoinlib uses the default BIP84 keys path in “m/84’/0’/0’/0/0” format. You can specify a different key path or witness type when creating a wallet

I found a bug!
--------------

Please help out project and post your `issue <https://github.com/1200wd/bitcoinlib/issues>`_ on Github.
Try to include all code and data so we can reproduce and solve the issue.

I have another question
-----------------------

Maybe your question already has an answer om `Github Discussions <https://github.com/1200wd/bitcoinlib/discussions>`_.
Or search for an answer is this `documentation <https://bitcoinlib.readthedocs.io/en/latest/>`_.

If that does not answer your question, please post your question on the
`Github Discussions Q&A <https://github.com/1200wd/bitcoinlib/discussions/categories/q-a>`_.



..
    My transaction is not confirming
    Is Bitcoinlib secure?
    Donations?

