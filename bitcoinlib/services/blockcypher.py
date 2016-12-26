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

from bitcoinlib.services.baseclient import BaseClient, ClientError

PROVIDERNAME = 'blockcypher'


class BlockCypher(BaseClient):

    def __init__(self, network):
        super(self.__class__, self).__init__(network, PROVIDERNAME)

    def request(self, method, data, parameter='', variables=None):
        url = self.url + method + '/' + data
        if parameter:
            url += '/' + parameter
        try:
            resp = super(self.__class__, self).request(url, variables)
            return resp
        except ClientError:
            if self.resp.status_code != 200:
                if self.resp.status_code == 429:
                    message = "Maximum number of request reached for BlockCypher"
                else:
                    message = "Error connecting to BlockCypher, response code %d. Message %s" % \
                              (self.resp.status_code, self.resp.text)
                raise ClientError(message)
            return self.resp

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
