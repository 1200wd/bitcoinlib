# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    bitcoind deamon
#    © 2017 June - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.services.baseclient import BaseClient


PROVIDERNAME = 'qtumd'

_logger = logging.getLogger(__name__)


class ConfigError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.warning(msg)

    def __str__(self):
        return self.msg

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class QtumdClient(BaseClient):
    """
    Class to interact with qtumd, the Qtum deamon
    """

    @staticmethod
    def from_config(configfile=None, network='qtum'):
        """
        Read settings from qtumd config file

        :param configfile: Path to config file. Leave empty to look in default places
        :type: str
        :param network: Qtum mainnet or testnet. Default is qtum mainnet
        :type: str

        :return QtumdClient:
        """
        config = configparser.ConfigParser()
        if not configfile:
            cfn = os.path.join(os.path.expanduser("~"), '.bitcoinlib/config/qtum.conf')
            if not os.path.isfile(cfn):
                cfn = os.path.join(os.path.expanduser("~"), '.qtum/qtum.conf')
            if not os.path.isfile(cfn):
                raise ConfigError("Please install qtum client and specify a path to config file if path is not "
                                  "default. Or place a config file in .bitcoinlib/config/qtum.conf to reference to "
                                  "an external server.")
        else:
            cfn = os.path.join(DEFAULT_SETTINGSDIR, configfile)
            if not os.path.isfile(cfn):
                raise ConfigError("Config file %s not found" % cfn)
        with open(cfn, 'r') as f:
            config_string = '[rpc]\n' + f.read()
        config.read_string(config_string)
        try:
            if config.get('rpc', 'testnet'):
                network = 'qtum_testnet'
        except configparser.NoOptionError:
            pass
        if config.get('rpc', 'rpcpassword') == 'specify_rpc_password':
            raise ConfigError("Please update config settings in %s" % cfn)
        try:
            port = config.get('rpc', 'port')
        except configparser.NoOptionError:
            if network == 'qtum_testnet':
                port = 8333
            else:
                port = 8333
        try:
            server = config.get('rpc', 'bind')
        except configparser.NoOptionError:
            server = '127.0.0.1'
        url = "http://%s:%s@%s:%s" % (config.get('rpc', 'rpcuser'), config.get('rpc', 'rpcpassword'), server, port)
        return QtumdClient(network, url)

    def __init__(self, network='qtum', base_url='', denominator=100000000, api_key=''):
        """
        Open connection to qtum node

        :param network: Qtum mainnet or testnet. Default is qtum mainnet
        :type: str
        :param base_url: Connection URL in format http(s)://user:password@host:port.
        :type: str
        :param denominator: Denominator for this currency. Should be always 100000000 (satoshis) for qtum
        :type: str
        :param api_key: Leave empty for
        :type: str
        """
        if not base_url:
            bdc = self.from_config('', network)
            base_url = bdc.base_url
            network = bdc.network
        if len(base_url.split(':')) != 4:
            raise ConfigError("Qtumd connection URL must be of format 'http(s)://user:password@host:port,"
                              "current format is %s. Please set url in providers.json file" % base_url)
        if 'password' in base_url:
            raise ConfigError("Invalid password 'password' in qtumd provider settings. "
                              "Please set password and url in providers.json file")
        _logger.info("Connect to qtumd on %s" % base_url)
        self.proxy = AuthServiceProxy(base_url)
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def getutxos(self, addresslist):
        res = self.proxy.listunspent(3, 9999999, addresslist)
        txs = []
        for tx in res:
            txs.append({
                'address': tx['address'],
                'tx_hash': tx['txid'],
                'confirmations': tx['confirmations'],
                'output_n': tx['vout'],
                'index': 0,
                'value': int(round(tx['amount'] * self.units, 0)),
                'script': tx['scriptPubKey'],
                'date': 0
            })
        return txs

    def getbalance(self, addresslist):
        res = self.proxy.listunspent(3, 9999999, addresslist)
        balance = 0
        for tx in res:
            balance += tx['values']
        return balance

    def getrawtransaction(self, txid):
        res = self.proxy.getrawtransaction(txid)
        return res

    def sendrawtransaction(self, rawtx):
        return self.proxy.sendrawtransaction(rawtx)
    
    def estimatefee(self, blocks):
        try:
            res = self.proxy.estimatesmartfee(blocks)['feerate']
        except KeyError:
            res = self.proxy.estimatefee(blocks)
        return int(res * self.units)


if __name__ == '__main__':
    #
    # SOME EXAMPLES
    #

    from pprint import pprint

    qdc = QtumdClient()

    print("\n=== SERVERINFO ===")
    pprint(qdc.proxy.getnetworkinfo())

    print("\n=== Best Block ===")
    blockhash = qdc.proxy.getbestblockhash()
    bestblock = qdc.proxy.getblock(blockhash)
    bestblock['tx'] = '...' + str(len(bestblock['tx'])) + ' transactions...'
    pprint(bestblock)

    print("\n=== Mempool ===")
    rmp = qdc.proxy.getrawmempool()
    pprint(rmp[:25])
    print('... truncated ...')
    print("Mempool Size %d" % len(rmp))

    # print("\n=== Raw Transaction by txid ===")
    # t = qdc.getrawtransaction('7eb5332699644b753cd3f5afba9562e67612ea71ef119af1ac46559adb69ea0d')
    # pprint(t)

    print("\n=== Current network fees ===")
    t = qdc.estimatefee(5)
    pprint(t)
