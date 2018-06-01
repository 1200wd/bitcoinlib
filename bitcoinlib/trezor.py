# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Trezor class - Wrapper for python-trezor library use to communicate with Trezor hardware wallet
#    © 2018 June - 1200 Web Development <http://1200wd.com/>
#


from bitcoinlib.main import *
from bitcoinlib.keys import HDKey
from bitcoinlib.networks import DEFAULT_NETWORK
try:
    from trezorlib import coins
    from trezorlib import messages as proto
    from trezorlib.client import TrezorClient
    from trezorlib.tools import parse_path
    from trezorlib.transport import get_transport
    TREZORLIB_INSTALLED = True
except:
    TREZORLIB_INSTALLED = False

TREZOR_NETWORKS = {
    'bitcoin': 'Bitcoin',
    'testnet': 'Testnet',
    'litecoin': 'Litecoin',
    'dash': 'Dash'
}

_logger = logging.getLogger(__name__)


class TrezorError(Exception):
    """
    Handle Trezor class Exceptions

    """
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


class Trezor:

    def __init__(self, network=DEFAULT_NETWORK):
        if not TREZORLIB_INSTALLED:
            raise TrezorError("Please install python-trezor library before using this class")
        transport = get_transport()
        self.client = TrezorClient(transport)
        self.network = network
        self.network_trezor = TREZOR_NETWORKS[network]
        self.client.set_tx_api(coins.tx_api[self.network_trezor])

    def __del__(self):
        self.client.close()

    def key_for_path(self, path, network=None):
        if network is None:
            network = self.network
            network_trezor = self.network_trezor
        else:
            network_trezor = TREZOR_NETWORKS[network]
        self.client.set_tx_api(coins.tx_api[network_trezor])
        account_key = parse_path(path)
        account_node = self.client.get_public_node(account_key)
        key = HDKey(key=account_node.node.public_key, chain=account_node.node.chain_code, isprivate=False,
                    depth=account_node.node.depth, child_index=account_node.node.child_num,
                    parent_fingerprint=account_node.node.fingerprint, network=network)
        print(key.wif_public())
        print(account_node.xpub)
        return key
