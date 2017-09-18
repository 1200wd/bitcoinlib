# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Network class
#
#    © 2017 September - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.networks import *

#
# Network examples
#

network = Network('bitcoin')
print("\n=== Get all WIF prefixes ===")
print("WIF Prefixes: %s" % network_values_for('prefix_wif'))

print("\n=== Get all HDkey private prefixes ===")
print("HDkey private prefixes: %s" % network_values_for('prefix_hdkey_private', output_as='str'))

print("\n=== Get network(s) for WIF prefix B0 ===")
print("WIF Prefixes: %s" % network_by_value('prefix_wif', 'B0'))

print("\n=== Get HD key private prefix for current network ===")
print("self.prefix_hdkey_private: %s" % network.prefix_hdkey_private)

print("\n=== Network parameters ===")
for k in network.__dir__():
    if k[:1] != '_':
        v = eval('network.%s' % k)
        if not callable(v):
            print("%25s: %s" % (k, v))
