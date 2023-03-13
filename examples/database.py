# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES -Database direct queries
#
#    © 2022 November - 1200 Web Development <http://1200wd.com/>
#


from bitcoinlib.wallets import *
from sqlalchemy.sql import text

print("\n=== Query database directly to use limit on large databases ===")
wallet_delete_if_exists('wallet_query', force=True)
if wallet_exists('wallet_query'):
    w = Wallet('wallet_query')
else:
    pk = 'tobacco defy swarm leaf flat pyramid velvet pen minor twist maximum extend'
    w = Wallet.create(
        keys=pk, network='bitcoinlib_test',
        name='wallet_query')
    w.get_keys(number_of_keys=50)
    w.utxos_update()

wallet_id = w.wallet_id

db = Db()
res = db.session.execute(text("SELECT * FROM transactions WHERE wallet_id= %d LIMIT 5" % wallet_id))
for row in res:
    print(row[1].hex())
