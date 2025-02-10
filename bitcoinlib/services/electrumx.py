# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Electrumx client
#    © 2025 January - 1200 Web Development <http://1200wd.com/>
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
import socket
import sys
try:
    import aiorpcx
except ImportError:
    pass
import asyncio
from bitcoinlib.main import MAX_TRANSACTIONS
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction
from bitcoinlib.keys import Address, sha256
from bitcoinlib.scripts import Script

PROVIDERNAME = 'electrumx'


_logger = logging.getLogger(__name__)


class ElectrumxClient(BaseClient):

    def __init__(self, network, base_url, denominator, api_key, *args):
        self.aiorpcx_installed = True
        if 'aiorpcx' not in sys.modules:
            self.aiorpcx_installed = False
            _logger.warning('Aiorpcx library not installed, using sockets directly now. Please install aiorpcx library '
                            'when using ElectumX client for faster and more reliable results')
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key, *args)

    def compose_request(self, method, parameters=None):
        try:
            host, port = self.base_url.split(':')
        except ValueError:
            raise ClientError('Please specify ElectrumX uri in format host:port')
        parameters = parameters or []
        if self.aiorpcx_installed:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            if sock.connect_ex((host, int(port))) != 0:
                raise ClientError('ElectrumX server %s unavailable at port %s' % (host, port))
            sock.close()

            async def main(host, port, method, parameters):
                async with aiorpcx.connect_rs(host, port, framer=aiorpcx.NewlineFramer(5000000)) as session:
                    session.sent_request_timeout = self.timeout
                    return await session.send_request(method, parameters)

            loop = asyncio.get_event_loop()
            return loop.run_until_complete(main(host, port, method, parameters))
        else:
            content = {
                "method": method,
                "params": parameters if parameters else [],
                "id": 0
            }

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, int(port)))
            import json
            from time import sleep
            sock.sendall(json.dumps(content).encode('utf-8')+b'\n')
            sleep(0.5)
            sock.shutdown(socket.SHUT_WR)
            res = ""
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                res += data.decode()
            sock.close()

            parsed_resp = json.loads(res)
            if 'result' in parsed_resp:
                return parsed_resp['result']
            else:
                raise ClientError("Electrumx error: %s" % parsed_resp['error'])

    def _get_scripthash(self, address):
        address_obj = Address.parse(address)
        return sha256(Script(public_hash=address_obj.hash_bytes,
                                   script_types=[address_obj.script_type]).as_bytes())[::-1].hex()

    def getbalance(self, addresslist):
        balance = 0
        for address in addresslist:
            scripthash = self._get_scripthash(address)
            res = self.compose_request('blockchain.scripthash.get_balance', [scripthash])
            balance += res['confirmed'] + res['unconfirmed']
        return balance

    def getutxos(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        scripthash = self._get_scripthash(address)
        res = self.compose_request('blockchain.scripthash.listunspent', [scripthash])
        self.latest_block = self.blockcount() if not self.latest_block else self.latest_block
        utxos = []
        for u in res:
            if u['tx_hash'] == after_txid:
                utxos = []
                continue
            block_height = None if not u['height'] else u['height']
            confirmations = self.latest_block - block_height if self.latest_block else None
            utxos.append({
                'address': address,
                'txid': u['tx_hash'],
                'confirmations': confirmations,
                'output_n': u['tx_pos'],
                'input_n': 0,
                'block_height': block_height,
                'fee': None,
                'size': 0,
                'value': u['value'],
                'script': '',
                'date': None
            })
        return utxos[:limit]

    def _parse_transaction(self, tx, block_height=None, get_input_values=True):
        confirmations = tx['confirmations']
        status = 'unconfirmed'
        # FIXME: Number of confirmations returned by Electrumx is not always correct, use block database or query
        #  electrumx for correct blockheight?
        if confirmations:
            status = 'confirmed'
            self.latest_block = self.blockcount() if not self.latest_block else self.latest_block
            block_height = self.latest_block - confirmations + 1
        tx_date = None if not tx.get('blocktime') else datetime.fromtimestamp(tx['blocktime'], timezone.utc)

        rawtx = self.compose_request('blockchain.transaction.get', [tx['txid'], False])
        t = Transaction.parse_hex(rawtx, strict=self.strict, network=self.network)
        t.confirmations = confirmations
        t.status = status
        t.date = tx_date
        t.block_height = block_height
        t.rawtx = bytes.fromhex(rawtx)
        t.size = tx['size']
        t.vsize = tx['vsize']
        t.network = self.network
        for n, i in enumerate(t.inputs):
            if not t.coinbase and not i.value and get_input_values:
                # This does not work with very large transactions, increase MAX_SEND in electrumx config
                try:
                    ptx = self.compose_request('blockchain.transaction.get', [i.prev_txid.hex(), True])
                    i.value = round([x['value'] for x in ptx['vout'] if x['n'] == i.output_n_int][0]
                                / self.network.denominator)
                except:
                    pass
            t.input_total += i.value
        t.update_totals()
        return t

    def gettransaction(self, txid, block_count=None):
        tx = self.compose_request('blockchain.transaction.get', [txid, True])
        return self._parse_transaction(tx, block_count)

    def gettransactions(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        scripthash = self._get_scripthash(address)
        txids = self.compose_request('blockchain.scripthash.get_history', [scripthash])
        txids_after = []
        for tx in txids:
            txids_after.append(tx['tx_hash'])
            if tx['tx_hash'] == after_txid:
                txids_after = []

        txs = []
        for txid in txids_after[:limit]:
            txs.append(self.gettransaction(txid))

        return txs

    def getrawtransaction(self, txid):
        return self.compose_request('blockchain.transaction.get', [txid, False])

    def sendrawtransaction(self, rawtx):
        txid = self.compose_request('blockchain.transaction.broadcast', [rawtx])
        return {
            'txid': txid,
            'response_dict': txid
        }

    def estimatefee(self, blocks):
        return round(self.compose_request('blockchain.estimatefee', [blocks]) / self.network.denominator)

    def blockcount(self):
        return self.compose_request('blockchain.headers.subscribe')['height']

    def mempool(self, txid):
        if txid:
            t = self.gettransaction(txid)
            if t and not t.confirmations:
                return [t.txid]
        return []

    # Only returns headers, not full block
    # def getblock(self, blockid, parse_transactions, page, limit):
    #     braw = self.getrawblock(blockid)
    #     return Block.parse(bytes.fromhex(braw), height=blockid, parse_transactions=parse_transactions, limit=limit)

    # def getrawblock(self, blockid):
    #     res = self.compose_request('blockchain.block.header', [blockid])
    #     return res

    # def isspent(self, txid, output_n):
    #     res = self.compose_request('isspent', txid, str(output_n))
    #     return 1 if res['spent'] else 0
    #
    # def getinfo(self):
    #     res = self.compose_request('')
    #     info = {k: v for k, v in res.items() if k in ['chain', 'blockcount', 'hashrate', 'mempool_size',
    #                                                   'difficulty']}
    #     return info
