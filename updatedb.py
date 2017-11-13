# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Update database
#    © 2017 November - 1200 Web Development <http://1200wd.com/>
#
#    This script creates a database with latest structure and copies only wallets and keys from old database
#    Transactions, UTXO's and values are not copied, but can be recreated with utxos_update and transaction_update
#    methods of the Wallet class.
#

import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shutil import move
from bitcoinlib.main import DEFAULT_DATABASE, DEFAULT_DATABASEDIR
from bitcoinlib.db import Base, DbWallet, DbKey, DbKeyMultisigChildren


DATABASE_BACKUP = os.path.join(DEFAULT_DATABASEDIR, "bitcoinlib.backup-%s.sqlite" %
                               datetime.now().strftime("%Y%m%d-%I:%M"))

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

print("Database %s has been updated, backup of old database has been created at %s" %
      (DEFAULT_DATABASE, DATABASE_BACKUP))