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

# Network, address_type_normal, address_type_p2sh, wif, extended_wif_public and extended_wif_private
NETWORK_BITCOIN = 'bitcoin'
NETWORK_BITCOIN_TESTNET = 'testnet'
NETWORK_LITECOIN = 'litecoin'
NETWORKS = {
    NETWORK_BITCOIN: {
        'description': 'Bitcoin',
        'symbol': '฿',
        'code': 'BTC',
        'address': b'\x00',
        'address_p2sh': b'\x05',
        'wif': b'\x80',
        'hdkey_private': b'\x04\x88\xAD\xE4',
        'hdkey_public': b'\x04\x88\xB2\x1E',
        'bip44_cointype': 0,
    },
    NETWORK_BITCOIN_TESTNET: {
        'description': 'Bitcoin Test Network 3',
        'symbol': 'TBTC',
        'code': 'TBTC',
        'address': b'\x6F',
        'address_p2sh': b'\x05',
        'wif': b'\xEF',
        'hdkey_private': b'\x04\x35\x83\x94',
        'hdkey_public': b'\x04\x35\x87\xCF',
        'bip44_cointype': 1,
    },
    NETWORK_LITECOIN: {
        'description': 'Litcoin Network',
        'symbol': 'LTC',
        'code': 'LTC',
        'address': b'\x30',
        'address_p2sh': b'\x05',
        'wif': b'\xB0',
        'hdkey_private': b'\x01\x9D\x9C\xFE',
        'hdkey_public': b'\x01\x9D\xA4\x62',
        'bip44_cointype': 2,
    },
}


def network_get_values(field):
    return [nv[field] for nv in NETWORKS.values()]


def get_network_by_value(field, value):
    return [nv for nv in NETWORKS if NETWORKS[nv][field] == value]


if __name__ == '__main__':
    #
    # NETWORK EXAMPLES
    #

    print("\n=== Get all WIF prefixes ===")
    print("WIF Prefixes: %s" % network_get_values('wif'))

    print("\n=== Get network for WIF prefix B0 ===")
    print("WIF Prefixes: %s" % get_network_by_value('wif', b'\xB0'))
