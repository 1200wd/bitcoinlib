# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    BitGo Client
#    © 2017 May - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.transactions import Transaction

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'bitgo'


class BitGoClient(BaseClient):

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def compose_request(self, category, data, cmd='', variables=None, method='get'):
        if data:
            data = '/' + data
        url_path = category + data
        if cmd:
            url_path += '/' + cmd
        return self.request(url_path, variables, method=method)

    def getbalance(self, addresslist):
        balance = 0
        for address in addresslist:
            res = self.compose_request('address', address)
            balance += res['balance']
        return balance

    def getutxos(self, addresslist):
        utxos = []
        for address in addresslist:
            skip = 0
            total = 1
            while total > skip:
                variables = {'limit': 100, 'skip': skip}
                res = self.compose_request('address', address, 'unspents', variables)
                for unspent in res['unspents']:
                    utxos.append(
                        {
                            'address': unspent['address'],
                            'tx_hash': unspent['tx_hash'],
                            'confirmations': unspent['confirmations'],
                            'output_n': unspent['tx_output_n'],
                            'index': 0,
                            'value': int(round(unspent['value'] * self.units, 0)),
                            'script': unspent['script'],
                         }
                    )
                total = res['total']
                skip = res['start'] + res['count']
                if skip > 2000:
                    _logger.warning("BitGoClient: UTXO's list has been truncated, list is incomplete")
                    break
        return utxos

    def gettransactions(self, addresslist):
        txs = []
        for address in addresslist:
            skip = 0
            total = 1
            while total > skip:
                variables = {'limit': 100, 'skip': skip}
                res = self.compose_request('address', address, 'tx', variables)
                for tx in res['transactions']:
                    if tx['id'] in [t['hash'] for t in txs]:
                        break
                    status = 'unconfirmed'
                    if tx['confirmations']:
                        status = 'confirmed'
                    txs.append({
                        'hash': tx['id'],
                        'date': datetime.strptime(tx['date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                        'confirmations': tx['confirmations'],
                        'block_height': tx['height'],
                        'block_hash': tx['blockhash'],
                        'fee': tx['fee'],
                        'size': 0,
                        'inputs': [],
                        'outputs': [],
                        'input_total': 0,
                        'output_total': 0,
                        'raw': '',
                        'network': self.network,
                        'status': status
                    })
                total = res['total']
                skip = res['start'] + res['count']
                if skip > 2000:
                    _logger.warning("BitGoClient: Transactions list has been truncated, list is incomplete")
                    break
        for tx in txs:
            rawtx = self.getrawtransaction(tx['hash'])
            t = Transaction.import_raw(rawtx)
            tx['inputs'] = [i.dict() for i in t.inputs]
            tx['outputs'] = [o.dict() for o in t.outputs]
        return txs

# {'address': '38qJv2aD8vNZSoxbFSinim7zmpwSyPDSep',
#  'output_index': '00000001',
#  'prev_hash': 'd87c9d31dec2c0a12cb8e6ee38d1c3c6fb47e8ba8270d80600b72fd5a2cad09d',
#  'public_key': ['020f060a8d8af1f86c1ff75b001072594cb9c3f7fb2a4fd9df2b497cf0e3237038',
#                 '0271b18e48c6d362696d439422b0ab933a031ec16ed0e51c1a1fc558c03f50f520',
#                 '03c531065db2e61f2b86840b6371dc19f80ec7827e9ca3619cafa132c891f989e0'],
#  'redeemscript': '5221020f060a8d8af1f86c1ff75b001072594cb9c3f7fb2a4fd9df2b497cf0e3237038210271b18e48c6d362696d439422b0ab933a031ec16ed0e51c1a1fc558c03f50f5202103c531065db2e61f2b86840b6371dc19f80ec7827e9ca3619cafa132c891f989e053ae',
#  'script_type': 'p2sh_multisig',
#  'sequence': 'ffffffff',
#  'signatures': ['db9a8b8e83920439d660e3fccbabc502f2467abd07482f9b3e7a15bc2f9f8979197f180cf686183f684d0751a5f0338585cab49f22bbf85f00e6a37b55bec550',
#                 '327885e08b84505750ef35223847e64fab6dbd8c9a1bd91ba1d84fd831cd7b2354021459830442595ba303caa4cbdcad3aaa61f224d2bd6bd43dcf47214d7f41'],
#  'tid': 0,
#  'unlocking_script': '00483045022100db9a8b8e83920439d660e3fccbabc502f2467abd07482f9b3e7a15bc2f9f89790220197f180cf686183f684d0751a5f0338585cab49f22bbf85f00e6a37b55bec550014730440220327885e08b84505750ef35223847e64fab6dbd8c9a1bd91ba1d84fd831cd7b23022054021459830442595ba303caa4cbdcad3aaa61f224d2bd6bd43dcf47214d7f41014c695221020f060a8d8af1f86c1ff75b001072594cb9c3f7fb2a4fd9df2b497cf0e3237038210271b18e48c6d362696d439422b0ab933a031ec16ed0e51c1a1fc558c03f50f5202103c531065db2e61f2b86840b6371dc19f80ec7827e9ca3619cafa132c891f989e053ae'}
# pprint(t.outputs[0].dict())
# {'address': '3NfRtyHPDPicXj9pLh4mw2yoyAycpKw8mT',
#  'amount': 7990000,
#  'lock_script': 'a914e60dd2333925d54165bb3042054e61952f75f51887',
#  'public_key': '',
#  'public_key_hash': 'e60dd2333925d54165bb3042054e61952f75f518'}

    def gettransaction(self, txid):
        res = self.compose_request('tx', txid)
        return res

    def getrawtransaction(self, txid):
        res = self.compose_request('tx', txid)
        return res['hex']

    def estimatefee(self, blocks):
        res = self.compose_request('tx', 'fee', variables={'numBlocks': blocks})
        return res['feePerKb']
