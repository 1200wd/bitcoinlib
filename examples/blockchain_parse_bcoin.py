# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Deserialize and Verify all transactions from the latest block using Bcoin provider
#
#    Just use for testing and experimenting, this library is not optimized for blockchain parsing!
#
#    © 2020 April - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.services.services import Service
from pprint import pprint


srv = Service(providers=['bcoin'])

# Get latest block
latest_block = srv.blockcount()

print("Getting latest block %s" % latest_block)
latest_block = srv.getblock(latest_block)
transactions = latest_block['txs']
print("Found %d transactions" % len(transactions))

MAX_TRANSACTIONS = 100
count = 0
count_segwit = 0
for tx in transactions[:MAX_TRANSACTIONS]:
    print("\n=== Deserialize transaction #%d (segwit %d) ===" % (count, count_segwit))
    count += 1
    t = srv.gettransaction(tx['hash'])

    t.verify()
    t.info()
    if t.witness_type != 'legacy':
        count_segwit += 1
    if not t.verified:
        input("Transaction could not be verified, press any key to continue")
