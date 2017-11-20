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
from datetime import datetime
from bitcoinlib.services.baseclient import BaseClient

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'blocktrail'


class BlockTrail(BaseClient):

    def __init__(self, network, base_url, denominator, api_key=''):
        if not api_key:
            raise ValueError("API key is needed to connect to BlockTrail")
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def compose_request(self, function, data, parameter='', variables=None, method='get', page=1):
        url_path = function
        if data:
            url_path += '/' + data
        if parameter:
            url_path += '/' + parameter
        if variables is None:
            variables = {}
        if self.api_key:
            variables.update({'api_key': self.api_key})
        return self.request(url_path, variables, method)

    def getbalance(self, addresslist):
        balance = 0.0
        for address in addresslist:
            res = self.compose_request('address', address)
            balance += int(res['balance'])
        return int(balance * self.units)

    def getutxos(self, addresslist):
        utxos = []
        for address in addresslist:
            # res = self.compose_request('address', address, 'unspent-outputs')
            current_page = 1
            while len(utxos) < 2000:
                variables = {'page': current_page, 'limit': 200}
                res = self.compose_request('address', address, 'unspent-outputs', variables)
                for utxo in res['data']:
                    utxos.append({
                        'address': address,
                        'tx_hash': utxo['hash'],
                        'confirmations': utxo['confirmations'],
                        'output_n': utxo['index'],
                        'index': 0,
                        'value': int(round(utxo['value'] * self.units, 0)),
                        'script': '',
                    })
                if current_page*200 > int(res['total']):
                    break
                current_page += 1

        if len(utxos) >= 2000:
            _logger.warning("BlockTrail: UTXO's list has been truncated, UTXO list is incomplete")
        return utxos

    def gettransactions(self, addresslist):
        txs = []
        for address in addresslist:
            # res = self.compose_request('address', address, 'unspent-outputs')
            current_page = 1
            while len(txs) < 2000:
                variables = {'page': current_page, 'limit': 200}
                res = self.compose_request('address', address, 'transactions', variables)
                for tx in res['data']:
                    if tx['hash'] in [t['hash'] for t in txs]:
                        break
                    inputs = []
                    outputs = []
                    for ti in tx['inputs']:
                        inputs.append({
                            'prev_hash': ti['output_hash'],
                            'input_n': ti['output_index'],
                            'address': ti['address'],
                            'value': int(round(ti['value'] * self.units, 0)),
                            'double_spend': None,
                            'script': ti['script_signature']
                            # TODO: Add 'script_type': ti['type']
                        })
                    for to in tx['outputs']:
                        outputs.append({
                            'output_n': to['index'],
                            'address': to['address'],
                            'value': int(round(to['value'] * self.units, 0)),
                            'spent': bool(to['spent_hash']),
                            'script': to['script_hex']
                        })
                    status = 'unconfirmed'
                    if tx['confirmations']:
                        status = 'confirmed'
                    txs.append({
                        'hash': tx['hash'],
                        'date': datetime.strptime(tx['time'], "%Y-%m-%dT%H:%M:%S+%f"),
                        'confirmations': tx['confirmations'],
                        'block_height': tx['block_height'],
                        'fee': tx['total_fee'],
                        'size': 0,
                        'inputs': inputs,
                        'outputs': outputs,
                        'status': status
                    })
                if current_page*200 > int(res['total']):
                    break
                current_page += 1

        if len(txs) >= 2000:
            _logger.warning("BlockTrail: UTXO's list has been truncated, UTXO list is incomplete")
        return txs

    def estimatefee(self, blocks):
        res = self.compose_request('fee-per-kb', '')
        if blocks <= 10:
            return res['optimal']
        else:
            return res['low_priority']
