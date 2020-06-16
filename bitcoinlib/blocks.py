# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    BLOCK parsing and construction
#    © 2020 Juni - 1200 Web Development <http://1200wd.com/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from bitcoinlib.encoding import *
from bitcoinlib.transactions import transaction_deserialize, Transaction


def parse_transactions(self, limit=0):
    n = 0
    while self.txs_data and (limit == 0 or n < limit):
        t = transaction_deserialize(self.txs_data, network=self.network, check_size=False)
        self.transactions.append(t)
        self.txs_data = self.txs_data[t.size:]
        n += 1


class Block:

    def __init__(self, blockhash, version, prev_block, merkle_root, time, bits, nonce, transactions=None,
                 height=None, confirmations=None, network=DEFAULT_NETWORK):
        self.blockhash = to_bytes(blockhash)
        if isinstance(version, int):
            self.version = struct.pack('>L', version)
            self.version_int = version
        else:
            self.version = to_bytes(version)
            self.version_int = 0 if not self.version else struct.unpack('>L', self.version)[0]
        self.prev_block = to_bytes(prev_block)
        self.merkle_root = to_bytes(merkle_root)
        self.time = time
        if not isinstance(time, int):
            self.time = struct.unpack('>L', time)[0]
        if isinstance(bits, int):
            self.bits = struct.pack('>L', bits)
            self.bits_int = bits
        else:
            self.bits = to_bytes(bits)
            self.bits_int = 0 if not self.bits else struct.unpack('>L', self.bits)[0]
        if isinstance(nonce, int):
            self.nonce = struct.pack('>L', nonce)
            self.nonce_int = nonce
        else:
            self.nonce = to_bytes(nonce)
            self.nonce_int = 0 if not self.nonce else struct.unpack('>L', self.nonce)[0]
        self.transactions = transactions
        self.txs_data = None
        self.height = height
        self.confirmations = confirmations
        self.network = network
        self.tx_count = None
        if not height and len(self.transactions) and isinstance(self.transactions[0], Transaction):
            # first bytes of unlocking script of coinbase transaction contain block height
            self.block_height = struct.unpack('<L', self.transactions[0].inputs[0].unlocking_script[1:4] + b'\x00')[0]

    def __repr__(self):
        return "<Block(%s, %d, transactions: %d)>" % (to_hexstring(self.blockhash), self.height, self.tx_count)

    @classmethod
    def from_raw(cls, rawblock, blockhash=None, parse_transactions=False, network=DEFAULT_NETWORK):
        blockhash_calc = double_sha256(rawblock[:80])[::-1]
        if not blockhash:
            blockhash = blockhash_calc
        elif blockhash != blockhash_calc:
            raise ValueError("Provided blockhash does not correspond to calculated blockhash %s" % blockhash_calc)

        version = rawblock[0:4][::-1]
        prev_block = rawblock[4:36][::-1]
        merkle_root = rawblock[36:68][::-1]
        time = rawblock[68:72][::-1]
        bits = rawblock[72:76][::-1]
        nonce = rawblock[76:80][::-1]
        tx_count, size = varbyteint_to_int(rawblock[80:89])
        txs_data = rawblock[80+size:]

        # Parse coinbase transaction so we can extract extra information
        transactions = [transaction_deserialize(txs_data, network=network, check_size=False)]
        txs_data = txs_data[transactions[0].size:]

        while parse_transactions and txs_data:
            t = transaction_deserialize(txs_data, network=network, check_size=False)
            transactions.append(t)
            txs_data = txs_data[t.size:]
            # TODO: verify transactions, need input value from previous txs
            # if verify and not t.verify():
            #     raise ValueError("Could not verify transaction %s in block %s" % (t.txid, blockhash))

        if parse_transactions and tx_count != len(transactions):
            raise ValueError("Number of found transactions %d is not equal to expected number %d" %
                             (len(transactions), tx_count))

        block = cls(blockhash, version, prev_block, merkle_root, time, bits, nonce, transactions, network=network)
        block.txs_data = txs_data
        block.tx_count = tx_count
        return block

    def parse_transactions(self, limit=0):
        n = 0
        while self.txs_data and (limit == 0 or n < limit):
            t = transaction_deserialize(self.txs_data, network=self.network, check_size=False)
            self.transactions.append(t)
            self.txs_data = self.txs_data[t.size:]
            n += 1
        return self

    def as_dict(self):
        return {
            'blockhash': to_hexstring(self.blockhash),
            'height': self.height,
            'version': self.version_int,
            'prev_block': to_hexstring(self.prev_block),
            'merkle_root': to_hexstring(self.merkle_root),
            'timestamp': self.time,
            'bits': self.bits_int,
            'nonce': self.nonce_int,
            'target': self.target_hex,
            'difficulty': self.difficulty,
            'tx_count': self.tx_count,
            'transactions': self.transactions
        }

    @property
    def target(self):
        exponent = self.bits[0]
        coefficient = struct.unpack('>L', b'\x00' + self.bits[1:])[0]
        return coefficient * 256 ** (exponent - 3)

    @property
    def target_hex(self):
        return hex(self.target)[2:].zfill(64)

    @property
    def difficulty(self):
        difficulty = 0xffff * 256 ** (0x1d - 3) / self.target
        return 0xffff001d if difficulty < 0xffff001d else difficulty
