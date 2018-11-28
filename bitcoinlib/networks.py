# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    NETWORK class reads network definitions and with helper methods
#    © 2017 - 2018 November - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.main import *
from bitcoinlib.encoding import to_hexstring, normalize_var, change_base, to_bytes, EncodingError


_logger = logging.getLogger(__name__)


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
        f = open(fn)
    except FileNotFoundError:
        fn = CURRENT_INSTALLDIR_DATA + "/networks.json"
        f = open(fn)

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
    nws = [(nv, NETWORK_DEFINITIONS[nv]['priority'])
           for nv in NETWORK_DEFINITIONS if NETWORK_DEFINITIONS[nv][field] == value]
    if not nws:
        try:
            value = to_hexstring(value).upper()
        except TypeError:
            pass
        nws = [(nv, NETWORK_DEFINITIONS[nv]['priority'])
               for nv in NETWORK_DEFINITIONS if NETWORK_DEFINITIONS[nv][field] == value]
    return [nw[0] for nw in sorted(nws, key=lambda x: x[1], reverse=True)]


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


def prefix_search(wif, network=None):
    """
    Extract network, script type and public/private information from WIF prefix.

    :param wif: WIF string or prefix in bytes or hexadecimal string
    :type wif: str, bytes
    :param network: Limit search to specified network
    :type network: str

    :return dict:
    """

    key_hex = change_base(wif, 58, 16)
    if not key_hex:
        key_hex = to_hexstring(wif)
    prefix = key_hex[:8].upper()
    matches = []
    for nw in NETWORK_DEFINITIONS:
        if network is not None and nw != network:
            continue
        data = NETWORK_DEFINITIONS[nw]
        for pf in data['prefixes_wif']:
            if pf[1] == prefix:
                matches.append({
                    'prefix': prefix,
                    'is_private': True if pf[0] == 'private' else False,
                    'prefix_str': pf[2],
                    'network': nw,
                    'script_types': pf[3]
                })
    return matches


class Network:
    """
    Network class with all network definitions. 
    
    Prefixes for WIF, P2SH keys, HD public and private keys, addresses. A currency symbol and type, the 
    denominator (such as satoshi) and a BIP0044 cointype.
    
    """

    def __init__(self, network_name=DEFAULT_NETWORK):
        if network_name not in NETWORK_DEFINITIONS:
            raise NetworkError("Network %s not found in network definitions" % network_name)
        self.name = network_name

        self.currency_name = NETWORK_DEFINITIONS[network_name]['currency_name']
        self.currency_name_plural = NETWORK_DEFINITIONS[network_name]['currency_name_plural']
        self.currency_code = NETWORK_DEFINITIONS[network_name]['currency_code']
        self.currency_symbol = NETWORK_DEFINITIONS[network_name]['currency_symbol']
        self.description = NETWORK_DEFINITIONS[network_name]['description']
        self.prefix_address_p2sh = binascii.unhexlify(NETWORK_DEFINITIONS[network_name]['prefix_address_p2sh'])
        self.prefix_address = binascii.unhexlify(NETWORK_DEFINITIONS[network_name]['prefix_address'])
        self.prefix_bech32 = NETWORK_DEFINITIONS[network_name]['prefix_bech32']
        self.prefix_wif = binascii.unhexlify(NETWORK_DEFINITIONS[network_name]['prefix_wif'])
        self.prefix_hdkey_public = binascii.unhexlify(NETWORK_DEFINITIONS[network_name]['prefix_hdkey_public'])
        self.prefix_hdkey_private = binascii.unhexlify(NETWORK_DEFINITIONS[network_name]['prefix_hdkey_private'])
        self.denominator = NETWORK_DEFINITIONS[network_name]['denominator']
        self.bip44_cointype = NETWORK_DEFINITIONS[network_name]['bip44_cointype']
        self.dust_amount = NETWORK_DEFINITIONS[network_name]['dust_amount']
        self.fee_default = NETWORK_DEFINITIONS[network_name]['fee_default']
        self.fee_min = NETWORK_DEFINITIONS[network_name]['fee_min']
        self.fee_max = NETWORK_DEFINITIONS[network_name]['fee_max']
        self.priority = NETWORK_DEFINITIONS[network_name]['priority']
        self.prefixes_wif = NETWORK_DEFINITIONS[network_name]['prefixes_wif']

        # This could be more shorter and more flexible with this code, but this gives 'Unresolved attributes' warnings
        # for f in list(NETWORK_DEFINITIONS[network_name].keys()):
        #     exec("self.%s = NETWORK_DEFINITIONS[network_name]['%s']" % (f, f))

    def __repr__(self):
        return "<Network: %s>" % self.name

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

    def wif_prefix(self, is_private=False, witness_type='legacy', multisig=False):
        """
        Get WIF prefix for this network and specifications in arguments

        :param is_private: Private or public key, default is True
        :type is_private: bool
        :param witness_type: Legacy, segwit or p2sh-segwit
        :type witness_type: str
        :param multisig: Multisignature or single signature wallet. Default is not multisig
        :type multisig: True

        :return bytes:
        """
        script_type = script_type_default(witness_type, multisig, locking_script=True)
        if script_type == 'p2sh' and witness_type in ['p2sh-segwit', 'segwit']:
            script_type = 'p2sh_p2wsh' if multisig else 'p2sh_p2wpkh'
        if is_private:
            ip = 'private'
        else:
            ip = 'public'
        found_prefixes = [to_bytes(pf[1]) for pf in self.prefixes_wif if pf[0] == ip and script_type in pf[3]]
        if found_prefixes:
            return found_prefixes[0]
        else:
            raise NetworkError("WIF Prefix for script type %s not found" % script_type)
