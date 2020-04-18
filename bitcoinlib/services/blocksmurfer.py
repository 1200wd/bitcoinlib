# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Blocksmurfer client
#    © 2020 Januari - 1200 Web Development <http://1200wd.com/>
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
from datetime import datetime
from bitcoinlib.main import MAX_TRANSACTIONS
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction
from bitcoinlib.encoding import to_hexstring

PROVIDERNAME = 'blocksmurfer'


_logger = logging.getLogger(__name__)


class BlocksmurferClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, function, parameter='', variables=None, post_data='', method='get'):
        url_path = function
        if parameter:
            url_path += '/' + parameter
        if variables is None:
            variables = {}
        if self.api_key:
            variables.update({'token': self.api_key})
        return self.request(url_path, variables, method, post_data=post_data)

    def getbalance(self, addresslist):
        balance = 0
        for address in addresslist:
            res = self.compose_request('address/balance', address)
            balance += res['data']['balance']
        return balance

    def getutxos(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):
        res = self.compose_request('utxos', address, {'after_txid': after_txid})
        block_count = self.blockcount()
        utxos = []
        for u in res['data']:
            block_height = None if not u['block_height'] else u['block_height']
            confirmations = u['confirmations']
            if block_height and not confirmations:
                confirmations = block_count - block_height
            # if not block_height and confirmations:
            #     block_height = block_count - confirmations
            utxos.append({
                'address': address,
                'tx_hash': u['tx_hash'],
                'confirmations': confirmations,
                'output_n': u['output_n'],
                'input_n': u['input_n'],
                'block_height': block_height,
                'fee': u['fee'],
                'size': u['size'],
                'value': u['value'],
                'script': u['script'],
                'date': datetime.strptime(u['date'][:19], "%Y-%m-%dT%H:%M:%S")
            })
        return utxos[:max_txs]

    def _parse_transaction(self, tx):
        t = Transaction.import_raw(tx['raw_hex'], network=self.network)
        if t.hash != tx['txid']:
            raise ClientError("Different hash from Blocksmurfer when parsing transaction")
        t.block_height = None if not tx['block_height'] else tx['block_height']
        t.confirmations = tx['confirmations']
        t.date = datetime.strptime(tx['date'][:19], "%Y-%m-%dT%H:%M:%S")
        if t.block_height and not t.confirmations and tx['status'] == 'confirmed':
            block_count = self.blockcount()
            t.confirmations = block_count - t.block_height
        # if not t.block_height and t.confirmations:
        #     block_count = self.blockcount()
        #     t.block_height = block_count - t.confirmations
        t.status = tx['status']
        t.fee = tx['fee']
        for ti in t.inputs:
            t.inputs[ti.index_n].value = tx['inputs'][ti.index_n]['value']
        for to in t.outputs:
            t.outputs[to.output_n].spent = tx['outputs'][to.output_n]['spent']
        t.update_totals()
        return t

    def gettransaction(self, txid):
        tx = self.compose_request('tx', txid)
        return self._parse_transaction(tx['data'])

    def gettransactions(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):
        prtxs = []
        while True:
            res = self.compose_request('tx/address', address, {'after_txid': after_txid})
            txs = res['data']
            prtxs += txs
            if not txs or len(txs) < max_txs:
                break
            after_txid = txs[-1:][0]['txid']
        txs = []
        for tx in prtxs[::-1]:
            t = self._parse_transaction(tx)
            if t:
                txs.append(t)
        return txs[:max_txs]

    def getrawtransaction(self, txid):
        tx = self.compose_request('tx/hex', txid)
        return tx['data']['rawtx']

    def sendrawtransaction(self, rawtx):
        res = self.compose_request('tx', post_data=rawtx, method='post')
        return {
            'txid': res,
            'response_dict': res
        }

    def estimatefee(self, blocks):
        variables = {
            'blocks': str(blocks)
        }
        res = self.compose_request('fees', variables=variables)
        return res['data']['estimated_fee_sat_kb']

    def blockcount(self):
        return self.compose_request('blocks', 'count')['data']['block_count']

    def mempool(self, txid):
        if txid:
            t = self.gettransaction(txid)
            if t and not t.confirmations:
                return [t.hash]
        # else:
            # return self.compose_request('mempool', 'txids')
        return []
