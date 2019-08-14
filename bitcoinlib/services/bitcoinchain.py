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

    # def getbalance(self, addresslist):

    # def getutxos(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):

    # def gettransactions(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):

    def _parse_transaction(self, tx):
        witness_type = 'legacy'
        # if len([ti['witness'] for ti in tx['inputs'] if ti['witness'] != '00']):
        #     witness_type = 'segwit'
        coinbase = False
        if tx['inputs'][0]['output_ref']['tx'] == '00' * 32:
            coinbase = True
        status = 'unconfirmed'
        if tx['confirmations']:
            status = 'confirmed'
        # confirmations=tx['confirmations'], block_height=tx['height'],
        t = Transaction(locktime=tx['lock_time'], version=tx['version'], network=self.network,
                        fee=tx['fee'], hash=tx['self_hash'], date=datetime.fromtimestamp(tx['block_time']),
                        block_hash=tx['blocks'][0],
                        status=status, coinbase=coinbase, witness_type=witness_type)
        for ti in tx['inputs']:
            witness_type = 'legacy'
            script = ti['in_script']['hex']
            address = ti['sender']
            value = ti['value']
            # , sequence=ti['sequence']
            t.add_input(prev_hash=ti['output_ref']['tx'], output_n=ti['output_ref']['number'],
                        unlocking_script=script, address=address, value=value,
                        witness_type=witness_type)
        output_n = 0
        for to in tx['outputs']:
            t.add_output(value=to['value'], address=to['receiver'], lock_script=to['out_script']['hex'],
                         output_n=output_n, spent=to['spent'])
            output_n += 1
        t.update_totals()
        if t.coinbase:
            t.input_total = t.output_total
        return t

    def gettransaction(self, txid):
        res = self.compose_request('tx', data=txid)
        return self._parse_transaction(res[0])

    # [
    #     {
    #         "block_time": 1454518654,
    #         "blocks": [
    #             "000000000000000008e2bd2b7b157d9d785de1f91362c26b0e14bb683a0d0f9a"
    #         ],
    #         "fee": 0.0001,
    #         "inputs": [
    #             {
    #                 "in_script": {
    #                     "asm": "3044022005bb558d74075072e1337cd65b8c389821ad76ebda32b8e038ad2de7c85a9a9e022003d7e4657b1843bc1a09ec8d0d724654217d9aa3d2f642d1a0b5ded5fcdabdaa01 04911ae54558e8c94244bbd7c310fd55520d6b1f0c9e7174ad8751aba06511e12bd9de7a3d788783665c6eaeb56ea3bd78e3a75adfd4d0ced8858f0063c987e29d",
    #                     "hex": "473044022005bb558d74075072e1337cd65b8c389821ad76ebda32b8e038ad2de7c85a9a9e022003d7e4657b1843bc1a09ec8d0d724654217d9aa3d2f642d1a0b5ded5fcdabdaa014104911ae54558e8c94244bbd7c310fd55520d6b1f0c9e7174ad8751aba06511e12bd9de7a3d788783665c6eaeb56ea3bd78e3a75adfd4d0ced8858f0063c987e29d"
    #                 },
    #                 "output_ref": {
    #                     "number": 1,
    #                     "tx": "79d33fe99c51192acb6387a5e99cd577adaba1f4660656111abcb150baca22f0"
    #                 },
    #                 "sender": "1DXCePi1fg8m3z1avQtLaZrEpJVHYKaojZ",
    #                 "value": 300
    #             }
    #         ],
    #         "lock_time": 0,
    #         "outputs": [
    #             {
    #                 "out_script": {
    #                     "asm": "OP_DUP OP_HASH160 120e3598edbf89ae3f3c653bb080c5fc3adc5bb8 OP_EQUALVERIFY OP_CHECKSIG",
    #                     "hex": "76a914120e3598edbf89ae3f3c653bb080c5fc3adc5bb888ac",
    #                     "reqSigs": 1,
    #                     "type": "pubkeyhash"
    #                 },
    #                 "receiver": "12eUBjjzm9dzmCGmGxH8W3y3SCjm5zR1oz",
    #                 "spending_input": {
    #                     "number": 0,
    #                     "tx": "84df9279705a4c793445636432eb47e6a7797dc7e35b6016a3ea42de7a32c764"
    #                 },
    #                 "spent": true,
    #                 "value": 49.83331666
    #             },
    #             {
    #                 "out_script": {
    #                     "asm": "OP_DUP OP_HASH160 b488b68c869b4f7e0e718720432d6f7a7473007b OP_EQUALVERIFY OP_CHECKSIG",
    #                     "hex": "76a914b488b68c869b4f7e0e718720432d6f7a7473007b88ac",
    #                     "reqSigs": 1,
    #                     "type": "pubkeyhash"
    #                 },
    #                 "receiver": "1HTaQXDPaaqhvJLYTUxP6Ec5TQwYN6A6KA",
    #                 "spent": false,
    #                 "value": 49.83331666
    #             },
    #             {
    #                 "out_script": {
    #                     "asm": "OP_DUP OP_HASH160 2720b0b3cb536fd851b894fd953b368e73dd0795 OP_EQUALVERIFY OP_CHECKSIG",
    #                     "hex": "76a9142720b0b3cb536fd851b894fd953b368e73dd079588ac",
    #                     "reqSigs": 1,
    #                     "type": "pubkeyhash"
    #                 },
    #                 "receiver": "14ZtWqgUU6AS2sFaJJWLcyvR9FrRuRg8oB",
    #                 "spending_input": {
    #                     "number": 0,
    #                     "tx": "4783a469a0b4e98dcb34b58304b717536634506e8b48d51056d7528e3bb15b38"
    #                 },
    #                 "spent": true,
    #                 "value": 1
    #             },
    #             {
    #                 "out_script": {
    #                     "asm": "OP_DUP OP_HASH160 8cbb060e0b0e040beb6aa62924b05c110cb75c77 OP_EQUALVERIFY OP_CHECKSIG",
    #                     "hex": "76a9148cbb060e0b0e040beb6aa62924b05c110cb75c7788ac",
    #                     "reqSigs": 1,
    #                     "type": "pubkeyhash"
    #                 },
    #                 "receiver": "1Dq7eVGbm1t4jBasyCxUH6Lwsg8TL9QdCb",
    #                 "spent": false,
    #                 "value": 49.83331666
    #             },
    #             {
    #                 "out_script": {
    #                     "asm": "OP_DUP OP_HASH160 30fed2a84bb68f0d34cdcefc28041003b20ecb9f OP_EQUALVERIFY OP_CHECKSIG",
    #                     "hex": "76a91430fed2a84bb68f0d34cdcefc28041003b20ecb9f88ac",
    #                     "reqSigs": 1,
    #                     "type": "pubkeyhash"
    #                 },
    #                 "receiver": "15U4hcVkCqFA3hn6NdVbJbewiid6T83eoe",
    #                 "spent": false,
    #                 "value": 49.83331666
    #             },
    #             {
    #                 "out_script": {
    #                     "asm": "OP_DUP OP_HASH160 9c3e7572824f4b1f0cab33818d62d6ed72fdc478 OP_EQUALVERIFY OP_CHECKSIG",
    #                     "hex": "76a9149c3e7572824f4b1f0cab33818d62d6ed72fdc47888ac",
    #                     "reqSigs": 1,
    #                     "type": "pubkeyhash"
    #                 },
    #                 "receiver": "1FF9Edyk4onJ4SCJCYxsKyZ76aUu4Q7CCZ",
    #                 "spent": false,
    #                 "value": 49.83331666
    #             },
    #             {
    #                 "out_script": {
    #                     "asm": "OP_DUP OP_HASH160 1eb588fb6cb913cb205b6803d0e3e448061b365a OP_EQUALVERIFY OP_CHECKSIG",
    #                     "hex": "76a9141eb588fb6cb913cb205b6803d0e3e448061b365a88ac",
    #                     "reqSigs": 1,
    #                     "type": "pubkeyhash"
    #                 },
    #                 "receiver": "13oNk2xrLXueqWciNx9p43QRAnakmaGHWv",
    #                 "spent": false,
    #                 "value": 49.8333167
    #             }
    #         ],
    #         "rec_time": 1454518679,
    #         "self_hash": "4890e5a53a8bbe9ac2a1a9723784fc40a0a8644ff0f9ebeb7f13780d0cb25f2d",
    #         "total_input": 300,
    #         "total_output": 299.9999,
    #         "total_spend_output": 50.83331666,
    #         "version": 1
    #     }
    # ]

    # def getrawtransaction(self, txid):

    def block_count(self):
        res = self.compose_request('status')
        return res['height']

    # def mempool(self, txid):
