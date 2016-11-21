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

from bitcoinrpc.authproxy import AuthServiceProxy
import configparser


def create_bitcoind_service_proxy(rpc_username, rpc_password, server='127.0.0.1', port=8332, use_https=False):
    protocol = 'https' if use_https else 'http'
    uri = '%s://%s:%s@%s:%s' % (protocol, rpc_username, rpc_password, server, port)
    print(uri)
    return AuthServiceProxy(uri)


class BitcoindClient:

    def __init__(self, use_https=False, server='127.0.0.1', port=8332, version_byte=0):
        self.type = 'bitcoind'
        config = configparser.ConfigParser()
        config.read('bitcoind.ini')
        self.proxy = create_bitcoind_service_proxy(config['rpc']['rpcuser'],
                                                   config['rpc']['rpcpassword'],
                                                   use_https=config['rpc']['use_https'],
                                                   server=config['rpc']['server'],
                                                   port=config['rpc']['port'])
        self.version_byte = version_byte


if __name__ == '__main__':
    bdc = BitcoindClient(server='192.168.13.20', port=18332)
    # bdc = BitcoindClient(server='80.127.136.50')
    commands = ["getblockhash", 400000]
    print(bdc.proxy.getinfo())
