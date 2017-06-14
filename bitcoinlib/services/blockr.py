# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Blockr.io Client
#    © 2016 November - 1200 Web Development <http://1200wd.com/>
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

from bitcoinlib.services.baseclient import BaseClient

PROVIDERNAME = 'blockr'


class BlockrClient(BaseClient):

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def compose_request(self, category, function, data='', variables=None, method='get'):
        url_path = category + '/' + function + '/' + data
        r = self.request(url_path, variables, method)
        return r['data']

    def getbalance(self, addresslist):
        addresses = ','.join(addresslist)
        res = self.compose_request('address', 'balance', addresses)
        balance = 0
        if not isinstance(res, list):
            res = [res]
        for rec in res:
            balance += float(rec['balance'])
        return int(round(balance * self.units, 0))

    def getutxos(self, addresslist):
        addresses = ','.join(addresslist)
        res = self.compose_request('address', 'unspent', addresses)
        utxos = []
        if not isinstance(res, list):
            res = [res]
        for a in res:
            address = a['address']
            for utxo in a['unspent']:
                utxos.append({
                    'address': address,
                    'tx_hash': utxo['tx'],
                    'confirmations': utxo['confirmations'],
                    'output_n': utxo['n'],
                    'index': 0,
                    'value': int(round(float(utxo['amount']) * self.units, 0)),
                    'script': utxo['script'],
                })
        return utxos

    def getrawtransaction(self, txid):
        res = self.compose_request('tx', 'raw', txid)
        return res['tx']['hex']

    def decoderawtransaction(self, rawtx):
        return self.compose_request('tx', 'decode', variables={'hex': rawtx}, method='post')

    def sendrawtransaction(self, rawtx):
        return self.compose_request('tx', 'push', variables={'hex': rawtx}, method='post')
