# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    BitcoinLib Test Network for Unit Tests
#    © 2018 February - 1200 Web Development <http://1200wd.com/>
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

import logging
import hashlib
from bitcoinlib.services.baseclient import BaseClient
from bitcoinlib.encoding import addr_to_pubkeyhash, to_hexstring, to_bytes

_logger = logging.getLogger(__name__)

PROVIDERNAME = 'bitcoinlib'


class BitcoinLibTestClient(BaseClient):
    """
    Dummy service client for bitcoinlib test network. Only used for testing.

    Does not make any connection to a service provider, so can be used offline.

    """

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def getbalance(self, addresslist):
        """
        Dummy getbalance method for bitcoinlib testnet

        :param addresslist: List of addresses
        :type addresslist: list

        :return int:
        """
        return self.units * len(addresslist)

    def getutxos(self, addresslist, utxos_per_address=2):
        """
        Dummy method to retreive UTXO's. This method creates a new UTXO for each address provided out of the
        testnet void, which can be used to create test transactions for the bitcoinlib testnet.

        :param addresslist: List of addresses
        :type addresslist: list
        :param utxos_per_address: Number of UTXO's to be created per address
        :type utxos_per_address: int

        :return list: The created UTXO set
        """
        utxos = []
        for n in range(utxos_per_address):
            for address in addresslist:
                pkh = str(n).encode() + addr_to_pubkeyhash(address)[1:]
                utxos.append(
                    {
                        'address': address,
                        'tx_hash': hashlib.sha256(pkh).hexdigest(),
                        'confirmations': 10,
                        'output_n': 0,
                        'index': 0,
                        'value': 1 * self.units,
                        'script': '',
                    }
                )
        return utxos

    def estimatefee(self, blocks):
        """
        Dummy estimate fee method for the bitcoinlib testnet.

        :param blocks: Number of blocks
        :type blocks: int

        :return int: Fee as 1000 // number of blocks
        """
        return 1000 // blocks

    def sendrawtransaction(self, rawtx):
        """
        Dummy method to send transactions on the bitcoinlib testnet. The bitcoinlib testnet does not exists,
        so it just returns the transaction hash.

        :param rawtx: A raw transaction hash
        :type rawtx: bytes, str

        :return str: Transaction hash
        """
        txid = to_hexstring(hashlib.sha256(hashlib.sha256(to_bytes(rawtx)).digest()).digest()[::-1])
        return {
            'txid': txid,
            'response_dict': {}
        }
