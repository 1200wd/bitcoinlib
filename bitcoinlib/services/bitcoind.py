# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Client for bitcoind deamon
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

from datetime import datetime
import struct
from bitcoinlib.main import *
from bitcoinlib.services.authproxy import AuthServiceProxy
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction
from bitcoinlib.encoding import to_hexstring
from bitcoinlib.networks import Network


PROVIDERNAME = 'bitcoind'

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


class BitcoindClient(BaseClient):
    """
    Class to interact with bitcoind, the Bitcoin deamon
    """

    @staticmethod
    def from_config(configfile=None, network='bitcoin'):
        """
        Read settings from bitcoind config file

        :param configfile: Path to config file. Leave empty to look in default places
        :type: str
        :param network: Bitcoin mainnet or testnet. Default is bitcoin mainnet
        :type: str

        :return BitcoindClient:
        """
        try:
            config = configparser.ConfigParser(strict=False)
        except TypeError:
            config = configparser.ConfigParser()
        config_fn = 'bitcoin.conf'
        if network == 'testnet':
            config_fn = 'bitcoin-testnet.conf'
        if not configfile:
            cfn = os.path.join(os.path.expanduser("~"), '.bitcoinlib/config/%s' % config_fn)
            if not os.path.isfile(cfn):  # Linux
                cfn = os.path.join(os.path.expanduser("~"), '.bitcoin/%s' % config_fn)
            if not os.path.isfile(cfn):  # Try Windows path
                cfn = os.path.join(os.path.expanduser("~"), 'Application Data/Bitcoin/%s' % config_fn)
            if not os.path.isfile(cfn):  # Try Max path
                cfn = os.path.join(os.path.expanduser("~"), 'Library/Application Support/Bitcoin/%s' % config_fn)
            if not os.path.isfile(cfn):
                raise ConfigError("Please install bitcoin client and specify a path to config file if path is not "
                                  "default. Or place a config file in .bitcoinlib/config/bitcoin.conf to reference to "
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
                port = 18332
            else:
                port = 8332
        server = '127.0.0.1'
        if 'rpcconnect' in config['rpc']:
            server = config.get('rpc', 'rpcconnect')
        elif 'bind' in config['rpc']:
            server = config.get('rpc', 'bind')
        elif 'externalip' in config['rpc']:
            server = config.get('rpc', 'externalip')
        elif 'server' in config['rpc']:
            server = config.get('rpc', 'server')
        url = "http://%s:%s@%s:%s" % (config.get('rpc', 'rpcuser'), config.get('rpc', 'rpcpassword'), server, port)
        return BitcoindClient(network, url)

    def __init__(self, network='bitcoin', base_url='', denominator=100000000, *args):
        """
        Open connection to bitcoin node

        :param network: Bitcoin mainnet or testnet. Default is bitcoin mainnet
        :type: str
        :param base_url: Connection URL in format http(s)://user:password@host:port.
        :type: str
        :param denominator: Denominator for this currency. Should be always 100000000 (satoshis) for bitcoin
        :type: str
        """
        if isinstance(network, Network):
            network = network.name
        if not base_url:
            bdc = self.from_config('', network)
            base_url = bdc.base_url
            network = bdc.network
        if len(base_url.split(':')) != 4:
            raise ConfigError("Bitcoind connection URL must be of format 'http(s)://user:password@host:port,"
                              "current format is %s. Please set url in providers.json file or check bitcoin config "
                              "file" % base_url)
        if 'password' in base_url:
            raise ConfigError("Invalid password in bitcoind provider settings. "
                              "Please replace default password and set url in providers.json or bitcoin.conf file")
        _logger.info("Connect to bitcoind on %s" % base_url)
        self.proxy = AuthServiceProxy(base_url)
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def getrawtransaction(self, txid):
        res = self.proxy.getrawtransaction(txid)
        return res

    def gettransaction(self, txid):
        tx = self.proxy.getrawtransaction(txid, 1)
        t = Transaction.import_raw(tx['hex'], network=self.network)
        t.confirmations = tx['confirmations']
        if t.confirmations:
            t.status = 'confirmed'
            t.verified = True
        for i in t.inputs:
            if i.prev_hash == b'\x00' * 32:
                i.value = t.output_total
                i.script_type = 'coinbase'
                continue
            txi = self.proxy.getrawtransaction(to_hexstring(i.prev_hash), 1)
            i.value = int(round(float(txi['vout'][i.output_n_int]['value']) / self.network.denominator))
        for o in t.outputs:
            o.spent = None
        t.block_hash = tx['blockhash']
        t.version = struct.pack('>L', tx['version'])
        t.date = datetime.fromtimestamp(tx['blocktime'])
        t.hash = txid
        t.update_totals()
        return t

    def getutxos(self, addresslist):
        txs = []

        for addr in addresslist:
            res = self.proxy.getaddressinfo(addr)
            if not (res['ismine'] or res['iswatchonly']):
                raise ClientError("Address %s not found in bitcoind wallet, use 'importaddress' to add address to "
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
        pres = ''
        try:
            pres = self.proxy.estimatesmartfee(blocks)
            res = pres['feerate']
        except KeyError as e:
            _logger.warning("bitcoind error: %s, %s" % (e, pres))
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
    # base_url = 'http://bitcoinrpc:passwd@host:8332'
    # bdc = BitcoindClient(base_url=base_url)

    # 2. Or connect using default settings or settings from config file
    bdc = BitcoindClient()

    print("\n=== SERVERINFO ===")
    pprint(bdc.proxy.getnetworkinfo())

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
