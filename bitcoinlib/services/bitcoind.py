# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    bitcoind deamon
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

from bitcoinlib.services.authproxy import AuthServiceProxy
import configparser


class BitcoindClient:

    @classmethod
    def from_config(cls, configfile='bitcoind.ini'):
        config = configparser.ConfigParser()
        config.read(configfile)
        cls.version_byte = config['rpc']['version_byte']
        return BitcoindClient(config['rpc']['rpcuser'],
                              config['rpc']['rpcpassword'],
                              config['rpc'].getboolean('use_https'),
                              config['rpc']['server'],
                              config['rpc']['port'])

    def __init__(self, user, password, use_https=False, server='127.0.0.1', port=8332):
        self.type = 'bitcoind'
        protocol = 'https' if use_https else 'http'
        uri = '%s://%s:%s@%s:%s' % (protocol, user, password, server, port)
        print(uri)
        self.proxy = AuthServiceProxy(uri)


if __name__ == '__main__':
    #
    # SOME EXAMPLES
    #

    from pprint import pprint
    bdc = BitcoindClient.from_config('bitcoind-testnet-local.ini')

    print("\n=== SERVERINFO ===")
    pprint(bdc.proxy.getinfo())

    print("\n=== Best Block ===")
    blockhash = bdc.proxy.getbestblockhash()
    pprint(bdc.proxy.getblock(blockhash))

    print("\n=== Mempool ===")
    rmp = bdc.proxy.getrawmempool()
    pprint(rmp)
    print("Mempool Size %d" % len(rmp))
