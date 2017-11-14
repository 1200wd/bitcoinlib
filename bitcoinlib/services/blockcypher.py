# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    BlockCypher client
#    © 2017 April - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.services.baseclient import BaseClient

PROVIDERNAME = 'blockcypher'

_logger = logging.getLogger(__name__)


class BlockCypher(BaseClient):

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def compose_request(self, function, data, parameter='', variables=None, method='get'):
        url_path = function + '/' + data
        if parameter:
            url_path += '/' + parameter
        if variables is None:
            variables = {}
        if self.api_key:
            variables.update({'token': self.api_key})
        return self.request(url_path, variables, method)

    def getbalance(self, addresslist):
        addresses = ';'.join(addresslist)
        res = self.compose_request('addrs', addresses, 'balance')
        balance = 0.0
        if not isinstance(res, list):
            res = [res]
        for rec in res:
            balance += float(rec['final_balance'])
        return int(balance * self.units)

    def getutxos(self, addresslist):
        return self.gettransactions(addresslist, unspent_only=True)

    def gettransactions(self, addresslist, unspent_only=False):
        transactions = []
        for address in addresslist:
            res = self.compose_request('addrs', address, variables={'unspentOnly': int(unspent_only), 'limit': 2000})
            if not isinstance(res, list):
                res = [res]
            for a in res:
                address = a['address']
                if 'txrefs' not in a:
                    continue
                if len(a['txrefs']) > 500:
                    _logger.warning("BlockCypher: Large number of transactions for address %s, "
                                    "Transaction list may be incomplete" % address)
                for tx in a['txrefs']:
                    transactions.append({
                        'address': address,
                        'tx_hash': tx['tx_hash'],
                        'confirmations': tx['confirmations'],
                        'block_height': tx['block_height'],
                        'date': datetime.strptime(tx['confirmed'], "%Y-%m-%dT%H:%M:%SZ"),
                        'input_n': tx['tx_input_n'],
                        'output_n': tx['tx_output_n'],
                        'double_spend': tx['double_spend'],
                        'index': 0,
                        'value': int(round(tx['value'] * self.units, 0)),
                        'script': '',
                    })
        return transactions

    def sendrawtransaction(self, rawtx):
        return self.compose_request('txs', 'push', variables={'tx': rawtx}, method='post')

    def decoderawtransaction(self, rawtx):
        return self.compose_request('txs', 'decode', variables={'tx': rawtx}, method='post')

    def estimatefee(self, blocks):
        res = self.compose_request('', '')
        if blocks <= 10:
            return res['high_fee_per_kb']
        else:
            return res['medium_fee_per_kb']
