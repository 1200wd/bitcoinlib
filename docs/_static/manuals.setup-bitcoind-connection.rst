How to connect bitcoinlib to a Bitcoin node
===========================================

This manual explains how to connect to a bitcoind server on your localhost or an a remote server.

Running your own bitcoin node allows you to create a large number of requests, faster response times,
and more control, privacy and independence. However you need to install and maintain it and it used
a lot of resources.

.. warning::
    With a standard Bitcoin node you can only retrieve block and transaction information. You can not
    query the node for information about specific addresses. So it not suitable to run in combination with a Bitcoinlib
    wallet. If you would like to use Bitcoinlib wallets and not be dependent on external providers you should use a
    `Bcoin node <manuals.setup-bcoin.html>`_ instead.


Bitcoin node settings
---------------------

This manual assumes you have a full bitcoin node up and running.
For more information on how to install a full node read https://bitcoin.org/en/full-node

Please make sure you have server and txindex option set to 1.

Generate a RPC authorization configuration string online: https://jlopp.github.io/bitcoin-core-rpc-auth-generator/
or with the Python tool you can find in the Bitcoin repository: https://github.com/bitcoin/bitcoin/blob/master/share/rpcauth/rpcauth.py

So your bitcoin.conf file for testnet should look something like this. For mainnet use port 8332,
and remove the 'testnet=1' line.

.. code-block:: text

    server=1
    port=18332
    txindex=1
    testnet=1
    rpcauth=bitcoinlib:01cf8eb434e3c9434e244daf3fc1cc71$9cdfb346b76935569683c12858e13147eb5322399580ba51d2d878148a880d1d
    rpcbind=0.0.0.0
    rpcallowip=192.168.0.0/24

To increase your privacy and security, and for instance if you run a Bitcoin node on your home network, you can
use TOR. Bitcoind has TOR support build in, and it is ease to setup.
See https://en.bitcoin.it/wiki/Setting_up_a_Tor_hidden_service

If you have a TOR service running you can add these lines to your bitcoin.conf settings to only use TOR.

.. code-block:: text

    proxy=127.0.0.1:9050
    bind=127.0.0.1
    onlynet=onion


Connect using provider settings
-------------------------------

Connection settings can be added to the service provider settings file in
.bitcoinlib/config/providers.json

Example:

.. code-block:: json

  {
    "bitcoind.testnet": {
      "provider": "bitcoind",
      "network": "testnet",
      "client_class": "BitcoindClient",
      "url": "http://user:password@server_url:18332",
      "api_key": "",
      "priority": 11,
      "denominator": 100000000
    }
  }


Connect using base_url argument
-------------------------------

You can also directly pass connection string wit the 'base_url' argument in the BitcoindClient object.

This provides more flexibility but also the responsibility to store user and password information in a secure way.

.. code-block:: python

    from bitcoinlib.services.bitcoind import BitcoindClient

    base_url = 'http://user:password@server_url:18332'
    bdc = BitcoindClient(base_url=base_url)
    txid = 'e0cee8955f516d5ed333d081a4e2f55b999debfff91a49e8123d20f7ed647ac5'
    rt = bdc.getrawtransaction(txid)
    print("Raw: %s" % rt)


You can directly r

.. code-block:: python

    from bitcoinlib.services.bitcoind import BitcoindClient

    # Retrieve some blockchain information and statistics
    bdc.proxy.getblockchaininfo()
    bdc.proxy.getchaintxstats()
    bdc.proxy.getmempoolinfo()

    # Add a node to the node list
    bdc.proxy.addnode('blocksmurfer.io', 'add')



Please note: Using a remote bitcoind server
-------------------------------------------

Using RPC over a public network is unsafe, so since bitcoind version 0.18 remote RPC for all network interfaces
are disabled. The rpcallowip option cannot be used to listen on all network interfaces and rpcbind has to be used to
define specific IP addresses to listen on. See https://bitcoin.org/en/release/v0.18.0#configuration-option-changes

You could setup a openvpn or ssh tunnel to connect to a remote server to avoid this issues.
