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

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Boolean, Sequence, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASEFILE = 'data/bitcoinlib.sqlite'
Base = declarative_base()
engine = create_engine('sqlite:///%s' % DATABASEFILE)
Session = sessionmaker(bind=engine)
session = Session()

class DbWallet(Base):
    __tablename__ = 'dbwallets'
    id = Column(Integer, Sequence('wallet_id_seq'), primary_key=True)
    name = Column(String(50), unique=True)
    owner = Column(String(50))
    network = Column(String(20))
    purpose = Column(Integer, default=44)
    main_key_id = Column(Integer, ForeignKey('dbwalletkeys.id'))


# class DbWalletAccount(Base):
#     __tablename__ = 'dbwalletaccounts'
#     id = Column(Integer, Sequence('account_id_seq'), primary_key=True)
#     wallet_id = Column(Integer, ForeignKey('dbwallets.id'))
#     name = Column(String(50), unique=True)


# Use following BIP 44 path
# m / purpose' / coin_type' / account' / change / address_index
# Path: Master / Bip44 / Bitcoin / Account 1 / Internal or External / Index
class DbWalletKey(Base):
    __tablename__ = 'dbwalletkeys'
    id = Column(Integer, Sequence('key_id_seq'), primary_key=True)
    parent_id = Column(Integer, Sequence('parent_id_seq'))
    name = Column(String(50))
    wallet_id = Column(Integer, ForeignKey('dbwallets.id'))
    network = Column(String(20))
    account_id = Column(Integer)
    depth = Column(Integer)
    change = Column(Integer) # TODO: 0 or 1 (0=external receiving address, 1=internal change addresses)
    address_index = Column(Integer) # TODO: constraint gap no longer than 20
    key = Column(String(255), unique=True)
    key_wif = Column(String(255), unique=True)
    address = Column(String(255), unique=True)
    purpose = Column(Integer, default=44)
    is_private = Column(Boolean)
    path = Column(String(100))

Base.metadata.create_all(engine)
