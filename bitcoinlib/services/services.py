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

    def __init__(self, network=NETWORK_BITCOIN, min_providers=1, max_providers=5):
        self.network = network

        # Find available providers for this network
        self.providers = [x for x in serviceproviders[network]]
        self.min_providers = min_providers
        self.max_providers = max_providers

    def getbalance(self, addresslist):
        # if not addresslist:
        #     return False
        if isinstance(addresslist, (str, unicode)):
            addresslist = [addresslist]

        provcount = 0
        provresults = []
        for provider in self.providers:
            try:
                client = getattr(services, provider)
                servicemethod = getattr(client, serviceproviders[self.network][provider][0])
                res = servicemethod(network=self.network).getbalance(addresslist)
                if self.min_providers <= 1:
                    return res
                else:
                    provresults.append(
                        {provcount: res}
                    )
            except Exception as e:
                print("Error calling balance method of %s. Error message %s" % (provider, e))

            provcount += 1
            if provcount >= self.max_providers:
                return provresults

        return provresults
