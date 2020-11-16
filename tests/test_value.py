# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Value Class
#    © 2020 November - 1200 Web Development <http://1200wd.com/>
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

import unittest
from bitcoinlib.value import *


class TestValue(unittest.TestCase):

    def test_value_class(self):
        self.assertEqual(str(Value(10)), '10.00000000 BTC')
        self.assertEqual(int(Value(10)), 1000000000)
        self.assertEqual(str(Value('10')), '10.00000000 BTC')
        self.assertEqual(str(Value('10 ltc')), '10.00000000 LTC')
        self.assertEqual(str(Value('10', network='litecoin')), '10.00000000 LTC')
        self.assertEqual(str(Value('10', network='dash_testnet')), '10.00000000 tDASH')
        self.assertEqual(str(Value('10 tDASH')), '10.00000000 tDASH')
        self.assertEqual(float(Value('0.001 BTC')), 100000.0)
        self.assertEqual(float(Value('1 msat')), 0.001)
        self.assertEqual(int(Value('1 BTC')), 100000000)
        self.assertEqual(str(Value('10 mBTC')), '0.01000000 BTC')
        self.assertEqual(str(Value(10, 'm')), '0.01000000 BTC')
        self.assertEqual(str(Value('10 µBTC')), '0.00001000 BTC')
        self.assertEqual(str(Value(10, 'µ')), '0.00001000 BTC')
        self.assertEqual(str(Value(10, 'sat')), '0.00000010 BTC')
        self.assertEqual(str(Value(10, 'k')), '10000.00000000 BTC')
        self.assertEqual(str(Value('10 sat')), '0.00000010 BTC')
        self.assertEqual(str(Value('10 satLTC')), '0.00000010 LTC')
        self.assertEqual(str(Value('10 sat', network='litecoin')), '0.00000010 LTC')
        self.assertEqual(str(Value('10 fliepflap')), '10.00000000 BTC')
        self.assertEqual(str(Value('10 mfliepflap')), '0.01000000 BTC')
        
    def test_value_class_str(self):
        self.assertEqual(Value(10).str(), '10.00000000 BTC')
        self.assertEqual(Value(10).str('m'), '10000.00000 mBTC')
        self.assertEqual(Value(10).str('mBTC'), '10000.00000 mBTC')
        self.assertEqual(Value(10).str('MBTC'), '0.00001000 MBTC')
        self.assertEqual(Value(0.000000123).str('sat'), '12 sat')
        self.assertEqual(Value(0.000000123).str(0.00000001), '12 sat')
        self.assertEqual(Value(0.000000123).str('n'), '123 nBTC')
        self.assertEqual(Value(0.000000123).str('nBTC'), '123 nBTC')
        self.assertEqual(Value(0.12345678901).str('mBTC'), '123.45679 mBTC')
        self.assertEqual(Value(0.12345678901).str('mBTC', decimals=8), '123.45678901 mBTC')
        self.assertEqual(Value(0.123456789016).str('mBTC', decimals=8), '123.45678902 mBTC')
        self.assertEqual(Value(0.1234567890122).str('mBTC', decimals=10), '123.4567890122 mBTC')
        self.assertEqual(Value(0.12345678901).str('mBTC', decimals=1), '123.5 mBTC')
        self.assertEqual(Value(0.000000123).str('msat'), '12300 msat')
        self.assertEqual(Value(0.000000123).str('µsat'), '12300000 µsat')
        self.assertEqual(Value(10).str('m'), '10000.00000 mBTC')
        self.assertEqual(Value(10000000000000).str('m'), '10000000000000000.00000 mBTC')
        self.assertEqual(Value(10).str(0.001), '10000.00000 mBTC')
        self.assertEqual(Value('10 kBTC').str(), '10000.00000000 BTC')
        self.assertEqual(Value('10 kLTC').str(), '10000.00000000 LTC')
        self.assertEqual(Value('0.00021 YBTC').str(), '210000000000000000000.00000000 BTC')
        self.assertEqual(Value('127127504620 Doge').str('TDoge'), '0.12712750 TDOGE')
