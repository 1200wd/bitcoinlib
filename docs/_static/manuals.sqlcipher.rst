Using SQLCipher encrypted database
==================================

To protect your data such as the private keys you can use SQLCipher to encrypt the full database. SQLCipher is a
SQLite extension which uses 256-bit AES encryption and also works together with SQLAlchemy.

Is quite easy to setup and use with Bitcoinlib. First install the required packages, the following works on Ubuntu, but
your system might require other packages. Please read https://www.zetetic.net/sqlcipher/ for installations instructions.

.. code-block:: bash

    $ sudo apt install sqlcipher libsqlcipher0 libsqlcipher-dev
    $ pip install pysqlcipher3


Now you can use a SQLCipher database URI to create and query a encrypted database:

.. code-block:: python

    password = 'secret'
    filename = '~/.bitcoinlib/database/bcl_encrypted.db'
    db_uri = 'sqlite+pysqlcipher://:%s@/%s?cipher=aes-256-cfb&kdf_iter=64000' % (password, filename)
    wlt = Wallet.create('bcltestwlt4', network='bitcoinlib_test', db_uri=db_uri)

If you look at the contents of the SQLite database you can see it is encrypted.

.. code-block:: bash

    $ cat ~/.bitcoinlib/database/bcl_encrypted.db
    <outputs unreadable random garbage>

