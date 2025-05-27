# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Deserialize and Verify all transactions from the latest block
#    Just use for testing and experimenting, this library is not optimized for blockchain parsing!
#
#    © 2018 - 2025 May - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.services.services import *


srv = Service(network='testnet', strict=False)
latest_block = srv.blockcount()
block = srv.getblock(latest_block, parse_transactions=False)
transactions = block.transactions


MAX_TRANSACTIONS = 100
count = 0
count_segwit = 0
for txid in transactions[:MAX_TRANSACTIONS]:
    print("\n=== Deserialize transaction #%d (segwit %d) ===" % (count, count_segwit))
    count += 1
    t = srv.gettransaction(txid)
    t.verify()
    t.info()
    if t.witness_type != 'legacy':
        count_segwit += 1
    if not t.verified:
        input("Transaction could not be verified, press any key to continue")
