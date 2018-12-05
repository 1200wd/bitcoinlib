# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Litecore.io Client
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

from datetime import datetime
import struct
from bitcoinlib.services.baseclient import BaseClient
from bitcoinlib.transactions import Transaction

PROVIDERNAME = 'litecoreio'


class LitecoreIOClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, category, data, cmd='', variables=None, method='get'):
        url_path = category
        if data:
            url_path += '/' + data + '/' + cmd
        return self.request(url_path, variables, method=method)

    def getutxos(self, addresslist):
        addresslist = self._addresslist_convert(addresslist)
        addresses = ';'.join([a.address for a in addresslist])
        res = self.compose_request('addrs', addresses, 'utxo')
        txs = []
        for tx in res:
            address = [x.address_orig for x in addresslist if x.address == tx['address']][0]
            txs.append({
                'address': address,
                'tx_hash': tx['txid'],
                'confirmations': tx['confirmations'],
                'output_n': tx['vout'],
                'input_n': 0,
                'block_height': tx['height'],
                'fee': None,
                'size': 0,
                'value': tx['satoshis'],
                'script': tx['scriptPubKey'],
                'date': None
            })
        return txs

    def _convert_to_transaction(self, tx):
        if tx['confirmations']:
            status = 'confirmed'
        else:
            status = 'unconfirmed'
        fees = None if 'fees' not in tx else int(round(float(tx['fees']) * self.units, 0))
        value_in = 0 if 'valueIn' not in tx else tx['valueIn']
        isCoinbase = False
        if 'isCoinBase' in tx and tx['isCoinBase']:
            value_in = tx['valueOut']
            isCoinbase = True
        t = Transaction(locktime=tx['locktime'], version=tx['version'], network=self.network,
                        fee=fees, size=tx['size'], hash=tx['txid'],
                        date=datetime.fromtimestamp(tx['blocktime']), confirmations=tx['confirmations'],
                        block_height=tx['blockheight'], block_hash=tx['blockhash'], status=status,
                        input_total=int(round(float(value_in) * self.units, 0)), coinbase=isCoinbase,
                        output_total=int(round(float(tx['valueOut']) * self.units, 0)))
        for ti in tx['vin']:
            if isCoinbase:
                t.add_input(prev_hash=32 * b'\0', output_n=4*b'\xff', unlocking_script=ti['coinbase'], index_n=ti['n'],
                            script_type='coinbase', sequence=ti['sequence'])
            else:
                value = int(round(float(ti['value']) * self.units, 0))
                t.add_input(prev_hash=ti['txid'], output_n=ti['vout'], unlocking_script=ti['scriptSig']['hex'],
                            index_n=ti['n'], value=value, sequence=ti['sequence'],
                            double_spend=False if ti['doubleSpentTxID'] is None else ti['doubleSpentTxID'])
        for to in tx['vout']:
            value = int(round(float(to['value']) * self.units, 0))
            t.add_output(value=value, lock_script=to['scriptPubKey']['hex'],
                         spent=True if to['spentTxId'] else False, output_n=to['n'])
        return t

    def gettransactions(self, addresslist):
        addresslist = self._addresslist_convert(addresslist)
        addresses = ';'.join([a.address for a in addresslist])
        res = self.compose_request('addrs', addresses, 'txs')
        txs = []
        for tx in res['items']:
            txs.append(self._convert_to_transaction(tx))
        return txs

    def gettransaction(self, tx_id):
        tx = self.compose_request('tx', tx_id)
        return self._convert_to_transaction(tx)

    def getbalance(self, addresslist):
        balance = 0
        addresslist = self._addresslist_convert(addresslist)
        for a in addresslist:
            res = self.compose_request('addr', a.address, 'balance')
            balance += res
        return balance

    def getrawtransaction(self, tx_id):
        res = self.compose_request('rawtx', tx_id)
        return res['rawtx']

    def sendrawtransaction(self, rawtx):
        res = self.compose_request('tx', 'send', variables={'rawtx': rawtx}, method='post')
        return {
            'txid': res['txid'],
            'response_dict': res
        }

    def block_count(self):
        res = self.compose_request('status', '', variables={'q': 'getinfo'})
        return res['info']['blocks']
