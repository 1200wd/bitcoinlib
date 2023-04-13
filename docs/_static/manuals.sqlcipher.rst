Using SQLCipher encrypted database
==================================

To protect your data such as the private keys you can use SQLCipher to encrypt the full database. SQLCipher is a
SQLite extension which uses 256-bit AES encryption and also works together with SQLAlchemy.

Is quite easy to setup and use with Bitcoinlib. First install the required packages, the following works on Ubuntu, but
your system might require other packages. Please read https://www.zetetic.net/sqlcipher/ for installations instructions.

.. code-block:: bash

    $ sudo apt install sqlcipher libsqlcipher0 libsqlcipher-dev
    $ pip install sqlcipher3-binary
    # Previous, but now unmaintained: $ pip install pysqlcipher3


Create an Encrypted Database for your Wallet
--------------------------------------------

Now you can simply create and use an encrypted database by supplying a password as argument to the Wallet object:

.. code-block:: python

    password = 'secret'
    db_uri = '/home/user/.bitcoinlib/database/bcl_encrypted.db'
    wlt = wallet_create_or_open('bcltestwlt4', network='bitcoinlib_test', db_uri=db_uri, db_password=password)


Encrypt using Database URI
--------------------------

You can also use a SQLCipher database URI to create and query a encrypted database:

.. code-block:: python

    password = 'secret'
    filename = '/home/user/.bitcoinlib/database/bcl_encrypted.db'
    db_uri = 'sqlite+pysqlcipher://:%s@/%s?cipher=aes-256-cfb&kdf_iter=64000' % (password, filename)
    wlt = Wallet.create('bcltestwlt4', network='bitcoinlib_test', db_uri=db_uri)

If you look at the contents of the SQLite database you can see it is encrypted.

.. code-block:: bash

    $ cat ~/.bitcoinlib/database/bcl_encrypted.db
    <outputs unreadable random garbage>
