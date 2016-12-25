# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    BlockCypher client
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
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from bitcoinlib.config.services import serviceproviders


class BlockCypherError(Exception):
    pass


class BlockCypher:

    def __init__(self, network):
        try:
            self.url = serviceproviders[network]['blockcypher'][1]
        except:
            raise BlockCypherError("This Network is not supported by BlockCypher")

    def request(self, method, data, parameter='', variables=None):
        url = self.url + method + '/' + data
        if parameter:
            url += '/' + parameter
        if variables:
            url += '?' + urlencode(variables)
        resp = requests.get(url)
        data = json.loads(resp.text)
        from pprint import pprint
        pprint(data)
        if resp.status_code != 200:
            if resp.status_code == 429:
                message = "Maximum number of request reached for BlockCypher"
            else:
                message = "Error connecting to BlockCypher, response code %d. Message %s" % \
                          (resp.status_code, resp.text)
            raise BlockCypherError(message)
        return data

    def getbalance(self, addresslist):
        addresses = ';'.join(addresslist)
        res = self.request('addrs', addresses, 'balance')
        if isinstance(res, dict):
            return float(res['final_balance'])
        else:
            balance = 0
            for rec in res:
                balance += float(rec['final_balance'])
            return balance

    def utxos(self, addresslist):
        addresses = ';'.join(addresslist)
        res = self.request('addrs', addresses, variables=[('unspentOnly', 1)])
        utxos = []
        for a in res:
            address = a['address']
            if a['n_tx'] == 0:
                continue
            for utxo in a['unspent']:
                utxos.append({
                    'address': address,
                    'tx_hash': utxo['tx'],
                    'confirmations': utxo['confirmations'],
                    'output_n': utxo['n'],
                    'index': 0,
                    'value': utxo['amount'],
                    'script': utxo['script'],
                })
        return utxos
