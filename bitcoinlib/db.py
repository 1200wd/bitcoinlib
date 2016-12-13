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

import os
import csv
import binascii
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Boolean, Sequence, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


DEFAULT_DATABASEDIR = os.path.join(os.path.dirname(__file__), 'data/')
DEFAULT_DATABASEFILE = 'bitcoinlib.sqlite'
DEFAULT_DATABASE = DEFAULT_DATABASEDIR + DEFAULT_DATABASEFILE

Base = declarative_base()


class DbInit:

    def __init__(self, databasefile=DEFAULT_DATABASE):
        engine = create_engine('sqlite:///%s' % databasefile)
        Session = sessionmaker(bind=engine)

        if not os.path.exists(databasefile):
            if not os.path.exists(DEFAULT_DATABASEDIR):
                os.makedirs(DEFAULT_DATABASEDIR)
            Base.metadata.create_all(engine)
            self._import_config_data(Session)

        self.session = Session()

    @staticmethod
    def _import_config_data(ses):
        for fn in os.listdir(DEFAULT_DATABASEDIR):
            if fn.endswith(".csv"):
                with open('%s%s' % (DEFAULT_DATABASEDIR, fn), 'r') as file:
                    session = ses()
                    tablename = fn.split('.')[0]
                    reader = csv.DictReader(file)
                    for row in reader:
                        for fld in row:
                            if row[fld][:2] == 'h(':
                                row[fld] = binascii.unhexlify(row[fld].strip('h(').strip(')'))
                        if tablename == 'networks':
                            session.add(DbNetwork(**row))
                        elif tablename == 'providers':
                            session.add(DbProvider(**row))
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
    network = Column(String(20))
    purpose = Column(Integer, default=44)
    main_key_id = Column(Integer)
    keys = relationship("DbKey", back_populates="wallet")
    balance = Column(Integer)


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
    address = Column(String(255), unique=True)
    purpose = Column(Integer, default=44)
    is_private = Column(Boolean)
    path = Column(String(100))
    wallet_id = Column(Integer, ForeignKey('wallets.id'))
    wallet = relationship("DbWallet", back_populates="keys")
    balance = Column(Integer)


class DbNetwork(Base):
    __tablename__ = 'networks'
    name = Column(String(20), unique=True, primary_key=True)
    description = Column(String(50))
    symbol = Column(String(5), unique=True)
    code = Column(String(10), unique=True)
    address = Column(String(10), unique=True)
    address_p2sh = Column(String(10), unique=True)
    wif = Column(String(10), unique=True)
    hdkey_private = Column(String(10), unique=True)
    hdkey_public = Column(String(10), unique=True)
    bip44_cointype = Column(String(10), unique=True)


class DbProvider(Base):
    __tablename__ = 'providers'
    id = Column(Integer, Sequence('provider_id_seq'), primary_key=True)
    name = Column(String(50), unique=True)
    network = Column(String(20))
    base_url = Column(String(100))
    api_key = Column(String(100))


class DbTransaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, Sequence('transaction_id_seq'), primary_key=True)
    transaction_id = Column(String(50), unique=True)


class DbUtxo(Base):
    __tablename__ = 'utxos'
    id = Column(Integer, Sequence('utxo_id_seq'), primary_key=True)


if __name__ == '__main__':
    DbInit()