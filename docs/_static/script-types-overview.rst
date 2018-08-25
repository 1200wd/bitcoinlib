Script types
============

Locking scripts
---------------

Scripts lock funds in transaction outputs (UTXO's).
Also called ScriptSig.


+-------------+---------------------------+-----------+-------------------+------------+
| Script type | Name                      | Encoding  | Key type / Script | Prefix BTC |
+=============+===========================+===========+===================+============+
| p2pkh       | Pay to Public Key Hash    | base58    | Public key hash   | 1          |
+-------------+---------------------------+-----------+-------------------+------------+
| p2sh        | Pay to Script Hash        | base58    | Redeemscript hash | 3          |
+-------------+---------------------------+-----------+-------------------+------------+
| p2wpkh      | Pay to Wallet Pub Key Hash| bech32    | Public key hash   | bc         |
+-------------+---------------------------+-----------+-------------------+------------+
| p2wsh       | Pay to Wallet Script Hash | bech32    | Redeemscript hash | bc         |
+-------------+---------------------------+-----------+-------------------+------------+
| multisig    | Multisig script           | base58    | Multisig script   | 3          |
+-------------+---------------------------+-----------+-------------------+------------+
| pubkey      | Public Key (obsolete)     | base58    | Public Key        | 1          |
+-------------+---------------------------+-----------+-------------------+------------+
| nulldata    | Nulldata                  | n/a       | OP_RETURN script  | n/a        |
+-------------+---------------------------+-----------+-------------------+------------+


Unlocking scripts
-----------------

Scripts used in transaction inputs to unlock funds from previous outputs.
Also called ScriptPubKey.

