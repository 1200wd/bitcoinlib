# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    blockchain_info client
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

import requests
import json

BLOCKEXPLORER_API_BASE_URL = "https://testnet.blockexplorer.com/api/"


class BlockExplorerClient:

    def __init__(self, api_key=None):
        self.provider = 'blockexplorer'
        if api_key:
            self.auth = (api_key, '')
        else:
            self.auth = None

    def request(self, category, data, method):
        url = BLOCKEXPLORER_API_BASE_URL + category + '/' + data + '/' + method
        resp = requests.get(url)
        data = json.loads(resp.text)
        return data

    def getbalance(self, address):
        return self.request('addr', address, 'balance')

    def utxos(self, addresslist):
        addresses = ','.join(addresslist)
        return self.request('addrs', addresses, 'utxo')

    def getbalances(self, addresslist):
        utxos = self.utxos(addresslist)
        balance = 0
        for utxo in utxos:
            balance += utxo['amount']
        return balance
