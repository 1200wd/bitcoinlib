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
from bitcoinlib.transactions import Transaction

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
                    _logger.warning("BitGoClient: UTXO's list has been truncated, list is incomplete")
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
                    status = 'unconfirmed'
                    if tx['confirmations']:
                        status = 'confirmed'
                    txs.append({
                        'hash': tx['id'],
                        'date': datetime.strptime(tx['date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                        'confirmations': tx['confirmations'],
                        'block_height': tx['height'],
                        'block_hash': tx['blockhash'],
                        'fee': tx['fee'],
                        'size': 0,
                        'inputs': [],
                        'outputs': [],
                        'input_total': 0,
                        'output_total': 0,
                        'raw': '',
                        'network': self.network,
                        'status': status,
                        'tmp_input_values':
                            [(inp['account'], -inp['value']) for inp in tx['entries'] if inp['value'] < 0],
                    })
                total = res['total']
                skip = res['start'] + res['count']
                if skip > 2000:
                    _logger.warning("BitGoClient: Transactions list has been truncated, list is incomplete")
                    break
        for tx in txs:
            rawtx = self.getrawtransaction(tx['hash'])
            t = Transaction.import_raw(rawtx)
            input_total = 0
            for i in t.inputs:
                value = [x[1] for x in tx['tmp_input_values'] if x[0] == i.address]
                if len(value) != 1:
                    _logger.warning("BitGoClient: Address %s input value should be found 1 times in value list")
                i.value = value[0]
                input_total += value[0]
            tx['inputs'] = [i.dict() for i in t.inputs]
            tx['outputs'] = [o.dict() for o in t.outputs]
            tx['input_total'] = input_total
            tx['output_total'] = input_total - tx['fee']
            tx['raw'] = t.raw()
            tx['size'] = len(tx['raw'])
            del(tx['tmp_input_values'])
        return txs

    def gettransaction(self, txid):
        tx = self.compose_request('tx', txid)
        t = Transaction.import_raw(tx['hex'])
        if tx['confirmations']:
            t.status = 'confirmed'
        t.hash = txid
        t.date = datetime.strptime(tx['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        t.confirmations = tx['confirmations']
        if 'height' in tx:
            t.block_height = tx['height']
            t.block_hash = tx['blockhash']
        t.fee = tx['fee']
        t.rawtx = tx['hex']
        t.size = len(t.raw())
        t.network_name = self.network
        input_values = [(inp['account'], -inp['value']) for inp in tx['entries'] if inp['value'] < 0]
        t.input_total = 0
        for i in t.inputs:
            value = [x[1] for x in input_values if x[0] == i.address]
            if len(value) != 1:
                _logger.warning("BitGoClient: Address %s input value should be found exactly 1 times in value list")
            i.value = value[0]
            t.input_total += value[0]
        return t

    def getrawtransaction(self, txid):
        res = self.compose_request('tx', txid)
        return res['hex']

    def estimatefee(self, blocks):
        res = self.compose_request('tx', 'fee', variables={'numBlocks': blocks})
        return res['feePerKb']
