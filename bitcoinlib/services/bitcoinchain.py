# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Bitcoinchain client
#    © 2019 August - 1200 Web Development <http://1200wd.com/>
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

import math
import logging
from datetime import datetime
from bitcoinlib.main import MAX_TRANSACTIONS
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction
from bitcoinlib.keys import deserialize_address
from bitcoinlib.encoding import EncodingError, varstr, to_bytes

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'bitcoinchain'


class BitcoinchainClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, category, command='', data='', variables=None):
        url_path = category
        if command:
            url_path += '/' + command
        if data:
            if url_path[-1:] != '/':
                url_path += '/'
            url_path += data
        return self.request(url_path, variables=variables)

    def getbalance(self, addresslist):
        balance = 0.0
        for address in addresslist:
            res = self.compose_request('address', data=address)
            balance += float(res[0]['balance'])
        return int(balance * self.units)

    def getutxos(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):
        res = self.compose_request('address', 'utxo', data=address)
        utxos = []
        res_utxos = sorted(res[0]['utxo'], key=lambda x: x['confirmations'], reverse=True)
        for utxo in res_utxos:
            utxos.append({
                'address': address,
                'tx_hash': utxo['transaction_hash'],
                'confirmations': utxo['confirmations'],
                'output_n': utxo['output_index'],
                'input_n': -1,
                'block_height': None,
                'fee': None,
                'size': 0,
                'value': round(utxo['amount'] * self.units),
                'script': utxo['script_hex'],
                'date': None,
            })
            if utxo['transaction_hash'] == after_txid:
                utxos = []
        return utxos[:max_txs]

    # {
    #     "amount": 0.00071328,
    #     "confirmations": 48154,
    #     "output_index": 0,
    #     "script": "OP_DUP OP_HASH160 d05f72aad2b7c60d3eb3fa04c13d0d725087cb38 OP_EQUALVERIFY OP_CHECKSIG",
    #     "script_hex": "76a914d05f72aad2b7c60d3eb3fa04c13d0d725087cb3888ac",
    #     "script_reqSigs": 1,
    #     "script_type": "pubkeyhash",
    #     "spent": false,
    #     "transaction_hash": "44b46fde492423e7ab55a1dd94510bb72eee809ca4be12be99be98dd85609b4c"
    # },

    def gettransactions(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):
        res = self.compose_request('address', 'txs', data=address)
        txs = []
        for t in res[0]:
            t = self._parse_transaction(t['tx'])
            txs.append(t)
            if t.hash == after_txid:
                txs = []
        return txs[:max_txs]

    def _parse_transaction(self, tx):
        witness_type = 'legacy'
        coinbase = False
        if tx['inputs'][0]['output_ref']['tx'] == '00' * 32:
            coinbase = True
        status = 'unconfirmed'
        if tx['block_time']:
            status = 'confirmed'
        t = Transaction(locktime=tx['lock_time'], version=tx['version'], network=self.network,
                        fee=round(tx['fee'] * self.units), hash=tx['self_hash'], date=datetime.fromtimestamp(tx['block_time']),
                        block_hash=tx['blocks'][0],
                        status=status, coinbase=coinbase, witness_type=witness_type)
        for ti in tx['inputs']:
            witness_type = 'legacy'
            script = ti['in_script']['hex']
            address = ti['sender']
            value = round(ti['value'] * self.units)
            t.add_input(prev_hash=ti['output_ref']['tx'], output_n=ti['output_ref']['number'],
                        unlocking_script=script, address=address, value=value,
                        witness_type=witness_type)
        output_n = 0
        for to in tx['outputs']:
            value = round(to['value'] * self.units)
            t.add_output(value=value, address=to['receiver'], lock_script=to['out_script']['hex'],
                         output_n=output_n, spent=to['spent'])
            output_n += 1
        t.update_totals()
        if t.coinbase:
            t.input_total = t.output_total
        return t

    def gettransaction(self, txid):
        res = self.compose_request('tx', data=txid)
        return self._parse_transaction(res[0])

    def block_count(self):
        res = self.compose_request('status')
        return res['height']

    # def mempool(self, txid):
