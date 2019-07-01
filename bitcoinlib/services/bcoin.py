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

    def block_count(self):
        return self.compose_request('')['chain']['height']

    def gettransaction(self, tx_id):
        tx = self.compose_request('tx', tx_id)
        status = 'unconfirmed'
        if tx['confirmations']:
            status = 'confirmed'
        witness_type = 'legacy'
        # if tx['has_witness']:
        #     witness_type = 'segwit'
        # input_total = tx['input_total']
        # if tx['is_coinbase']:
        #     input_total = tx['output_total']
        # def __init__(self, inputs=None, outputs=None, locktime=0, version=1, network=DEFAULT_NETWORK,
        #              fee=None, fee_per_kb=None, size=None, hash='', date=None, confirmations=None,
        #              block_height=None, block_hash=None, input_total=0, output_total=0, rawtx='', status='new',
        #              coinbase=False, verified=False, witness_type='legacy', flag=None):
        # tx['is_coinbase']
        coinbase = False
        # tx['output_total']
        # output_total = None
        # input_total = None
        t = Transaction(locktime=tx['locktime'], version=tx['version'], network=self.network,
                        fee=tx['fee'], size=len(tx['hex']), hash=tx['hash'],
                        date=datetime.fromtimestamp(tx['mtime']),
                        confirmations=tx['confirmations'], block_height=tx['height'], block_hash=tx['block'],
                        rawtx=tx['hex'], status=status,
                        coinbase=coinbase, witness_type=witness_type)
        return t
