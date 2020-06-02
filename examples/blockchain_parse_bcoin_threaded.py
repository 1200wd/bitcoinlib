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

import time
from bitcoinlib.services.bcoin import BcoinClient
from pprint import pprint
import multiprocessing
from multiprocessing import Queue, Process, current_process, Pool


start_time = time.time()

processors = multiprocessing.cpu_count()
print("You have %d processors so starting %d threads" % (processors, processors))


bcc = BcoinClient('bitcoin', ''
                  'https://x:8d49e6c7f3774a76bc6a78b22c6fbfc19444b893e78a1fbc3a0145f78e81d3b5@coineva.com:28332/',
                  100000000)


def parse_tx(tx, block):
    tx['confirmations'] = block['depth']
    tx['time'] = block['time']
    tx['height'] = block['height']
    tx['block'] = block['hash']
    t = bcc._parse_transaction(tx)
    # if t.hash != tx['hash']:
    # print(t.hash, t.verify())
    return t

#
#
# def read_blocks(queue):
#     for n in range(600000, 600010):
#         block = bcc.compose_request('block', n)
#         for tx in block['txs']:
#             queue.put((tx, block))
#
#
# def process_txs(queue):
#     # while queue.empty() is False:
#     count = 0
#     while True:
#         tx, block = queue.get()
#         t = parse_tx(tx, block)
#         count += 1
#         print(count, t.hash)
#
# multiprocessing.set_start_method("fork")
# queue = multiprocessing.Queue()
# childProcess0 = multiprocessing.Process(target=read_blocks, args=(queue,))
# childProcess1 = multiprocessing.Process(target=process_txs, args=(queue,))
#
# childProcess0.start()
# childProcess1.start()
#
# # Wait for child processes to finish
#
# childProcess0.join()
# childProcess1.join()

# procs = []



# data = []

for n in range(600000, 600010):
    po = Pool(processes=6)
    block = bcc.compose_request('block', n)
    start_time = time.time()
    res = po.starmap(parse_tx, [(tx, block) for tx in block['txs']])

    po.close()
    po.join()
    data = res.get()

    print(data)
    print(len(data))






# for q in queue:
#     print(q.get())
# queue = Queue()
#
# parsed_tx = []
# for tx in block['txs']:
#     queue.put(tx)
#     # proc = multiprocessing.Process(target=parse_tx, args=tx)
#     # t = parse_tx(tx, block)
#     # parsed_tx.append(t)
#
# cnt = 0
# while not queue.empty():
#     tx = queue.get()
#     t = parse_tx(tx, block)
#     print(cnt)
#     parsed_tx.append(t)
#     cnt += 1
#
# pprint(parsed_tx)

# Get latest block
# blocks = [srv.blockcount()]

# Get first block
# blocks = [1]

# Check first 100000 blocks
# blocks = range(1, 100000)

# Check some more recent blocks
# blocks = range(626001, 626002)
#
#
# for block in blocks:
#     print("Getting block %s" % block)
#     block_dict = srv.getblock(block, parse_transactions=False, limit=99999)
#     transactions = block_dict['txs']
#     print("Found %d transactions" % len(transactions))
#
#     MAX_TRANSACTIONS = 10000
#     count = 0
#     count_segwit = 0
#
#     for txid in transactions[:MAX_TRANSACTIONS]:
#
#         print("=== Deserialize transaction %s (#%d, segwit %d) ===" % (t.hash, count, count_segwit))
#         count += 1
#         t.verify()
#         # t.info()
#         if t.witness_type != 'legacy':
#             count_segwit += 1
#         if not t.verified:
#             print(50 * "!")
#             print("Transaction could not be verified!!")



print("--- %s seconds ---" % (time.time() - start_time))
