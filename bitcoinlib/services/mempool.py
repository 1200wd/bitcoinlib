# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    mempool.space client
#    © 2021 November - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.encoding import varstr

PROVIDERNAME = 'mempool'
# Please note: In the Blockstream API, the first couple of Bitcoin blocks are not correctly indexed,
# so transactions from these blocks are missing.

_logger = logging.getLogger(__name__)


class MempoolClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, function, data='', parameter='', variables=None, post_data='', method='get'):
        url_path = function
        if data:
            url_path += '/' + data
        if parameter:
            url_path += '/' + parameter
        if variables is None:
            variables = {}
        if self.api_key:
            variables.update({'token': self.api_key})
        return self.request(url_path, variables, method, post_data=post_data)

    def getbalance(self, addresslist):
        pass

    def getutxos(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        pass

    def gettransaction(self, txid, blockcount=None):
        pass

    def gettransactions(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        pass

    def getrawtransaction(self, txid):
        return self.compose_request('tx', txid, 'hex')

    def sendrawtransaction(self, rawtx):
        pass

    def estimatefee(self, blocks):
        estimates = self.compose_request('fees', 'recommended')
        #{'fastestFee': 3, 'halfHourFee': 3, 'hourFee': 3, 'minimumFee': 1}
        if blocks < 2:
            return estimates['fastestFee']
        elif blocks < 4:
            return estimates['halfHourFee']
        if blocks < 7:
            return estimates['hourFee']
        else:
            return estimates['minimumFee']

    def blockcount(self):
        res = self.compose_request(('blocks', 'tip', 'height'))
        return res

    def mempool(self, txid):
        pass

    def getblock(self, blockid, parse_transactions, page, limit):
        pass

    def getrawblock(self, blockid):
        pass

    def isspent(self, txid, output_n):
        pass

    def getinfo(self):
        pass