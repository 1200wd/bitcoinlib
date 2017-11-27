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
from bitcoinlib.services.baseclient import BaseClient, ClientError


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
        # Sleep for 0.2 seconds to avoid 429 errors
        time.sleep(0.2)
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

    def getutxos(self, addresslist):
        txs = []
        for address in addresslist:
            lasttx = ''
            while len(txs) < 1000:
                res = self.compose_request('get_tx_unspent', address, lasttx)
                if res['status'] != 'success':
                    pass
                for tx in res['data']['txs']:
                    txs.append({
                        'address': address,
                        'tx_hash': tx['txid'],
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
                if len(res['data']['txs']) < 100:
                    break
        if len(txs) >= 1000:
            _logger.warning("ChainSo: transaction list has been truncated, and thus is incomplete")
        return txs

    def gettransactions(self, addresslist):
        txs = []
        tx_ids = []
        for address in addresslist:
            res = self.compose_request('address', address)
            if res['status'] != 'success':
                pass
            for tx in res['data']['txs']:
                if tx['txid'] not in tx_ids:
                    tx_ids.append(tx['txid'])

        for tx_hash in tx_ids:
            res = self.compose_request('get_tx', tx_hash)
            tx = res['data']
            inputs = []
            outputs = []
            input_total = 0
            output_total = 0
            for ti in tx['inputs']:
                value = int(round(float(ti['value']) * self.units, 0))
                inputs.append({
                    'prev_hash': ti['from_output']['txid'],
                    'input_n': ti['from_output']['output_no'],
                    'address': ti['address'],
                    'value': value,
                    'double_spend': None,
                    'script': '',
                })
                input_total += value
            for to in tx['outputs']:
                value = int(round(float(to['value']) * self.units, 0))
                outputs.append({
                    'address': to['address'],
                    'output_n': to['output_no'],
                    'value': value,
                    'spent': None,
                    'script': '',
                })
                output_total += value
            status = 'unconfirmed'
            fee = input_total - output_total
            if tx['confirmations']:
                status = 'confirmed'
            txs.append({
                'hash': tx_hash,
                'date': datetime.fromtimestamp(tx['time']),
                'confirmations': tx['confirmations'],
                'block_height': None,
                'fee': fee,
                'size': tx['size'],
                'inputs': inputs,
                'outputs': outputs,
                'input_total': input_total,
                'output_total': output_total,
                'raw': tx['tx_hex'],
                'network': self.network,
                'status': status,
            })
        return txs
