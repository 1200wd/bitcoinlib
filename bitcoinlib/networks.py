# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Network Definitions
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

import json
import binascii
import math
from bitcoinlib.main import DEFAULT_SETTINGSDIR, CURRENT_INSTALLDIR_DATA, DEFAULT_NETWORK
from bitcoinlib.encoding import to_hexstring, normalize_var


class Network:

    def __init__(self, network_name=DEFAULT_NETWORK):
        try:
            f = open(DEFAULT_SETTINGSDIR+"/networks.json", "r")
        except:
            f = open(CURRENT_INSTALLDIR_DATA + "/networks.json", "r")

        self.networks = json.loads(f.read())
        self.network_name = network_name
        self.prefix_wif = binascii.unhexlify(self.networks[network_name]['prefix_wif'])
        self.currency_code = self.networks[network_name]['currency_code']
        self.currency_symbol = self.networks[network_name]['currency_symbol']
        self.prefix_address_p2sh = binascii.unhexlify(self.networks[network_name]['prefix_address_p2sh'])
        self.prefix_address = binascii.unhexlify(self.networks[network_name]['prefix_address'])
        self.prefix_hdkey_public = binascii.unhexlify(self.networks[network_name]['prefix_hdkey_public'])
        self.description = self.networks[network_name]['description']
        self.prefix_hdkey_private = binascii.unhexlify(self.networks[network_name]['prefix_hdkey_private'])
        self.denominator = self.networks[network_name]['denominator']
        self.bip44_cointype = self.networks[network_name]['bip44_cointype']

        # This could be more shorter and more flexible with this code, but this gives 'Unresolved attributes' warnings
        # for f in list(self.networks[network_name].keys()):
        #     exec("self.%s = self.networks[network_name]['%s']" % (f, f))

    def __repr__(self):
        return "<Network: %s>" % self.network_name

    @staticmethod
    def _format_value(field, value):
        if field[:6] == 'prefix':
            return binascii.unhexlify(value)
        elif field == 'denominator':
            return float(value)
        else:
            return value

    def network_values_for(self, field, output_as='default'):
        r = [self._format_value(field, nv[field]) for nv in self.networks.values()]
        if output_as == 'default':
            return r
        elif output_as == 'str':
            return [normalize_var(i) for i in r]

    def network_by_value(self, field, value):
        value = to_hexstring(value).upper()
        return [nv for nv in self.networks if self.networks[nv][field].upper() == value]

    def network_defined(self, network):
        if network not in list(self.networks.keys()):
            return False
        return True

    def print_value(self, value):
        symb = self.networks[network]['code']
        denominator = self.networks[network]['denominator']
        denominator_size = -int(math.log10(denominator))
        balance = round(value * denominator, denominator_size)
        format_str = "%%.%df %%s" % denominator_size
        return format_str % (balance, symb)


if __name__ == '__main__':
    #
    # NETWORK EXAMPLES
    #

    network = Network('bitcoin')
    print("\n=== Get all WIF prefixes ===")
    print("WIF Prefixes: %s" % network.network_values_for('prefix_wif'))

    print("\n=== Get all HDkey private prefixes ===")
    print("HDkey private prefixes: %s" % network.network_values_for('prefix_hdkey_private', output_as='str'))

    print("\n=== Get network(s) for WIF prefix B0 ===")
    print("WIF Prefixes: %s" % network.network_by_value('prefix_wif', 'B0'))

    print("\n=== Get HD key private prefix for current network ===")
    print("self.prefix_hdkey_private: %s" % network.prefix_hdkey_private)

    print("\n=== Network parameters ===")
    for k in network.__dir__():
        if k[:1] != '_':
            v = eval('network.%s' % k)
            if not callable(v):
                print("%25s: %s" % (k, v))
                # print("self.%s = self.networks[network_name]['%s']" % (k, k))
