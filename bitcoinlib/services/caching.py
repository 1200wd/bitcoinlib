# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Cache client and provider - administer blockchain information in a database cache
#    © 2020 february - 1200 Web Development <http://1200wd.com/>
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
from datetime import datetime
from bitcoinlib.main import MAX_TRANSACTIONS
from bitcoinlib.db_cache import *
from bitcoinlib.services.baseclient import BaseClient, ClientError
from bitcoinlib.transactions import Transaction
from bitcoinlib.encoding import to_hexstring

PROVIDERNAME = 'caching'

_logger = logging.getLogger(__name__)


class CacheClient(BaseClient):

    def __init__(self, network, base_url='', denominator='', *args):
        self.session = DbInit().session
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, *args)

    def getbalance(self, addresslist):
        balance = 0
        for address in addresslist:
            pass
        return balance

    def getutxos(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):
        pass

    def gettransaction(self, txid):
        tx = self.session.query(dbCacheTransaction).filter_by(txid=txid).first()
        if not tx:
            raise ClientError("Transaction not found in cache")
        t = Transaction.import_raw(tx.raw, tx.network_name)
        t.date = tx.date
        t.confirmations = tx.confirmations
        t.block_hash = tx.block_hash
        t.block_height = tx.block_height
        t.status = 'confirmed'
        return t

    def gettransactions(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):
        pass

    def getrawtransaction(self, txid):
        pass

    def estimatefee(self, blocks):
        pass

    def blockcount(self):
        pass

    def mempool(self, txid):
        pass

    def store_transaction(self, t):
        # Only store complete and confirmed transaction in cache
        if not t.hash or not t.date or not t.block_height or not t.network or not t.confirmations:
            return False
        raw_hex = t.raw_hex()
        if not raw_hex:
            return False
        new_tx = dbCacheTransaction(txid=t.hash, date=t.date, confirmations=t.confirmations,
                                    block_height=t.block_height, block_hash=t.block_hash, network_name=t.network.name,
                                    raw=raw_hex)
        self.session.add(new_tx)
        self.session.commit()

#date = Column(DateTime, default=datetime.datetime.utcnow,
    #               doc="Date when transaction was confirmed and included in a block. "
    #                   "Or when it was created when transaction is not send or confirmed")
    # confirmations = Column(Integer, default=0,
    #                        doc="Number of confirmation when this transaction is included in a block. "
    #                            "Default is 0: unconfirmed")
    # block_height = Column(Integer, index=True, doc="Number of block this transaction is included in")
    # block_hash = Column(String(64), index=True, doc="Transaction is included in block with this hash")
    # network_name = Column(String(20), doc="Blockchain network name of this transaction")
    # raw = Column(Text(),
    #              doc="Raw transaction hexadecimal string. Transaction is included in raw format on the blockchain")
    # addresses = relationship('dbCacheAddress', secondary='cache_transactions_node')
    # nodes = relationship("dbCacheTransactionNode", cascade="all,delete",
    #                      doc="List of all inputs and outputs as dbCacheTransactionNode objects")