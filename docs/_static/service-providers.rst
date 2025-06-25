How to use Service Providers?
=============================

Bitcoinlib uses external service providers to get address, transaction and blockchain information for your wallet or other application.

**If you install Bitcoinlib it uses external and free service providers, so you do not have to do anything extra to get it working.**

However those free providers have transaction limits, slow responses, downtimes or changing Api's which can cause unexpected results. For larges wallets, complicated projects with a lot of requests or production environments, you basically have three options.


Setup a local node
------------------

You need a server with a large storage and a stable connection at your home or a hosting provider. And then follow the manual to setup an `Blockbook <manuals.setup-blockbook.html>`_,
`ElectrumX <manuals.setup-electrumx.html>`_ or `Bcoin <manuals.setup-bcoin.html>`_ server.

You can also setup a `Bitcoind Node <manuals.setup-bitcoind-connection>`_, but a standard node cannot get utxo's or address information for external wallet addresses.


Get a payed subscription
------------------------

There a many providers which offer a payed subscription, many unfortunately are really expensive.

At the time of writing Nownodes offers a $20 a month subscription. You can create an account and use the example providers configuration file at https://github.com/1200wd/bitcoinlib/blob/master/bitcoinlib/data/providers.examples-nownodes.json


Add another service Provider
----------------------------

You can also `Add another service Provider <manuals.add-provider.html>`_ to this library by updating settings and write a new service provider class.

If you tested the new provider thoroughly don't forget to create a pull request ;)