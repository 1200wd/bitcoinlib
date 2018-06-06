# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    CryptoID Chainz client
#    © 2018 June - 1200 Web Development <http://1200wd.com/>
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
import time
from datetime import datetime
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction


_logger = logging.getLogger(__name__)

PROVIDERNAME = 'cryptoid'


# Zie https://github.com/PeerAssets/pypeerassets/blob/master/pypeerassets/provider/cryptoid.py
class CryptoID(BaseClient):

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def compose_request(self, func, variables=None, method='get'):
        url_path = ''
        if variables is None:
            variables = {}
        variables.update({'q': func})
        if not self.api_key:
            raise ClientError("Request a CryptoID API key before using this provider")
        variables.update({'key': self.api_key})
        return self.request(url_path, variables, method)

    def getbalance(self, addresslist):
        balance = 0.0
        for address in addresslist:
            res = self.compose_request('getbalance', {'a': address})
            balance += float(res)
        return int(balance * self.units)

    def getutxos(self, addresslist):
        utxos = []
        for address in addresslist:
            variables = {'active': address}
            res = self.compose_request('unspent', variables=variables)
            if len(res['unspent_outputs']) > 29:
                _logger.warning("CryptoID: Large number of outputs for address %s, "
                                "UTXO list may be incomplete" % address)
            for utxo in res['unspent_outputs']:
                utxos.append({
                    'address': address,
                    'tx_hash': utxo['tx_hash'],
                    'confirmations': utxo['confirmations'],
                    'output_n': utxo['tx_output_n'] if 'tx_output_n' in utxo else utxo['tx_ouput_n'],
                    'value': int(utxo['value']),
                    'script': utxo['script'],
                })
        return utxos

    def gettransactions(self, addresslist):
        addresses = "|".join(addresslist)
        txs = []
        tx_ids = []
        variables = {'active': addresses, 'n': 100}
        res = self.compose_request('multiaddr', variables=variables)
        latest_block = res['info']['latest_block']['height']
        for tx in res['txs']:
            if tx['id'] not in tx_ids:
                tx_ids.append(tx['id'])
        for tx_id in tx_ids:
            t = self.gettransaction(tx_id)
            t.confirmations = latest_block - t.block_height
            txs.append(t)
        return txs

    def gettransaction(self, tx_id):
        variables = {'t': tx_id, 'hex': True}
        tx = self.compose_request('txinfo', variables=variables)
        raw_tx = self.getrawtransaction(tx_id)
        t = Transaction.import_raw(raw_tx, self.network)
        input_total = None
        for n, i in enumerate(t.inputs):
            if 'prev_out' in tx['inputs'][n]:
                i.value = tx['inputs'][n]['prev_out']['value']
                input_total = input_total + i.value if input_total is not None else i.value
        for n, o in enumerate(t.outputs):
            o.spent = tx['out'][n]['spent']
        # if tx['relayed_by'] == '0.0.0.0':
        if tx['block_height']:
            t.status = 'confirmed'
        else:
            t.status = 'unconfirmed'
        t.hash = tx_id
        t.date = datetime.fromtimestamp(tx['time'])
        t.block_height = tx['block_height']
        t.rawtx = raw_tx
        t.size = tx['size']
        t.network_name = self.network
        t.locktime = tx['lock_time']
        t.version = struct.pack('>L', tx['ver'])
        t.input_total = input_total
        t.fee = t.input_total - t.output_total
        return t

    def getrawtransaction(self, tx_id):
        return self.compose_request('rawtx', tx_id, {'format': 'hex'})
