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

from bitcoinlib.db import *

NETWORK_BITCOIN = 'bitcoin'
NETWORK_BITCOIN_TESTNET = 'testnet'
NETWORK_LITECOIN = 'litecoin'


class Network:

    def __init__(self, databasefile=DEFAULT_DATABASE):
        self.session = DbInit(databasefile=databasefile).session
        dbnetwork = self.session.query(DbNetwork).all()
        self.network = {}
        for r in dbnetwork:
            dict = r.__dict__
            try:
                dict.pop('_sa_instance_state')
            except:
                pass
            for item in dict:
                if item in ['address', 'address_p2sh', 'wif', 'hdkey_private', 'hdkey_public']:
                    dict[item] = binascii.unhexlify(dict[item])
            self.network.update({dict['name']: dict})

    def network_get_values(self, field):
        return [nv[field] for nv in self.network.values()]

    def get_network_by_value(self, field, value):
        return [nv for nv in self.network if self.network[nv][field] == value]


if __name__ == '__main__':
    #
    # NETWORK EXAMPLES
    #

    # First recreate database to avoid already exist errors
    import os
    test_databasefile = 'bitcoinlib.test.sqlite'
    test_database = DEFAULT_DATABASEDIR + test_databasefile
    if os.path.isfile(test_database):
        os.remove(test_database)

    nw = Network(databasefile=test_databasefile)

    print("\n=== Bitcoin Testnet 3 parameters ===")
    from pprint import pprint
    pprint(nw.network['testnet'])

    print("\n=== Get all WIF prefixes ===")
    print("WIF Prefixes: %s" % nw.network_get_values('wif'))

    print("\n=== Get network for WIF prefix B0 ===")
    print("WIF Prefixes: %s" % nw.get_network_by_value('wif', b'\xB0'))
