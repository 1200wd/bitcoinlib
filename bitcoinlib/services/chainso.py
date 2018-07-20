# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    BlockTrail client
#    © 2017-2018 June - 1200 Web Development <http://1200wd.com/>
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
import time
from datetime import datetime
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction


_logger = logging.getLogger(__name__)

PROVIDERNAME = 'chainso'


class ChainSo(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, function, data='', parameter='', variables=None, method='get'):
        url_path = function
        url_path += '/' + self.provider_coin_id
        if data:
            url_path += '/' + data
        if parameter:
            url_path += '/' + parameter
        if variables is None:
            variables = {}
        if self.api_key:
            variables.update({'api_key': self.api_key})
        # Sleep for n seconds to avoid 429 errors
        time.sleep(1)
        return self.request(url_path, variables, method)

    def sendrawtransaction(self, rawtx):
        res = self.compose_request('send_tx', variables={'tx_hex': rawtx}, method='post')
        return {
            'txid': '' if 'data' not in res else res['data']['txid'],
            'response_dict': res
        }

    def getbalance(self, addresslist):
        balance = 0.0
        for address in addresslist:
            res = self.compose_request('get_address_balance', address)
            balance += float(res['data']['confirmed_balance']) + float(res['data']['unconfirmed_balance'])
        return int(balance * self.units)

    def getutxos(self, addresslist):
        txs = []
        count = 0
        for address in addresslist:
            lasttx = ''
            while len(txs) < 1000:
                res = self.compose_request('get_tx_unspent', address, lasttx)
                if res['status'] != 'success':
                    pass
                for tx in res['data']['txs']:
                    txs.append({
                        'address': address,
                        'tx_hash': tx['txid'],
                        'confirmations': tx['confirmations'],
                        'output_n': -1 if 'output_no' not in tx else tx['output_no'],
                        'input_n': -1 if 'input_no' not in tx else tx['input_no'],
                        'block_height': None,
                        'fee': None,
                        'size': 0,
                        'value': int(round(float(tx['value']) * self.units, 0)),
                        'script': tx['script_hex'],
                        'date': datetime.fromtimestamp(tx['time']),
                    })
                    lasttx = tx['txid']
                if len(res['data']['txs']) < 100:
                    break
            count += 1
            if not count % 10:
                time.sleep(60)
        if len(txs) >= 1000:
            _logger.warning("ChainSo: transaction list has been truncated, and thus is incomplete")
        return txs

    def getrawtransaction(self, txid):
        res = self.compose_request('get_tx', txid)
        return res['data']['tx_hex']

    def gettransaction(self, tx_id):
        res = self.compose_request('get_tx', tx_id)
        tx = res['data']
        raw_tx = tx['tx_hex']
        t = Transaction.import_raw(raw_tx, network=self.network)
        input_total = 0
        output_total = 0
        for n, i in enumerate(t.inputs):
            i.value = int(round(float(tx['inputs'][n]['value']) * self.units, 0))
            input_total += i.value
        for o in t.outputs:
            # TODO: Check if output is spent (still neccessary?)
            o.spent = None
            output_total += o.value
        t.hash = tx_id
        t.block_hash = tx['blockhash']
        t.date = datetime.fromtimestamp(tx['time'])
        t.rawtx = raw_tx
        t.size = tx['size']
        t.network = self.network
        t.locktime = tx['locktime']
        t.input_total = input_total
        t.output_total = output_total
        t.fee = t.input_total - t.output_total
        t.confirmations = tx['confirmations']
        if tx['confirmations']:
            t.status = 'confirmed'
        else:
            t.status = 'unconfirmed'
        return t

    def gettransactions(self, address_list):
        txs = []
        addr_txs = []
        for address in address_list:
            res = self.compose_request('address', address)
            if res['status'] != 'success':
                pass
            for tx in res['data']['txs']:
                if tx['txid'] not in [t[0] for t in addr_txs]:
                    addr_txs.append(
                        (
                            tx['txid'],
                            [] if 'outgoing' not in tx else tx['outgoing']['outputs'],
                            # '' if 'incoming' not in tx else tx['incoming'],
                        )
                    )
        for addr_tx in addr_txs:
            t = self.gettransaction(addr_tx[0])
            for out in addr_tx[1]:
                n = out['output_no']
                if out['address'] == t.outputs[n].address and t.outputs[n].output_n == n:
                    if t.outputs[n].spent is not None:
                        continue
                    if out['spent'] is None:
                        t.outputs[n].spent = False
                    else:
                        t.outputs[n].spent = True
                else:
                    raise ValueError("Unexpected output order in gettransaction call")
            txs.append(t)
        return txs

    def block_count(self):
        return self.compose_request('get_info')['data']['blocks']
