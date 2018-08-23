Script types
============

Locking scripts
---------------

Scripts lock funds in transaction outputs (UTXO's)

+-------------+---------------------------+-----------+-------------------+------------+
| Script type | Name                      | Encoding  | Key type / Script | Prefix BTC |
+============+============================+===========+===================+============+
| p2pkh       | Pay to public key hash    | base58    | Public key hash   |      1     |
+-------------+---------------------------+-----------+-------------------+------------+
| p2sh        | Pay to script hash        | base58    | Redeemscript hash |      3     |
+-------------+---------------------------+-----------+-------------------+------------+
| p2wpkh      | Pay to wallet pub key hash| bech32    | Public key hash   |     bc     |
+-------------+---------------------------+-----------+-------------------+------------+
| p2wsh       | Pay to wallet script hash | bech32    | Redeemscript hash |     bc     |
+-------------+---------------------------+-----------+-------------------+------------+
| multisig    | Multisig script           | base58    | Multisig script   |      3     |
+-------------+---------------------------+-----------+-------------------+------------+
| nulldata    | Nulldata                  | n/a       | OP_RETURN script  |      -     |
+-------------+---------------------------+-----------+-------------------+------------+


Unlocking scripts
-----------------

Scripts used transaction inputs to unlock funds from previous outputs.

