# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Client for litecoind deamon
#    © 2018 - 2020 Oct - 1200 Web Development <http://1200wd.com/>
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

import configparser
from bitcoinlib.main import *
from bitcoinlib.networks import Network
from bitcoinlib.services.authproxy import AuthServiceProxy
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction


PROVIDERNAME = 'litecoind'

_logger = logging.getLogger(__name__)


class ConfigError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.info(msg)

    def __str__(self):
        return self.msg


def _read_from_config(configparser, section, value, fallback=None):
    try:
        return configparser.get(section, value)
    except Exception:
        return fallback


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
        config = configparser.ConfigParser(strict=False)
        config_fn = 'litecoin.conf'
        if isinstance(network, Network):
            network = network.name
        if network == 'testnet':
            config_fn = 'litecoin-testnet.conf'

        cfn = None
        if not configfile:
            config_locations = ['~/.bitcoinlib', '~/.litecoin', '~/Application Data/Litecoin',
                                '~/Library/Application Support/Litecoin']
            for location in config_locations:
                cfn = Path(location, config_fn).expanduser()
                if cfn.exists():
                    break
        else:
            cfn = Path(BCL_DATA_DIR, 'config', configfile)

        if not cfn or not cfn.is_file():
            raise ConfigError("Config file %s not found. Please install Litecoin client and specify a path to config "
                              "file if path is not default. Or place a config file in .bitcoinlib/litecoin.conf to "
                              "reference to an external server." % cfn)

        try:
            config.read(cfn)
        except Exception:
            with cfn.open() as f:
                config_string = '[rpc]\n' + f.read()
            config.read_string(config_string)

        testnet = _read_from_config(config, 'rpc', 'testnet')
        if testnet:
            network = 'testnet'
        if _read_from_config(config, 'rpc', 'rpcpassword') == 'specify_rpc_password':
            raise ConfigError("Please update config settings in %s" % cfn)
        if network == 'testnet':
            port = 19332
        else:
            port = 9332
        port = _read_from_config(config, 'rpc', 'rpcport', port)
        server = '127.0.0.1'
        server = _read_from_config(config, 'rpc', 'rpcconnect', server)
        server = _read_from_config(config, 'rpc', 'bind', server)
        server = _read_from_config(config, 'rpc', 'externalip', server)
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
        if isinstance(network, Network):
            network = network.name
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

    # def getbalance

    def getutxos(self, address, after_txid='', limit=MAX_TRANSACTIONS):
        txs = []

        res = self.proxy.getaddressinfo(address)
        if not (res['ismine'] or res['iswatchonly']):
            raise ClientError("Address %s not found in litecoind wallet, use 'importaddress' to add address to "
                              "wallet." % address)

        txs_list = self.proxy.listunspent(0, 99999999, [address])
        for t in sorted(txs_list, key=lambda x: x['confirmations'], reverse=True):
            txs.append({
                'address': t['address'],
                'txid': t['txid'],
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
            if t['txid'] == after_txid:
                txs = []

        return txs

    def _parse_transaction(self, tx, block_height=None, get_input_values=True):
        t = Transaction.parse_hex(tx['hex'], strict=False, network=self.network)
        t.confirmations = None if 'confirmations' not in tx else tx['confirmations']
        if t.confirmations or block_height:
            t.status = 'confirmed'
            t.verified = True
        for i in t.inputs:
            if i.prev_txid == b'\x00' * 32:
                i.script_type = 'coinbase'
                continue
            if get_input_values:
                txi = self.proxy.getrawtransaction(i.prev_txid.hex(), 1)
                i.value = int(round(float(txi['vout'][i.output_n_int]['value']) / self.network.denominator))
        for o in t.outputs:
            o.spent = None
        t.block_height = block_height
        t.version = tx['version'].to_bytes(4, 'big')
        t.date = datetime.utcfromtimestamp(tx['blocktime'])
        t.update_totals()
        return t

    def gettransaction(self, txid):
        tx = self.proxy.getrawtransaction(txid, 1)
        return self._parse_transaction(tx)

    # def gettransactions

    def getrawtransaction(self, txid):
        res = self.proxy.getrawtransaction(txid)
        return res

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
            _logger.info("litecoind error: %s, %s" % (e, pres))
            res = self.proxy.estimatefee(blocks)
        return int(res * self.units)

    def blockcount(self):
        return self.proxy.getblockcount()

    def mempool(self, txid=''):
        txids = self.proxy.getrawmempool()
        if not txid:
            return txids
        elif txid in txids:
            return [txid]
        return False

    def getblock(self, blockid, parse_transactions=True, page=1, limit=None):
        if isinstance(blockid, int):
            blockid = self.proxy.getblockhash(blockid)
        if not limit:
            limit = 99999

        txs = []
        if parse_transactions:
            bd = self.proxy.getblock(blockid, 2)
            for tx in bd['tx'][(page - 1) * limit:page * limit]:
                # try:
                tx['blocktime'] = bd['time']
                tx['blockhash'] = bd['hash']
                txs.append(self._parse_transaction(tx, block_height=bd['height'], get_input_values=False))
                # except Exception as e:
                #     _logger.error("Could not parse tx %s with error %s" % (tx['txid'], e))
            # txs += [tx['hash'] for tx in bd['tx'][len(txs):]]
        else:
            bd = self.proxy.getblock(blockid, 1)
            txs = bd['tx']

        block = {
            'bits': int(bd['bits'], 16),
            'depth': bd['confirmations'],
            'block_hash': bd['hash'],
            'height': bd['height'],
            'merkle_root': bd['merkleroot'],
            'nonce': bd['nonce'],
            'prev_block': bd['previousblockhash'],
            'time': bd['time'],
            'tx_count': bd['nTx'],
            'txs': txs,
            'version': bd['version'],
            'page': page,
            'pages': None,
            'limit': limit
        }
        return block

    def getrawblock(self, blockid):
        if isinstance(blockid, int):
            blockid = self.proxy.getblockhash(blockid)
        return self.proxy.getblock(blockid, 0)

    def isspent(self, txid, index):
        res = self.proxy.gettxout(txid, index)
        if not res:
            return True
        return False

    def getinfo(self):
        info = self.proxy.getmininginfo()
        return {
            'blockcount': info['blocks'],
            'chain': info['chain'],
            'difficulty': int(info['difficulty']),
            'hashrate': int(info['networkhashps']),
            'mempool_size': int(info['pooledtx']),
        }


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
