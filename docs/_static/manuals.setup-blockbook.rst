How to connect Bitcoinlib to a Blockbook server
===============================================

Trezor's Blockbook is a back-end service for Trezor Suite and can also be used as back-end service provider for
Bitcoinlib. Blockbook indexes addresses, transactions, unspent outputs and balances and can be used for fast
blockchain queries. Blockbook also support Litecoin, Dash, Dogecoin and various testnets.

If you want to use Bitcoinlib as a wallet, run many blockchain queries or write an application which is dependant on
frequent requests to blockchain service providers you should use a Blockbook service or install a
`Bcoin <manuals.setup-bcoin.html>`_ node.


Install Blockbook server
------------------------

You can find some instructions on how to install a Blockbook server on
https://coineva.com/blockbook-setup-as-bitcoinlib-backend.html.

You will need a powerful server with enough memory and diskspace. Blockbook runs a full Bitcoin core node on the
background, and maintains a large RocksDB database to store additional blockchain data. But once installed and
synchronised it runs fast and smooth.


Use Blockbook with Bitcoinlib
-----------------------------

To use Blockbook with bitcoinlib add the credentials to the providers.json configuration file in the .bitcoinlib directory.

.. code-block:: json

    "blockbook": {
      "provider": "blockbook",
      "network": "bitcoin",
      "client_class": "BlockbookClient",
      "provider_coin_id": "",
      "url": "https://<servername>:9130/",
      "api_key": "",
      "priority": 20,
      "denominator": 100000000,
      "network_overrides": null,
      "timeout", 0
    }

You can increase the priority so the Service object always connects to the Blockbook service first.
