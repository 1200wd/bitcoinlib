# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Deserialize and Verify all transactions from the specified blocks using Bcoin provider
#
#    Just use for testing and experimenting, this library is not optimized for blockchain parsing!
#
#    © 2020 April - 1200 Web Development <http://1200wd.com/>
#

from time import sleep
from bitcoinlib.services.services import Service
from pprint import pprint


srv = Service(providers=['bcoin'])

# Get latest block
# blocks = [srv.blockcount()]

# Get first block
# blocks = [1]

# Check first 100000 blocks
# blocks = range(1, 100000)

# Check some more recent blocks
blocks = range(625000, 629060)


for block in blocks:
    print("Getting block %s" % block)
    block_dict = srv.getblock(block, parse_transactions=True, limit=99999)
    transactions = block_dict['txs']
    print("Found %d transactions" % len(transactions))

    MAX_TRANSACTIONS = 10000
    count = 0
    count_segwit = 0

    for t in transactions[:MAX_TRANSACTIONS]:
        print("=== Deserialize transaction %s (#%d, segwit %d) ===" % (t.hash, count, count_segwit))
        count += 1
        t.verify()
        # t.info()
        if t.witness_type != 'legacy':
            count_segwit += 1
        if not t.verified:
            print(50 * "!")
            print("Transaction could not be verified!!")
