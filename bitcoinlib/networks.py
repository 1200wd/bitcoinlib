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
from bitcoinlib.main import DEFAULT_SETTINGSDIR, CURRENT_INSTALLDIR_DATA


class Networks:

    def __init__(self, name='bitcoin'):
        try:
            f = open(DEFAULT_SETTINGSDIR+"/networks.json", "r")
        except:
            f = open(CURRENT_INSTALLDIR_DATA + "/networks.json", "r")
        self.networks = json.loads(f.read())
        self.name = name
        self.keys_network = list(self.networks[name].keys())

    def values_for(self, field):
        return [nv[field] for nv in self.networks.values()]

    def network_by_value(self, field, value):
        return [nv for nv in self.networks if self.networks[nv][field] == value]

    def network_defined(self, network):
        if network not in list(self.networks.keys()):
            return False
        return True

    def __getattr__(self, attr):
        if attr in self.keys_network:
            r = self.networks[self.name][attr]
            if attr in ['address', 'address_p2sh', 'wif', 'hdkey_public', 'hdkey_private']:
                return binascii.unhexlify(r)
            else:
                return r
        else:
            raise ValueError("This class has no '%s' attribute" % attr)

    def print_value(self, value):
        symb = self.networks[network]['code']
        denominator = float(self.networks[network]['denominator'])
        denominator_size = -int(math.log10(denominator))
        balance = round(value * denominator, denominator_size)
        format_str = "%%.%df %%s" % denominator_size
        return format_str % (balance, symb)


if __name__ == '__main__':
    #
    # NETWORK EXAMPLES
    #

    network = Networks('bitcoin')
    print("\n=== Get all WIF prefixes ===")
    print("WIF Prefixes: %s" % network.values_for('wif'))

    print("\n=== Get network(s) for WIF prefix B0 ===")
    print("WIF Prefixes: %s" % network.network_by_value('wif', 'B0'))

    print("\n=== Bitcoin network parameters ===")
    for k in network.keys_network:
        print("%25s: %s" % (k, eval("network.%s" % k)))
