# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Value class examples
#
#    © 2020 December - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.values import Value


print("A couple of ways to create a Value class with 10 bitcoins")
print(Value("10"))
print(Value("10 BTC"))
print(Value("10000 mBTC", denominator=1))
print(Value(10))
print(Value("0.01 kBTC", denominator=1))


print("\nSome ways to represent a value of 0.12 BTC")
print(Value("0.12 BTC"))
print(Value("0.12 BTC", denominator=1))
print(Value("0.12 BTC", denominator='m'))
print(Value("0.12 BTC", denominator='sat'))


print("\nWith the str() method you can format the Value as string in any format")
v = Value("512 mBTC")
print(v.str())
print(v.str(denominator=1))
print(v.str(denominator=1, decimals=3))
print(v.str(denominator='sat'))
print(v.str(denominator=0.01))  # a centi-bitcoin, not really standard, but you could use it
print(v.str(denominator=1, currency_repr='symbol'))
print(v.str(denominator=1, currency_repr='name'))

print("\nThe str_unit() is a shorter version of str(denominator=1)")
v = Value("512 mBTC")
print(v.str(denominator=1))
print(v.str_unit())

print("\nThe denominator can also be determined automatically with str(denominator='auto') or str_auto()")
print(Value('0.0000012 BTC').str_auto())
print(Value('0.0000012 BTC').str(denominator='auto'))
print(Value('0.0005 BTC').str_auto())

print("\nYou can use any arithmetic operators on Value object")
print(Value('50000 sat') == Value('5000 fin'))  # 1 Satoshi equals 10 Finney, see https://en.bitcoin.it/wiki/Units
print(Value('1 btc') > Value('2 btc'))
print(Value('1000 LTC') / 5)
print(Value('0.002 BTC') + 0.02)
print(int(Value("10.1 BTC")))
print(float(Value("10.1 BTC")))
print(round(Value("10.123 BTC"), 2).str())
print(Value("10.1 BTC"))

print("\nUnder the hood bitcoin works with values in the smallest denominator Satoshi's.")
print("\nYou can get them with the value_sat() attribute")
v = Value("512 mBTC")
print(v.value_sat)

print("When serializing transactions or scripts there is a bytes or hex version available")
print(Value('12345 sat').to_bytes())
print(Value('12345 sat').to_hex())
