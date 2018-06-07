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
        variables.update({'currency': self.provider_coin_id})
        if include_raw:
            variables.update({'include_raw': None})
        return self.request(url_path, variables, method=method)

    def getbalance(self, addresslist):
        balance = 0
        for address in addresslist:
            variables = {'address': address}
            res = self.compose_request('address_balance', variables=variables)
            balance += int(res['balance'])
        return balance * self.units
