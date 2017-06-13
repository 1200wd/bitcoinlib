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

from bitcoinlib.services.baseclient import BaseClient

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
        variables.update({'limit': 100})
        variables.update({'page': 1})
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
            res = self.compose_request('address', address, 'unspent-outputs')
            current_page = 1
            while current_page <= int(res['total']):
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
                current_page += 1
                if current_page < int(res['total']):
                    res = self.compose_request('address', address, 'unspent-outputs', page=current_page)
        return utxos

    def estimatefee(self, blocks):
        res = self.compose_request('fee-per-kb', '')
        if blocks <= 10:
            return res['optimal']
        else:
            return res['low_priority']
