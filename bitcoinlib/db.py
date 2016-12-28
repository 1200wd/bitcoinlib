# -*- coding: utf-8 -*-
#
#    bitcoinlib db.py
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

import csv
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Float, String, Boolean, Sequence, ForeignKey
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
            if not os.path.exists(CURRENT_INSTALLDIR_DATA):
                os.makedirs(CURRENT_INSTALLDIR_DATA)
            Base.metadata.create_all(engine)
            self._import_config_data(Session)

        self.session = Session()

    @staticmethod
    def _import_config_data(ses):
        for fn in os.listdir(CURRENT_INSTALLDIR_DATA):
            if fn.endswith(".csv"):
                with open('%s%s' % (CURRENT_INSTALLDIR_DATA, fn), 'r') as csvfile:
                    session = ses()
                    tablename = fn.split('.')[0]
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if tablename == 'providers':
                            session.add(DbProvider(**row))
                        elif tablename == 'networks':
                            session.add(DbNetwork(**row))
                        else:
                            raise ImportError(
                                "Unrecognised table '%s', please update import mapping or remove file" % tablename)
                    session.commit()
                    session.close()


class DbWallet(Base):
    __tablename__ = 'wallets'
    id = Column(Integer, Sequence('wallet_id_seq'), primary_key=True)
    name = Column(String(50), unique=True)
    owner = Column(String(50))
    network_name = Column(String, ForeignKey('networks.name'))
    network = relationship("DbNetwork")
    purpose = Column(Integer, default=44)
    main_key_id = Column(Integer)
    keys = relationship("DbKey", back_populates="wallet")
    balance = Column(Float, default=0)


class DbKey(Base):
    __tablename__ = 'keys'
    id = Column(Integer, Sequence('key_id_seq'), primary_key=True)
    parent_id = Column(Integer, Sequence('parent_id_seq'))
    name = Column(String(50))
    account_id = Column(Integer)
    depth = Column(Integer)
    change = Column(Integer)  # TODO: 0 or 1 (0=external receiving address, 1=internal change addresses)
    address_index = Column(Integer)  # TODO: constraint gap no longer than 20
    key = Column(String(255), unique=True)
    key_wif = Column(String(255), unique=True)
    key_type = Column(String(10))
    address = Column(String(255), unique=True)
    purpose = Column(Integer, default=44)
    is_private = Column(Boolean)
    path = Column(String(100))
    wallet_id = Column(Integer, ForeignKey('wallets.id'))
    wallet = relationship("DbWallet", back_populates="keys")
    utxos = relationship("DbUtxo", back_populates="key")
    balance = Column(Float, default=0)


class DbNetwork(Base):
    __tablename__ = 'networks'
    name = Column(String(20), unique=True, primary_key=True)
    description = Column(String(50))


class DbProvider(Base):
    __tablename__ = 'providers'
    name = Column(String(50), primary_key=True, unique=True)
    provider = Column(String(50))
    network_name = Column(String, ForeignKey('networks.name'))
    network = relationship("DbNetwork")
    base_url = Column(String(100))
    api_key = Column(String(100))


class DbTransaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, Sequence('transaction_id_seq'), primary_key=True)
    transaction_id = Column(String(50), unique=True)


class DbUtxo(Base):
    __tablename__ = 'utxos'
    id = Column(Integer, Sequence('utxo_id_seq'), primary_key=True)
    key_id = Column(Integer, ForeignKey('keys.id'))
    key = relationship("DbKey", back_populates="utxos")
    tx_hash = Column(String(64), unique=True)
    confirmations = Column(Integer)
    output_n = Column(Integer)
    index = Column(Integer)
    value = Column(Float)
    script = Column(String)


if __name__ == '__main__':
    DbInit()
