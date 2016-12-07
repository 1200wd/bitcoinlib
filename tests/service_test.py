# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
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

from pprint import pprint
from decimal import *
import getpass
from bitcoinlib.services import bitcoind

bd = bitcoind.BitcoindClient().proxy

# Create a list of unspent transactions, and calculate total spendable
unspent = bd.listunspent(0)
amount_total = 0
inputs = []
for utxo in unspent:
    print("Transaction %s:%i has %i unspent satoshi's" % (utxo['txid'], utxo['vout'], utxo['amount']*10000000))
    inputs.append({
            "txid": utxo['txid'],
            "vout": utxo['vout'],
        })
    amount_total += utxo['amount']
print("Total spendable is %i satoshi" % (amount_total*10000000))

# Create raw transaction with unspent outputs
output_address = '1LeNnarTMFen6kmZ4kB4VhUJivDa2mTa7w'
amount_total -= Decimal('0.0001')
rt = bd.createrawtransaction(inputs, {output_address: amount_total})

# Sign and broadcast transaction
wallet_password = getpass.getpass("Enter wallet Passphrase:")
bd.walletpassphrase(wallet_password, 3)
srt = bd.signrawtransaction(rt)
print("=== This is the transaction:")
pprint(bd.decoderawtransaction(srt['hex']))

# Do not uncomment this line, unless you really want to broadcast the transaction
# bd.sendrawtransaction(srt['hex'])

