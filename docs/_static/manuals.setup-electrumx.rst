How to connect Bitcoinlib to an ElectrumX server
================================================

ElectrumX is a backend for the well-known Electrum Bitcoin wallets. It can also be used as back-end service provider
for Bitcoinlib wallets. ElectrumX uses a running Bitcoin core node and adds an extra layer with indexes to allow
for fast address, unspent outputs and transactions queries. ElectrumX is focussed on Bitcoin wallets and has no option
to query blocks and large non-standard transactions.

If you want to use Bitcoinlib as a wallet, run many blockchain queries or write an application which is dependent on
frequent requests to blockchain service providers you should use a `Blockbook <manuals.setup-blockbook.html>`_,
ElectrumX or `Bcoin <manuals.setup-bcoin.html>`_ server.


Install ElectrumX server
------------------------

You can find instructions on how to install a ElectrumX server on
https://media.blocksmurfer.io/install-electrumx-as-bitcoinlib-backend.html


Use ElectrumX with Bitcoinlib
-----------------------------

To use ElectrumX with bitcoinlib add the credentials to the providers.json configuration file in the .bitcoinlib directory.

.. code-block:: json

    "localhost.electrumx": {
        "provider": "electrumx",
        "network": "bitcoin",
        "client_class": "ElectrumxClient",
        "provider_coin_id": "",
        "url": "localhost:50001",
        "api_key": "",
        "priority": 100,
        "denominator": 1,
        "network_overrides": null
    },

You can increase the priority so the Service object always connects to the ElectrumX service first.

ElectrumX also support Bitcoin testnet, testnet4, regtest and signet. Other coins such as Dogecoin, Litecoin
and Dash are also supported. To setup simply update the ports and add add the coin as argument when calling ElectrumX,
for instance for testnet4 use: electrumx_server --testnet4
