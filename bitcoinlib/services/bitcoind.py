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
        return BitcoindClient(config.get('rpc', 'rpcuser'),
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


if __name__ == '__main__':
    #
    # SOME EXAMPLES
    #

    from pprint import pprint
    bdc = BitcoindClient.from_config()
    # bdc = BitcoindClient.from_config('bitcoind-testnet.ini')

    # TODO: Fix non-mandatory-script-verify-flag (Non-canonical signature: S value is unnecessarily high) error
    # see https://github.com/vbuterin/pybitcointools/issues/89
    # or https://groups.google.com/forum/#!topic/bitcoin-xt/S5dGO6Mig_M - not a bug???
    # https://github.com/bitcoin/bips/blob/master/bip-0062.mediawiki
    rawtx = '0100000005181685d3ed6b5f40057810ea3724a224ba4283d1a166caaa313687bd8db0d9f3000000006b483045022055c1af6ac28d505233476b3a83fec4f403c728a5c657ab58a2e51244d4edce26022100a813636d6e22096cdaf599d684bee0219cb55257eb05f960b5f4292d77695ada01210204911589a1dafd820d449bf3bfcea63bf372fa8829b568e3cfb9e04c90d057defffffffd181685d3ed6b5f40057810ea3724a224ba4283d1a166caaa313687bd8db0d9f3010000006a47304402200b66268f8aa75db3c4ebc73bdc3a6b58c40c889c9c081256da8d0459afc9f71302202c63ad4dcd773f1c58d2d9b6386d423a6fac880e011f0d8dde0eb466798195460121032890044c5d6c17d13178b85e5ab4bbeb341c0a80477acc608f168099d08b4efcfffffffd181685d3ed6b5f40057810ea3724a224ba4283d1a166caaa313687bd8db0d9f3020000006a47304402203719922d03e5fb9207baa9eaeac93ead7f2e25c8db81b54202c207adfc06addb02204ffa1ae66d5d2262254c5ab2ecf861fe7c05d1f18ea6bf887f3b181b5d21e23401210322988b4602ab2ef0ef57a66b337296b6bcdd96a2ffc2eb189b7ec018fc4565befffffffd181685d3ed6b5f40057810ea3724a224ba4283d1a166caaa313687bd8db0d9f3030000006a47304402204690c54cbe29f83a1624df9f77eb80fb74b05a2e2dfa0aed3d74c3899f84addd0220218be18959cc1109465c233d3da14bd0da281b0e0f3416beb7f1645f9f0011710121027084e4c09141f04afbf58bb6c04aefc1575d75612e1c033790945dd6380188c2fffffffd181685d3ed6b5f40057810ea3724a224ba4283d1a166caaa313687bd8db0d9f3040000006c49304602210094d967a65e44f099338baab306696c47aef71f4a02b47a3d348b3920d0af663502210080ddae5805d6ea5a8991dfa11496f1fecb975c09dea11643c6f7b2783a1a731e0121025bb2ec9076fa1c7b8c4bd61e785278f4d9d43644c92d0fc036ebd60f8a2d57c3fffffffd01c0ef0b08000000001976a9143c1e136fbc9cfabe35d6d5d41474295721d44f9c88ac00000000'
    bdc.sendrawtransaction(rawtx)

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
