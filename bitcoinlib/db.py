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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy import ForeignKey

Base = declarative_base()
engine = create_engine('sqlite:///data/bitcoinlib.sqlite', echo=True)

class Wallet(Base):
    __tablename__ = 'wallets'
    id = Column(Integer, Sequence('wallet_id_seq'), primary_key=True)
    name = Column(String(50))
    owner = Column(String(50))

class Network(Base):
    __tablename__ = 'networks'
    id = Column(Integer, Sequence('network_id_seq'), primary_key=True)
    name = Column(String(50))

class Key(Base):
    __tablename__ = 'keys'
    id = Column(Integer, Sequence('key_id_seq'), primary_key=True)
    name = Column(String(50))
    network_id = Column(Integer, ForeignKey('networks.id'))
    wallet_id = Column(Integer, ForeignKey('wallets.id'))
    key = Column(Integer)
    key_wif = Column(String(255))
    address = Column(String(255))


Base.metadata.create_all(engine)