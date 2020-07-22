# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Block examples
#
#    © 2020 July - 1200 Web Development <http://1200wd.com/>
#

from pprint import pprint
from bitcoinlib.blocks import *
from bitcoinlib.services.services import *


print("=== Create Block object (block 120000) ===")
# def __init__(self, block_hash, version, prev_block, merkle_root, time, bits, nonce, transactions=None,
#              height=None, confirmations=None, network=DEFAULT_NETWORK):
b = Block(block_hash='0000000000000e07595fca57b37fea8522e95e0f6891779cfd34d7e537524471', version=1,
          prev_block='000000000000337828025b947973252acf8d668b3bb459c1c6e70b2e5827bca4',
          merkle_root='6dbba50b72ad0569c2449090a371516e3865840e905483cac0f54d96944eee28',
          time=1303687201, bits=453031340, nonce=4273989260, height=120000)
pprint(b.as_dict())


print("=== Parse raw block (block 100) ===")
raw_block = "010000007de867cc8adc5cc8fb6b898ca4462cf9fd667d7830a275277447e60800000000338f121232e169d3100edd82004dc2a1f0e1f030c6c488fa61eafa930b0528fe021f7449ffff001d36b4af9a0101000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0804ffff001d02fd04ffffffff0100f2052a01000000434104f5eeb2b10c944c6b9fbcfff94c35bdeecd93df977882babc7f3a2cf7f5c81d3b09a68db7f0e04f21de5d4230e75e6dbe7ad16eefe0d4325a62067dc6f369446aac00000000"
b = Block.from_raw(bytes.fromhex(raw_block), height=100, parse_transactions=True)
pprint(b.as_dict())


print("=== Get Bitcoin block with height 430000 from service providers ===")
srv = Service()
b = srv.getblock(430000)
pprint(b.as_dict())


print("=== Get Litecoin block with height 1000000 from service providers ===")
srv = Service(network='litecoin')
b = srv.getblock(1000000)
pprint(b.as_dict())
