# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    BitGo Client
#    © 2017 May - 1200 Web Development <http://1200wd.com/>
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

PROVIDERNAME = 'bitgo'


class BitGoClient(BaseClient):

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def compose_request(self, category, data, cmd='', variables=None, method='get'):
        if data:
            data = '/' + data
        url_path = category + data
        if cmd:
            url_path += '/' + cmd
        return self.request(url_path, variables, method=method)

    def getbalance(self, addresslist):
        balance = 0
        for address in addresslist:
            res = self.compose_request('address', address)
            balance += res['balance']
        return balance

    def getutxos(self, addresslist):
        utxos = []
        for address in addresslist:
            skip = 0
            total = 1
            while total > skip:
                variables = {'limit': 100, 'skip': skip}
                res = self.compose_request('address', address, 'unspents', variables)
                for unspent in res['unspents']:
                    utxos.append(
                        {
                            'address': unspent['address'],
                            'tx_hash': unspent['tx_hash'],
                            'confirmations': unspent['confirmations'],
                            'output_n': unspent['tx_output_n'],
                            'index': 0,
                            'value': int(round(unspent['value'] * self.units, 0)),
                            'script': unspent['script'],
                         }
                    )
                total = res['total']
                skip = res['start'] + res['count']
                if skip > 2000:
                    _logger.warning("BitGoClient: UTXO's list has been truncated, UTXO list is incomplete")
                    break
        return utxos

    def gettransactions(self, addresslist):
        txs = []
        for address in addresslist:
            skip = 0
            total = 1
            while total > skip:
                variables = {'limit': 100, 'skip': skip}
                res = self.compose_request('address', address, 'tx', variables)
                for tx in res['transactions']:
                    if tx['id'] in [t['hash'] for t in txs]:
                        break
                    inputs = []
                    outputs = []
                    # FIXME: Assumes entries are in same order as inputs
                    input_entries = [ie for ie in tx['entries'] if ie['value'] < 0][::-1]
                    for i in tx['inputs']:
                        ti = input_entries.pop()
                        inputs.append({
                            'prev_hash': i['previousHash'],
                            'input_n': i['previousOutputIndex'],
                            'address': ti['account'],
                            'value': int(round(-ti['value'] * self.units, 0)),
                        })
                    for to in tx['outputs']:
                        outputs.append({
                            'output_n': to['vout'],
                            'address': to['account'],
                            'value': int(round(to['value'] * self.units, 0)),
                            'spent': None
                        })
                    txs.append({
                        'hash': tx['id'],
                        'date': datetime.strptime(tx['date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                        'confirmations': tx['confirmations'],
                        'block_height': tx['height'],
                        'fee': tx['fee'],
                        'inputs': inputs,
                        'outputs': outputs
                    })
                total = res['total']
                skip = res['start'] + res['count']
                if skip > 2000:
                    _logger.warning("BitGoClient: UTXO's list has been truncated, UTXO list is incomplete")
                    break
        return txs

    def getrawtransaction(self, txid):
        res = self.compose_request('tx', txid)
        return res['hex']

    def estimatefee(self, blocks):
        res = self.compose_request('tx', 'fee', variables={'numBlocks': blocks})
        return res['feePerKb']
