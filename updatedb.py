# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Update database to new version -
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
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shutil import move
from bitcoinlib.main import DEFAULT_DATABASE, DEFAULT_DATABASEDIR
from bitcoinlib.db import Base, DbWallet, DbKey, DbKeyMultisigChildren


DATABASE_BACKUP = os.path.join(DEFAULT_DATABASEDIR, "bitcoinlib.backup-%d.sqlite" %
                               datetime.now().strftime("%A, %d. %B %Y %I:%M%p"))

# Move old database to temporary database
move(DEFAULT_DATABASE, DATABASE_BACKUP)

# Create new database
engine = create_engine('sqlite:///%s' % DEFAULT_DATABASE)
Base.metadata.create_all(engine)

# Copy wallets and keys to new database
Session = sessionmaker(bind=engine)
session = Session()

engine_backup = create_engine('sqlite:///%s' % DATABASE_BACKUP)
Session_backup = sessionmaker(bind=engine_backup)
session_backup = Session_backup()

wallets = session_backup.query(DbWallet).all()
for wallet in wallets:
    fields = wallet.__dict__
    del(fields['children'])
    del(fields['_sa_instance_state'])
    session.add(DbWallet(**fields))
session.commit()

keys = session_backup.query(DbKey).all()
for key in keys:
    fields = key.__dict__
    del (fields['_sa_instance_state'])
    fields['used'] = False  # To force rescan of all keys
    # db_main_key = DbKey(**fields)
    session.add(DbKey(**fields))
session.commit()

keysubs = session_backup.query(DbKeyMultisigChildren).all()
for keysub in keysubs:
    fields = keysub.__dict__
    del (fields['_sa_instance_state'])
    session.add(DbKeyMultisigChildren(**fields))
session.commit()
