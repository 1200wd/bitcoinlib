# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Litecore.io Client
#    © 2018 June - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction

PROVIDERNAME = 'multiexplorer'


class MultiexplorerClient(BaseClient):

    def __init__(self, network, base_url, denominator, *args):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def compose_request(self, func, variables, service_id='fallback', include_raw=False, method='get'):
        url_path = func + '/' + service_id
        if not isinstance(variables, dict):
            raise ClientError("Cannot compose request without variables. Variables must be of type dictionary.")
        if method =='get':
            variables.update({'currency': self.provider_coin_id})
        else:
            url_path += '?currency=%s' % self.provider_coin_id
        if include_raw:
            variables.update({'include_raw': None})
        return self.request(url_path, variables, method=method)

    # Disabled: returns different denominated values
    # def getbalance(self, addresslist):
    #     balance = 0
    #     for address in addresslist:
    #         variables = {'address': address}
    #         res = self.compose_request('address_balance', variables=variables)
    #         balance += res['balance']
    #     return int(balance)

    # def getutxos(self, addresslist):
    #     txs = []
    #     for address in addresslist:
    #         variables = {'address': address}
    #         res = self.compose_request('unspent_outputs', variables=variables)
    #         for tx in res['utxos']:
    #             txs.append({
    #                 'address': address,
    #                 'tx_hash': tx['txid'],
    #                 'confirmations': tx['confirmations'],
    #                 'output_n': tx['vout'],
    #                 'input_n': None,
    #                 'block_height': None,
    #                 'fee': None,
    #                 'size': 0,
    #                 'value': tx['amount'],
    #                 'script': tx['scriptPubKey'],
    #                 'date': None,
    #             })
    #     return txs

    # def gettransaction(self, tx_id):
    #     variables = {'txid': tx_id, 'include_raw': 'true'}
    #     res = self.compose_request('single_transaction', variables=variables)
    #     tx = res['transaction']
    #     if tx['confirmations']:
    #         status = 'confirmed'
    #     else:
    #         status = 'unconfirmed'
    #     isCoinbase = False
    #     if 'isCoinBase' in tx and tx['isCoinBase']:
    #         tx['total_in'] = tx['valueOut']
    #         isCoinbase = True
    #     blockdate = datetime.strptime(tx['time'], "%Y-%m-%dT%H:%M:%S.%f+00:00")
    #     t = Transaction(network=self.network, fee=tx['fee'], size=tx['size'], hash=tx['txid'],
    #                     date=blockdate, confirmations=int(tx['confirmations']),
    #                     block_height=tx['block_number'], block_hash=tx['block_hash'], status=status,
    #                     input_total=tx['total_in'], coinbase=isCoinbase)
    #     for ti in tx['inputs']:
    #         if isCoinbase:
    #             t.add_input(prev_hash=32 * b'\0', output_n=4*b'\xff', unlocking_script=ti['coinbase'], index_n=ti['n'],
    #                         script_type='coinbase')
    #         else:
    #             t.add_input(prev_hash=ti['txid'])  #  missing info ...
    #     for to in tx['vout']:
    #         value = int(round(float(to['value']) * self.units, 0))
    #         address = ''
    #         try:
    #             address = to['scriptPubKey']['addresses'][0]
    #         except ValueError:
    #             pass
    #         t.add_output(value=value, address=address, lock_script=to['scriptPubKey']['hex'],
    #                      spent=True if to['spentTxId'] else False, output_n=to['n'])
    #     return t

    # https://multiexplorer.com/api/historical_transactions/fallback/?address=123Nc1QiMbJT7RuvsEwNoopmkYi47M2SDX&extended_fetch=true¤cy=btc&fiat=usd
    # def gettransactions(self, addresslist):
    #     txs = []
    #     input_total = 0
    #     for address in addresslist:
    #         variables = {'address': address, 'extended_fetch': True}
    #         tx = self.compose_request('historical_transactions', variables=variables, service_id='private3')
    #         t = Transaction.import_raw(tx['hex'])
    #         for n, i in enumerate(t.inputs):
    #             i.value = tx['inputs'][n]['amount']
    #             input_total += i.value
    #         # for n, o in enumerate(t.outputs):
    #         #     o.spent = tx['out'][n]['spent']
    #         txs.append(t)
    #     return txs

    # FIXME: Not working, receive 500 errors
    # def sendrawtransaction(self, rawtx):
    #     variables = {'tx': rawtx}
    #     res = self.compose_request('push_tx', service_id='average4', variables=variables, method='post')
    #     return {
    #         'txid': res['txid'],
    #         'response_dict': res
    #     }
