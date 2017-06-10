# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
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

from bitcoinlib.main import *
from bitcoinlib.services.authproxy import AuthServiceProxy

_logger = logging.getLogger(__name__)


class ConfigError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class BitcoindClient:

    @classmethod
    def from_config(cls, configfile='bitcoind.ini'):
        config = configparser.ConfigParser()
        cfn = os.path.join(DEFAULT_SETTINGSDIR, configfile)
        if not os.path.isfile(cfn):
            raise ConfigError("Config file %s not found" % cfn)
        config.read(cfn)
        cls.version_byte = config.get('rpc', 'version_byte')
        return cls(config.get('rpc', 'rpcuser'),
                   config.get('rpc', 'rpcpassword'),
                   config.getboolean('rpc', 'use_https'),
                   config.get('rpc', 'server'),
                   config.get('rpc', 'port'))

    def __init__(self, user, password, use_https=False, server='127.0.0.1', port=8332):
        self.type = 'bitcoind'
        protocol = 'https' if use_https else 'http'
        uri = '%s://%s:%s@%s:%s' % (protocol, user, password, server, port)
        _logger.debug("Connect to bitcoind on %s" % uri)
        self.proxy = AuthServiceProxy(uri)

    def getrawtransaction(self, txid):
        res = self.proxy.getrawtransaction(txid)
        return res

    def sendrawtransaction(self, rawtx):
        return self.proxy.sendrawtransaction(rawtx)
    
    def estimatefee(self, blocks):
        return self.proxy.estimatefee(blocks)


if __name__ == '__main__':
    #
    # SOME EXAMPLES
    #

    from pprint import pprint
    bdc = BitcoindClient.from_config()
    # bdc = BitcoindClient.from_config('bitcoind-testnet.ini')

    print("\n=== SERVERINFO ===")
    pprint(bdc.proxy.getinfo())

    print("\n=== Best Block ===")
    blockhash = bdc.proxy.getbestblockhash()
    bestblock = bdc.proxy.getblock(blockhash)
    bestblock['tx'] = '...' + str(len(bestblock['tx'])) + ' transactions...'
    pprint(bestblock)

    print("\n=== Mempool ===")
    rmp = bdc.proxy.getrawmempool()
    pprint(rmp[:25])
    print('... truncated ...')
    print("Mempool Size %d" % len(rmp))

    print("\n=== Raw Transaction by txid ===")
    t = bdc.getrawtransaction('7eb5332699644b753cd3f5afba9562e67612ea71ef119af1ac46559adb69ea0d')
    pprint(t)

    print("\n=== Current network fees ===")
    t = bdc.estimatefee(5)
    pprint(t)
