# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Main Service connector
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

import sys
from bitcoinlib.config.networks import NETWORK_BITCOIN
from bitcoinlib.config.services import serviceproviders
from bitcoinlib import services


class ServiceError(Exception):
    pass


class Service(object):

    def __init__(self, network=NETWORK_BITCOIN, min_providers=1, max_providers=5):
        self.network = network

        # Find available providers for this network
        self.providers = [x for x in serviceproviders[network]]
        self.min_providers = min_providers
        self.max_providers = max_providers

    def _provider_execute(self, method, argument):
        provcount = 0
        provresults = []
        for provider in self.providers:
            try:
                client = getattr(services, provider)
                providerclient = getattr(client, serviceproviders[self.network][provider][0])
                providermethod = getattr(providerclient(network=self.network), method)
                res = providermethod(argument)
                if self.min_providers <= 1:
                    return res
                else:
                    provresults.append(
                        {provider: res}
                    )
                    provcount += 1
            # except services.baseclient.ClientError or AttributeError as e:
            except Exception as e:
                print(e)
                # pass

            if provcount >= self.max_providers:
                return provresults

        if not provcount:
            raise ServiceError("No valid service provider found")

        return provresults

    def getbalance(self, addresslist):
        if not addresslist:
            return
        if isinstance(addresslist, (str, unicode if sys.version < '3' else str)):
            addresslist = [addresslist]

        return self._provider_execute('getbalance', addresslist)

    def getutxos(self, addresslist):
        if not addresslist:
            return
        if isinstance(addresslist, (str, unicode if sys.version < '3' else str)):
            addresslist = [addresslist]

        return self._provider_execute('utxos', addresslist)


if __name__ == '__main__':
    addresslst = ['n3UKaXBRDhTVpkvgRH7eARZFsYE989bHjw', 'mvA148DL7EFtWxM3VoZjRVcpg2f1VDJadq']
    print(Service(network='testnet', min_providers=3).getbalance(addresslst))
    from pprint import pprint
    pprint(Service(network='testnet', min_providers=3).getutxos(addresslst))
