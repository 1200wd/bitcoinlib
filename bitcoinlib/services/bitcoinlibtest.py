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

    def __init__(self, network, base_url, denominator, api_key=''):
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def getbalance(self, addresslist):
        return self.units * len(addresslist)

    def getutxos(self, addresslist, utxos_per_address=2):
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
        return int(1000 / blocks)

    def sendrawtransaction(self, rawtx):
        txid = to_hexstring(hashlib.sha256(hashlib.sha256(to_bytes(rawtx)).digest()).digest()[::-1])
        return {'txid': txid}
