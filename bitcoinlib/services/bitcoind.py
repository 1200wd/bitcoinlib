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


class BitcoindClient:

    def __init__(self, configfile='bitcoind.ini'):
        self.type = 'bitcoind'
        config = configparser.ConfigParser()
        config.read(configfile)
        protocol = 'https' if config['rpc'].getboolean('use_https') else 'http'
        uri = '%s://%s:%s@%s:%s' % (protocol, config['rpc']['rpcuser'], config['rpc']['rpcpassword'],
                                    config['rpc']['server'], config['rpc']['port'])
        self.proxy = AuthServiceProxy(uri)
        self.version_byte = config['rpc']['version_byte']


if __name__ == '__main__':
    bdc = BitcoindClient()
    commands = ["getblockhash", 400000]
    print(bdc.proxy.getinfo())
