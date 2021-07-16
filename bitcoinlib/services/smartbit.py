# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Smartbit.com.au client
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

import logging
from datetime import datetime
from bitcoinlib.main import MAX_TRANSACTIONS
from bitcoinlib.services.baseclient import BaseClient
from bitcoinlib.transactions import Transaction
from bitcoinlib.encoding import varstr
from bitcoinlib.keys import Address

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'smartbit'
REQ_LIMIT = 10
REQ_LIMIT_TOTAL = 50
# Please note: In the Bitaps API, the first couple of Bitcoin blocks are not correctly indexed,
# so transactions from these blocks are missing.


class SmartbitClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, category, command='', data='', variables=None, req_type='blockchain', method='get'):
        url_path = req_type + '/' + category
        if data:
            if url_path[-1:] != '/':
                url_path += '/'
            url_path += data
        if command:
            url_path += '/' + command
        return self.request(url_path, variables=variables, method=method)

    def _parse_transaction(self, tx):
        status = 'unconfirmed'
        if tx['confirmations']:
            status = 'confirmed'
        witness_type = 'legacy'
        if 'inputs' in tx and [ti['witness'] for ti in tx['inputs'] if ti['witness'] and ti['witness'] != ['NULL']]:
            witness_type = 'segwit'
        input_total = tx['input_amount_int']
        t_time = None
        if tx['time']:
            t_time = datetime.utcfromtimestamp(tx['time'])
        t = Transaction(locktime=tx['locktime'], version=int(tx['version']), network=self.network, fee=tx['fee_int'],
                        size=tx['size'], txid=tx['txid'], date=t_time,
                        confirmations=tx['confirmations'], block_height=tx['block'], status=status,
                        input_total=input_total, coinbase=tx['coinbase'],
                        output_total=tx['output_amount_int'], witness_type=witness_type)
        index_n = 0
        if tx['coinbase']:
            t.add_input(prev_txid=b'\00' * 32, output_n=0, value=0)
        else:
            for ti in tx['inputs']:
                unlocking_script = ti['script_sig']['hex']
                witness_type = 'legacy'
                if ti['witness'] and ti['witness'] != ['NULL']:
                    address = Address.parse(ti['addresses'][0])
                    if address.script_type == 'p2sh':
                        witness_type = 'p2sh-segwit'
                    else:
                        witness_type = 'segwit'
                t.add_input(prev_txid=ti['txid'], output_n=ti['vout'], unlocking_script=unlocking_script,
                            index_n=index_n, value=ti['value_int'], address=ti['addresses'][0], sequence=ti['sequence'],
                            witness_type=witness_type, witnesses=ti['witness'] if ti['witness'] != ['NULL'] else [],
                            strict=False)
                index_n += 1

        for to in tx['outputs']:
            spent = False
            spending_txid = None
            if 'spend_txid' in to and to['spend_txid']:
                spent = True
                spending_txid = to['spend_txid']
            address = ''
            if to['addresses']:
                address = to['addresses'][0]
            t.add_output(value=to['value_int'], address=address, lock_script=to['script_pub_key']['hex'],
                         spent=spent, output_n=to['n'], spending_txid=spending_txid, strict=False)
        return t

    def getbalance(self, addresslist):
        res = self.compose_request('address', 'wallet', ','.join(addresslist))
        return res['wallet']['total']['balance_int']

    def getutxos(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        utxos = []
        utxo_list = []
        next_link = ''
        while True:
            variables = {'limit': REQ_LIMIT, 'next': next_link, 'dir': 'asc'}
            res = self.compose_request('address', 'unspent', address, variables=variables)
            next_link = res['paging']['next']
            for utxo in res['unspent']:
                utxo_list.append(utxo['txid'])
                if utxo['txid'] == after_txid:
                    utxo_list = []
            if not next_link or len(utxos) > REQ_LIMIT_TOTAL:
                break
        for txid in utxo_list[:limit]:
            t = self.gettransaction(txid)
            for utxo in t.outputs:
                if utxo.address != address:
                    continue
                utxos.append(
                    {
                        'address': utxo.address,
                        'txid': t.txid,
                        'confirmations': t.confirmations,
                        'output_n': utxo.output_n,
                        'input_n': 0,
                        'block_height': t.block_height,
                        'fee': t.fee,
                        'size': t.size,
                        'value': utxo.value,
                        'script': utxo.lock_script.hex(),
                        'date': t.date
                    })
        return utxos

    def gettransaction(self, txid):
        res = self.compose_request('tx', data=txid)
        return self._parse_transaction(res['transaction'])

    def gettransactions(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        txs = []
        next_link = ''
        while True:
            variables = {'limit': REQ_LIMIT, 'next': next_link, 'dir': 'asc'}
            res = self.compose_request('address', data=address, variables=variables)
            next_link = '' if 'transaction_paging' not in res['address'] else \
                res['address']['transaction_paging']['next']
            if 'transactions' not in res['address']:
                break
            res_tx = sorted(res['address']['transactions'], key=lambda k: (k['block'] is None, k['block']))
            for tx in res_tx:
                t = self._parse_transaction(tx)
                txs.append(t)
                if t.txid == after_txid:
                    txs = []
            if not next_link or len(txs) > REQ_LIMIT_TOTAL:
                break
        return txs[:limit]

    def getrawtransaction(self, txid):
        res = self.compose_request('tx', data=txid, command='hex')
        return res['hex'][0]['hex']

    def sendrawtransaction(self, rawtx):
        res = self.compose_request('pushtx', variables={'hex': rawtx}, method='post')
        return {
            'txid': res['txid'],
            'response_dict': res
        }

    # def estimatefee

    def blockcount(self):
        return self.compose_request('totals')['totals']['block_count'] - 1

    def mempool(self, txid):
        if txid:
            tx = self.compose_request('tx', data=txid)
            if tx['transaction']['confirmations'] == 0:
                return [tx['transaction']['hash']]
        return False

    def getblock(self, blockid, parse_transactions, page, limit):
        if limit > 100:
            limit = 100
        if page > 1:  # Paging does not work with Smartbit
            return False
        variables = {'limit': limit}
        bd = self.compose_request('block', str(blockid), variables=variables)['block']
        if parse_transactions:
            txs = []
            for tx in bd['transactions']:
                # try:
                txs.append(self._parse_transaction(tx))
                # except Exception as e:
                #     _logger.error("Could not parse tx %s with error %s" % (tx['txid'], e))
        else:
            txs = [tx['txid'] for tx in bd['transactions']]

        block = {
            'bits': int(bd['bits'], 16),
            'depth': bd['confirmations'],
            'block_hash': bd['hash'],
            'height': bd['height'],
            'merkle_root': bd['merkleroot'],
            'nonce': bd['nonce'],
            'prev_block': bd['previous_block_hash'],
            'time': bd['time'],
            'tx_count': bd['transaction_count'],
            'txs': txs,
            'version': bd['version'],
            'page': page,
            'pages': None if not limit else int(bd['transaction_count'] // limit) + (bd['transaction_count'] % limit > 0),
            'limit': limit
        }
        return block

    def isspent(self, txid, output_n):
        t = self.gettransaction(txid)
        return 1 if t.outputs[output_n].spent else 0

    # def getinfo(self):
