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
from bitcoinlib.config.config import NETWORK_DENOMINATORS


class Value:

    def __init__(self, value, symbol=None, currency=None, denominator=1, network=DEFAULT_NETWORK):
        self.network = network
        if not isinstance(network, Network):
            self.network = Network(network)
        self.symbol = symbol
        self.currency = currency if currency else self.network.currency_name
        self.denominator = denominator if denominator else self.network.denominator
        if not isinstance(value, str):
            dens = [den for den, symb in NETWORK_DENOMINATORS.items() if symb == symbol]
            if dens:
                self.denominator = dens[0]
            self.value = float(value) * (self.denominator / self.network.denominator)
        else:
            value_items = value.split()
            value = value_items[0]
            cur = self.currency
            if len(value_items) > 1:
                cur = value_items[1]
            network_names = [n for n in NETWORK_DEFINITIONS if
                             NETWORK_DEFINITIONS[n]['currency_code'] == cur.upper()]
            denominator = 1
            if network_names:
                self.network = Network(network_names[0])
                self.currency = cur
            else:
                for den, symb in NETWORK_DENOMINATORS.items():
                    if len(symb) and cur[:len(symb)] == symb:
                        cur = self.currency[len(symb):]
                        network_names = [n for n in NETWORK_DEFINITIONS if
                                         NETWORK_DEFINITIONS[n]['currency_code'] == cur.upper()]
                        if network_names:
                            self.network = Network(network_names[0])
                            self.currency = cur
                        denominator = den
                        break
            self.value = float(value) * (denominator / self.network.denominator)

    def __str__(self):
        return self.str()

    def str(self, symbol=None):
        symb = self.network.currency_code
        denominator = self.network.denominator
        denominator_size = -int(math.log10(denominator))
        balance = round(self.value * denominator, denominator_size)
        format_str = "%%.%df %%s" % denominator_size
        return format_str % (balance, symb)

