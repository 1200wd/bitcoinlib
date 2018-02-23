# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    NETWORK class reads network definitions and with helper methods
#    © 2017 April - 1200 Web Development <http://1200wd.com/>
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

import json
import binascii
import math
import logging
from bitcoinlib.main import DEFAULT_SETTINGSDIR, CURRENT_INSTALLDIR_DATA
from bitcoinlib.encoding import to_hexstring, normalize_var


_logger = logging.getLogger(__name__)


DEFAULT_NETWORK = 'bitcoin'


class NetworkError(Exception):
    """
    Network Exception class
    """
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def read_network_definitions():
    """
    Returns network definitions from json file in settings dir

    :return dict: Network definitions
    """
    try:
        fn = DEFAULT_SETTINGSDIR + "/networks.json"
        f = open(fn, "r")
    except FileNotFoundError:
        fn = CURRENT_INSTALLDIR_DATA + "/networks.json"
        f = open(fn, "r")

    try:
        network_definitions = json.loads(f.read())
    except json.decoder.JSONDecodeError as e:
        errstr = "Error reading provider definitions from %s: %s" % (fn, e)
        _logger.warning(errstr)
        raise NetworkError(errstr)
    f.close()
    return network_definitions

NETWORK_DEFINITIONS = read_network_definitions()


def _format_value(field, value):
    if field[:6] == 'prefix':
        return binascii.unhexlify(value)
    elif field == 'denominator':
        return float(value)
    else:
        return value


def network_values_for(field, output_as='default'):
    """
    Return all prefixes mentioned field, i.e.: prefix_wif, prefix_address_p2sh, prefix_hdkey_public, etc
    
    :param field: Prefix name from networks definitions (networks.json)
    :type field: str
    :param output_as: Output as string or hexstring. Default is string or hexstring depending on field type.
    :type output_as: str
    
    :return str: 
    """
    r = [_format_value(field, nv[field]) for nv in NETWORK_DEFINITIONS.values()]
    if output_as == 'str':
        return [normalize_var(i) for i in r]
    elif output_as == 'hex':
        return [to_hexstring(i) for i in r]
    else:
        return r


def network_by_value(field, value):
    """
    Return all networks for field and (prefix) value.
    
    For Example:
        network_by_value('prefix_wif', 'B0')
        
    Returns:
        ['litecoin']
    
    :param field: Prefix name from networks definitions (networks.json)
    :type field: str
    :param value: Value of network prefix
    :type value: str, bytes
    
    :return list: Of network name strings 
    """
    try:
        value = to_hexstring(value).upper()
    except:
        pass
    return [nv for nv in NETWORK_DEFINITIONS if NETWORK_DEFINITIONS[nv][field] == value]


def network_defined(network):
    """
    Is network defined?
    
    Networks of this library are defined in networks.json in the operating systems user path.
    
    :param network: Network name
    :type network: str
    
    :return bool: 
    """
    if network not in list(NETWORK_DEFINITIONS.keys()):
        return False
    return True


class Network:
    """
    Network class with all network definitions. 
    
    Prefixes for WIF, P2SH keys, HD public and private keys, addresses. A currency symbol and type, the 
    denominator (such as satoshi) and a BIP0044 cointype.
    
    """

    def __init__(self, network_name=DEFAULT_NETWORK):
        if network_name not in NETWORK_DEFINITIONS:
            raise NetworkError("Network %s not found in network definitions" % network_name)
        self.network_name = network_name
        self.prefix_wif = binascii.unhexlify(NETWORK_DEFINITIONS[network_name]['prefix_wif'])
        self.currency_name = NETWORK_DEFINITIONS[network_name]['currency_name']
        self.currency_name_plural = NETWORK_DEFINITIONS[network_name]['currency_name_plural']
        self.currency_code = NETWORK_DEFINITIONS[network_name]['currency_code']
        self.currency_symbol = NETWORK_DEFINITIONS[network_name]['currency_symbol']
        self.prefix_address_p2sh = binascii.unhexlify(NETWORK_DEFINITIONS[network_name]['prefix_address_p2sh'])
        self.prefix_address = binascii.unhexlify(NETWORK_DEFINITIONS[network_name]['prefix_address'])
        self.prefix_hdkey_public = binascii.unhexlify(NETWORK_DEFINITIONS[network_name]['prefix_hdkey_public'])
        self.description = NETWORK_DEFINITIONS[network_name]['description']
        self.prefix_hdkey_private = binascii.unhexlify(NETWORK_DEFINITIONS[network_name]['prefix_hdkey_private'])
        self.denominator = NETWORK_DEFINITIONS[network_name]['denominator']
        self.bip44_cointype = NETWORK_DEFINITIONS[network_name]['bip44_cointype']
        self.dust_amount = NETWORK_DEFINITIONS[network_name]['dust_amount']

        # This could be more shorter and more flexible with this code, but this gives 'Unresolved attributes' warnings
        # for f in list(NETWORK_DEFINITIONS[network_name].keys()):
        #     exec("self.%s = NETWORK_DEFINITIONS[network_name]['%s']" % (f, f))

    def __repr__(self):
        return "<Network: %s>" % self.network_name

    def print_value(self, value):
        """
        Return the value as string with currency symbol
        
        :param value: Value in smallest denominitor such as Satoshi
        :type value: int, float
        
        :return str: 
        """
        symb = self.currency_code
        denominator = self.denominator
        denominator_size = -int(math.log10(denominator))
        balance = round(value * denominator, denominator_size)
        format_str = "%%.%df %%s" % denominator_size
        return format_str % (balance, symb)
