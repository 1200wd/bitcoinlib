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
    """
    Class to represent and convert cryptocurrency values
    """

    def __init__(self, value, denominator=1, network=DEFAULT_NETWORK):
        """
        Create a new Value class.

        >>> Value(10).str()
        '0.00000010 BTC'

        >>> Value('10 sat').str()
        '0.00000010 BTC'

        >>> Value('1 BTC').str()
        '1.00000000 BTC'

        >>> Value('1 doge').str()
        '1.00000000 DOGE'

        >>> Value(10).str()
        '0.00000010 BTC'

        >>> Value(500000).str('mBTC')
        '5.00000 mBTC'

        :param value: Value as integer, float or string. Numeric values must be supllied in smallest denominator such as Satoshi's. String values must be in the format: <value> [<denominator>][<currency_symbol>]
        :type value: int, float, str
        :param symbol: Denominator symbol, such as m=milli, k=kilo, etc. See NETWORK_DENOMINATORS for list of available denominator symbols.
        :param denominator:
        :param network:
        """
        self.network = network
        if not isinstance(network, Network):
            self.network = Network(network)
        if isinstance(denominator, str):
            dens = [den for den, symb in NETWORK_DENOMINATORS.items() if symb == denominator]
            if dens:
                denominator = dens[0]
        self.denominator = denominator if denominator else 1

        if isinstance(value, str):
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
                        elif len(cur_code):
                            raise ValueError("Currency symbol not recognised")
                        self.denominator = den
                        break
            self.value = float(value) * self.denominator
        else:
            self.value = float(value) * self.denominator

    def __str__(self):
        return self.str()

    def __repr__(self):
        if self.value:
            return "Value(value=%d, denominator=%.8f, network='%s')" % \
                   (int(self.value), self.denominator, self.network.name)
        else:
            return "Value()"

    def str(self, denominator=None, decimals=None):
        if denominator is None:
            denominator = self.denominator
        elif denominator == 'auto':
            for den, symb in NETWORK_DENOMINATORS.items():
                if symb in ['n', 'fin', 'da', 'c', 'd', 'h']:
                    continue
                if 1 <= self.value / den < 1000:
                    denominator = den
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
        balance = round(self.value / denominator, decimals)
        cur_code = self.network.currency_code
        if 'sat' in den_symb and self.network.name == 'bitcoin':
            cur_code = ''
        return ("%%.%df %%s%%s" % decimals) % (balance, den_symb, cur_code)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        if self.value > self.network.denominator:
            return round(self.value, -int(math.log10(self.network.denominator)))
        else:
            return self.value

    def __lt__(self, other):
        if self.network != other.network:
            raise ValueError("Cannot compare values from different networks")
        return self.value < other.value

    def __le__(self, other):
        if self.network != other.network:
            raise ValueError("Cannot compare values from different networks")
        return self.value <= other.value

    def __eq__(self, other):
        if self.network != other.network:
            raise ValueError("Cannot compare values from different networks")
        return self.value == other.value

    def __ne__(self, other):
        if self.network != other.network:
            raise ValueError("Cannot compare values from different networks")
        return self.value != other.value

    def __ge__(self, other):
        if self.network != other.network:
            raise ValueError("Cannot compare values from different networks")
        return self.value >= other.value

    def __gt__(self, other):
        if self.network != other.network:
            raise ValueError("Cannot compare values from different networks")
        return self.value > other.value

    def __add__(self, other):
        if isinstance(other, Value):
            if self.network != other.network:
                raise ValueError("Cannot calculate with values from different networks")
            other = other.value
        return Value(self.value + other, self.denominator, self.network)

    def __iadd__(self, other):
        if isinstance(other, Value):
            if self.network != other.network:
                raise ValueError("Cannot calculate with values from different networks")
            other = other.value
        return Value(self.value + other, self.denominator, self.network)

    def __isub__(self, other):
        if isinstance(other, Value):
            if self.network != other.network:
                raise ValueError("Cannot calculate with values from different networks")
            other = other.value
        return Value(self.value - other, self.denominator, self.network)

    def __sub__(self, other):
        if isinstance(other, Value):
            if self.network != other.network:
                raise ValueError("Cannot calculate with values from different networks")
            other = other.value
        return Value(self.value - other, self.denominator, self.network)

    def __mul__(self, other):
        return Value(self.value * other, self.denominator, self.network)

    def __truediv__(self, other):
        return Value(self.value / other, self.denominator, self.network)

    def __floordiv__(self, other):
        return Value(((self.value / self.denominator) // other) * self.denominator, self.denominator, self.network)

    def __round__(self, n=0):
        val = round(self.value / self.denominator, n) * self.denominator
        return Value(val, self.denominator, self.network)

    def __index__(self):
        return int(self)

    @property
    def value_sat(self):
        return int(self.value / self.network.denominator)

    def to_bytes(self, length, byteorder='big'):
        return self.value_sat.to_bytes(length, byteorder)

    def to_hex(self, length, byteorder='big'):
        return self.value_sat.to_bytes(length // 2, byteorder).hex()

