Install, Update and Tweak BitcoinLib
====================================

Installation
------------

Install with pip
~~~~~~~~~~~~~~~~

.. code-block:: none

    $ pip install bitcoinlib

Package can be found at https://pypi.org/project/bitcoinlib/

Install from source
~~~~~~~~~~~~~~~~~~~

Required packages for Ubuntu, for other systems see below:

``apt install build-essential python3-dev libgmp3-dev pkg-config postgresql postgresql-contrib mariadb-server libpq-dev libmysqlclient-dev pkg-config``

Create a virtual environment for instance on linux with virtualenv:

.. code-block:: bash

    $ virtualenv -p ~/.virtualenvs/bitcoinlib
    $ source ~/.virtualenvs/bitcoinlib/bin/activate

Then clone the repository and install dependencies:

.. code-block:: bash

    $ git clone https://github.com/1200wd/bitcoinlib.git
    $ cd bitcoinlib
    $ python -m pip install .

You can test your local installation by running all unittests:

.. code-block:: bash

    $ python -m unittest


Package dependencies
~~~~~~~~~~~~~~~~~~~~

Required Python Packages, are automatically installed upon installing bitcoinlib:

* fastecdsa (or ecdsa on Windows)
* sqlalchemy
* requests
* numpy
* pycryptodome


Other requirements Linux
~~~~~~~~~~~~~~~~~~~~~~~~

On Debian, Ubuntu or their derivatives:

``apt install build-essential python3-dev libgmp3-dev pkg-config postgresql postgresql-contrib mariadb-server libpq-dev libmysqlclient-dev pkg-config``

On Fedora, CentOS or RHEL:

``dnf install python3-devel gmp-devel``

On Alpine Linux, lightweight Linux used for Docker images:

``apk add python3-dev gmp-dev py3-pip gcc musl-dev libpq-dev postgresql postgresql-contrib mariadb-dev mysql-client``

On Kali linux:

``apt install libgmp3-dev postgresql postgresql-contrib libpq-dev pkg-config default-libmysqlclient-dev default-mysql-server``


Development environment
~~~~~~~~~~~~~~~~~~~~~~~

Install database packages for MySQL and PostgreSQL

``apt install mysql-server postgresql postgresql-contrib libmysqlclient-dev pkg-config libpq-dev``

Check for the latest version of the PostgreSQL dev server:

``apt install postgresql-server-dev-<version>``

From library root directory install the Python requirements

``python -m pip install .[dev]``

Then run the unittests to see if everything works

``python -m unittest``



Other requirements Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~

This library requires a Microsoft Visual C++ Compiler. For python version 3.5+ you will need Visual C++ 14.0.
Install Microsoft Visual Studio and include the "Microsoft Visual C++ Build Tools" which can be downloaded from
https://visualstudio.microsoft.com/downloads. Also see https://wiki.python.org/moin/WindowsCompilers

The fastecdsa library is not enabled at this moment in the windows install, the slower ecdsa library is installed.
Installation of fastecdsa on Windows is possible but not easy, read https://github.com/AntonKueltz/fastecdsa/issues/11
for steps you could take to install this library.

When using Python on Windows it needs to be set to UTF-8 mode. You can do this by adding the PYTHONUTF8=1 to the
environment variables or use the -X utf8 command line option. Please see
https://docs.python.org/3/using/windows.html#win-utf8-mode for more information.


Update Bitcoinlib
-----------------

Before you update make sure to backup your database! Also backup your settings files in ./bitcoinlib/config if you
have made any changes.

If you installed the library with pip upgrade with

.. code-block:: none

    $ pip install bitcoinlib --upgrade

Otherwise pull the git repository.

After an update it might be necessary to update the config files. The config files will be overwritten
with new versions if you delete the .bitcoinlib/install.log file.

.. code-block:: none

    $ rm .bitcoinlib/install.log

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

Please make sure you have the Python development and SSL development packages installed, see 'Other requirements'
above.

You can also use pycryptodome, pyscrypt or scrypt. pyscript is a pure Python scrypt password-based key
derivation library. It works but it is slow when using BIP38 password protected keys.

If you run into issues do not hesitate to contact us or file an issue at https://github.com/1200wd/bitcoinlib/issues


Using library in other software
-------------------------------

If you use the library in other software and want to change file locations and other settings you can specify a
location for a config file in the BCL_CONFIG_FILE:

.. code-block:: python

    os.environ['BCL_CONFIG_FILE'] = '/var/www/blocksmurfer/bitcoinlib.ini'


Service providers and local nodes
---------------------------------

You can `Add another service Provider <manuals.add-provider.html>`_ to this library by updating settings
and write a new service provider class.

To increase reliability, speed and privacy or if you use this library in a production environment it
is advised to run your own Bcoin or Bitcoin node.

More setup information:

* `Setup connection to Bcoin node <manuals.setup-bcoin.html>`_
* `Setup connection to Bitcoin node <manuals.setup-bitcoind-connection.html>`_

Some service providers require an API key to function or allow additional requests.
You can add this key to the provider settings file in .bitcoinlib/providers.json
