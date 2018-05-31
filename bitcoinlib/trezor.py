# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Trezor class - Wrapper for python-trezor library use to communicate with Trezor hardware wallet
#    © 2018 June - 1200 Web Development <http://1200wd.com/>
#


from bitcoinlib.main import *
try:
    from trezorlib import coins
    from trezorlib import messages as proto
    from trezorlib.client import TrezorClient
    from trezorlib.tools import parse_path
    from trezorlib.transport import get_transport
    TREZORLIB_INSTALLED = True
except:
    TREZORLIB_INSTALLED = False


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

    def __init__(self, network_name='Bitcoin'):
        if not TREZORLIB_INSTALLED:
            raise TrezorError("Please install python-trezor library before using this class")
        transport = get_transport()
        self.client = TrezorClient(transport)
        self.client.set_tx_api(coins.tx_api[network_name])

    def __del__(self):
        self.client.close()

    def key_for_path(self, path, network='Bitcoin'):
        self.client.set_tx_api(coins.tx_api[network])
        account_key = parse_path(path)
        node = self.client.get_public_node(account_key).node
        return node.public_key
        # return self.client.get_public_node(account_key).xpub
