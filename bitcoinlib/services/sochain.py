# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    SoChain Client - API v3, see https://sochain.com/docs
#    1200 Web Development <http://1200wd.com/>
#    © 2026 October
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
from datetime import datetime, timezone
from decimal import Decimal
from bitcoinlib.main import MAX_TRANSACTIONS
from bitcoinlib.encoding import int_to_varbyteint, double_sha256
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction

PROVIDERNAME = 'sochain'
# Lookups work without an API key, with a daily limit per IP. To use a key, set 'api_key' for the provider in
# providers.json: the base client sends it in the Api-Key header.
#
# SoChain does not return raw transactions. They are rebuilt from the transaction's fields with each input's
# sequence number. For answers without sequence numbers, these are tried for all inputs until the hash matches
# the transaction ID.
SEQUENCES = [0xffffffff, 0xfffffffd, 0xfffffffe, 0]
HISTORY_PAGE_SIZE = 100
HISTORY_MAX_PAGES = 50
UTXO_PAGE_SIZE = 10

_logger = logging.getLogger(__name__)


def _varbytes(hexstr):
    data = bytes.fromhex(hexstr)
    return int_to_varbyteint(len(data)) + data


class SoChainClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, function, data='', parameter='', variables=None, method='get'):
        url_path = function + '/' + self.provider_coin_id
        if data:
            url_path += '/' + data
        if parameter:
            url_path += '/' + str(parameter)
        res = self.request(url_path, variables, method)
        if not isinstance(res, dict) or res.get('status') != 'success':
            raise ClientError("Unexpected response from SoChain for %s: %s" % (url_path, res))
        return res['data']

    def _to_units(self, amount):
        # Amounts are exact decimal strings, avoid the rounding errors of floats
        return int(Decimal(amount) * Decimal(self.units))

    def _rawtx(self, tx):
        version = (tx['version'] & 0xffffffff).to_bytes(4, 'little')
        locktime = tx['locktime'].to_bytes(4, 'little')
        inputs = []
        for ti in tx['inputs']:
            prev = ti['previous_output']
            if prev:
                outpoint = bytes.fromhex(prev['hash'])[::-1] + prev['index'].to_bytes(4, 'little')
            else:
                outpoint = b'\0' * 32 + b'\xff' * 4
            inputs.append(outpoint + _varbytes(ti['scriptSig']['hex']))
        outputs = b''.join([self._to_units(to['value']).to_bytes(8, 'little') + _varbytes(to['script']['hex'])
                            for to in tx['outputs']])
        given = [ti.get('sequence') for ti in tx['inputs']]
        if all(isinstance(s, int) and 0 <= s <= 0xffffffff for s in given):
            tries = [given]
        else:
            tries = [[s] * len(inputs) for s in SEQUENCES]
        for sequences in tries:
            txdata = int_to_varbyteint(len(inputs)) + \
                b''.join([i + s.to_bytes(4, 'little') for i, s in zip(inputs, sequences)]) + \
                int_to_varbyteint(len(tx['outputs'])) + outputs
            if double_sha256(version + txdata + locktime)[::-1].hex() == tx['hash']:
                break
        else:
            if len(tries) == 1:
                raise ClientError("SoChain: rebuilt raw transaction %s does not match its transaction ID" % tx['hash'])
            raise ClientError("SoChain: could not rebuild raw transaction %s, input sequence numbers unknown" %
                              tx['hash'])
        if any([ti['witness'] for ti in tx['inputs']]):
            witnesses = b''.join([int_to_varbyteint(len(ti['witness'])) +
                                  b''.join([_varbytes(w) for w in ti['witness']]) for ti in tx['inputs']])
            rawtx = version + b'\0\1' + txdata + witnesses + locktime
        else:
            rawtx = version + txdata + locktime
        if len(rawtx) != tx['size']:
            raise ClientError("SoChain: rebuilt raw transaction %s has size %d instead of %d" %
                              (tx['hash'], len(rawtx), tx['size']))
        return rawtx

    def _parse_transaction(self, tx):
        t = Transaction.parse_bytes(self._rawtx(tx), strict=self.strict, network=self.network)
        t.txid = tx['hash']
        t.block_height = tx['block_height']
        t.block_hash = tx['block_hash']
        t.confirmations = tx['confirmations']
        if tx['block_height'] is None:
            t.status = 'unconfirmed'
            t.date = None
        else:
            t.status = 'confirmed'
            t.date = datetime.fromtimestamp(tx['time'], timezone.utc)
        for n, ti in enumerate(tx['inputs']):
            if not t.coinbase:
                t.inputs[n].value = self._to_units(ti['value'])
            if not t.inputs[n].address and ti['address']:
                # Address of the spent output, when it can not be derived from the unlocking script (i.e. p2pk, p2tr)
                t.inputs[n].address = ti['address']
        for n, to in enumerate(tx['outputs']):
            t.outputs[n].spent = to['spent'] is not None
            if to['spent']:
                t.outputs[n].spending_txid = to['spent']['hash']
                t.outputs[n].spending_index_n = to['spent']['index']
        t.update_totals()
        t.fee = self._to_units(tx['fee'])
        return t

    def getbalance(self, addresslist):
        balance = 0
        for address in addresslist:
            res = self.compose_request('balance', address)
            balance += self._to_units(res['confirmed']) + self._to_units(res['unconfirmed'])
        return balance

    def getutxos(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        utxos = []
        after_txid_found = not after_txid
        page = 1
        while True:
            res = self.compose_request('unspent_outputs', address, page)
            for utxo in res['outputs']:
                confirmations = 0
                if utxo['block'] is not None:
                    self.latest_block = self.blockcount() if not self.latest_block else self.latest_block
                    confirmations = max(self.latest_block - utxo['block'] + 1, 1)
                utxos.append({
                    'address': address,
                    'txid': utxo['hash'],
                    'confirmations': confirmations,
                    'output_n': utxo['index'],
                    'input_n': 0,
                    'block_height': utxo['block'],
                    'fee': None,
                    'size': 0,
                    'value': self._to_units(utxo['value']),
                    'script': utxo['script'],
                    'date': None
                })
                if utxo['hash'] == after_txid:
                    utxos = []
                    after_txid_found = True
            # Outputs are listed oldest first: stop at the last page, or when enough outputs after after_txid are found
            if len(res['outputs']) < UTXO_PAGE_SIZE or (after_txid_found and len(utxos) >= limit):
                break
            page += 1
        return utxos[:limit]

    def gettransaction(self, txid):
        tx = self.compose_request('transaction', txid)
        return self._parse_transaction(tx)

    def gettransactions(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        # The address history is listed newest first: walk back to after_txid or to the first transaction
        txids = []
        txids_seen = set()
        variables = {'page_size': HISTORY_PAGE_SIZE}
        for _ in range(HISTORY_MAX_PAGES):
            res = self.compose_request('transactions', address, variables=variables)
            page_txids = [tx['hash'] for tx in res['transactions']]
            after_txid_found = after_txid in page_txids
            if after_txid_found:
                page_txids = page_txids[:page_txids.index(after_txid)]
            for txid in page_txids:
                # Rows can repeat after a reorg
                if txid not in txids_seen:
                    txids.append(txid)
                    txids_seen.add(txid)
            if after_txid_found or not res['next_cursor']:
                break
            variables = {'page_size': HISTORY_PAGE_SIZE, 'cursor': res['next_cursor']}
        else:
            raise ClientError("SoChain: more than %d transactions to walk through for address %s" %
                              (HISTORY_PAGE_SIZE * HISTORY_MAX_PAGES, address))
        txs = []
        for txid in txids[::-1][:limit]:
            txs.append(self.gettransaction(txid))
        return txs

    def getrawtransaction(self, txid):
        tx = self.compose_request('transaction', txid)
        return self._rawtx(tx).hex()

    # def sendrawtransaction(self, rawtx):
    #     Not available, SoChain API v3 has no endpoint to broadcast transactions

    def estimatefee(self, blocks):
        mempool = self.compose_request('network_info')['mempool']
        if mempool.get('loading') or not mempool['blocks']:
            return False
        blocks = max(blocks, 1)
        quotes = [q for q in (mempool.get('quote_targets') or {}).values()
                  if isinstance(q, dict) and q.get('within_blocks')]
        if quotes:
            # Dogecoin: fee rates its mining pools accepted lately. Use the cheapest one within the requested blocks.
            in_time = [q['fee_rate'] for q in quotes if q['within_blocks'] <= blocks]
            rate = min(in_time) if in_time else min(quotes, key=lambda q: q['within_blocks'])['fee_rate']
            return round(rate * 1000)
        # Fee rates of the next projected blocks, in the smallest denominator per vbyte
        projected = mempool['blocks'][min(blocks, len(mempool['blocks'])) - 1]
        if projected['num_txs']:
            rate = projected.get('median_fee_rate_precise') or projected['median_fee_rate']
        else:
            # This projected block is empty, so the lowest accepted fee rate confirms within the requested blocks
            rate = projected.get('min_fee_rate_possible_precise') or projected['min_fee_rate_possible']
        return round(Decimal(rate) * 1000)

    def blockcount(self):
        return self.compose_request('network_info')['block_count']

    def mempool(self, txid):
        if txid:
            res = self.compose_request('transaction_status', txid)
            if res['status'] == 'pending':
                return [txid]
            return []
        # Listing all transactions in the mempool is not available
        return False

    def getblock(self, blockid, parse_transactions, page, limit):
        bd = self.compose_request('block', str(blockid))
        if parse_transactions:
            txs = []
            for txid in bd['txs'][(page-1)*limit:page*limit]:
                txs.append(self.gettransaction(txid))
        else:
            txs = bd['txs']

        block = {
            'bits': int(bd['bits'], 16),
            'depth': bd['confirmations'],
            'block_hash': bd['hash'],
            'height': bd['height'],
            'merkle_root': bd['merkleroot'],
            'nonce': bd['nonce'],
            'prev_block': bd['previous_block_hash'] or b'',
            'time': bd['time'],
            'tx_count': bd['num_txs'],
            'txs': txs,
            'version': bd['version'],
            'page': page,
            'pages': None if not limit else int(bd['num_txs'] // limit) + (bd['num_txs'] % limit > 0),
            'limit': limit
        }
        return block

    # def getrawblock(self, blockid):
    #     Not available, SoChain API v3 has no raw blocks

    def isspent(self, txid, output_n):
        tx = self.compose_request('transaction', txid)
        return 1 if tx['outputs'][output_n]['spent'] else 0

    def getinfo(self):
        info = self.compose_request('network_info')
        latest_block = self.compose_request('latest_blocks_summary')['blocks'][0]
        return {
            'blockcount': info['block_count'],
            'chain': self.provider_coin_id,
            'difficulty': round(float(latest_block['difficulty'])),
            'hashrate': round(float(info['hashrate'])),
            'mempool_size': info['mempool']['mempool_txs'],
        }
