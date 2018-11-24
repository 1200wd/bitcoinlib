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
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'bitgo'


class BitGoClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, category, data, cmd='', variables=None, method='get'):
        if data:
            data = '/' + data
        url_path = category + data
        if cmd != '':
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
                            'input_n': 0,
                            'block_height': unspent['blockHeight'],
                            'fee': None,
                            'size': 0,
                            'value': int(round(unspent['value'] * self.units, 0)),
                            'script': unspent['script'],
                            'date': datetime.strptime(unspent['date'], "%Y-%m-%dT%H:%M:%S.%fZ")

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
        tx_ids = []
        for address in addresslist:
            skip = 0
            total = 1
            while total > skip:
                variables = {'limit': 100, 'skip': skip}
                res = self.compose_request('address', address, 'tx', variables)
                for tx in res['transactions']:
                    if tx['id'] not in tx_ids:
                        tx_ids.append(tx['id'])
                total = res['total']
                skip = res['start'] + res['count']
                if skip > 2000:
                    _logger.warning("BitGoClient: Transactions list has been truncated, list is incomplete")
                    break
        for tx_id in tx_ids:
            txs.append(self.gettransaction(tx_id))
        return txs

    def gettransaction(self, tx_id):
        tx = self.compose_request('tx', tx_id)
        t = Transaction.import_raw(tx['hex'], network=self.network)
        if tx['confirmations']:
            t.status = 'confirmed'
        t.hash = tx_id
        t.date = datetime.strptime(tx['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        t.confirmations = tx['confirmations']
        if 'height' in tx:
            t.block_height = tx['height']
            t.block_hash = tx['blockhash']
        t.fee = tx['fee']
        t.rawtx = tx['hex']
        t.size = len(tx['hex']) // 2
        t.network = self.network
        if t.coinbase:
            input_values = []
            t.input_total = t.output_total
        else:
            input_values = [(inp['account'], -inp['value']) for inp in tx['entries'] if inp['value'] < 0]
            t.input_total = sum([x[1] for x in input_values])
        for i in t.inputs:
            if not i.address:
                raise ClientError("Address missing in input. Provider might not support segwit transactions")
            if len(t.inputs) != len(input_values):
                i.value = None
                continue
            value = [x[1] for x in input_values if x[0] == i.address]
            if len(value) != 1:
                _logger.warning("BitGoClient: Address %s input value should be found exactly 1 times in value list" %
                                i.address)
                i.value = None
            else:
                i.value = value[0]
        for o in t.outputs:
            o.spent = None
        if t.input_total != t.output_total + t.fee:
            t.input_total = t.output_total + t.fee
        return t

    def getrawtransaction(self, txid):
        tx = self.compose_request('tx', txid)
        t = Transaction.import_raw(tx['hex'], network=self.network)
        for i in t.inputs:
            if not i.address:
                raise ClientError("Address missing in input. Provider might not support segwit transactions")
        return tx['hex']

    def estimatefee(self, blocks):
        res = self.compose_request('tx', 'fee', variables={'numBlocks': blocks})
        return res['feePerKb']

    # def block_count(self):
    #     return self.proxy.getblockcount()
