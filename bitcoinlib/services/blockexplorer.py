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
            for vin in tx['vin']:
                txs.append({
                    'address': vin['addr'],
                    'tx_hash': tx['txid'],
                    'confirmations': tx['confirmations'],
                    'block_height': tx['blockheight'],
                    'date': datetime.fromtimestamp(tx['blocktime']),
                    'input_n': vin['n'],
                    'output_n': -1,
                    'double_spend': False if vin['doubleSpentTxID'] is None else vin['doubleSpentTxID'],
                    'spent': False if 'spentTxId' not in vin else True,
                    'prev_hash': vin['txid'],
                    'value': int(round(vin['value'] * self.units, 0)),
                    'script': vin['scriptSig']['hex'],
                })
            for vout in tx['vout']:
                txs.append({
                    'address': vout['scriptPubKey']['addresses'][0],
                    'tx_hash': tx['txid'],
                    'confirmations': tx['confirmations'],
                    'block_height': tx['blockheight'],
                    'date': datetime.fromtimestamp(tx['blocktime']),
                    'input_n': -1,
                    'output_n': vout['n'],
                    'double_spend': None,
                    'spent': False if vout['spentTxId'] not in vout else True,
                    'prev_hash': '',
                    'value': int(round(float(vout['value']) * self.units, 0)),
                    'script': vout['scriptPubKey']['hex'],
                })

        return txs

        # txs = {
        #      'blockhash': '000000002190d712c0c461d5ff389b929a98ed3ee1c7175a110a68b2a2cee2e9',
        #      'blockheight': 1209767,
        #      'blocktime': 1507466589,
        #      'confirmations': 20671,
        #      'fees': 0.00026192,
        #      'locktime': 0,
        #      'size': 226,
        #      'time': 1507466589,
        #      'txid': '757ca7f3a395fa8edc0d261042ff88e077de6c2a069d2e4468d6ea4b679e028b',
        #      'valueIn': 0.08970937,
        #      'valueOut': 0.08944745,
        #      'version': 1,
        #      'vin': [{'addr': 'n14ecTtK4FAmK9irj9fnnqjnVrJtYLwM8V',
        #               'doubleSpentTxID': None,
        #               'n': 0,
        #               'scriptSig': {'asm': '3045022100efaccd93b5dadf76c2d4f80ad1a305cd92ff2c4554cd02e66410d9aab8994001022031e873e218ccdcd87c17e55b2fcc61e1a9e425f775eeec9194fa51b5039932da[ALL] '
        #                                    '02ea011dbee8a1184fb59cb99dda290fce8893f8dbe151eb3091034054f00245ca',
        #                             'hex': '483045022100efaccd93b5dadf76c2d4f80ad1a305cd92ff2c4554cd02e66410d9aab8994001022031e873e218ccdcd87c17e55b2fcc61e1a9e425f775eeec9194fa51b5039932da012102ea011dbee8a1184fb59cb99dda290fce8893f8dbe151eb3091034054f00245ca'},
        #               'sequence': 4294967295,
        #               'txid': '9df91f89a3eb4259ce04af66ad4caf3c9a297feea5e0b3bc506898b6728c5003',
        #               'value': 0.08970937,
        #               'valueSat': 8970937,
        #               'vout': 1}],
        #      'vout': [{'n': 0,
        #                'scriptPubKey': {'addresses': ['mmUHBuNE25zCu4RqoCBsHEuf8xUEqZCQf3'],
        #                                 'asm': 'OP_DUP OP_HASH160 '
        #                                        '414f4758ea8b34439e46b1af9ab2a6a7ef291439 '
        #                                        'OP_EQUALVERIFY OP_CHECKSIG',
        #                                 'hex': '76a914414f4758ea8b34439e46b1af9ab2a6a7ef29143988ac',
        #                                 'type': 'pubkeyhash'},
        #                'spentHeight': None,
        #                'spentIndex': None,
        #                'spentTxId': None,
        #                'value': '0.01000000'},
        #               {'n': 1,
        #                'scriptPubKey': {'addresses': ['mhpMi5aU1tqbiivuFm2WM8HrxFewRySy84'],
        #                                 'asm': 'OP_DUP OP_HASH160 '
        #                                        '193ade3e4e24dc05f59f4d2a75747964496a3654 '
        #                                        'OP_EQUALVERIFY OP_CHECKSIG',
        #                                 'hex': '76a914193ade3e4e24dc05f59f4d2a75747964496a365488ac',
        #                                 'type': 'pubkeyhash'},
        #                'spentHeight': None,
        #                'spentIndex': None,
        #                'spentTxId': None,
        #                'value': '0.07944745'}]}


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
