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
from bitcoinlib.services.baseclient import BaseClient

PROVIDERNAME = 'blockexplorer'


class BlockExplorerClient(BaseClient):

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def compose_request(self, category, data, cmd='', variables=None, method='get'):
        url_path = category + '/' + data + '/' + cmd
        return self.request(url_path, variables, method=method)

    def getutxos(self, addresslist):
        addresses = ','.join(addresslist)
        res = self.compose_request('addrs', addresses, 'utxo')
        txs = []
        for tx in res:
            txs.append({
                'address': tx['address'],
                'tx_hash': tx['txid'],
                'confirmations': tx['confirmations'],
                'output_n': tx['vout'],
                'index': 0,
                'value': int(round(tx['amount'] * self.units, 0)),
                'script': tx['scriptPubKey'],
                'date': 0
            })
        return txs

    def gettransactions(self, addresslist):
        addresses = ','.join(addresslist)
        res = self.compose_request('addrs', addresses, 'txs')
        txs = []
        for tx in res['items']:
            inputs = []
            outputs = []
            for ti in tx['vin']:
                inputs.append({
                    'address': ti['addr'],
                    'input_n': ti['n'],
                    'double_spend': False if ti['doubleSpentTxID'] is None else ti['doubleSpentTxID'],
                    'prev_hash': ti['txid'],
                    'value': int(round(ti['value'] * self.units, 0)),
                    'script': ti['scriptSig']['hex'],
                })
            for to in tx['vout']:
                outputs.append({
                    'address': to['scriptPubKey']['addresses'][0],
                    'output_n': to['n'],
                    'spent': True if to['spentTxId'] else False,
                    'value': int(round(float(to['value']) * self.units, 0)),
                    'script': to['scriptPubKey']['hex'],
                })
            txs.append({
                'hash': tx['txid'],
                'date': datetime.fromtimestamp(tx['blocktime']),
                'confirmations': tx['confirmations'],
                'block_height': tx['blockheight'],
                'fee': int(round(float(tx['fees']) * self.units, 0)),
                'size': tx['size'],
                'inputs': inputs,
                'outputs': outputs
            })

        return txs

    def getbalance(self, addresslist):
        utxos = self.getutxos(addresslist)
        balance = 0
        for utxo in utxos:
            balance += utxo['value']
        return balance

    def getrawtransaction(self, txid):
        res = self.compose_request('rawtx', txid)
        return res['rawtx']

    def sendrawtransaction(self, rawtx):
        return self.compose_request('tx', 'send', variables={'rawtx': rawtx}, method='post')

    # TODO: Implement this method, if possible
    # def decoderawtransaction(self, rawtx):
    #     return self.compose_request('txs', 'decode', variables={'tx': rawtx}, method='post')

    def estimatefee(self, blocks):
        # Testnet hack: Blockexplorer gives bogus results for testnet for blocks > 1
        # if self.network == 'testnet':
        #     blocks = 1

        res = self.compose_request('utils', 'estimatefee', variables={'nbBlocks': blocks})
        fee = int(res[str(blocks)] * self.units)
        if fee < 1:
            raise ValueError("Fee cannot be estimated, blockexplorer returns value < 1")
        return fee
