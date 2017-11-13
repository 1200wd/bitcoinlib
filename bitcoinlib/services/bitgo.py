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
        # TODO: write this method if possible
        pass

    def getrawtransaction(self, txid):
        res = self.compose_request('tx', txid)
        return res['tx']['hex']

    def estimatefee(self, blocks):
        res = self.compose_request('tx', 'fee', variables={'numBlocks': blocks})
        return res['feePerKb']
