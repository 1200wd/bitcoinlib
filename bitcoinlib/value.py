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

    def __init__(self, value, symbol=None, denominator=1, network=DEFAULT_NETWORK):
        self.network = network
        if not isinstance(network, Network):
            self.network = Network(network)
        self.symbol = symbol
        self.denominator = denominator if denominator else self.network.denominator
        if not isinstance(value, str):
            dens = [den for den, symb in NETWORK_DENOMINATORS.items() if symb == symbol]
            if dens:
                self.denominator = dens[0]
            self.value = float(value) * (self.denominator / self.network.denominator)
        else:
            value_items = value.split()
            value = value_items[0]
            cur_code = self.network.currency_code
            if len(value_items) > 1:
                cur_code = value_items[1]
            network_names = [n for n in NETWORK_DEFINITIONS if
                             NETWORK_DEFINITIONS[n]['currency_code'].upper() == cur_code.upper()]
            denominator = 1
            if network_names:
                self.network = Network(network_names[0])
                self.currency = cur_code
            else:
                for den, symb in NETWORK_DENOMINATORS.items():
                    if len(symb) and cur_code[:len(symb)] == symb:
                        cur_code = cur_code[len(symb):]
                        network_names = [n for n in NETWORK_DEFINITIONS if
                                         NETWORK_DEFINITIONS[n]['currency_code'].upper() == cur_code.upper()]
                        if network_names:
                            self.network = Network(network_names[0])
                            self.currency = cur_code
                        denominator = den
                        break
            self.value = float(value) * (denominator / self.network.denominator)

    def __str__(self):
        return self.str()

    def str(self, denominator=None, decimals=None):
        if denominator is None:
            denominator = 1
        elif isinstance(denominator, str):
            dens = [den for den, symb in NETWORK_DENOMINATORS.items() if symb == denominator[:len(symb)] and len(symb)]
            if len(dens) > 1:
                dens = [den for den, symb in NETWORK_DENOMINATORS.items() if symb == denominator]
            if dens:
                denominator = dens[0]
        if denominator in NETWORK_DENOMINATORS:
            den_symb = NETWORK_DENOMINATORS[denominator]
        else:
            raise ValueError("Denominator not found in NETWORK_DENOMINATORS definition")

        if decimals is None:
            decimals = -int(math.log10(self.network.denominator / denominator))
            if decimals > 8:
                decimals = 8
        if decimals < 0:
            decimals = 0
        balance = round(self.value * (self.network.denominator / denominator), decimals)
        cur_code = self.network.currency_code
        if 'sat' in den_symb and self.network.name == 'bitcoin':
            cur_code = ''
        return ("%%.%df %%s%%s" % decimals) % (balance, den_symb, cur_code)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return self.value