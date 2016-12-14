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
from bitcoinlib.config.services import serviceproviders
from bitcoinlib import services


class Service(object):

    def __init__(self, network=NETWORK_BITCOIN, max_providers=99):
        self.network = network

        # Find available providers for this network
        self.providers = [x for x in serviceproviders[network]]

    def getbalance(self, addresslist):
        if len(addresslist) == 1:
            addresslist = [addresslist]

        for provider in self.providers:
            try:
                client = getattr(services, provider)
                servicemethod = getattr(client, serviceproviders[self.network][provider][0])
                return servicemethod(network=self.network).getbalance(addresslist)
            except Exception, e:
                print("Error calling balance method of %s. Error message %s" % (provider, e))
