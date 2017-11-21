# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    BlockTrail client
#    © 2017 June - 1200 Web Development <http://1200wd.com/>
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
import time
from datetime import datetime
from bitcoinlib.services.baseclient import BaseClient

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'chainso'
NETWORKCODES = {
    'bitcoin': 'BTC',
    'testnet': 'BTCTEST',
    'dash': 'DASH',
    'dash_testnet': 'DASHTEST',
    'litecoin': 'LTC',
    'litecoin_testnet': 'LTCTEST'
}


class ChainSo(BaseClient):

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def compose_request(self, function, data='', parameter='', variables=None, method='get'):
        url_path = function
        url_path += '/' + NETWORKCODES[self.network]
        if data:
            url_path += '/' + data
        if parameter:
            url_path += '/' + parameter
        if variables is None:
            variables = {}
        if self.api_key:
            variables.update({'api_key': self.api_key})
        return self.request(url_path, variables, method)

    def getrawtransaction(self, txid):
        res = self.compose_request('get_tx', txid)
        return res['data']['tx_hex']

    def sendrawtransaction(self, rawtx):
        return self.compose_request('send_tx', variables={'tx_hex': rawtx}, method='post')

    def getbalance(self, addresslist):
        balance = 0.0
        for address in addresslist:
            res = self.compose_request('get_address_balance', address)
            balance += float(res['data']['confirmed_balance']) + float(res['data']['unconfirmed_balance'])
        return int(balance * self.units)

    def _gettransactions(self, addresslist, method):
        txs = []
        for address in addresslist:
            lasttx = ''
            while len(txs) < 1000:
                res = self.compose_request(method, address, lasttx)
                if res['status'] != 'success':
                    pass
                for tx in res['data']['txs']:
                    txs.append({
                        'address': address,
                        'hash': tx['txid'],
                        'confirmations': tx['confirmations'],
                        'output_n': -1 if 'output_no' not in tx else tx['output_no'],
                        'input_n': -1 if 'input_no' not in tx else tx['input_no'],
                        'block_height': None,
                        'fee': None,
                        'size': 0,
                        'value': int(round(float(tx['value']) * self.units, 0)),
                        'script': tx['script_hex'],
                        'date': datetime.fromtimestamp(tx['time']),
                    })
                    lasttx = tx['txid']
                time.sleep(0.3)
                if len(res['data']['txs']) < 100:
                    break

        if len(txs) >= 1000:
            _logger.warning("ChainSo: transaction list has been truncated, and thus is incomplete")
        return txs

    def getutxos(self, addresslist):
        return self._gettransactions(addresslist, 'get_tx_unspent')

    def gettransactions(self, addresslist):
        tx_list = self._gettransactions(addresslist, 'get_tx_received') + \
                  self._gettransactions(addresslist, 'get_tx_spent')
        txs = []
        for tx in tx_list:
            if tx['hash'] not in [t['hash'] for t in txs]:
                txs.append({
                    'hash': tx['hash'],
                    'date': tx['date'],
                    'confirmations': tx['confirmations'],
                    'block_height': tx['block_height'],
                    'fee': tx['fee'],
                    'size': tx['size'],
                    'inputs': [],
                    'outputs': [],
                    'status': 'incomplete',
                })
            if tx['input_n'] != -1:
                next((item for item in txs if item['hash'] == tx['hash']))['inputs'].append({
                    'prev_hash': '' if 'spent_by' not in tx else tx['spent_by'],
                    'input_n': tx['input_n'],
                    'address': tx['address'],
                    'value': tx['value'],
                    'double_spend': None,
                    'script': tx['script']
                })
            else:
                next((item for item in txs if item['hash'] == tx['hash']))['outputs'].append({
                    'address': tx['address'],
                    'output_n': tx['output_n'],
                    'value': tx['value'],
                    'spent': None,
                    'script': tx['script']
                })
        return txs
