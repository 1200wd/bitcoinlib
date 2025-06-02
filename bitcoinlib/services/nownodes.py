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

    def compose_request(self, function='', params=None, method='post'):
        url_path = self.api_key
        data = {
            "jsonrpc": "2.0",
            "method": function,
            "data": [] if not params else params
        }
        return self.request(url_path, variables={}, post_data=data, method=method)

    # def _convert_to_transaction(self, tx):

    # def getbalance(self, addresslist):

    # def getutxos(self, address, after_txid='', limit=MAX_TRANSACTIONS):

    # def gettransaction(self, txid):

    # def gettransactions(self, address, after_txid='', limit=MAX_TRANSACTIONS):

    # def getrawtransaction(self, txid):

    # def sendrawtransaction(self, rawtx):

    # def estimatefee(self, blocks):

    def blockcount(self):
        method = 'getblockchaininfo'
        return self.compose_request(method)

    # def mempool(self, txid):

    # def getblock(self, blockid, parse_transactions, page, limit):

    # def getrawblock(self, blockid):

    # def isspent(self, txid, output_n):

    # def getinfo(self):
