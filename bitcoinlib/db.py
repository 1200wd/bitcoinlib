# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    DataBase - SqlAlchemy database definitions
#    © 2017 April - 1200 Web Development <http://1200wd.com/>
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

import csv
import enum
import datetime
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Float, CheckConstraint, String, Boolean, Sequence, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from bitcoinlib.main import *

_logger = logging.getLogger(__name__)
_logger.info("Using Database %s" % DEFAULT_DATABASE)
Base = declarative_base()


class DbInit:

    def __init__(self, databasefile=DEFAULT_DATABASE):
        engine = create_engine('sqlite:///%s' % databasefile)
        Session = sessionmaker(bind=engine)

        if not os.path.exists(databasefile):
            if not os.path.exists(DEFAULT_DATABASEDIR):
                os.makedirs(DEFAULT_DATABASEDIR)
            if not os.path.exists(DEFAULT_SETTINGSDIR):
                os.makedirs(DEFAULT_SETTINGSDIR)
            Base.metadata.create_all(engine)
            self._import_config_data(Session)

        self.session = Session()

    @staticmethod
    def _import_config_data(ses):
        for fn in os.listdir(DEFAULT_SETTINGSDIR):
            if fn.endswith(".csv"):
                with open('%s%s' % (DEFAULT_SETTINGSDIR, fn), 'r') as csvfile:
                    session = ses()
                    tablename = fn.split('.')[0]
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if tablename == 'networks':
                            session.add(DbNetwork(**row))
                        else:
                            raise ImportError(
                                "Unrecognised table '%s', please update import mapping or remove file" % tablename)
                    session.commit()
                    session.close()


class DbWallet(Base):
    """
    Database definitions for wallets in Sqlalchemy format
    
    Contains one or more keys.
     
    """
    __tablename__ = 'wallets'
    id = Column(Integer, Sequence('wallet_id_seq'), primary_key=True)
    name = Column(String(50), unique=True)
    owner = Column(String(50))
    network_name = Column(String, ForeignKey('networks.name'))
    network = relationship("DbNetwork")
    purpose = Column(Integer, default=44)
    main_key_id = Column(Integer)
    keys = relationship("DbKey", back_populates="wallet")
    balance = Column(Integer, default=0)

    def __repr__(self):
        return "<DbWallet(name='%s', network='%s'>" % (self.name, self.network_name)


class DbKey(Base):
    """
    Database definitions for keys in Sqlalchemy format
    
    Part of a wallet, and used by transactions

    """
    __tablename__ = 'keys'
    id = Column(Integer, Sequence('key_id_seq'), primary_key=True)
    parent_id = Column(Integer, Sequence('parent_id_seq'))
    name = Column(String(50), index=True)
    account_id = Column(Integer, index=True)
    depth = Column(Integer)
    change = Column(Integer)
    address_index = Column(Integer, index=True)
    key = Column(String(255), unique=True)
    wif = Column(String(255), unique=True, index=True)
    key_type = Column(String(10), default='bip32')
    address = Column(String(255), unique=True)
    purpose = Column(Integer, default=44)
    is_private = Column(Boolean)
    path = Column(String(100))
    wallet_id = Column(Integer, ForeignKey('wallets.id'))
    wallet = relationship("DbWallet", back_populates="keys")
    transaction_inputs = relationship("DbTransactionInput", cascade="all,delete", back_populates="key")
    transaction_outputs = relationship("DbTransactionOutput", cascade="all,delete", back_populates="key")
    balance = Column(Integer, default=0)
    used = Column(Boolean, default=False)
    network_name = Column(String, ForeignKey('networks.name'))
    network = relationship("DbNetwork")
    tree_index = Column(Integer, default=0, doc="Index of key structure. Can be used to disdinguish multiple key "
                                                "structures, i.e. for multisig or importing external unrelated keys")
    # TODO: Put in seperate table with n-m relation, so key can be used for multiple multisig structures (?)
    redeemscript = Column(String, doc="Raw redeemscript for P2SH transactions used for multisig")
    multisig_master_key_id = Column(Integer, doc="This key is part of a multisig key and related to this master key ID")
    multisig_n_required = Column(Integer, doc="Number of required signature for multisig, only used for "
                                              "multisignature master key")
    multisig_key_order = Column(Integer, doc="Key order for multisignature")

    __table_args__ = (CheckConstraint(key_type.in_(['single', 'bip32', 'bip44', 'multisig'])),)

    def __repr__(self):
        return "<DbKey(id='%s', name='%s', key='%s'>" % (self.id, self.name, self.wif)


class DbNetwork(Base):
    """
    Database definitions for networks in Sqlalchemy format

    """
    __tablename__ = 'networks'
    name = Column(String(20), unique=True, primary_key=True)
    description = Column(String(50))

    def __repr__(self):
        return "<DbNetwork(name='%s', description='%s'>" % (self.name, self.description)


class TransactionType(enum.Enum):
    incoming = 1
    outgoing = 2


class DbTransaction(Base):
    """
    Database definitions for transactions in Sqlalchemy format
    
    Refers to 1 or more keys which can be part of a wallet
    
    """
    __tablename__ = 'transactions'
    id = Column(Integer, Sequence('transaction_id_seq'), primary_key=True)
    hash = Column(String(64), unique=True)
    version = Column(Integer, default=1)
    lock_time = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    coinbase = Column(Boolean, default=False)
    confirmations = Column(Integer, default=0)
    size = Column(Integer)
    inputs = relationship("DbTransactionInput", cascade="all,delete")
    outputs = relationship("DbTransactionOutput", cascade="all,delete")
    # TODO: TYPE: watch-only, wallet, incoming, outgoing
    # TODO: Add network field (?)

    def __repr__(self):
        return "<DbTransaction(hash='%s', confirmations='%s')>" % (self.hash, self.confirmations)


class DbTransactionInput(Base):
    __tablename__ = 'transaction_inputs'
    transaction_id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    transaction = relationship("DbTransaction", back_populates='inputs')
    index = Column(Integer, primary_key=True)
    prev_hash = Column(String(64))
    output_n = Column(Integer, default=0)
    script = Column(String)
    sequence = Column(Integer)
    value = Column(Integer, default=0)
    spend = Column(Boolean(), default=False)
    key_id = Column(Integer, ForeignKey('keys.id'), index=True)
    key = relationship("DbKey", back_populates="transaction_inputs")


class DbTransactionOutput(Base):
    __tablename__ = 'transaction_outputs'
    transaction_id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    transaction = relationship("DbTransaction", back_populates='outputs')
    output_n = Column(Integer, primary_key=True)
    key_id = Column(Integer, ForeignKey('keys.id'), index=True)
    key = relationship("DbKey", back_populates="transaction_outputs")
    script = Column(String)
    value = Column(Integer, default=0)
    spend = Column(Boolean(), default=False)


if __name__ == '__main__':
    DbInit()
