# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Blockchair client
#    © 2018 October - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.keys import deserialize_address
from bitcoinlib.encoding import EncodingError, varstr, to_bytes

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'blockchair'
REQUEST_LIMIT = 25


class BlockChairClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, command, query_vars=None, data=None, offset=0):
        url_path = ''
        variables = {}
        if command != 'stats':
            variables.update({'limit': REQUEST_LIMIT})
        if offset:
            variables.update({'offset': offset})
        if command:
            url_path += command
        if data:
            url_path += data
        if query_vars is not None:
            varstr = ','.join(['%s(%s)' % (qv, query_vars[qv]) for qv in query_vars])
            variables.update({'q': varstr})
        return self.request(url_path, variables)

    def getbalance(self, addresslist):
        balance = 0
        for address in addresslist:
            res = self.compose_request('dashboards/address/', data=address)
            balance += int(res['data'][address]['address']['balance'])
        return balance

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
        return utxos

    def gettransactions(self, addresslist):
        tx_ids = []
        for address in addresslist:
            # offset = 0
            # transaction_count = None
            # while transaction_count is100 None or offset < transaction_count:
            res = self.compose_request('dashboards/address/', data=address)
            addr = res['data'][address]
            transaction_count = addr['address']['transaction_count']
            if transaction_count > REQUEST_LIMIT:
                _logger.warning("Transactions truncated. Found more transactions for address %s then request limit."
                                % addr)
            tx_ids += addr['transactions']
            # offset += REQUEST_LIMIT
        tx_ids = list(set(tx_ids))
        txs = []
        if len(tx_ids) > REQUEST_LIMIT:
            _logger.warning("Transactions truncated. Found more transactions for this addresslist then request limit.")
        for tx_id in tx_ids[:REQUEST_LIMIT]:
            txs.append(self.gettransaction(tx_id))
        return txs

    def gettransaction(self, tx_id):
        res = self.compose_request('dashboards/transaction/', data=tx_id)

        tx = res['data'][tx_id]['transaction']
        confirmations = res['context']['state'] - tx['block_id']
        status = 'unconfirmed'
        if confirmations:
            status = 'confirmed'
        witness_type = 'legacy'
        if tx['has_witness']:
            witness_type = 'segwit'
        input_total = tx['input_total']
        if tx['is_coinbase']:
            input_total = tx['output_total']
        t = Transaction(locktime=tx['lock_time'], version=tx['version'], network=self.network,
                        fee=tx['fee'], size=tx['size'], hash=tx['hash'],
                        date=datetime.strptime(tx['time'], "%Y-%m-%d %H:%M:%S"),
                        confirmations=confirmations, block_height=tx['block_id'], status=status,
                        input_total=input_total, coinbase=tx['is_coinbase'],
                        output_total=tx['output_total'], witness_type=witness_type)
        index_n = 0
        for ti in res['data'][tx_id]['inputs']:
            if ti['spending_witness']:
                witnesses = b"".join([varstr(to_bytes(x)) for x in ti['spending_witness'].split(",")])
                t.add_input(prev_hash=ti['transaction_hash'], output_n=ti['index'],
                            unlocking_script=witnesses, index_n=index_n, value=ti['value'],
                            address=ti['recipient'], witness_type='segwit')
            else:
                t.add_input(prev_hash=ti['transaction_hash'], output_n=ti['index'],
                            unlocking_script_unsigned=ti['script_hex'], index_n=index_n, value=ti['value'],
                            address=ti['recipient'], unlocking_script=ti['spending_signature_hex'])
            index_n += 1
        for to in res['data'][tx_id]['outputs']:
            try:
                deserialize_address(to['recipient'], network=self.network.name)
                addr = to['recipient']
            except EncodingError:
                addr = ''
            t.add_output(value=to['value'], address=addr, lock_script=to['script_hex'],
                         spent=to['is_spent'], output_n=to['index'])
        return t

    def estimatefee(self, blocks):
        # Non-scientific method to estimate transaction fees. It's probably good when it looks complicated...
        res = self.compose_request('stats')
        memtx = res['data']['mempool_transactions']
        memsize = res['data']['mempool_size']
        medfee = res['data']['median_transaction_fee_24h']
        avgfee = res['data']['average_transaction_fee_24h']
        memtotfee = res['data']['mempool_total_fee_usd']
        price = res['data']['market_price_usd']
        avgtxsize = memsize / memtx
        mempool_feekb = ((memtotfee / price * 100000000) / memtx) * medfee/avgfee
        avgfeekb_24h = avgtxsize * (medfee / 1000)
        fee_estimate = (mempool_feekb + avgfeekb_24h) / 2
        estimated_fee = int(fee_estimate * (1 / math.log(blocks+2, 6)))
        if estimated_fee < self.network.dust_amount:
            estimated_fee = self.network.dust_amount
        return estimated_fee

    def block_count(self):
        """
        Get latest block number: The block number of last block in longest chain on the blockchain

        :return int:
        """
        res = self.compose_request('stats')
        return res['context']['state']
