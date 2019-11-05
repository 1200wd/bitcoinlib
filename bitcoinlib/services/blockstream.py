# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    BlockstreamClient client
#    © 2019 November - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.main import MAX_TRANSACTIONS
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction
from bitcoinlib.encoding import to_hexstring

PROVIDERNAME = 'blockstream'

_logger = logging.getLogger(__name__)


class BlockstreamClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, function, data='', parameter='', variables=None, post_data='', method='get'):
        url_path = function
        if data:
            url_path += '/' + data
        if parameter:
            url_path += '/' + parameter
        if variables is None:
            variables = {}
        if self.api_key:
            variables.update({'token': self.api_key})
        return self.request(url_path, variables, method, post_data=post_data)

    def getbalance(self, addresslist):
        balance = 0
        for address in addresslist:
            res = self.compose_request('address', data=address)
            balance += (res['chain_stats']['funded_txo_sum'] - res['chain_stats']['spent_txo_sum'])
        return balance

    # def getutxos(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):

    def gettransaction(self, txid):
        tx = self.compose_request('tx', txid)
        block_height = self.blockcount()
        confirmations = block_height - tx['status']['block_height']
        status = 'unconfirmed'
        if tx['status']['confirmed']:
            status = 'confirmed'
        witness_type = 'legacy'
        # if tx['has_witness']:
        #     witness_type = 'segwit'
        # input_total = tx['input_total']
        # if tx['is_coinbase']:
        #     input_total = tx['output_total']
        t = Transaction(locktime=tx['locktime'], version=tx['version'], network=self.network,
                        fee=tx['fee'], size=tx['size'], hash=tx['txid'],
                        date=datetime.fromtimestamp(tx['status']['block_time']),
                        confirmations=confirmations, block_height=block_height, status=status,
                        coinbase=tx['vin'][0]['is_coinbase'], witness_type=witness_type)
        index_n = 0
        for ti in tx['vin']:
            # if ti['spending_witness']:
            #     witnesses = b"".join([varstr(to_bytes(x)) for x in ti['spending_witness'].split(",")])
            #     t.add_input(prev_hash=ti['transaction_hash'], output_n=ti['index'],
            #                 unlocking_script=witnesses, index_n=index_n, value=ti['value'],
            #                 address=ti['recipient'], witness_type='segwit')
            # else:
            t.add_input(prev_hash=ti['txid'], output_n=ti['vout'],
                        unlocking_script_unsigned=ti['prevout']['scriptpubkey'], index_n=index_n,
                        value=ti['prevout']['value'], address=ti['prevout']['scriptpubkey_address'],
                        unlocking_script=ti['scriptsig'])
            index_n += 1
        index_n = 0
        for to in tx['vout']:
            # try:
            #     deserialize_address(to['recipient'], network=self.network.name)
            #     addr = to['recipient']
            # except EncodingError:
            #     addr = ''
            address = ''
            if 'scriptpubkey_address' in to:
                address = to['scriptpubkey_address']
            t.add_output(value=to['value'], address=address, lock_script=to['scriptpubkey'],
                         output_n=index_n)
            index_n += 1
        return t
    # def gettransactions(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):

    def getrawtransaction(self, txid):
        return self.compose_request('tx', txid, 'hex')

    def sendrawtransaction(self, rawtx):
        res = self.compose_request('tx', post_data=rawtx, method='post')
        return {
            'txid': res,
            'response_dict': res
        }

    def estimatefee(self, blocks):
        est = self.compose_request('fee-estimates')
        closest = (sorted([int(i) - blocks for i in est.keys() if int(i) - blocks >= 0]))
        if closest:
            return int(est[str(closest[0] + blocks)])
        else:
            return int(est[str(sorted([int(i) for i in est.keys()])[-1:][0])])

    def blockcount(self):
        return self.compose_request('blocks', 'tip', 'height')

    # def mempool(self, txid):
