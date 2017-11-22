# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    blockchain_info client
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
from bitcoinlib.services.baseclient import BaseClient

PROVIDERNAME = 'blockchaininfo'

_logger = logging.getLogger(__name__)


class BlockchainInfoClient(BaseClient):

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def compose_request(self, cmd, parameter='', variables=None, method='get'):
        url_path = cmd
        if parameter:
            url_path += '/' + parameter
        return self.request(url_path, variables, method=method)

    def getbalance(self, addresslist):
        addresses = {'active': '|'.join(addresslist)}
        res = self.compose_request('balance', variables=addresses)
        balance = 0
        for address in res:
            balance += res[address]['final_balance']
        return balance

    def getutxos(self, addresslist):
        utxos = []
        for address in addresslist:
            variables = {'active': address, 'limit': 1000}
            res = self.compose_request('unspent', variables=variables)
            if len(res['unspent_outputs']) > 299:
                _logger.warning("BlockchainInfoClient: Large number of outputs for address %s, "
                                "UTXO list may be incomplete" % address)
            for utxo in res['unspent_outputs']:
                utxos.append({
                    'address': address,
                    'tx_hash': utxo['tx_hash_big_endian'],
                    'confirmations': utxo['confirmations'],
                    'output_n': utxo['tx_output_n'],
                    'index':  utxo['tx_index'],
                    'value': int(round(utxo['value'] * self.units, 0)),
                    'script': utxo['script'],
                })
        return utxos

    def gettransactions(self, addresslist):
        addresses = "|".join(addresslist)
        txs = []
        variables = {'active': addresses, 'limit': 100}
        # res = self.compose_request('multiaddr', variables=variables)
        res = {'info': {'symbol_local': {'symbol': '$', 'symbolAppearsAfter': False, 'name': 'U.S. dollar', 'code': 'USD', 'local': True, 'conversion': 12058.88595188}, 'latest_block': {'hash': '0000000000000000006832ac69aa0eb190dc20a08b982310d236b02827d90dda', 'block_index': 1641090, 'time': 1511348622, 'height': 495576}, 'symbol_btc': {'symbol': 'BTC', 'symbolAppearsAfter': True, 'name': 'Bitcoin', 'code': 'BTC', 'local': False, 'conversion': 100000000.0}, 'nconnected': 0, 'conversion': 100000000.0}, 'wallet': {'total_sent': 0, 'n_tx_filtered': 2, 'total_received': 9000, 'n_tx': 2, 'final_balance': 9000}, 'txs': [{'vout_sz': 3, 'ver': 1, 'tx_index': 153235888, 'double_spend': False, 'vin_sz': 1, 'block_height': 415336, 'weight': 1040, 'balance': 9000, 'time': 1465378572, 'inputs': [{'prev_out': {'type': 0, 'addr_tag': 'Please help student', 'value': 9738, 'addr': '13erKEzxsbYM68UpaqwfeGzSoVrcS4T4GM', 'n': 0, 'tx_index': 141579440, 'spent': True, 'script': '76a9141d18cecdfbfe6a8fd9b59fe52f48a7e8ee84387c88ac'}, 'witness': '', 'script': '483045022100e40f8f3513f8adbd69cec6f5b1b8fa2110724c5ad472bc8a6a72b479f71891c7022050cb537d115337f182cfe5728fed531297a93bbe8eb33a6bd22b3e161754e30a012103c35334ae22227e869a681cf89d603b57d14346bf194b01ab097499d9ed6f93b6', 'sequence': 4294967294}], 'size': 260, 'lock_time': 410835, 'result': 3500, 'hash': 'd36b4294a5c84650489e9b317b9482c3a0e4184c0982fb88af6d7f78bf0fd175', 'relayed_by': '0.0.0.0', 'out': [{'type': 0, 'value': 3500, 'addr': '15gHNr4TCKmhHDEG31L2XFNvpnEcnPSQvd', 'n': 2, 'tx_index': 153235888, 'spent': False, 'script': '76a914334e656c736f6e2d4d616e64656c612e6a70673f88ac'}], 'fee': 2600}, {'vout_sz': 32, 'ver': 1, 'tx_index': 44222775, 'double_spend': False, 'vin_sz': 1, 'block_height': 273536, 'weight': 4984, 'balance': 5500, 'time': 1386401628, 'inputs': [{'prev_out': {'type': 0, 'value': 15724500, 'addr': '16LseQUKmhA1XUq39QmxNg9c1bPQq6Jxvh', 'n': 3, 'tx_index': 44217743, 'spent': True, 'script': '76a9143a9acef57a9b6c9308360ba4d801796a4d1bfe1488ac'}, 'witness': '', 'script': '4830450220454506f817e7a96f56bc5b1e27365e7e00b838652fa95172fe08259117ff998c022100c227681ea312e5d6dea791c54f4065f6e964127838da2262e936eb746a09229f0121030c8d5aaf2213561bb70d5acf01b8c54794568642cb5068424ab11c914619818a', 'sequence': 4294967295}], 'size': 1246, 'lock_time': 0, 'result': 5500, 'hash': '8881a937a437ff6ce83be3a89d77ea88ee12315f37f7ef0dd3742c30eef92dba', 'relayed_by': '85.17.239.32', 'out': [{'type': 0, 'value': 5500, 'addr': '15gHNr4TCKmhHDEG31L2XFNvpnEcnPSQvd', 'n': 21, 'tx_index': 44222775, 'spent': False, 'script': '76a914334e656c736f6e2d4d616e64656c612e6a70673f88ac'}], 'fee': 20000}], 'recommend_include_fee': True, 'addresses': [{'total_sent': 0, 'total_received': 9000, 'account_index': 0, 'n_tx': 2, 'final_balance': 9000, 'change_index': 0, 'address': '15gHNr4TCKmhHDEG31L2XFNvpnEcnPSQvd'}]}
        for tx in res['txs']:
            inputs = []
            outputs = []
            for ti in tx['inputs']:
                inputs.append({
                    'prev_hash': '',
                    'input_n': ti['prev_out']['n'],
                    'address': ti['prev_out']['addr'],
                    'value': int(round(ti['prev_out']['value'] * self.units, 0)),
                    'double_spend': tx['double_spend'],
                    'script': ti['prev_out']['script'],
                })
            for to in tx['out']:
                outputs.append({
                    'address': to['addr'],
                    'output_n': to['n'],
                    'value': int(round(float(to['value']) * self.units, 0)),
                    'spent': to['spent'],
                    'script': to['script'],
                })
            status = 'unconfirmed'
            if tx['confirmations']:
                status = 'confirmed'
            txs.append({
                'hash': tx['hash'],
                'date': datetime.fromtimestamp(tx['time']),
                'confirmations': tx['confirmations'],
                'block_height': tx['blockheight'],
                'fee': int(round(float(tx['fees']) * self.units, 0)),
                'size': tx['size'],
                'inputs': inputs,
                'outputs': outputs,
                'status': status
            })

        return res

    def getrawtransaction(self, txid):
        res = self.compose_request('rawtx', txid, {'format': 'hex'})
        return res

