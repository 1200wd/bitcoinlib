# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    VALUE - representing cryptocurrency values
#    © 2020 October - 1200 Web Development <http://1200wd.com/>
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

from bitcoinlib.networks import *


class Value:

    def __init__(self, value, network=None):
        self.network = network
        self.value = value
        if isinstance(value, str):
            value, cur = value.split()
            self.value = float(value)
            network_names = [n for n in NETWORK_DEFINITIONS if
                             NETWORK_DEFINITIONS[n]['currency_code'] == cur.upper()]
            if network_names:
                self.network = Network(network_names[0])

        if not self.network:
            self.network = DEFAULT_NETWORK

        if not isinstance(self.network, Network):
            self.network = Network(network)

    def __str__(self):
        return self.str()

    def str(self):
        symb = self.network.currency_code
        denominator = self.network.denominator
        denominator_size = -int(math.log10(denominator))
        balance = round(self.value * denominator, denominator_size)
        format_str = "%%.%df %%s" % denominator_size
        return format_str % (balance, symb)

