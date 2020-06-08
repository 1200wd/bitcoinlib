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


class Block:

    def __init__(self, blockhash, version, prev_block, merkle_root, timestamp, bits, nonce):
        self.blockhash = blockhash
        self.version = version
        self.version_int = struct.unpack('<L', version)[0]
        self.prev_block = prev_block
        self.merkle_root = merkle_root
        self.timestamp = struct.unpack('<L', timestamp)[0]
        self.bits = bits
        self.bits_int = struct.unpack('>L', bits)[0]
        self.nonce = nonce
        self.nonce_int = struct.unpack('>L', nonce)[0]
        # self.target = None
        # self.difficulty = None
        self.transactions = None

    @classmethod
    def from_raw(cls, rawblock, blockhash=None):
        if not blockhash:
            blockhash = double_sha256(rawblock[:80])[::-1]
        version = rawblock[0:4]
        prev_block = rawblock[4:36][::-1]
        merkle_root = rawblock[36:68][::-1]
        timestamp = rawblock[68:72]
        bits = rawblock[72:76]
        nonce = rawblock[76:80]
        tx_count, size = varbyteint_to_int(rawblock[80:89])
        return cls(blockhash, version, prev_block, merkle_root, timestamp, bits, nonce)

    def as_dict(self):
        return {
            'blockhash': to_hexstring(self.blockhash),
            'version': self.version_int,
            'prev_block': to_hexstring(self.prev_block),
            'merkle_root': to_hexstring(self.merkle_root),
            'timestamp': self.timestamp,
            'bits': self.bits_int,
            'nonce': self.nonce_int,
            'target': self.target_hex,
            'difficulty': self.difficulty,
        }

    @property
    def target(self):
        exponent = self.bits[-1]
        coefficient = struct.unpack('<L', b'\x00' + self.bits[:-1])[0]
        return coefficient * 256 ** (exponent - 3)

    @property
    def target_hex(self):
        return hex(self.target)[2:].zfill(64)

    @property
    def difficulty(self):
        difficulty = 0xffff * 256 ** (0x1d - 3) / self.target
        return 0xffff001d if difficulty < 0xffff001d else difficulty
