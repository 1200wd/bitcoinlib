# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    IMPORT DATABASE - Extract wallet keys and information from old Bitcoinlib database and move to actual database
#    © 2024 February - 1200 Web Development <http://1200wd.com/>
#
# TODO: Currently skips multisig wallets


import sqlalchemy as sa
from sqlalchemy.sql import text
from bitcoinlib.main import *
from bitcoinlib.wallets import Wallet, wallet_create_or_open


DATABASE_TO_IMPORT = 'sqlite:///' + os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib_test.sqlite')

def import_database():
    print(DATABASE_TO_IMPORT)
    engine = sa.create_engine(DATABASE_TO_IMPORT)
    con = engine.connect()

    wallets = con.execute(text(
        'SELECT w.name, k.private, w.owner, w.network_name, k.account_id, k.address, w.witness_type FROM wallets AS w '
        'INNER JOIN keys AS k ON w.main_key_id = k.id WHERE multisig=0')).fetchall()

    for wallet in wallets:
        print("Import wallet %s" % wallet[0])
        w = wallet_create_or_open(wallet[0], wallet[1], wallet[2], wallet[3], wallet[4], witness_type=wallet[6])


if __name__ == '__main__':
    import_database()
