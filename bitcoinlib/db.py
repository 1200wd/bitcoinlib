# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    DataBase - SqlAlchemy database definitions
#    © 2017 September - 1200 Web Development <http://1200wd.com/>
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
try:
    import enum
except:
    import enum34 as enum
import datetime
from sqlalchemy import create_engine, func
from sqlalchemy import Column, Integer, UniqueConstraint, CheckConstraint, String, Boolean, Sequence, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from bitcoinlib.main import *

_logger = logging.getLogger(__name__)
_logger.info("Using Database %s" % DEFAULT_DATABASE)
Base = declarative_base()


class DbInit:
    """
    Initialize database and open session

    Import data if database did not exist yet

    """
    def __init__(self, databasefile=DEFAULT_DATABASE):
        self.engine = create_engine('sqlite:///%s' % databasefile)
        Session = sessionmaker(bind=self.engine)

        if not os.path.exists(databasefile):
            if not os.path.exists(DEFAULT_DATABASEDIR):
                os.makedirs(DEFAULT_DATABASEDIR)
            if not os.path.exists(DEFAULT_SETTINGSDIR):
                os.makedirs(DEFAULT_SETTINGSDIR)
            Base.metadata.create_all(self.engine)
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
    scheme = Column(String(25))
    main_key_id = Column(Integer)
    keys = relationship("DbKey", back_populates="wallet")
    transactions = relationship("DbTransaction", back_populates="wallet")
    # balance = Column(Integer, default=0)
    multisig_n_required = Column(Integer, default=1, doc="Number of required signature for multisig, "
                                                         "only used for multisignature master key")
    sort_keys = Column(Boolean, default=False, doc="Sort keys in multisig wallet")
    parent_id = Column(Integer, ForeignKey('wallets.id'))
    children = relationship("DbWallet", lazy="joined", join_depth=2)

    __table_args__ = (CheckConstraint(scheme.in_(['single', 'bip44', 'multisig']), name='constrained_allowed_schemes'),)

    def __repr__(self):
        return "<DbWallet(name='%s', network='%s'>" % (self.name, self.network_name)


class DbKeyMultisigChildren(Base):
    """
    Use many-to-many relationship for multisig keys. A multisig keys contains 2 or more child keys
    and a child key can be used in more then one multisig key.

    """
    __tablename__ = 'key_multisig_children'

    parent_id = Column(Integer, ForeignKey('keys.id'), primary_key=True)
    child_id = Column(Integer, ForeignKey('keys.id'), primary_key=True)
    key_order = Column(Integer, Sequence('key_multisig_children_id_seq'))


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
    address_index = Column(Integer)
    public = Column(String(255), index=True)
    private = Column(String(255), index=True)
    wif = Column(String(255), index=True)
    compressed = Column(Boolean, default=True)
    key_type = Column(String(10), default='bip32')
    address = Column(String(255), index=True)
    purpose = Column(Integer, default=44)
    is_private = Column(Boolean)
    path = Column(String(100))
    wallet_id = Column(Integer, ForeignKey('wallets.id'), index=True)
    wallet = relationship("DbWallet", back_populates="keys")
    transaction_inputs = relationship("DbTransactionInput", cascade="all,delete", back_populates="key")
    transaction_outputs = relationship("DbTransactionOutput", cascade="all,delete", back_populates="key")
    balance = Column(Integer, default=0)
    used = Column(Boolean, default=False)
    network_name = Column(String, ForeignKey('networks.name'))
    network = relationship("DbNetwork")
    multisig_parents = relationship("DbKeyMultisigChildren", backref='child_key',
                                    primaryjoin=id == DbKeyMultisigChildren.child_id)
    multisig_children = relationship("DbKeyMultisigChildren", backref='parent_key',
                                     order_by="DbKeyMultisigChildren.key_order",
                                     primaryjoin=id == DbKeyMultisigChildren.parent_id)

    __table_args__ = (
        CheckConstraint(key_type.in_(['single', 'bip32', 'multisig']), name='constraint_key_types_allowed'),
        UniqueConstraint('wallet_id', 'public', name='constraint_wallet_pubkey_unique'),
        UniqueConstraint('wallet_id', 'private', name='constraint_wallet_privkey_unique'),
        UniqueConstraint('wallet_id', 'wif', name='constraint_wallet_wif_unique'),
        UniqueConstraint('wallet_id', 'address', name='constraint_wallet_address_unique'),
    )

    def __repr__(self):
        return "<DbKey(id='%s', name='%s', wif='%s'>" % (self.id, self.name, self.wif)


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
    """
    Incoming or Outgoing transaction Enumeration
    """
    incoming = 1
    outgoing = 2


class DbTransaction(Base):
    """
    Database definitions for transactions in Sqlalchemy format
    
    Refers to 1 or more keys which can be part of a wallet
    
    """
    __tablename__ = 'transactions'
    id = Column(Integer, Sequence('transaction_id_seq'), primary_key=True)
    hash = Column(String(64), index=True)
    wallet_id = Column(Integer, ForeignKey('wallets.id'), index=True)
    wallet = relationship("DbWallet", back_populates="transactions")
    version = Column(Integer, default=1)
    locktime = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    coinbase = Column(Boolean, default=False)
    confirmations = Column(Integer, default=0)
    block_height = Column(Integer, index=True)
    block_hash = Column(String(64), index=True)
    size = Column(Integer)
    fee = Column(Integer)
    inputs = relationship("DbTransactionInput", cascade="all,delete")
    outputs = relationship("DbTransactionOutput", cascade="all,delete")
    status = Column(String, default='new')
    input_total = Column(Integer, default=0)
    output_total = Column(Integer, default=0)
    network_name = Column(String, ForeignKey('networks.name'))
    network = relationship("DbNetwork")
    raw = Column(String)

    __table_args__ = (
        UniqueConstraint('wallet_id', 'hash', name='constraint_wallet_transaction_hash_unique'),
        CheckConstraint(status.in_(['new', 'incomplete', 'unconfirmed', 'confirmed']),
                        name='constraint_status_allowed'),
    )

    def __repr__(self):
        return "<DbTransaction(hash='%s', confirmations='%s')>" % (self.hash, self.confirmations)


class DbTransactionInput(Base):
    """
    Transaction Input Table

    Relates to Transaction table and Key table

    """
    __tablename__ = 'transaction_inputs'
    transaction_id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    transaction = relationship("DbTransaction", back_populates='inputs')
    index_n = Column(Integer, primary_key=True)
    key_id = Column(Integer, ForeignKey('keys.id'), index=True)
    key = relationship("DbKey", back_populates="transaction_inputs")
    prev_hash = Column(String(64))
    output_n = Column(Integer)
    script = Column(String)
    script_type = Column(String, default='p2pkh')
    sequence = Column(Integer)
    value = Column(Integer, default=0)
    double_spend = Column(Boolean, default=False)

    __table_args__ = (CheckConstraint(script_type.in_(['', 'coinbase', 'sig_pubkey', 'p2pkh', 'p2sh_multisig',
                                                       'multisig', 'p2sh', 'pubkey', 'nulldata']),
                                      name='constraint_script_types_allowed'),)


class DbTransactionOutput(Base):
    """
    Transaction Output Table

    Relates to Transaction and Key table

    When spent is False output is considered an UTXO

    """
    __tablename__ = 'transaction_outputs'
    transaction_id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    transaction = relationship("DbTransaction", back_populates='outputs')
    output_n = Column(Integer, primary_key=True)
    key_id = Column(Integer, ForeignKey('keys.id'), index=True)
    key = relationship("DbKey", back_populates="transaction_outputs")
    script = Column(String)
    script_type = Column(String, default='pubkey')
    value = Column(Integer, default=0)
    spent = Column(Boolean(), default=False)

    # TODO: sig_pubkey ?
    __table_args__ = (CheckConstraint(script_type.in_(['', 'sig_pubkey', 'p2pkh', 'p2sh_multisig', 'multisig', 'p2sh',
                                                       'pubkey', 'nulldata']),
                                      name='constraint_script_types_allowed'),)


if __name__ == '__main__':
    DbInit()
