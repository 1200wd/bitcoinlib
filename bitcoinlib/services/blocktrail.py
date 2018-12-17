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
from datetime import datetime
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'blocktrail'


class BlockTrail(BaseClient):

    def __init__(self, network, base_url, denominator, api_key, *args):
        if not api_key:
            raise ValueError("API key is needed to connect to BlockTrail")
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key, *args)

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
            # res = self.compose_request('address', address, 'unspent-outputs')
            current_page = 1
            while len(utxos) < 2000:
                variables = {'page': current_page, 'limit': 200}
                res = self.compose_request('address', address, 'unspent-outputs', variables)
                for utxo in res['data']:
                    utxos.append({
                        'address': address,
                        'tx_hash': utxo['hash'],
                        'confirmations': utxo['confirmations'],
                        'output_n': utxo['index'],
                        'input_n': 0,
                        'block_height': None,
                        'fee': None,
                        'size': 0,
                        'value': int(round(utxo['value'] * self.units, 0)),
                        'script': utxo['script_hex'],
                        'date': datetime.strptime(utxo['time'], "%Y-%m-%dT%H:%M:%S+%f")
                    })
                if current_page*200 > int(res['total']):
                    break
                current_page += 1

        if len(utxos) >= 2000:
            _logger.warning("BlockTrail: UTXO's list has been truncated, UTXO list is incomplete")
        return utxos

    def gettransactions(self, addresslist):
        txs = []
        for address in addresslist:
            # res = self.compose_request('address', address, 'unspent-outputs')
            current_page = 1
            while len(txs) < 2000:
                variables = {'page': current_page, 'limit': 200}
                res = self.compose_request('address', address, 'transactions', variables)
                for tx in res['data']:
                    if tx['hash'] in [t.hash for t in txs]:
                        break
                    if tx['confirmations']:
                        status = 'confirmed'
                    else:
                        status = 'unconfirmed'
                    t = Transaction(network=self.network, fee=tx['total_fee'], hash=tx['hash'],
                                    date=datetime.strptime(tx['time'], "%Y-%m-%dT%H:%M:%S+%f"),
                                    confirmations=tx['confirmations'], block_height=tx['block_height'],
                                    block_hash=tx['block_hash'], status=status,
                                    input_total=tx['total_input_value'], output_total=tx['total_output_value'])
                    for index_n, ti in enumerate(tx['inputs']):
                        t.add_input(prev_hash=ti['output_hash'], output_n=ti['output_index'],
                                    unlocking_script=ti['script_signature'],
                                    index_n=index_n, value=int(round(ti['value'] * self.units, 0)))
                    for to in tx['outputs']:
                        t.add_output(value=int(round(to['value'] * self.units, 0)), address=to['address'],
                                     lock_script=to['script_hex'],
                                     spent=bool(to['spent_hash']))
                    txs.append(t)
                if current_page*200 > int(res['total']):
                    break
                current_page += 1

        if len(txs) >= 2000:
            _logger.warning("BlockTrail: UTXO's list has been truncated, UTXO list is incomplete")
        return txs

    def gettransaction(self, tx_id):
        tx = self.compose_request('transaction', tx_id)

        rawtx = tx['raw']
        t = Transaction.import_raw(rawtx, network=self.network)
        if tx['confirmations']:
            t.status = 'confirmed'
        else:
            t.status = 'unconfirmed'

        if t.coinbase:
            t.input_total = t.output_total
        else:
            t.input_total = tx['total_input_value']
        t.output_total = tx['total_output_value']
        t.fee = tx['total_fee']
        t.hash = tx['hash']
        t.block_hash = tx['block_hash']
        t.block_height = tx['block_height']
        t.confirmations = tx['confirmations']
        t.date = datetime.strptime(tx['block_time'], "%Y-%m-%dT%H:%M:%S+%f")
        t.size = tx['size']
        for n, i in enumerate(t.inputs):
            if not tx['inputs'][n]['address']:
                raise ClientError("Address missing in input. Provider might not support segwit transactions")
            i.value = tx['inputs'][n]['value']
        for n, o in enumerate(t.outputs):
            if tx['outputs'][n]['address']:
                o.spent = True if 'spent_hash' in tx['outputs'][n] else False

        return t

    def estimatefee(self, blocks):
        res = self.compose_request('fee-per-kb', '')
        if blocks <= 10:
            return res['optimal']
        else:
            return res['low_priority']
