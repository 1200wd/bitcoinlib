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

import logging
from bitcoinlib.services.baseclient import BaseClient

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'chainso'
NETWORKCODES = {
    'bitcoin': 'BTC',
    'testnet': 'BTCTEST',
    'dash': 'DASH',
    'dash_testnet': 'DASHTEST',
    'litecoin': 'LTC',
    'litecoin_testnet': 'LTCTEST'
}


class ChainSo(BaseClient):

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def compose_request(self, function, data='', parameter='', variables=None, method='get'):
        url_path = function
        url_path += '/' + NETWORKCODES[self.network]
        if data:
            url_path += '/' + data
        if parameter:
            url_path += '/' + parameter
        if variables is None:
            variables = {}
        if self.api_key:
            variables.update({'api_key': self.api_key})
        return self.request(url_path, variables, method)

    def getrawtransaction(self, txid):
        res = self.compose_request('get_tx', txid)
        return res['data']['tx_hex']

    def sendrawtransaction(self, rawtx):
        return self.compose_request('send_tx', variables={'tx_hex': rawtx}, method='post')

    def getbalance(self, addresslist):
        balance = 0.0
        for address in addresslist:
            res = self.compose_request('get_address_balance', address)
            balance += float(res['data']['confirmed_balance']) + float(res['data']['unconfirmed_balance'])
        return int(balance * self.units)

    def getutxos(self, addresslist):
        utxos = []
        lastutxo = ''
        for address in addresslist:
            while len(utxos) < 1000:
                res = self.compose_request('get_tx_unspent', address, lastutxo)
                for utxo in res['data']['txs']:
                    utxos.append({
                        'address': address,
                        'tx_hash': utxo['txid'],
                        'confirmations': utxo['confirmations'],
                        'output_n': utxo['output_no'],
                        'index': 0,
                        'value': int(round(float(utxo['value']) * self.units, 0)),
                        'script': utxo['script_hex'],
                    })
                    lastutxo = utxo['txid']
                if len(res['data']['txs']) < 100:
                    break
        if len(utxos) >= 1000:
            _logger.warning("ChainSo: UTXO's list has been truncated, UTXO list is incomplete")
        return utxos
