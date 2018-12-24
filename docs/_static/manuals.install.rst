Install, Update and Tweak BitcoinLib
====================================

Installation
------------

Install with pip
~~~~~~~~~~~~~~~~

.. code-block:: none

    $ pip install bitcoinlib

Package can be found at https://pypi.python.org/pypi/bitcoinlib/

Install from source
~~~~~~~~~~~~~~~~~~~

.. code-block:: none

    $ git clone https://github.com/1200wd/bitcoinlib
    $ cd bitcoinlib
    $ python setup.py install

Package dependencies
~~~~~~~~~~~~~~~~~~~~

Required Python Packages, are automatically installed upon installing bitcoinlib:

* ecdsa
* pyaes
* scrypt
* sqlalchemy
* requests
* enum34 (for older python installations)


Other requirements Linux
~~~~~~~~~~~~~~~~~~~~~~~~

``sudo apt install python-dev python3-dev``

To install OpenSSL development package on Debian, Ubuntu or their derivatives

``sudo apt install libssl-dev``

To install OpenSSL development package on Fedora, CentOS or RHEL

``sudo yum install openssl-devel``


Other requirements Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~

Tested on Windows 10 with Python 3.6 and pip installed. No special requirements needed.


Update Bitcoinlib
-----------------

Before you update make sure to backup your database! Also backup your settings files in ./bitcoinlib/config if you
have made any changes.

If you installed the library with pip upgrade with

.. code-block:: none

    $ pip install bitcoinlib --upgrade

Otherwise pull the git repository.

After an update it might be necessary to update the config files. The config files will be overwritten
with new versions if you delete the .bitcoinlib/logs/install.log file.

.. code-block:: none

    $ rm .bitcoinlib/logs/install.log

If the new release contains database updates you have to migrate the database with the updatedb.py command.
This program extracts keys and some wallet information from the old database and then creates a new database.
The updatedb.py command is just a helper tool and not guaranteed to work, it might fail if there are a lot
of database changes. So backup database / private keys first and use at your own risk!

.. code-block:: none

    $ python updatedb.py
    Wallet and Key data will be copied to new database. Transaction data will NOT be copied
    Updating database file: /home/guest/.bitcoinlib/database/bitcoinlib.sqlite
    Old database will be backed up to /home/guest/.bitcoinlib/database/bitcoinlib.sqlite.backup-20180711-01:46
    Type 'y' or 'Y' to continue or any other key to cancel: y


Troubleshooting
---------------

When you experience issues with the scrypt package when installing you can try to solve this by installing
scrypt seperately:
 pip intall scrypt

Please make sure you also have the Python development and SSL development packages installed, see 'Other requirements'
above.

You can also use pyscrypt instead of scrypt. Pyscrypt is a pure Python scrypt password-based key derivation library.
It works but it is slow when using BIP38 password protected keys.
 pip install pyscrypt

If you run into issues to not hesitate to contact us or file an issue at https://github.com/1200wd/bitcoinlib/issues


Tweak BitcoinLib
----------------

You can `Add another service Provider <manuals.add-provider.html>`_ to this library by updating settings
and write a new service provider class.

If you use this library in a production environment it is advised to run your own Bitcoin, Litecoin or Dash node,
both for privacy and reliability reasons. More setup information:
`Setup connection to bitcoin node <manuals.setup-bitcoind-connection.html>`_

Some service providers require an API key to function or allow additional requests.
You can add this key to the provider settings file in .bitcoinlib/config/providers.json
