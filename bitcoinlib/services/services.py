# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Main Service connector
#    © 2017 March - 1200 Web Development <http://1200wd.com/>
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
import logging
from bitcoinlib.config.networks import NETWORK_BITCOIN
from bitcoinlib.config.services import serviceproviders
from bitcoinlib import services

_logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


class Service(object):

    def __init__(self, network=NETWORK_BITCOIN, min_providers=1, max_providers=5):
        self.network = network

        # Find available providers for this network
        self.providers = [x for x in serviceproviders[network]]
        self.min_providers = min_providers
        self.max_providers = max_providers
        self.results = []
        self.errors = []
        self.resultcount = 0

    # TODO: Add preferred provider
    def _provider_execute(self, method, argument, providers=None):
        for provider in self.providers:
            if self.resultcount >= self.max_providers:
                break
            try:
                client = getattr(services, provider)
                providerclient = getattr(client, serviceproviders[self.network][provider][0])
                providermethod = getattr(providerclient(network=self.network), method)
                res = providermethod(argument)
                self.results.append(
                    {provider: res}
                )
                self.resultcount += 1
            # except services.baseclient.ClientError or AttributeError as e:
            except Exception as e:
                if not isinstance(e, AttributeError):
                    try:
                        err = e.msg
                    except Exception:
                        err = e
                    self.errors.append(
                        {provider: err}
                    )
                _logger.warning("%s.%s(%s) Error %s" % (provider, method, argument, e))

            if self.resultcount >= self.max_providers:
                break

        if not self.resultcount:
            return False
        return list(self.results[0].values())[0]

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

    def getrawtransaction(self, txid):
        return self._provider_execute('getrawtransaction', txid)

    def sendrawtransaction(self, rawtx):
        return self._provider_execute('sendrawtransaction', rawtx)

    def decoderawtransaction(self, rawtx):
        return self._provider_execute('decoderawtransaction', rawtx)


if __name__ == '__main__':
    from pprint import pprint
    # Get Balance and UTXO's for given bitcoin testnet3 addresses
    addresslst = ['mfvFzusKPZzGBAhS69AWvziRPjamtRhYpZ', 'mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2']
    srv = Service(network='testnet', min_providers=3)
    # First result only
    pprint(srv.getbalance(addresslst))
    # All results as dict
    pprint(srv.results)

    pprint(srv.getutxos(addresslst))

    # GET Raw Transaction data for given Transaction ID
    t = 'd3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955'
    print("\nGET Raw Transaction:")
    pprint(Service(network='testnet', min_providers=2).getrawtransaction(t))

    # DECODE Raw Transaction
    rt = '0100000001573ae2bb133f88cba0a96e9cf6179810a9fbdc2dc550c123b80c1ae1fc354855000000006b48304502200204f394bd46' \
         '324d677cf94768be99f5f7a0225545d1c9a1250a644873109b11022100a7e0d741705f3ea4fee169fa1b7907ecc54a26927e74f1f0' \
         'e339a824e55ee256012103e428723c145e61c35c070da86faadaf0fab21939223a5e6ce3e1cfd76bad133dffffffff02404b4c0000' \
         '0000001976a914ac19d3fd17710e6b9a331022fe92c693fdf6659588ac88e3bf0b000000001976a91463c98ad8e6b43c9b68fd81b2' \
         '02bb7266e439b1b988ac00000000'
    print("\nDECODE Raw Transaction:")
    pprint(Service(network='testnet').decoderawtransaction(rt))

    # SEND Raw Transaction data (Should give 'outputs already spent' error)
    rt = b'010000000108004b4c0394a211d4ec0d344b70bf1e3b1ce1731d11d1d30279ab0c0f6d9fd7000000006c493046022100ab18a72f7' \
         b'87e4c8ea5d2f983b99df28d27e13482b91fd6d48701c055af92f525022100d1c26b8a779896a53a026248388896501e724e46407f' \
         b'14a4a1b6478d3293da24012103e428723c145e61c35c070da86faadaf0fab21939223a5e6ce3e1cfd76bad133dffffffff0240420' \
         b'f00000000001976a914bbaeed8a02f64c9d40462d323d379b8f27ad9f1a88ac905d1818000000001976a914046858970a72d33817' \
         b'474c0e24e530d78716fc9c88ac00000000'
    print("\nSEND Raw Transaction:")
    srv = Service(network='testnet')
    if srv.sendrawtransaction(rt):
        print("Transaction send, result: ")
        pprint(srv.results)
    else:
        print("Transaction could not be send, errors:")
        pprint(srv.errors)
