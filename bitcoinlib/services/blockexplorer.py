# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
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

from datetime import datetime
import struct
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction

PROVIDERNAME = 'blockexplorer'


class BlockExplorerClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, category, data, cmd='', variables=None, method='get'):
        url_path = category
        if data:
            url_path += '/' + data + '/' + cmd
        return self.request(url_path, variables, method=method)

    def getutxos(self, addresslist):
        addresses = ','.join(addresslist)
        res = self.compose_request('addrs', addresses, 'utxo')
        txs = []
        for tx in res:
            txs.append({
                'address': tx['address'],
                'tx_hash': tx['txid'],
                'confirmations': 3 if tx['confirmations'] < 0 else tx['confirmations'],
                'output_n': tx['vout'],
                'input_n': 0,
                'block_height': None,
                'fee': None,
                'size': 0,
                'value': int(round(tx['amount'] * self.units, 0)),
                'script': tx['scriptPubKey'],
                'date': None
            })
        return txs

    def _convert_to_transaction(self, tx):
        if tx['confirmations'] > 0:
            status = 'confirmed'
        else:
            status = 'unconfirmed'
        fees = None if 'fees' not in tx else int(round(float(tx['fees']) * self.units, 0))
        value_in = 0 if 'valueIn' not in tx else tx['valueIn']
        isCoinbase = False
        if 'isCoinBase' in tx and tx['isCoinBase']:
            value_in = tx['valueOut']
            isCoinbase = True
        if tx['confirmations'] < 0:
            tx['confirmations'] = 0
        blocktime = datetime.fromtimestamp(tx['blocktime']) if 'blocktime' in tx else 0
        blockhash = tx['blockhash'] if 'blockhash' in tx else ''
        t = Transaction(locktime=tx['locktime'], version=tx['version'], network=self.network,
                        fee=fees, size=tx['size'], hash=tx['txid'],
                        date=blocktime, confirmations=tx['confirmations'],
                        block_height=tx['blockheight'], block_hash=blockhash, status=status,
                        input_total=int(round(float(value_in) * self.units, 0)), coinbase=isCoinbase,
                        output_total=int(round(float(tx['valueOut']) * self.units, 0)))
        for ti in tx['vin']:
            # sequence = struct.pack('<L', ti['sequence'])
            if isCoinbase:
                t.add_input(prev_hash=32 * b'\0', output_n=4*b'\xff', unlocking_script=ti['coinbase'], index_n=ti['n'],
                            script_type='coinbase', sequence=ti['sequence'])
            else:
                value = int(round(float(ti['value']) * self.units, 0))
                if not ti['scriptSig']['hex']:
                    raise ClientError("Missing unlocking script in BlockExplorer Input. Possible reason: Segwit is not "
                                      "supported")
                t.add_input(prev_hash=ti['txid'], output_n=ti['vout'], unlocking_script=ti['scriptSig']['hex'],
                            index_n=ti['n'], value=value, sequence=ti['sequence'],
                            double_spend=False if ti['doubleSpentTxID'] is None else ti['doubleSpentTxID'])
        for to in tx['vout']:
            value = int(round(float(to['value']) * self.units, 0))
            address = ''
            try:
                address = to['scriptPubKey']['addresses'][0]
            except (ValueError, KeyError):
                pass
            t.add_output(value=value, address=address, lock_script=to['scriptPubKey']['hex'],
                         spent=True if to['spentTxId'] else False, output_n=to['n'])
        return t

    def gettransactions(self, addresslist):
        addresses = ','.join(addresslist)
        res = self.compose_request('addrs', addresses, 'txs')
        txs = []
        for tx in res['items']:
            txs.append(self._convert_to_transaction(tx))
        return txs

    def gettransaction(self, tx_id):
        tx = self.compose_request('tx', tx_id)
        return self._convert_to_transaction(tx)

    def getbalance(self, addresslist):
        utxos = self.getutxos(addresslist)
        balance = 0
        for utxo in utxos:
            balance += utxo['value']
        return balance

    def getrawtransaction(self, tx_id):
        tx = self.compose_request('rawtx', tx_id)
        t = Transaction.import_raw(tx['rawtx'], network=self.network)
        for i in t.inputs:
            if not i.address:
                raise ClientError("Address missing in input. Provider might not support segwit transactions")
        return tx['rawtx']

    def sendrawtransaction(self, rawtx):
        res = self.compose_request('tx', 'send', variables={'rawtx': rawtx}, method='post')
        return {
            'txid': res['txid'],
            'response_dict': res
        }

    def block_count(self):
        res = self.compose_request('status', '', variables={'q': 'getinfo'})
        return res['info']['blocks']
