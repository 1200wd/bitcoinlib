10 Tips to Increase Privacy and Security
========================================

Ten tips for more privacy and security when using Bitcoin and Bitcoinlib:

1. Run your own `Bitcoin <https://bitcoinlib.readthedocs.io/en/latest/source/_static/manuals.setup-bitcoind-connection.html>`_
   or Bcoin node, so you are not depending on external Blockchain API service providers anymore.
   This not only increases your privacy, but also makes your application much faster and more reliable. And as extra bonus
   you support the Bitcoin network.
2. Use multi-signature wallets. So you are able to store your private keys in separate (offline) locations.
3. Use a minimal amount of inputs when creating a transaction. This is default behavior the Bitcoinlib Wallet
   object. You can set a hard limit when sending from a wallet with the max_utxos=1 attribute.
4. Use a random number of change outputs and shuffle order of inputs and outputs. This way it is not visible
   which output is the change output. In the Wallet object you can set the number_of_change_outputs to zero to
   generate a random number of change outputs.
5. Encrypt your database with SQLCipher.
6. Use password protected private keys. For instance use a password when
   `creating wallets <https://bitcoinlib.readthedocs.io/en/latest/source/bitcoinlib.wallets.html#bitcoinlib.wallets.Wallet.create>`_.
7. Backup private keys and passwords! I have no proof but I assume more bitcoins are lost because of lost private keys then there are lost due to hacking...
8. When using Bitcoinlib wallets the private keys are stored in a database. Make sure the database is in a safe location
   and check encryption, access rights, etc. Also check tip 2 and 5 again and see how you can minimize risks.
9. Test, try, review. Before working with any real value carefully test your applications using the testnet or small value transactions.
10. Read this tips, read some more about `Security <https://en.bitcoin.it/wiki/Storing_bitcoins>`_ and `Privacy <https://en.bitcoin.it/wiki/Privacy>`_
    and then think thorough about the best wallet setup, which is always a tradeoff between security, privacy and usability.
