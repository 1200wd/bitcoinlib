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

        if not os.path.exists(DEFAULT_DATABASEDIR):
            os.makedirs(DEFAULT_DATABASEDIR)
        Base.metadata.create_all(engine)
        self.session = Session()


class DbWallet(Base):
    __tablename__ = 'dbwallets'
    id = Column(Integer, Sequence('wallet_id_seq'), primary_key=True)
    name = Column(String(50), unique=True)
    owner = Column(String(50))
    network = Column(String(20))
    purpose = Column(Integer, default=44)
    # main_key_id = Column(Integer, ForeignKey('dbwalletkeys.id'))
    main_key_id = Column(Integer)
    keys = relationship("DbWalletKey", back_populates="wallet")


# Use following BIP 44 path
# m / purpose' / coin_type' / account' / change / address_index
# Path: Master / Bip44 / Bitcoin / Account 1 / Internal or External / Index
class DbWalletKey(Base):
    __tablename__ = 'dbwalletkeys'
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
    wallet_id = Column(Integer, ForeignKey('dbwallets.id'))
    wallet = relationship("DbWallet", back_populates="keys")
