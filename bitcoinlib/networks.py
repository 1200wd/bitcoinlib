# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    NETWORK class reads network definitions and with helper methods
#    © 2017 - 2020 November - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.encoding import *


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


def _read_network_definitions():
    """
    Returns network definitions from json file in settings dir

    :return dict: Network definitions
    """

    fn = Path(BCL_DATA_DIR, 'networks.json')
    f = fn.open()

    try:
        network_definitions = json.loads(f.read())
    except json.decoder.JSONDecodeError as e:
        raise NetworkError("Error reading provider definitions from %s: %s" % (fn, e))
    f.close()
    return network_definitions


NETWORK_DEFINITIONS = _read_network_definitions()


def _format_value(field, value):
    if field[:6] == 'prefix':
        return bytes.fromhex(value)
    elif field == 'denominator':
        return float(value)
    else:
        return value


def network_values_for(field):
    """
    Return all prefixes for field, i.e.: prefix_wif, prefix_address_p2sh, etc

    >>> network_values_for('prefix_wif')
    [b'\\x99', b'\\x80', b'\\xef', b'\\xb0', b'\\xcc', b'\\x9e', b'\\xf1']
    >>> network_values_for('prefix_address_p2sh')
    [b'\\x95', b'\\x05', b'\\xc4', b'2', b':', b'\\x10', b'\\x13', b'\\x16']

    :param field: Prefix name from networks definitions (networks.json)
    :type field: str

    :return str: 
    """
    return list(dict.fromkeys([_format_value(field, nv[field]) for nv in NETWORK_DEFINITIONS.values()]))


def network_by_value(field, value):
    """
    Return all networks for field and (prefix) value.
    
    Example, get available networks for WIF or address prefix

    >>> network_by_value('prefix_wif', 'B0')
    ['litecoin', 'litecoin_legacy']
    >>> network_by_value('prefix_address', '6f')
    ['testnet', 'litecoin_testnet']

    This method does not work for HD prefixes, use 'wif_prefix_search' instead

    >>> network_by_value('prefix_address', '043587CF')
    []
    
    :param field: Prefix name from networks definitions (networks.json)
    :type field: str
    :param value: Value of network prefix
    :type value: str

    :return list: Of network name strings 
    """
    nws = [(nv, NETWORK_DEFINITIONS[nv]['priority'])
           for nv in NETWORK_DEFINITIONS if NETWORK_DEFINITIONS[nv][field] == value]
    if not nws:
        try:
            value = value.upper()
        except TypeError:
            pass
        nws = [(nv, NETWORK_DEFINITIONS[nv]['priority'])
               for nv in NETWORK_DEFINITIONS if NETWORK_DEFINITIONS[nv][field] == value]
    return [nw[0] for nw in sorted(nws, key=lambda x: x[1], reverse=True)]


def network_defined(network):
    """
    Is network defined?
    
    Networks of this library are defined in networks.json in the operating systems user path.

    >>> network_defined('bitcoin')
    True
    >>> network_defined('ethereum')
    False
    
    :param network: Network name
    :type network: str
    
    :return bool: 
    """
    if network not in list(NETWORK_DEFINITIONS.keys()):
        return False
    return True


def wif_prefix_search(wif, witness_type=None, multisig=None, network=None):
    """
    Extract network, script type and public/private information from HDKey WIF or WIF prefix.

    Example, get bitcoin 'xprv' info:

    >>> wif_prefix_search('0488ADE4', network='bitcoin', multisig=False)
    [{'prefix': '0488ADE4', 'is_private': True, 'prefix_str': 'xprv', 'network': 'bitcoin', 'witness_type': 'legacy', 'multisig': False, 'script_type': 'p2pkh'}]

    Or retreive info with full WIF string:

    >>> wif_prefix_search('xprv9wTYmMFdV23N21MM6dLNavSQV7Sj7meSPXx6AV5eTdqqGLjycVjb115Ec5LgRAXscPZgy5G4jQ9csyyZLN3PZLxoM1h3BoPuEJzsgeypdKj', network='bitcoin', multisig=False)
    [{'prefix': '0488ADE4', 'is_private': True, 'prefix_str': 'xprv', 'network': 'bitcoin', 'witness_type': 'legacy', 'multisig': False, 'script_type': 'p2pkh'}]

    Can return multiple items if no network is specified:

    >>> [nw['network'] for nw in wif_prefix_search('0488ADE4', multisig=True)]
    ['bitcoin', 'regtest', 'dash', 'dogecoin']

    :param wif: WIF string or prefix as hexadecimal string
    :type wif: str
    :param witness_type: Limit search to specific witness type
    :type witness_type: str
    :param multisig: Limit search to multisig: false, true or None for both. Default is both
    :type multisig: bool
    :param network: Limit search to specified network
    :type network: str

    :return dict:
    """

    key_hex = wif
    if len(wif) > 8:
        try:
            key_hex = change_base(wif, 58, 16)
        except Exception:
            pass
    prefix = key_hex[:8].upper()
    matches = []
    for nw in NETWORK_DEFINITIONS:
        if network is not None and nw != network:
            continue
        data = NETWORK_DEFINITIONS[nw]
        for pf in data['prefixes_wif']:
            if pf[0] == prefix and (multisig is None or pf[3] is None or pf[3] == multisig) and \
                    (witness_type is None or pf[4] is None or pf[4] == witness_type):
                matches.append({
                    'prefix': prefix,
                    'is_private': True if pf[2] == 'private' else False,
                    'prefix_str': pf[1],
                    'network': nw,
                    'witness_type': pf[4],
                    'multisig': pf[3],
                    'script_type': pf[5]
                })
    return matches


# Replaced by Value class
@deprecated
def print_value(value, network=DEFAULT_NETWORK, rep='string', denominator=1, decimals=None):
    """
    Return the value as string with currency symbol

    Wrapper for the Network().print_value method.

    :param value: Value in smallest denominator such as Satoshi
    :type value: int, float
    :param network: Network name as string, default is 'bitcoin'
    :type network: str
    :param rep: Currency representation: 'string', 'symbol', 'none' or your own custom name
    :type rep: str
    :param denominator: Unit to use in representation. Default is 1. I.e. 1 = 1 BTC, 0.001 = milli BTC / mBTC, 1e-8 = Satoshi's
    :type denominator: float
    :param decimals: Number of digits after the decimal point, leave empty for automatic determination based on value. Use integer value between 0 and 8
    :type decimals: int

    :return str:
    """
    return Network(network_name=network).print_value(value, rep, denominator, decimals)


class Network(object):
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
        self.prefix_address_p2sh = bytes.fromhex(NETWORK_DEFINITIONS[network_name]['prefix_address_p2sh'])
        self.prefix_address = bytes.fromhex(NETWORK_DEFINITIONS[network_name]['prefix_address'])
        self.prefix_bech32 = NETWORK_DEFINITIONS[network_name]['prefix_bech32']
        self.prefix_wif = bytes.fromhex(NETWORK_DEFINITIONS[network_name]['prefix_wif'])
        self.denominator = NETWORK_DEFINITIONS[network_name]['denominator']
        self.bip44_cointype = NETWORK_DEFINITIONS[network_name]['bip44_cointype']
        self.dust_amount = NETWORK_DEFINITIONS[network_name]['dust_amount']  # Dust amount in satoshi
        self.fee_default = NETWORK_DEFINITIONS[network_name]['fee_default']  # Default fee in satoshi per kilobyte
        self.fee_min = NETWORK_DEFINITIONS[network_name]['fee_min']  # Minimum transaction fee in satoshi per kilobyte
        self.fee_max = NETWORK_DEFINITIONS[network_name]['fee_max']  # Maximum transaction fee in satoshi per kilobyte
        self.priority = NETWORK_DEFINITIONS[network_name]['priority']
        self.prefixes_wif = NETWORK_DEFINITIONS[network_name]['prefixes_wif']

        # This could be more shorter and more flexible with this code, but this gives 'Unresolved attributes' warnings
        # for f in list(NETWORK_DEFINITIONS[network_name].keys()):
        #     exec("self.%s = NETWORK_DEFINITIONS[network_name]['%s']" % (f, f))

    def __repr__(self):
        return "<Network: %s>" % self.name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    # Replaced by Value class
    @deprecated
    def print_value(self, value, rep='string', denominator=1, decimals=None):
        """
        Return the value as string with currency symbol

        Print value for 100000 satoshi as string in human readable format

        >>> Network('bitcoin').print_value(100000)
        '0.00100000 BTC'

        :param value: Value in smallest denominator such as Satoshi
        :type value: int, float
        :param rep: Currency representation: 'string', 'symbol', 'none' or your own custom name
        :type rep: str
        :param denominator: Unit to use in representation. Default is 1. I.e. 1 = 1 BTC, 0.001 = milli BTC / mBTC
        :type denominator: float
        :param decimals: Number of digits after the decimal point, leave empty for automatic determination based on value. Use integer value between 0 and 8
        :type decimals: int

        :return str: 
        """
        if denominator not in NETWORK_DENOMINATORS:
            raise NetworkError("Denominator not found in definitions, use one of the following values: %s" %
                               NETWORK_DENOMINATORS.keys())
        if value is None:
            return ""
        symb = rep
        if rep == 'string':
            symb = NETWORK_DENOMINATORS[denominator] + self.currency_code
        elif rep == 'symbol':
            symb = NETWORK_DENOMINATORS[denominator] + self.currency_symbol
        elif rep == 'none':
            symb = ''
        decimals = decimals if decimals is not None else -int(math.log10(self.denominator / denominator))
        decimals = 0 if decimals < 0 else decimals
        decimals = 8 if decimals > 8 else decimals
        balance = round(float(value) * self.denominator / denominator, decimals)
        format_str = "%%.%df %%s" % decimals
        return (format_str % (balance, symb)).rstrip()

    def wif_prefix(self, is_private=False, witness_type='legacy', multisig=False):
        """
        Get WIF prefix for this network and specifications in arguments

        >>> Network('bitcoin').wif_prefix()  # xpub
        b'\\x04\\x88\\xb2\\x1e'
        >>> Network('bitcoin').wif_prefix(is_private=True, witness_type='segwit', multisig=True)  # Zprv
        b'\\x02\\xaaz\\x99'

        :param is_private: Private or public key, default is True
        :type is_private: bool
        :param witness_type: Legacy, segwit or p2sh-segwit
        :type witness_type: str
        :param multisig: Multisignature or single signature wallet. Default is False: no multisig
        :type multisig: bool

        :return bytes:
        """
        script_type = script_type_default(witness_type, multisig, locking_script=True)
        if script_type == 'p2sh' and witness_type in ['p2sh-segwit', 'segwit']:
            script_type = 'p2sh_p2wsh' if multisig else 'p2sh_p2wpkh'
        if is_private:
            ip = 'private'
        else:
            ip = 'public'
        found_prefixes = [bytes.fromhex(pf[0]) for pf in self.prefixes_wif if pf[2] == ip and script_type == pf[5]]
        if found_prefixes:
            return found_prefixes[0]
        else:
            raise NetworkError("WIF Prefix for script type %s not found" % script_type)
