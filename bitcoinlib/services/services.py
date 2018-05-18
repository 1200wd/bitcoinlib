# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    SERVICES - Main Service connector
#    © 2017 June - 1200 Web Development <http://1200wd.com/>
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
import json
import random
from bitcoinlib.main import DEFAULT_SETTINGSDIR, CURRENT_INSTALLDIR_DATA
from bitcoinlib.networks import DEFAULT_NETWORK
from bitcoinlib import services

_logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


class Service(object):
    """
    Class to connect to various cryptocurrency service providers. Use to receive network and blockchain information,
    get specific transaction information, current network fees or push a raw transaction.

    The Service class connects to 1 or more service providers at random to retrieve or send information. When a
    certain service provider fail it automatically tries another one.

    """

    def __init__(self, network=DEFAULT_NETWORK, min_providers=1, max_providers=1, providers=None):
        """
        Open a service object for the specified network. By default the object connect to 1 service provider, but you
        can specify a list of providers or a minimum or maximum number of providers.

        :param network: Specify network used
        :type network: str
        :param min_providers: Minimum number of providers to connect to. Default is 1. Use for instance to receive
        fee information from a number of providers and calculate the average fee.
        :type min_providers: int
        :param max_providers: Maximum number of providers to connect to. Default is 1.
        :type max_providers: int
        :param providers: List of providers to connect to. Default is all providers and select a provider at random.
        :type providers: list

        """
        self.network = network
        if min_providers > max_providers:
            max_providers = min_providers
        try:
            fn = DEFAULT_SETTINGSDIR + "providers.json"
            f = open(fn, "r")
        except FileNotFoundError:
            fn = CURRENT_INSTALLDIR_DATA + "providers.json"
            f = open(fn, "r")

        try:
            self.providers_defined = json.loads(f.read())
        except json.decoder.JSONDecodeError as e:
            errstr = "Error reading provider definitions from %s: %s" % (fn, e)
            _logger.warning(errstr)
            raise ServiceError(errstr)
        f.close()

        # provider_list = list(self.providers_defined.keys())
        provider_list = list([self.providers_defined[x]['provider'] for x in self.providers_defined])
        if providers is None:
            providers = []
        for p in providers:
            if p not in provider_list:
                raise ServiceError("Provider '%s' not found in provider definitions" % p)

        self.providers = {}
        for p in self.providers_defined:
            if self.providers_defined[p]['network'] == network and \
                    (not providers or self.providers_defined[p]['provider'] in providers):
                self.providers.update({p: self.providers_defined[p]})

        if not self.providers:
            raise ServiceError("No providers found for network %s" % network)
        self.min_providers = min_providers
        self.max_providers = max_providers
        self.results = {}
        self.errors = {}
        self.resultcount = 0

    def _provider_execute(self, method, *arguments):
        self.results = {}
        self.errors = {}
        self.resultcount = 0

        provider_lst = [p[0] for p in sorted([(x, self.providers[x]['priority']) for x in self.providers],
                        key=lambda x: (x[1], random.random()), reverse=True)]

        for sp in provider_lst:
            if self.resultcount >= self.max_providers:
                break
            try:
                client = getattr(services, self.providers[sp]['provider'])
                providerclient = getattr(client, self.providers[sp]['client_class'])
                pc_instance = providerclient(self.network, self.providers[sp]['url'], self.providers[sp]['denominator'],
                                             self.providers[sp]['api_key'])
                if not hasattr(pc_instance, method):
                    continue
                providermethod = getattr(pc_instance, method)
                res = providermethod(*arguments)
                if res is False:
                    self.errors.update(
                        {sp: 'Received empty response'}
                    )
                    _logger.info("Empty response from %s when calling %s" % (sp, method))
                    continue
                self.results.update(
                    {sp: res}
                )
                self.resultcount += 1
            except Exception as e:
                if not isinstance(e, AttributeError):
                    try:
                        err = e.msg
                    except AttributeError:
                        err = e
                    self.errors.update(
                        {sp: err}
                    )
                    # -- Use this to debug specific Services errors --
                    # from pprint import pprint
                    # pprint(self.errors)
                _logger.warning("%s.%s(%s) Error %s" % (sp, method, arguments, e))

            if self.resultcount >= self.max_providers:
                break

        if not self.resultcount:
            _logger.warning("No successfull response from any serviceprovider: %s" % list(self.providers.keys()))
            return False
        return list(self.results.values())[0]

    def getbalance(self, addresslist):
        """
        Get balance for each address in addresslist provided

        :param addresslist: Address or list of addresses
        :type addresslist: list, str

        :return dict: Balance per address
        """
        if not addresslist:
            return
        if isinstance(addresslist, (str, unicode if sys.version < '3' else str)):
            addresslist = [addresslist]

        return self._provider_execute('getbalance', addresslist)

    def getutxos(self, addresslist):
        """
        Get list of unspent outputs (UTXO's) per address

        :param addresslist: Address or list of addresses
        :type addresslist: list, str

        :return dict: UTXO's per address
        """
        if not addresslist:
            return []
        if isinstance(addresslist, (str, unicode if sys.version < '3' else str)):
            addresslist = [addresslist]

        utxos = []
        while addresslist:
            res = self._provider_execute('getutxos', addresslist[:20])
            if res:
                utxos += res
            addresslist = addresslist[20:]
        return utxos

    def gettransactions(self, addresslist):
        """
        Get all transactions for each address in addresslist

        :param addresslist: Address or list of addresses
        :type addresslist: list, str

        :return list: List of Transaction objects
        """
        if not addresslist:
            return []
        if isinstance(addresslist, (str, unicode if sys.version < '3' else str)):
            addresslist = [addresslist]

        transactions = []
        addresses_per_request = 5
        while addresslist:
            res = self._provider_execute('gettransactions', addresslist[:addresses_per_request])
            if res is False:
                break
            for new_t in res:
                if new_t.hash not in [t.hash for t in transactions]:
                    transactions.append(new_t)
            addresslist = addresslist[addresses_per_request:]
        return transactions

    def gettransaction(self, txid):
        """
        Get a transaction by its transaction hash

        :param txid: Transaction identification hash
        :type txid: str

        :return Transaction: A single transaction object
        """
        return self._provider_execute('gettransaction', txid)

    def getrawtransaction(self, txid):
        """
        Get a raw transaction by its transaction hash

        :param txid: Transaction identification hash
        :type txid: str

        :return str: Raw transaction as hexstring
        """
        return self._provider_execute('getrawtransaction', txid)

    def sendrawtransaction(self, rawtx):
        """
        Push a raw transaction to the network

        :param rawtx: Raw transaction as hexstring
        :type rawtx: str

        :return dict: Send transaction result
        """
        return self._provider_execute('sendrawtransaction', rawtx)

    def estimatefee(self, blocks=3):
        """
        Estimate fee per kilobyte for a transaction for this network with expected confirmation within a certain
        amount of blocks

        :param blocks: Expection confirmation time in blocks. Default is 3.
        :type blocks: int

        :return int: Fee in smallest network denominator (satoshi)
        """
        fee = self._provider_execute('estimatefee', blocks)
        if not fee:
            raise ServiceError("Could not estimate fee. Errors: %s" % self.errors)
        return fee
