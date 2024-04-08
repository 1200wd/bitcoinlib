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
5. If it doesn't work out, do not hesitate to ask you question in the github discussions or post an issue!

Does Bitcoinlib support 'x'-coin
--------------------------------

Bitcoinlib main focus is on Bitcoin. But besides Bitcoin it supports Litecoin and Dogecoin. For testing
it supports Bitcoin testnet3, Bitcoin regtest, Litecoin testnet and Dogecoin testnet.

Support for Dash, Bitcoin Cash and Bitcoin SV has been dropped.

There are currently no plans to support other coins. Main problem with supporting new coins is the lack of
service provides with a working and stable API.

My wallet transactions are not (correctly) updating!
----------------------------------------------------

Most likely cause is a problem with a specific service provider.

Please set log level to 'debug' and check the logs in bitcoinlib.log to see if you can pin down the specific error.
You could then disable the provider and post the `issue <https://github.com/1200wd/bitcoinlib/issues>`_.

To avoid these kind of errors it is adviced to run your local `Bcoin node <manuals.setup-bcoin.html>`_.
With a local Bcoin node you do not depend on external Service providers which increases reliability, security, speed
and privacy.

Can I use Bitcoinlib with another database besides SQLite?
----------------------------------------------------------

Yes, the library can also work with PostgreSQL or MySQL / MariaDB databases.
For more information see: `Databases <manuals.databases.html>`_.

I found a bug!
--------------

Please help out project and post your `issue <https://github.com/1200wd/bitcoinlib/issues>`_ on Github.
Try to include all code and data so we can reproduce and solve the issue.

I have another question
-----------------------

Maybe your question already has an answer om `Github Discussions <https://github.com/1200wd/bitcoinlib/discussions>`_.
Or search for an answer is this `documentation <https://bitcoinlib.readthedocs.io/en/latest/>`_.

If that does not answer your question, please post your question on on the
`Github Discussions Q&A <https://github.com/1200wd/bitcoinlib/discussions/categories/q-a>`_.



..
    My transaction is not confirming
    I have imported a private key but address from other wallet does not match Bitcoinlib's address
    Is Bitcoinlib secure?
    Donations?

