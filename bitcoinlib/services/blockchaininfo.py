# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    blockchain_info client
#    © 2016 November - 1200 Web Development <http://1200wd.com/>
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


from bitcoinlib.services.baseclient import BaseClient

PROVIDERNAME = 'blockchaininfo'


class BlockchainInfoClient(BaseClient):

    def __init__(self, network):
        super(self.__class__, self).__init__(network, PROVIDERNAME)

    def request(self, method, parameter, variables=None):
        if parameter:
            parameter += '/'
        url = self.url + method + parameter
        return super(BlockchainInfoClient, self).request(url, variables)

    def getbalance(self, addresslist):
        parlist = [('active', 'o'.join(addresslist))]
        res = self.request('multiaddr', '', parlist)
        balance = 0
        for address in res['addresses']:
            balance += address['final_balance']

        return balance
