# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Blockchair client
#    © 2018 September - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.services.baseclient import BaseClient
from bitcoinlib.transactions import Transaction

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'blockchair'
REQUEST_LIMIT = 3


class BlockChairClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, command, query_vars=None, offset=0):
        url_path = ''
        variables = {'offset': offset, 'limit': REQUEST_LIMIT}
        if command:
            url_path += command
        if query_vars is not None:
            varstr = ','.join(['%s(%s)' % (qv, query_vars[qv]) for qv in query_vars])
            variables.update({'q': varstr})
        return self.request(url_path, variables)

    # def getbalance(self, addresslist):
    #     balance = 0.0
    #     for address in addresslist:
    #         res = self.compose_request('address', address)
    #         balance += int(res['balance'])
    #     return int(balance * self.units)

    def getutxos(self, addresslist):
        utxos = []
        for address in addresslist:
            offset = 0
            while True:
                res = self.compose_request('outputs', {'recipient': address, 'is_spent': 'false'}, offset=offset)
                current_block = res['context']['state']
                for utxo in res['data']:
                    if utxo['is_spent']:
                        continue
                    utxos.append({
                        'address': address,
                        'tx_hash': utxo['transaction_hash'],
                        'confirmations': current_block - utxo['block_id'],
                        'output_n': utxo['index'],
                        'input_n': 0,
                        'block_height': utxo['block_id'],
                        'fee': None,
                        'size': 0,
                        'value': utxo['value'],
                        'script': utxo['script_hex'],
                        'date': datetime.strptime(utxo['time'], "%Y-%m-%d %H:%M:%S")
                    })
                if not len(res['data']) or len(res['data']) < REQUEST_LIMIT:
                    break
                offset += REQUEST_LIMIT

        # if len(utxos) >= 2000:
        #     _logger.warning("BlockTrail: UTXO's list has been truncated, UTXO list is incomplete")
        return utxos

    # def gettransactions(self, addresslist):
    #     txs = []
    #     for address in addresslist:
    #         # res = self.compose_request('address', address, 'unspent-outputs')
    #         current_page = 1
    #         while len(txs) < 2000:
    #             variables = {'page': current_page, 'limit': 200}
    #             res = self.compose_request('address', address, 'transactions', variables)
    #             for tx in res['data']:
    #                 if tx['hash'] in [t.hash for t in txs]:
    #                     break
    #                 if tx['confirmations']:
    #                     status = 'confirmed'
    #                 else:
    #                     status = 'unconfirmed'
    #                 t = Transaction(network=self.network, fee=tx['total_fee'], hash=tx['hash'],
    #                                 date=datetime.strptime(tx['time'], "%Y-%m-%dT%H:%M:%S+%f"),
    #                                 confirmations=tx['confirmations'], block_height=tx['block_height'],
    #                                 block_hash=tx['block_hash'], status=status,
    #                                 input_total=tx['total_input_value'], output_total=tx['total_output_value'])
    #                 for index_n, ti in enumerate(tx['inputs']):
    #                     t.add_input(prev_hash=ti['output_hash'], output_n=ti['output_index'],
    #                                 unlocking_script=ti['script_signature'],
    #                                 index_n=index_n, value=int(round(ti['value'] * self.units, 0)))
    #                 for to in tx['outputs']:
    #                     t.add_output(value=int(round(to['value'] * self.units, 0)), address=to['address'],
    #                                  lock_script=to['script_hex'],
    #                                  spent=bool(to['spent_hash']))
    #                 txs.append(t)
    #             if current_page*200 > int(res['total']):
    #                 break
    #             current_page += 1
    #
    #     if len(txs) >= 2000:
    #         _logger.warning("BlockTrail: UTXO's list has been truncated, UTXO list is incomplete")
    #     return txs
    #
    # def gettransaction(self, tx_id):
    #     tx = self.compose_request('transaction', tx_id)
    #
    #     rawtx = tx['raw']
    #     t = Transaction.import_raw(rawtx, network=self.network)
    #     if tx['confirmations']:
    #         t.status = 'confirmed'
    #     else:
    #         t.status = 'unconfirmed'
    #
    #     if t.coinbase:
    #         t.input_total = t.output_total
    #     else:
    #         t.input_total = tx['total_input_value']
    #     t.output_total = tx['total_output_value']
    #     t.fee = tx['total_fee']
    #     t.hash = tx['hash']
    #     t.block_hash = tx['block_hash']
    #     t.block_height = tx['block_height']
    #     t.confirmations = tx['confirmations']
    #     t.date = datetime.strptime(tx['block_time'], "%Y-%m-%dT%H:%M:%S+%f")
    #     t.size = tx['size']
    #     for n, i in enumerate(t.inputs):
    #         i.value = tx['inputs'][n]['value']
    #     for n, o in enumerate(t.outputs):
    #         if tx['outputs'][n]['address']:
    #             o.spent = True if 'spent_hash' in tx['outputs'][n] else False
    #
    #     return t

    def estimatefee(self, blocks):
        # Non-scientific method to estimate transaction fees. It's probably good when it looks complicated...
        res = self.compose_request('stats')
        memtx = res['data']['mempool_transactions']
        memsize = res['data']['mempool_size']
        medfee = res['data']['median_trasaction_fee_24h']
        avgfee = res['data']['average_trasaction_fee_24h']
        memtotfee = res['data']['mempool_total_fee_usd']
        price = res['data']['market_price_usd']
        avgtxsize = memsize / memtx
        mempool_feekb = ((memtotfee / price * 100000000) / memtx) * medfee/avgfee
        avgfeekb_24h = avgtxsize * (medfee / 1000)
        fee_estimate = (mempool_feekb + avgfeekb_24h) / 2
        return int(fee_estimate * (1 / math.log(blocks+2, 6)))
