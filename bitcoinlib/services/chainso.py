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
from bitcoinlib.services.services import ServiceError


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
        txs = []
        for address in addresslist:
            res = self.compose_request('address', address)
            if res['status'] != 'success':
                pass
            for tx in res['data']['txs']:
                if tx['txid'] not in [t['hash'] for t in txs]:
                    txs.append({
                        'hash': tx['txid'],
                        'date': datetime.fromtimestamp(tx['time']),
                        'confirmations': tx['confirmations'],
                        'block_height': tx['block_no'],
                        'fee': None,
                        'size': 0,
                        'inputs': [],
                        'outputs': [],
                        'status': 'incomplete',
                    })
                if 'incoming' in tx:
                    if len(tx['incoming']['inputs']) > 1:
                        raise ServiceError("Chainso client: More then one input in incoming tx not supported")
                    next((item for item in txs if item['hash'] == tx['txid']))['inputs'].append({
                        'prev_hash': tx['incoming']['inputs'][0]['received_from']['txid'],
                        'input_n': tx['incoming']['inputs'][0]['received_from']['output_no'],
                        'address': tx['incoming']['inputs'][0]['address'],
                        'value': int(round(float(tx['incoming']['value']) * self.units, 0)),
                        'double_spend': None,
                        'script': tx['incoming']['script_hex']
                    })
                if 'outgoing' in tx:
                    if len(tx['outgoing']['outputs']) > 1:
                        print("Chainso client: More then one input in incoming tx not supported")
                    for tx_outp in tx['outgoing']['outputs']:
                        next((item for item in txs if item['hash'] == tx['txid']))['outputs'].append({
                                'address': tx_outp['address'],
                                'output_n': tx_outp['output_no'],
                                'value': int(round(float(tx_outp['value']) * self.units, 0)),
                                'spent': bool(tx_outp['spent']),
                                'script': ''
                            })
        return txs
