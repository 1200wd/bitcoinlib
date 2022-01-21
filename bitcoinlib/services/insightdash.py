# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Litecore.io Client
#    © 2018-2019 July - 1200 Web Development <http://1200wd.com/>
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

PROVIDERNAME = 'insightdash'
REQUEST_LIMIT = 50

_logger = logging.getLogger(__name__)


class InsightDashClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, category, data, cmd='', variables=None, method='get', offset=0):
        url_path = category
        if data:
            url_path += '/' + data + '/' + cmd
        if variables is None:
            variables = {}
        variables.update({'from': offset, 'to': offset+REQUEST_LIMIT})
        return self.request(url_path, variables, method=method)

    def _convert_to_transaction(self, tx):
        if tx['confirmations']:
            status = 'confirmed'
        else:
            status = 'unconfirmed'
        fees = None if 'fees' not in tx else int(round(float(tx['fees']) * self.units, 0))
        value_in = 0 if 'valueIn' not in tx else tx['valueIn']
        isCoinbase = False
        if 'isCoinBase' in tx and tx['isCoinBase']:
            isCoinbase = True
        txdate = None
        if 'blocktime' in tx:
            txdate = datetime.utcfromtimestamp(tx['blocktime'])
        t = Transaction(locktime=tx['locktime'], version=tx['version'], network=self.network,
                        fee=fees, size=tx['size'], txid=tx['txid'],
                        date=txdate, confirmations=tx['confirmations'],
                        block_height=tx['blockheight'], status=status,
                        input_total=int(round(float(value_in) * self.units, 0)), coinbase=isCoinbase,
                        output_total=int(round(float(tx['valueOut']) * self.units, 0)))
        for ti in tx['vin']:
            if isCoinbase:
                t.add_input(prev_txid=32 * b'\0', output_n=4*b'\xff', unlocking_script=ti['coinbase'], index_n=ti['n'],
                            script_type='coinbase', sequence=ti['sequence'], value=0)
            else:
                value = int(round(float(ti['value']) * self.units, 0))
                t.add_input(prev_txid=ti['txid'], output_n=ti['vout'], unlocking_script=ti['scriptSig']['hex'],
                            index_n=ti['n'], value=value, sequence=ti['sequence'],
                            double_spend=False if ti['doubleSpentTxID'] is None else ti['doubleSpentTxID'],
                            strict=self.strict)
        for to in tx['vout']:
            value = int(round(float(to['value']) * self.units, 0))
            t.add_output(value=value, lock_script=to['scriptPubKey']['hex'],
                         spent=True if to['spentTxId'] else False, output_n=to['n'],
                         spending_txid=None if not to['spentTxId'] else to['spentTxId'],
                         spending_index_n=None if not to['spentIndex'] else to['spentIndex'], strict=self.strict)
        return t

    def getbalance(self, addresslist):
        balance = 0
        addresslist = self._addresslist_convert(addresslist)
        for a in addresslist:
            res = self.compose_request('addr', a.address, 'balance')
            balance += res
        return balance

    def getutxos(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        address = self._address_convert(address)
        res = self.compose_request('addrs', address.address, 'utxo')
        txs = []
        for tx in res:
            if tx['txid'] == after_txid:
                break
            txs.append({
                'address': address.address_orig,
                'txid': tx['txid'],
                'confirmations': tx['confirmations'],
                'output_n': tx['vout'],
                'input_n': 0,
                'block_height': tx['height'],
                'fee': None,
                'size': 0,
                'value': tx['satoshis'],
                'script': tx['scriptPubKey'],
                'date': None
            })
        return txs[::-1][:limit]

    def gettransaction(self, tx_id):
        tx = self.compose_request('tx', tx_id)
        return self._convert_to_transaction(tx)

    def gettransactions(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        address = self._address_convert(address)
        res = self.compose_request('addrs', address.address, 'txs')
        txs = []
        txs_dict = res['items'][::-1]
        if after_txid:
            txs_dict = txs_dict[[t['txid'] for t in txs_dict].index(after_txid) + 1:]
        for tx in txs_dict[:limit]:
            if tx['txid'] == after_txid:
                break
            txs.append(self._convert_to_transaction(tx))
        return txs

    def getrawtransaction(self, tx_id):
        res = self.compose_request('rawtx', tx_id)
        return res['rawtx']

    def sendrawtransaction(self, rawtx):
        res = self.compose_request('tx', 'send', variables={'rawtx': rawtx}, method='post')
        return {
            'txid': res['txid'],
            'response_dict': res
        }

    # def estimatefee

    def blockcount(self):
        res = self.compose_request('status', '', variables={'q': 'getinfo'})
        return res['info']['blocks']

    def mempool(self, txid):
        res = self.compose_request('tx', txid)
        if res['confirmations'] == 0:
            return res['txid']
        return []

    def getblock(self, blockid, parse_transactions, page, limit):
        bd = self.compose_request('block', str(blockid))
        if parse_transactions:
            txs = []
            for txid in bd['tx'][(page-1)*limit:page*limit]:
                try:
                    txs.append(self.gettransaction(txid))
                except Exception as e:
                    _logger.error("Could not parse tx %s with error %s" % (txid, e))
        else:
            txs = bd['tx']

        block = {
            'bits': bd['bits'],
            'depth': bd['confirmations'],
            'hash': bd['hash'],
            'height': bd['height'],
            'merkle_root': bd['merkleroot'],
            'nonce': bd['nonce'],
            'prev_block': bd['previousblockhash'],
            'time': datetime.utcfromtimestamp(bd['time']),
            'total_txs': len(bd['tx']),
            'txs': txs,
            'version': bd['version'],
            'page': page,
            'pages': None if not limit else int(len(bd['tx']) // limit) + (len(bd['tx']) % limit > 0),
            'limit': limit
        }
        return block

    def isspent(self, txid, output_n):
        t = self.gettransaction(txid)
        return 1 if t.outputs[output_n].spent else 0

    def getinfo(self):
        info = self.compose_request('status', '')['info']
        return {
            'blockcount': info['blocks'],
            'chain': info['network'],
            'difficulty': int(float(info['difficulty'])),
            'hashrate': 0,
            'mempool_size': 0,
        }
