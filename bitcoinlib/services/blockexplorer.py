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
            txs.append({
                'address': tx['address'],
                'tx_hash': tx['txid'],
                'confirmations': tx['confirmations'],
                'output_n': -1 if 'vout' not in tx else tx['vout'],
                'input_n': -1 if 'vin' not in tx else tx['vin'],
                'index': 0,
                'value': int(round(tx['amount'] * self.units, 0)),
                'script': tx['scriptPubKey'],
                'date': 0
            })
        return txs        # TODO: Finish this
        # res = self.compose_request('addrs', addresses, 'txs')
        # /api/addrs/2NF2baYuJAkCKo5onjUKEPdARQkZ6SYyKd5,2NAre8sX2povnjy4aeiHKeEh97Qhn97tB1f/txs?from=0&to=20
        # from pprint import pprint
        # pprint(res)
        # {'from': 0,
        #  'items': [{'blockhash': '00000000000004c...d53cefe26e92fd5cd',
        #             'blockheight': 1153001,
        #             'blocktime': 1499977636,
        #             'confirmations': 28157,
        #             'fees': 8.15e-06,
        #             'locktime': 0,
        #             'size': 226,
        #             'time': 1499977636,
        #             'txid': '8bcac07df4a5...0d7cebf9b7d7ee',
        #             'valueIn': 4.50759446,
        #             'valueOut': 4.50758631,
        #             'version': 1,
        #             'vin': [{'addr': 'msrbEQkm1svA9r9x6Jaypb6cpSX1VepYHf',
        #                      'doubleSpentTxID': None,
        #                      'n': 0,
        #                      'scriptSig': {'asm':
        #                                        'hex':
        # 'sequence': 4294967295,
        #             'txid': '0cf6ad653cde...034abb65b1',
        # 'value': 4.50759446,
        # 'valueSat': 450759446,
        # 'vout': 0}],
        # 'vout': [{'n': 0,
        #           'scriptPubKey': {'addresses': ['mxdLD8SAG..MHp8N'],
        #                            'asm':,
        #           'hex': '76a914bbaeed8a02f6....88ac',
        #           'type': 'pubkeyhash'},
        #          'spentHeight': None,
        #                         'spentIndex': None,
        # 'spentTxId': None,
        # 'value': '0.00100000'},
        # {'n': 1,
        #  'scriptPubKey': {'addresses': ['n1JFNC8zMerPuY.53oagzK6'],
        #                   'asm': ...,
        #                   'hex': '76a914d8fb5bc...c428a88ac',
        #                   'type': 'pubkeyhash'},
        #  'spentHeight': 1153005,
        #  'spentIndex': 0,
        #  'spentTxId': 'a5308741fe17d...32e7659f09408c43008d',
        #  'value': '4.50658631'}]},

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
