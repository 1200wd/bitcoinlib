Encrypt Database or Private Keys
================================

If your database contains private keys it is a good idea to encrypt your data. This will not be done automatically. At the moment you have 2 options:

- Encrypt the database with SQLCipher. The database is fully encrypted and you need to provide the password in the Database URI when opening the database.
- Use a normal database but all private key data will be stored AES encrypted in the database. A key to encrypt and decrypt needs to be provided in the Environment.

Encrypt database with SQLCipher
-------------------------------

To protect your data such as the private keys you can use SQLCipher to encrypt the full database. SQLCipher is a
SQLite extension which uses 256-bit AES encryption and also works together with SQLAlchemy.

Is quite easy to setup and use with Bitcoinlib. First install the required packages, the following works on Ubuntu, but
your system might require other packages. Please read https://www.zetetic.net/sqlcipher/ for installations instructions.

.. code-block:: bash

    $ sudo apt install sqlcipher libsqlcipher0 libsqlcipher-dev
    $ pip install sqlcipher3-binary
    # Previous, but now unmaintained: $ pip install pysqlcipher3


**Create an Encrypted Database for your Wallet**

Now you can simply create and use an encrypted database by supplying a password as argument to the Wallet object:

.. code-block:: python

    password = 'secret'
    db_uri = '/home/user/.bitcoinlib/database/bcl_encrypted.db'
    wlt = wallet_create_or_open('bcltestwlt4', network='bitcoinlib_test', db_uri=db_uri, db_password=password)


**Encrypt using Database URI**

You can also use a SQLCipher database URI to create and query an encrypted database:

.. code-block:: python

    password = 'secret'
    filename = '/home/user/.bitcoinlib/database/bcl_encrypted.db'
    db_uri = 'sqlite+pysqlcipher://:%s@/%s?cipher=aes-256-cfb&kdf_iter=64000' % (password, filename)
    wlt = Wallet.create('bcltestwlt4', network='bitcoinlib_test', db_uri=db_uri)

If you look at the contents of the SQLite database you can see it is encrypted.

.. code-block:: bash

    $ cat ~/.bitcoinlib/database/bcl_encrypted.db
    <outputs unreadable random garbage>


Encrypt private key fields with AES
-----------------------------------

It is also possible to just encrypt the private keys in the database with secure AES encryption. You need to provide a key or password as environment variable.

* You can skip this step if you want, but this provides an extra warning / check when no encryption key is found: Enable database encryption in Bitcoinlib configuration settings at ~/.bitcoinlib/config.ini

.. code-block:: text

    # Encrypt private key field in database using symmetrically EAS encryption.
    # You need to set the password in the DB_FIELD_ENCRYPTION_KEY environment variable.
    database_encryption_enabled=True

You can provide an encryption key directly or use a password to create a key:

1. Generate a secure 32 bytes encryption key yourself with Bitcoinlib:

.. code-block:: python

    >>> from bitcoinlib.keys import Key
    >>> Key().private_hex()
    '2414966ea9f2de189a61953c333f61013505dfbf8e383b5ed6cb1981d5ec2620'

This key needs to be stored in the environment when creating or accessing a wallet. No extra arguments have to be provided to the Wallet class, the data is encrypted and decrypted at database level.

2. You can also just provide a password, and let Bitcoinlib create a key for you. You will need to pass the DB_FIELD_ENCRYPTION_PASSWORD environment variable.

There are several ways to store the key in an Environment variable, on Linux you can do:

.. code-block:: bash

    $ export DB_FIELD_ENCRYPTION_KEY='2414966ea9f2de189a61953c333f61013505dfbf8e383b5ed6cb1981d5ec2620'

or

.. code-block:: bash

    $ export DB_FIELD_ENCRYPTION_PASSWORD=ineedtorememberthispassword

Or in Windows:

.. code-block:: bash

    $ setx DB_FIELD_ENCRYPTION_KEY '2414966ea9f2de189a61953c333f61013505dfbf8e383b5ed6cb1981d5ec2620'

Environment variables can also be stored in an .env key, in a virtual environment or in Python code itself. However anyone with access to the key can decrypt your private keys.

Please make sure to remember and backup your encryption key or password, if you lose your key the private keys can not be recovered!
