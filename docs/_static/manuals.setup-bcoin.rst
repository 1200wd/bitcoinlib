How to connect Bitcoinlib to a Bcoin node
=========================================

Bcoin is a full bitcoin node implementation, which can be used to parse the blockchain, send transactions and run a
wallet. With a Bcoin node you can retrieve transaction and utxo information for specific addresses, this is not easily
possible with a `Bitcoind <manuals.setup-bitcoind-connection.html>`_ node. So if you want to use Bitcoinlib's
wallet functionality for instance and not be dependent on external providers the best option is to run a local
Bcoin node, `Blockbook <manuals.setup-blockbook.html>`_ or `ElectrumX <manuals.setup-electrumx.html>`_ server.


Install Bcoin node
------------------

You can find some instructions on how to install a bcoin node on https://media.blocksmurfer.io/install-bcoin-node-ubuntu.html.

There are also some Docker images available. We have created a Docker image with the most optimal settings for
bitcoinlib. You can install them with the following command.

.. code-block:: bash

    docker pull blocksmurfer/bcoin


Use Bcoin node with Bitcoinlib
------------------------------

To use Bcoin with bitcoinlib add the credentials to the providers.json configuration file in the .bitcoinlib directory.

.. code-block:: json

    "bcoin": {
        "provider": "bcoin",
        "network": "bitcoin",
        "client_class": "BcoinClient",
        "provider_coin_id": "",
        "url": "https://user:pass@localhost:8332/",
        "api_key": "",
        "priority": 20,
        "denominator": 100000000,
        "network_overrides": null,
        "timeout": 0
    },

You can increase the priority so the Service object always connects to the Bcoin node first.
