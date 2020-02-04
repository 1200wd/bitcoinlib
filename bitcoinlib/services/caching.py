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
        # def __init__(self, network, provider, base_url, denominator, api_key='', provider_coin_id='',
        #              network_overrides=None, timeout=TIMEOUT_REQUESTS, blockcount=None):
    # def getbalance(self, addresslist):
    #     balance = 0
    #     for address in addresslist:
    #         pass
    #     return balance
    #
    # def getutxos(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):
    #     pass

    def gettransaction(self, txid):
        tx = self.session.query(dbCacheTransaction).filter_by(txid=txid).first()
        if not tx:
            return False
        t = Transaction.import_raw(tx.raw, tx.network_name)
        for n in tx.nodes:
            if n.is_input:
                t.inputs[n.output_n].value = n.value
            else:
                t.outputs[n.output_n].spent = n.spent
        t.hash = txid
        t.date = tx.date
        t.confirmations = tx.confirmations
        t.block_hash = tx.block_hash
        t.block_height = tx.block_height
        t.status = 'confirmed'
        t.fee = tx.fee
        t.update_totals()
        if t.coinbase:
            t.input_total = t.output_total
        _logger.info("Retrieved transaction %s from cache" % txid)
        return t

    def gettransactions(self, address, after_txid='', max_txs=MAX_TRANSACTIONS):
        print(self.blockcount)
        return False

    def getrawtransaction(self, txid):
        tx = self.session.query(dbCacheTransaction).filter_by(txid=txid).first()
        if not tx:
            return False
        return tx.raw

    # def estimatefee(self, blocks):
    #     pass
    #
    def blockcount(self):
        dbvar = self.session.query(dbCacheVars).filter_by(varname='blockcount', network_name=self.network.name).\
                                                filter(dbCacheVars.expires > datetime.datetime.now()).scalar()
        if dbvar:
            return int(dbvar.value)
        return False


    # def mempool(self, txid):
    #     pass

    def store_blockcount(self, blockcount):
        dbvar = dbCacheVars(varname='blockcount', network_name=self.network.name, value=blockcount, type='int',
                            expires=datetime.datetime.now() + datetime.timedelta(seconds=60))
        self.session.merge(dbvar)
        self.session.commit()

    def store_transaction(self, t):
        # Only store complete and confirmed transaction in cache
        if not t.hash or not t.date or not t.block_height or not t.network or not t.confirmations:
            _logger.info("Caching for provider %s: Incomplete transaction missing hash, date, block_height, "
                         "network or confirmations info" % self.provider)
            return False
        raw_hex = t.raw_hex()
        if not raw_hex:
            _logger.info("Caching for provider %s: Raw hex missing in transaction" % self.provider)
            return False
        if self.session.query(dbCacheTransaction).filter_by(txid=t.hash).count():
            return False
        new_tx = dbCacheTransaction(txid=t.hash, date=t.date, confirmations=t.confirmations,
                                    block_height=t.block_height, block_hash=t.block_hash, network_name=t.network.name,
                                    fee=t.fee, raw=raw_hex)
        for i in t.inputs:
            if i.value is None or i.address is None or i.output_n is None:
                _logger.info("Caching for provider %s: Input value, address or output_n missing" % self.provider)
                return False
            new_node = dbCacheTransactionNode(txid=t.hash, address=i.address, output_n=i.output_n_int, value=i.value,
                                              is_input=True)
            self.session.add(new_node)
        for o in t.outputs:
            if o.value is None or o.address is None or o.output_n is None or o.spent is None:
                _logger.info("Caching for provider %s: Output value, address, spent info or output_n missing" %
                             self.provider)
                return False
            new_node = dbCacheTransactionNode(txid=t.hash, address=o.address, output_n=o.output_n, value=o.value,
                                              is_input=False, spent=o.spent)
            self.session.add(new_node)

        self.session.add(new_tx)
        try:
            self.session.commit()
            _logger.info("Added transaction %s to cache" % t.hash)
        except Exception as e:
            _logger.warning("Could not add transaction to cache: %s" % e)
