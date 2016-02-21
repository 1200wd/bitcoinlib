# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    bitcoind deamon
#    Copyright (C) 2016 February 
#    1200 Web Development
#    http://1200wd.com/
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

import sys
try:
    from bitcoinrpc.authproxy import AuthServiceProxy
except ImportError as exc:
    sys.stderr.write("Error: install python-bitcoinrpc (https://github.com/jgarzik/python-bitcoinrpc)\n")
    exit(-1)
import bitcoind_config

def create_bitcoind_service_proxy(rpc_username, rpc_password, server='127.0.0.1', port=8332, use_https=False):
    protocol = 'https' if use_https else 'http'
    uri = '%s://%s:%s@%s:%s' % (protocol, rpc_username, rpc_password, server, port)
    return AuthServiceProxy(uri)


class BitcoindClient:

    def __init__(self, use_https=False, server='127.0.0.1', port=8332, version_byte=0):
        self.type = 'bitcoind'
        config = bitcoind_config.read_default_config()
        if not all (u in config for u in ('rpcuser', 'rpcpassword')):
            raise EnvironmentError("Bitcoind config file does not contain username and/or password")
        self.proxy = create_bitcoind_service_proxy(config['rpcuser'], config['rpcpassword'], use_https=use_https, server=server, port=port)
        self.version_byte = version_byte

