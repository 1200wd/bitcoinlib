# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Client for Bcoin Node
#    © 2019 June - 1200 Web Development <http://1200wd.com/>
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

from datetime import datetime
import struct
from requests import ReadTimeout
from bitcoinlib.main import *
from bitcoinlib.services.authproxy import AuthServiceProxy
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction
from bitcoinlib.encoding import to_hexstring
from bitcoinlib.networks import Network


PROVIDERNAME = 'bcoin'

_logger = logging.getLogger(__name__)


class BcoinClient(BaseClient):
    """
    Class to interact with Bcoin API
    """

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, func, data='', parameter='', variables=None, method='get'):
        url_path = func
        if data:
            url_path += '/' + data
        if parameter:
            url_path += '/' + parameter
        if variables is None:
            variables = {}
        return self.request(url_path, variables, method, secure=False)

    def estimatefee(self, blocks):
        fee = self.compose_request('fee')['rate']
        if not fee:
            return False
        return fee

    def _parse_transaction(self, tx):
        status = 'unconfirmed'
        if tx['confirmations']:
            status = 'confirmed'
        # TODO: Segwit
        witness_type = 'legacy'
        coinbase = False
        if tx['inputs'][0]['prevout']['hash'] == '00' * 32:
            coinbase = True
        t = Transaction(locktime=tx['locktime'], version=tx['version'], network=self.network,
                        fee=tx['fee'], size=len(tx['hex']), hash=tx['hash'], date=datetime.fromtimestamp(tx['mtime']),
                        confirmations=tx['confirmations'], block_height=tx['height'], block_hash=tx['block'],
                        rawtx=tx['hex'], status=status, coinbase=coinbase, witness_type=witness_type)
        for ti in tx['inputs']:
            witness_type = 'legacy'
            if ti['witness'] != '00':
                witness_type = 'segwit'
            address = None
            value = 0
            if 'coin' in ti:
                address = ti['coin']['address']
                value = ti['coin']['value']
            t.add_input(prev_hash=ti['prevout']['hash'], output_n=ti['prevout']['index'],
                        unlocking_script=ti['script'], address=address, value=value,
                        witness_type=witness_type, sequence=ti['sequence'])
        output_n = 0
        for to in tx['outputs']:
            # spent = self.isspent(tx['hash'], output_n)
            t.add_output(value=to['value'], address=to['address'], lock_script=to['script'],
                         output_n=output_n, spent=None)
            output_n += 1
        return t

    def gettransaction(self, txid):
        tx = self.compose_request('tx', txid)
        return self._parse_transaction(tx)

    # def isspent(self, tx_id, index):
    #     try:
    #         self.compose_request('coin', tx_id, str(index))
    #     except ClientError:
    #         return True
    #     return False

    def gettransactions(self, addresslist):
        txs = []
        limit = 20
        last_txid = ''
        for address in addresslist:
            address_txs = []
            while True:
                variables = {'limit': limit, 'after': last_txid}
                retries = 0
                while retries < 3:
                    try:
                        res = self.compose_request('tx', 'address', address, variables)
                    except ReadTimeout as e:
                        _logger.warning("Bcoin client error: %s" % e)
                        retries += 1
                    except Exception as e:
                        pass
                    else:
                        break
                    finally:
                        if retries == 3:
                            raise ClientError("Max retries exceeded with bcoin Client")
                for tx in res:
                    address_txs.append(self._parse_transaction(tx))
                if len(res) == limit:
                    last_txid = res[limit-1]['hash']
                else:
                    break

            # Check which outputs are spent/unspent for this address
            address_inputs = [(to_hexstring(inp.prev_hash), inp.output_n_int) for ti in
                              [t.inputs for t in address_txs] for inp in ti if inp.address == address]
            for tx in address_txs:
                for to in tx.outputs:
                    if to.address != address:
                        continue
                    spent = True if (tx.hash, to.output_n) in address_inputs else False
                    address_txs[address_txs.index(tx)].outputs[to.output_n].spent = spent
            txs += address_txs
        return txs

    def getrawtransaction(self, txid):
        return self.compose_request('tx', txid)['hex']

    def sendrawtransaction(self, rawtx):
        res = self.compose_request('broadcast', variables={'tx': rawtx}, method='post')
        txid = ''
        if 'success' in res and res['success'] == 'true':
            t = Transaction.import_raw(rawtx)
            txid = t.hash
        return {
            'txid': txid,
            'response_dict': res
        }

    # def getutxos(self, addresslist):

    # def getbalance(self, addresslist):
    #     balance = 0.0
    #     for address in addresslist:
    #         res = tx = self.compose_request('address', address)
    #         balance += int(res['balance'])
    #     return int(balance * self.units)

    def block_count(self):
        return self.compose_request('')['chain']['height']
