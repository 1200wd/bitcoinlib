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

from bitcoinlib.config.networks import NETWORK_BITCOIN
from bitcoinlib.services.blockexplorer import BlockExplorerClient
from bitcoinlib import services


# name,network_name,base_url,api_key
# blockexplorer,bitcoin,https://blockexplorer.com/api/,
# blockexplorer.testnet,testnet,https://testnet.blockexplorer.com/api/,
# blockexplorer.litecoin,litecoin,https://testnet.blockexplorer.com/api/,

serviceproviders = {
    'bitcoin': {
        'blockexplorer': ('BlockExplorerClient', 'https://blockexplorer.com/api/'),
    },
    'testnet': {
        'blockexplorer': ('BlockExplorerClient', 'https://testnet.blockexplorer.com/api/'),
    },
    'litecoin': {
        'blockr': ('BlockrClient', 'http://btc.blockr.io/api/v1/'),
    }
}


class Service(object):

    def __init__(self, network=NETWORK_BITCOIN, max_providers=99):
        self.network = network

        # Find available providers for this network
        self.providers = ['blockexplorer']

    def getbalance(self, addresslist):
        if len(addresslist) == 1:
            addresslist = [addresslist]

        for provider in self.providers:
            client = getattr(services, provider)
            servicemethod = getattr(client, serviceproviders[self.network][provider][0])
            return servicemethod(network=self.network).getbalances(addresslist)
