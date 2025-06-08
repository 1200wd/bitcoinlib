# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Nownodes Client - see https://nownodes.gitbook.io/
#    1200 Web Development <http://1200wd.com/>
#    © 2025 May
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

import logging
from datetime import datetime, timezone
from bitcoinlib.main import MAX_TRANSACTIONS
from bitcoinlib.services.baseclient import BaseClient
from bitcoinlib.transactions import Transaction

PROVIDERNAME = 'nownodes'
REQUEST_LIMIT = 50

_logger = logging.getLogger(__name__)


class NownodesClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)
        self.proxy = None

    def compose_request(self, function='', params=None, method='post'):
        url_path = self.api_key
        data = {
            "jsonrpc": "2.0",
            "method": function,
            "params": [] if not params else params,
            "id": "curltest"
        }
        return self.request(url_path, variables=data, method=method)

    def _parse_transaction(self, tx, block_height=None):
        t = Transaction.parse_hex(tx['hex'], strict=self.strict, network=self.network)
        t.confirmations = tx.get('confirmations')
        t.block_hash = tx.get('blockhash')
        t.status = 'unconfirmed'
        for i in t.inputs:
            if i.prev_txid == b'\x00' * 32:
                i.script_type = 'coinbase'
                continue
            txi =  self.compose_request('getrawtransaction', [i.prev_txid.hex(), True])['result']
            i.value = int(round(float(txi['vout'][i.output_n_int]['value']) / self.network.denominator))

        for o in t.outputs:
            o.spent = None

        t.block_height = block_height if block_height else (
            self.compose_request('getblockheader', [t.block_hash])['result']['height'])
        if t.confirmations:
            t.status = 'confirmed'
            t.verified = True
        t.version = tx['version'].to_bytes(4, 'big')
        t.version_int = tx['version']
        t.date = None if 'time' not in tx else datetime.fromtimestamp(tx['time'], timezone.utc)
        t.update_totals()
        return t

    # def getbalance(self, addresslist):

    # def getutxos(self, address, after_txid='', limit=MAX_TRANSACTIONS):

    def gettransaction(self, txid):
        tx = self.compose_request('getrawtransaction', [txid, True])['result']
        t = self._parse_transaction(tx)
        return t

    # def gettransactions(self, address, after_txid='', limit=MAX_TRANSACTIONS):

    def getrawtransaction(self, txid):
        method = 'getrawtransaction'
        res = self.compose_request(method, [txid, False])
        return res['result']

    def sendrawtransaction(self, rawtx):
        res = self.compose_request('sendrawtransaction', [rawtx])['result']
        return {
            'txid': res,
            'response_dict': res
        }
    # def estimatefee(self, blocks):

    def blockcount(self):
        method = 'getblockchaininfo'
        res = self.compose_request(method)
        return res['result']['blocks']

    def mempool(self, txid=''):
        method = 'getrawmempool'
        res = self.compose_request(method)
        txids = res['result']
        if not txid:
            return txids
        elif txid in txids:
            return [txid]
        return []

    def getblock(self, blockid, parse_transactions, page, limit):
        if isinstance(blockid, int) or len(blockid) < 10:
            blockid = self.compose_request('getblockhash', [int(blockid)])['result']
        if not limit:
            limit = 99999

        txs = []
        if parse_transactions:
            bd = self.compose_request('getblock', [blockid, 2])['result']
            for tx in bd['tx'][(page - 1) * limit:page * limit]:
                tx['time'] = bd['time']
                tx['blockhash'] = bd['hash']
                txs.append(self._parse_transaction(tx, block_height=bd['height']))
        else:
            bd =  self.compose_request('getblock', [blockid, 1])['result']
            txs = bd['tx']

        block = {
            'bits': int(bd['bits'], 16),
            'depth': bd['confirmations'],
            'block_hash': bd['hash'],
            'height': bd['height'],
            'merkle_root': bd['merkleroot'],
            'nonce': bd['nonce'],
            'prev_block': None if 'previousblockhash' not in bd else bd['previousblockhash'],
            'time': bd['time'],
            'tx_count': bd['nTx'],
            'txs': txs,
            'version': bd['version'],
            'page': page,
            'pages': None,
            'limit': limit
        }
        return block

    def getrawblock(self, blockid):
        if isinstance(blockid, int):
            blockid = self.compose_request('getblockhash', [int(blockid)])['result']
        return self.compose_request('getblock', [blockid, 0])['result']

    def isspent(self, txid, output_n):
        params = [
            txid,
            output_n
        ]
        res = self.compose_request('gettxout', params)['result']
        return 0 if res else 1

    def getinfo(self):
        method = 'getmininginfo'
        res = self.compose_request(method)
        return {
            'blockcount': res['result']['blocks'],
            'chain': res['result']['chain'],
            'difficulty': int(res['result']['difficulty']),
            'hashrate': int(res['result']['networkhashps']),
            'mempool_size': int(res['result']['pooledtx']),
        }