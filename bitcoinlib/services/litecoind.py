# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Client for litecoind deamon
#    © 2018 June - 1200 Web Development <http://1200wd.com/>
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

from datetime import datetime
from bitcoinlib.main import *
from bitcoinlib.services.authproxy import AuthServiceProxy
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction
from bitcoinlib.encoding import to_hexstring


PROVIDERNAME = 'litecoind'

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


class LitecoindClient(BaseClient):
    """
    Class to interact with litecoind, the Litecoin deamon
    """

    @staticmethod
    def from_config(configfile=None, network='litecoin'):
        """
        Read settings from litecoind config file

        :param configfile: Path to config file. Leave empty to look in default places
        :type: str
        :param network: Litecoin mainnet or testnet. Default is litecoin mainnet
        :type: str

        :return LitecoindClient:
        """
        if PY3:
            config = configparser.ConfigParser(strict=False)
        else:
            config = configparser.ConfigParser()
        if not configfile:
            cfn = os.path.join(os.path.expanduser("~"), '.bitcoinlib/config/litecoin.conf')
            if not os.path.isfile(cfn):  # Try Linux path
                cfn = os.path.join(os.path.expanduser("~"), '.litecoin/litecoin.conf')
            if not os.path.isfile(cfn):  # Try Windows path
                cfn = os.path.join(os.path.expanduser("~"), 'Application Data/Litecoin/litecoin.conf')
            if not os.path.isfile(cfn):  # Try Max path
                cfn = os.path.join(os.path.expanduser("~"), 'Library/Application Support/Litecoin/litecoin.conf')
            if not os.path.isfile(cfn):
                raise ConfigError("Please install litecoin client and specify a path to config file if path is not "
                                  "default. Or place a config file in .bitcoinlib/config/litecoin.conf to reference to "
                                  "an external server.")
        else:
            cfn = os.path.join(BCL_CONFIG_DIR, configfile)
            if not os.path.isfile(cfn):
                raise ConfigError("Config file %s not found" % cfn)
        with open(cfn, 'r') as f:
            config_string = '[rpc]\n' + f.read()
        config.read_string(config_string)
        try:
            if int(config.get('rpc', 'testnet')):
                network = 'testnet'
        except configparser.NoOptionError:
            pass
        if config.get('rpc', 'rpcpassword') == 'specify_rpc_password':
            raise ConfigError("Please update config settings in %s" % cfn)
        try:
            port = config.get('rpc', 'rpcport')
        except configparser.NoOptionError:
            if network == 'testnet':
                port = 19332
            else:
                port = 9332
        server = '127.0.0.1'
        if 'rpcconnect' in config['rpc']:
            server = config.get('rpc', 'rpcconnect')
        elif 'bind' in config['rpc']:
            server = config.get('rpc', 'bind')
        elif 'externalip' in config['rpc']:
            server = config.get('rpc', 'externalip')
        url = "http://%s:%s@%s:%s" % (config.get('rpc', 'rpcuser'), config.get('rpc', 'rpcpassword'), server, port)
        return LitecoindClient(network, url)

    def __init__(self, network='litecoin', base_url='', denominator=100000000, *args):
        """
        Open connection to litecoin node

        :param network: Litecoin mainnet or testnet. Default is litecoin mainnet
        :type: str
        :param base_url: Connection URL in format http(s)://user:password@host:port.
        :type: str
        :param denominator: Denominator for this currency. Should be always 100000000 (satoshis) for litecoin
        :type: str
        """
        if not base_url:
            bdc = self.from_config('', network)
            base_url = bdc.base_url
            network = bdc.network
        if len(base_url.split(':')) != 4:
            raise ConfigError("Litecoind connection URL must be of format 'http(s)://user:password@host:port,"
                              "current format is %s. Please set url in providers.json file or check litecoin config "
                              "file" % base_url)
        if 'password' in base_url:
            raise ConfigError("Invalid password in litecoind provider settings. "
                              "Please replace default password and set url in providers.json or litecoin.conf file")
        _logger.info("Connect to litecoind on %s" % base_url)
        self.proxy = AuthServiceProxy(base_url)
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def getrawtransaction(self, txid):
        res = self.proxy.getrawtransaction(txid)
        return res

    def gettransaction(self, txid):
        tx = self.proxy.getrawtransaction(txid, 1)
        t = Transaction.import_raw(tx['hex'], network='litecoin')
        t.confirmations = tx['confirmations']
        if t.confirmations:
            t.status = 'confirmed'
            t.verified = True
        for i in t.inputs:
            txi = self.proxy.getrawtransaction(to_hexstring(i.prev_hash), 1)
            value = int(float(txi['vout'][i.output_n_int]['value']) / self.network.denominator)
            i.value = value
        t.block_hash = tx['blockhash']
        t.version = tx['version']
        t.date = datetime.fromtimestamp(tx['blocktime'])
        t.update_totals()
        return t

    def getutxos(self, addresslist):
        txs = []

        for addr in addresslist:
            res = self.proxy.validateaddress(addr)
            if not (res['ismine'] or res['iswatchonly']):
                raise ClientError("Address %s not found in Litecoind wallet, use 'importaddress' to add address to "
                                  "wallet." % addr)

        for t in self.proxy.listunspent(0, 99999999, addresslist):
            txs.append({
                'address': t['address'],
                'tx_hash': t['txid'],
                'confirmations': t['confirmations'],
                'output_n': t['vout'],
                'input_n': -1,
                'block_height': None,
                'fee': None,
                'size': 0,
                'value': int(t['amount'] * self.units),
                'script': t['scriptPubKey'],
                'date': None,
            })

        return txs

    def sendrawtransaction(self, rawtx):
        res = self.proxy.sendrawtransaction(rawtx)
        return {
            'txid': res,
            'response_dict': res
        }
    
    def estimatefee(self, blocks):
        try:
            res = self.proxy.estimatesmartfee(blocks)['feerate']
        except KeyError:
            res = self.proxy.estimatefee(blocks)
        return int(res * self.units)

    def block_count(self):
        return self.proxy.getblockcount()


if __name__ == '__main__':
    #
    # SOME EXAMPLES
    #

    from pprint import pprint

    # 1. Connect by specifying connection URL
    # base_url = 'http://litecoin:passwd@host:9432'
    # bdc = LitecoindClient(base_url=base_url)

    # 2. Or connect using default settings or settings from config file
    client = LitecoindClient()

    print("\n=== SERVERINFO ===")
    pprint(client.proxy.getnetworkinfo())

    print("\n=== Best Block ===")
    blockhash = client.proxy.getbestblockhash()
    bestblock = client.proxy.getblock(blockhash)
    bestblock['tx'] = '...' + str(len(bestblock['tx'])) + ' transactions...'
    pprint(bestblock)

    print("\n=== Mempool ===")
    rmp = client.proxy.getrawmempool()
    pprint(rmp[:25])
    print('... truncated ...')
    print("Mempool Size %d" % len(rmp))

    print("\n=== Raw Transaction by txid ===")
    t = client.getrawtransaction('fa3906a4219078364372d0e2715f93e822edd0b47ce146c71ba7ba57179b50f6')
    pprint(t)

    print("\n=== Current network fees ===")
    t = client.estimatefee(5)
    pprint(t)
