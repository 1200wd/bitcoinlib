# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Cache DataBase - SqlAlchemy database definitions for caching
#    © 2020 February - 1200 Web Development <http://1200wd.com/>
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

try:
    import enum
except ImportError:
    import enum34 as enum
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, ForeignKey, DateTime, Numeric, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from bitcoinlib.main import *

_logger = logging.getLogger(__name__)
_logger.info("Using Cache Database %s" % DEFAULT_DATABASE_CACHE)
Base = declarative_base()


class DbInit:
    """
    Initialize database and open session

    Create new database if is doesn't exist yet

    """
    def __init__(self, db_uri=None):
        self.engine = None
        self.session = None
        if db_uri is None:
            db_uri = DEFAULT_DATABASE_CACHE
        elif not db_uri:
            return
        o = urlparse(db_uri)

        if not o.scheme or len(o.scheme) < 2:
            db_uri = 'sqlite:///%s' % db_uri
        if db_uri.startswith("sqlite://") and ALLOW_DATABASE_THREADS:
            if "?" in db_uri:
                db_uri += "&"
            else:
                db_uri += "?"
            db_uri += "check_same_thread=False"

        self.engine = create_engine(db_uri, isolation_level='READ UNCOMMITTED')
        Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.session = Session()


class DbCacheTransactionNode(Base):
    """
    Link table for cache transactions and addresses
    """
    __tablename__ = 'cache_transactions_node'
    txid = Column(String(64), ForeignKey('cache_transactions.txid'), primary_key=True)
    transaction = relationship("DbCacheTransaction", back_populates='nodes', doc="Related transaction object")
    # TODO: Add fields to allow to create full transaction (+ split input / output?)
    # index_n = Column(BigInteger, primary_key=True,
    #                  doc="Output_n of previous transaction output that is spent in this input")
    # prev_hash = Column(String(64),
    #                    doc="Transaction hash of previous transaction. Previous unspent outputs (UTXO) is spent "
    #                        "in this input")
    output_n = Column(BigInteger, primary_key=True,
                      doc="Output_n of previous transaction output that is spent in this input")
    value = Column(Numeric(25, 0, asdecimal=False), default=0, doc="Value of transaction input")
    is_input = Column(Boolean, primary_key=True, doc="True if input, False if output")
    address = Column(String(255), doc="Address string base32 or base58 encoded")
    # script = Column(Text, doc="Unlocking script to unlock previous locked output")
    # sequence = Column(BigInteger, doc="Transaction sequence number. Used for timelock transaction inputs")
    spent = Column(Boolean, default=None, doc="Is output spent?")
    spending_txid = Column(String(64), doc="Transaction hash of input which spends this output")
    spending_index_n = Column(Integer, doc="Index number of transaction input which spends this output")


class DbCacheTransaction(Base):
    """
    Transaction Cache Table

    Database which stores transactions received from service providers as cache

    """
    __tablename__ = 'cache_transactions'
    txid = Column(String(64), primary_key=True, doc="Hexadecimal representation of transaction hash or transaction ID")
    date = Column(DateTime, default=datetime.utcnow,
                  doc="Date when transaction was confirmed and included in a block. "
                      "Or when it was created when transaction is not send or confirmed")
    # TODO: Add fields to allow to create full transaction
    # witness_type = Column(String(20), default='legacy', doc="Is this a legacy or segwit transaction?")
    # version = Column(Integer, default=1,
    #                  doc="Tranaction version. Default is 1 but some wallets use another version number")
    # locktime = Column(Integer, default=0,
    #                   doc="Transaction level locktime. Locks the transaction until a specified block "
    #                       "(value from 1 to 5 million) or until a certain time (Timestamp in seconds after 1-jan-1970)."
    #                       " Default value is 0 for transactions without locktime")
    # coinbase = Column(Boolean, default=False, doc="Is True when this is a coinbase transaction, default is False")
    confirmations = Column(Integer, default=0,
                           doc="Number of confirmation when this transaction is included in a block. "
                               "Default is 0: unconfirmed")
    block_height = Column(Integer, index=True, doc="Height of block this transaction is included in")
    block_hash = Column(String(64), index=True, doc="Hash of block this transaction is included in")  # TODO: Remove, is redundant
    network_name = Column(String(20), doc="Blockchain network name of this transaction")
    fee = Column(BigInteger, doc="Transaction fee")
    raw = Column(Text(),
                 doc="Raw transaction hexadecimal string. Transaction is included in raw format on the blockchain")
    nodes = relationship("DbCacheTransactionNode", cascade="all,delete",
                         doc="List of all inputs and outputs as DbCacheTransactionNode objects")
    order_n = Column(Integer, doc="Order of transaction in block")


class DbCacheAddress(Base):
    """
    Address Cache Table

    Stores transactions and unspent outputs (UTXO's) per address

    """
    __tablename__ = 'cache_address'
    address = Column(String(255), primary_key=True, doc="Address string base32 or base58 encoded")
    network_name = Column(String(20), doc="Blockchain network name of this transaction")
    balance = Column(Numeric(25, 0, asdecimal=False), default=0, doc="Total balance of UTXO's linked to this key")
    last_block = Column(Integer, doc="Number of last updated block")
    last_txid = Column(String(64), doc="Transaction ID of latest transaction in cache")
    n_utxos = Column(Integer, doc="Total number of UTXO's for this address")
    n_txs = Column(Integer, doc="Total number of transactions for this address")


class DbCacheBlock(Base):
    """
    Block Cache Table

    Stores block headers
    """
    __tablename__ = 'cache_blocks'
    height = Column(Integer, primary_key=True, doc="Height or sequence number for this block")
    block_hash = Column(LargeBinary(32), index=True, doc="Hash of this block")
    network_name = Column(String(20), doc="Blockchain network name")
    version = Column(BigInteger, doc="Block version to specify which features are used (hex)")
    prev_block = Column(LargeBinary(32), doc="Block hash of previous block")
    merkle_root = Column(LargeBinary(32), doc="Merkle root used to validate transaction in block")
    time = Column(BigInteger, doc="Timestamp to indicated when block was created")
    bits = Column(BigInteger, doc="Encoding for proof-of-work, used to determine target and difficulty")
    nonce = Column(BigInteger, doc="Nonce (number used only once or n-once) is used to create different block hashes")
    tx_count = Column(Integer, doc="Number of transactions included in this block")


class DbCacheVars(Base):
    """
    Table to store various blockchain related variables
    """
    __tablename__ = 'cache_variables'
    varname = Column(String(50), primary_key=True, doc="Variable unique name")
    network_name = Column(String(20), primary_key=True, doc="Blockchain network name of this transaction")
    value = Column(String(255), doc="Value of variable")
    type = Column(String(20), doc="Type of variable: int, string or float")
    expires = Column(DateTime, doc="Datetime value when variable expires")


if __name__ == '__main__':
    DbInit()
