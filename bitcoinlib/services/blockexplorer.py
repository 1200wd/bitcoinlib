# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Block Explorer Client
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
from bitcoinlib.config.services import serviceproviders


class BlockExplorerClient:

    def __init__(self, network):
        try:
            self.url = serviceproviders[network]['blockexplorer'][1]
        except:
            raise Warning("This Network is not supported by BlockExplorerClient")

    def request(self, category, data, method):
        url = self.url + category + '/' + data + '/' + method
        resp = requests.get(url)
        data = json.loads(resp.text)
        return data

    def utxos(self, addresslist):
        addresses = ','.join(addresslist)
        res = self.request('addrs', addresses, 'utxo')
        utxos = []
        for utxo in res:
            utxos.append({
                'address': utxo['address'],
                'tx_hash': utxo['txid'],
                'confirmations': utxo['confirmations'],
                'output_n': utxo['vout'],
                'index': 0,
                'value': utxo['amount'],
                'script': utxo['scriptPubKey'],
            })
        return utxos

    def getbalance(self, addresslist):
        utxos = self.utxos(addresslist)
        balance = 0
        for utxo in utxos:
            balance += utxo['value']
        return balance
