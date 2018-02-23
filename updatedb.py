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
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shutil import move
from bitcoinlib.main import DEFAULT_DATABASE, DEFAULT_DATABASEDIR
from bitcoinlib.db import Base, DbWallet, DbKey, DbKeyMultisigChildren
try:
    input = raw_input
except NameError:
    pass

DATABASE_BACKUP = os.path.join(DEFAULT_DATABASEDIR, "bitcoinlib.backup-%s.sqlite" %
                               datetime.now().strftime("%Y%m%d-%I:%M"))

print("Wallet and Key data will be copied to new database. Transaction data will NOT be copied")
print("Old database will be backed up to %s" % DATABASE_BACKUP)

if input("Type 'y' or 'Y' to continue or any other key to cancel: ") not in ['y', 'Y']:
    print("Aborted by user")
    sys.exit()

# Move old database to temporary database
move(DEFAULT_DATABASE, DATABASE_BACKUP)

try:
    # Create new database
    engine = create_engine('sqlite:///%s' % DEFAULT_DATABASE)
    Base.metadata.create_all(engine)

    # Copy wallets and keys to new database
    Session = sessionmaker(bind=engine)
    session = Session()

    engine_backup = create_engine('sqlite:///%s' % DATABASE_BACKUP)
    Session_backup = sessionmaker(bind=engine_backup)
    session_backup = Session_backup()

    wallets = session_backup.execute("SELECT * FROM wallets")
    for wallet in wallets:
        fields = dict(wallet)

        # Update, rename and delete fields
        try:
            del(fields['balance'])
        except:
            pass

        session.add(DbWallet(**fields))
    session.commit()

    keys = session_backup.execute("SELECT * FROM keys")
    for key in keys:
        fields = dict(key)

        # Update, rename and delete fields
        if 'key' in fields:
            if fields['is_private']:
                fields['private'] = fields['key']
            else:
                fields['public'] = fields['key']
            del(fields['key'])

        fields['used'] = False  # To force rescan of all keys
        session.add(DbKey(**fields))
    session.commit()

    keysubs = session_backup.execute("SELECT * FROM key_multisig_children")
    for keysub in keysubs:
        fields = dict(keysub)
        session.add(DbKeyMultisigChildren(**fields))
    session.commit()

    print("Database %s has been updated, backup of old database has been created at %s" %
          (DEFAULT_DATABASE, DATABASE_BACKUP))

except Exception as e:
    # If ANYTHING goes wrong move back to old database
    print(e)
    print("Errors occured, database not updated")
    move(DATABASE_BACKUP, DEFAULT_DATABASE)