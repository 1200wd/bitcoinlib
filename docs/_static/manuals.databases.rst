Using MySQL or PostgreSQL databases
===================================

Bitcoinlib uses the SQLite database by default, because it easy to use and requires no installation.

But you can also use other databases. At this moment Bitcoinlib is tested with MySQL and PostgreSQL.

The database URI can be passed to the Wallet or Service object, or you can set the database URI for wallets and / or cache in configuration file at ~/.bitcoinlib/config.ini

Using MariaDB / MySQL database
------------------------------

We assume you have a MySQL server at localhost. Unlike with the SQLite database MySQL databases are not created automatically, so create one from the mysql command prompt:

.. code-block:: mysql

    mysql> create database bitcoinlib;

Now create a user for your application and grant this user access. And off course replace the password 'secret' with
a better password.

.. code-block:: mysql

    mysql> create user bitcoinlib@localhost identified by 'secret';
    mysql> grant all on bitcoinlib.* to bitcoinlib@localhost with grant option;

In your application you can create a database link. The database tables are created when you first run the application

.. code-block:: python

    db_uri = 'mysql://bitcoinlib:secret@localhost:3306/bitcoinlib'
    w = wallet_create_or_open('wallet_mysql', db_uri=db_uri)
    w.info()

At the moment it is not possible to use MySQL database for `caching <manuals.caching.html>`_, because the BLOB transaction ID's are used as primary key. For caching you need to use a PostgreSQL or SQLite database.

Using PostgreSQL database
-------------------------

First create a user and the database from a shell. We assume you have a PostgreSQL server running at your Linux machine.

.. code-block:: bash

    $ su - postgres
    postgres@localhost:~$ createuser --interactive --pwprompt
    Enter name of role to add: bitcoinlib
    Enter password for new role:
    Enter it again:
    Shall the new role be a superuser? (y/n) n
    Shall the new role be allowed to create databases? (y/n) n
    Shall the new role be allowed to create more new roles? (y/n) n
    $ createdb bitcoinlib

And assume you unwisely have chosen the password 'secret' you can use the database as follows:

.. code-block:: python

    db_uri = 'postgresql+psycopg://bitcoinlib:secret@localhost:5432/'
    w = wallet_create_or_open('wallet_mysql', db_uri=db_uri)
    w.info()

Please note 'postgresql+psycopg' has to be used as scheme, because SQLalchemy uses the latest version 3 of psycopg, if not provided it will use psycopg2.

PostgreSQL can also be used for `caching <manuals.caching.html>`_ of service requests. The URI can be passed to the Service object or provided in the configuration file (~/.bitcoiinlib/config.ini)

.. code-block:: python

    srv = Service(cache_uri='postgresql+psycopg://postgres:postgres@localhost:5432/)
    res = srv.gettransactions('12spqcvLTFhL38oNJDDLfW1GpFGxLdaLCL')


Encrypt database or private keys
--------------------------------

If you are using wallets with private keys it is advised to use an encrypted database and / or to encrypt the private key fields.

Please read `Encrypt Database or Private Keys <manuals.sqlcipher.html>`_ for more information.
