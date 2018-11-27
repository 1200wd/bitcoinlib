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
import struct
from datetime import datetime
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction


_logger = logging.getLogger(__name__)

PROVIDERNAME = 'cryptoid'


class CryptoID(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, func=None, path_type='api', variables=None, method='get'):
        # API path: http://chainz.cryptoid.info/ltc/api.dws
        # Explorer path for raw tx: https://chainz.cryptoid.info/explorer/tx.raw.dws
        if variables is None:
            variables = {}
        if path_type == 'api':
            url_path = '%s/api.dws' % self.provider_coin_id
            variables.update({'q': func})
        else:
            url_path = 'explorer/tx.raw.dws'
            variables.update({'coin': self.provider_coin_id})
        if not self.api_key:
            raise ClientError("Request a CryptoID API key before using this provider")
        variables.update({'key': self.api_key})
        return self.request(url_path, variables, method)

    def getbalance(self, addresslist):
        balance = 0.0
        addresslist = self._addresslist_convert(addresslist)
        for a in addresslist:
            res = self.compose_request('getbalance', variables={'a': a.address})
            balance += float(res)
        return int(balance * self.units)

    def getutxos(self, addresslist):
        if not self.api_key:
            raise ClientError("Method getutxos() is not available for CryptoID without API key")
        utxos = []
        addresslist = self._addresslist_convert(addresslist)
        for a in addresslist:
            variables = {'active': a.address}
            res = self.compose_request('unspent', variables=variables)
            if len(res['unspent_outputs']) > 29:
                _logger.warning("CryptoID: Large number of outputs for address %s, "
                                "UTXO list may be incomplete" % a.address)
            for utxo in res['unspent_outputs']:
                utxos.append({
                    'address': a.address_orig,
                    'tx_hash': utxo['tx_hash'],
                    'confirmations': utxo['confirmations'],
                    'output_n': utxo['tx_output_n'] if 'tx_output_n' in utxo else utxo['tx_ouput_n'],
                    'input_n': 0,
                    'block_height': None,
                    'fee': None,
                    'size': 0,
                    'value': int(utxo['value']),
                    'script': utxo['script'],
                    'date': None
                })
        return utxos

    def gettransactions(self, addresslist):
        addresslist = self._addresslist_convert(addresslist)
        addresses = "|".join([a.address for a in addresslist])
        txs = []
        tx_ids = []
        variables = {'active': addresses, 'n': 100}
        res = self.compose_request('multiaddr', variables=variables)
        for tx in res['txs']:
            if tx['hash'] not in tx_ids:
                tx_ids.append(tx['hash'])
        for tx_id in tx_ids:
            t = self.gettransaction(tx_id)
            txs.append(t)
        return txs

    def gettransaction(self, tx_id):
        variables = {'id': tx_id, 'hex': None}
        tx = self.compose_request(path_type='explorer', variables=variables)
        t = Transaction.import_raw(tx['hex'], self.network)
        variables = {'t': tx_id}
        tx_api = self.compose_request('txinfo', path_type='api', variables=variables)
        for n, i in enumerate(t.inputs):
            i.value = int(round(tx_api['inputs'][n]['amount'] * self.units, 0))
        for n, o in enumerate(t.outputs):
            # TODO: Check if output is spent (still neccessary?)
            o.spent = None
        if tx['confirmations']:
            t.status = 'confirmed'
        else:
            t.status = 'unconfirmed'
        t.hash = tx_id
        t.date = datetime.fromtimestamp(tx['time'])
        t.block_height = tx_api['block']
        t.block_hash = tx['blockhash']
        t.confirmations = tx['confirmations']
        t.rawtx = tx['hex']
        t.size = tx['size']
        t.network = self.network
        t.locktime = tx['locktime']
        t.version = struct.pack('>L', tx['version'])
        t.input_total = int(round(tx_api['total_input'] * self.units, 0))
        t.output_total = int(round(tx_api['total_output'] * self.units, 0))
        t.fee = t.input_total - t.output_total
        return t

    def getrawtransaction(self, tx_id):
        variables = {'id': tx_id, 'hex': None}
        tx = self.compose_request(path_type='explorer', variables=variables)
        return tx['hex']

    def block_count(self):
        r = self.compose_request('getblockcount', path_type='api')
        return r
