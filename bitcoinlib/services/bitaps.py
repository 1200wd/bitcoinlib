# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    BitAps client
#    © 2019 August - 1200 Web Development <http://1200wd.com/>
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

import math
import logging
from datetime import datetime
from bitcoinlib.main import MAX_TRANSACTIONS
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction
from bitcoinlib.keys import deserialize_address
from bitcoinlib.encoding import EncodingError, varstr, to_bytes

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'bitaps'
# REQUEST_LIMIT = 100


class BitapsClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, category, command='', data='', variables=None, type='blockchain'):
        url_path = type + '/' + category
        if command:
            url_path += '/' + command
        if data:
            if url_path[-1:] != '/':
                url_path += '/'
            url_path += data
        return self.request(url_path, variables=variables)

    def getbalance(self, addresslist):
        pass

    def getutxos(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):
        pass

    def gettransactions(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):
        pass

    def gettransaction(self, txid):
        res = self.compose_request('transaction', txid)
        tx = res['data']
        t = Transaction.import_raw(tx['rawTx'], network=self.network)
        if tx['confirmations']:
            t.status = 'confirmed'
        t.hash = txid
        t.date = datetime.fromtimestamp(tx['blockTime'])
        t.confirmations = tx['confirmations']
        if 'blockHeight' in tx:
            t.block_height = tx['blockHeight']
            t.block_hash = tx['blockHash']
        t.fee = tx['fee']
        t.rawtx = tx['rawTx']
        t.size = tx['size']
        t.network = self.network
        for i in t.inputs:
            i.value = tx['vIn'][str(i.index_n)]['amount']
        for o in t.outputs:
            if tx['vOut'][str(o.output_n)]['spent']:
                o.spent = True
        t.input_total = tx['inputsAmount']
        t.output_total = tx['outputsAmount']
        return t

    def getrawtransaction(self, txid):
        tx = self.compose_request('transaction', txid)
        return tx['data']['rawTx']

    def block_count(self):
        return self.compose_request('block', 'last')['data']['block']['height']

    def mempool(self, txid=''):
        pass
