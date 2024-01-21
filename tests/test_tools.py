# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Bitcoinlib Tools
#    © 2018 - 2024 January - 1200 Web Development <http://1200wd.com/>
#

import os
import sys
import unittest
from subprocess import Popen, PIPE

try:
    import mysql.connector
    import psycopg2
    from parameterized import parameterized_class
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    pass  # Only necessary when mysql or postgres is used

from bitcoinlib.main import UNITTESTS_FULL_DATABASE_TEST
from bitcoinlib.db import BCL_DATABASE_DIR
from bitcoinlib.encoding import normalize_string

SQLITE_DATABASE_FILE = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlib.unittest.sqlite')
DATABASE_NAME = 'bitcoinlib_unittest'


def init_sqlite(_):
    if os.path.isfile(SQLITE_DATABASE_FILE):
        os.remove(SQLITE_DATABASE_FILE)


def init_postgresql(_):
    con = psycopg2.connect(user='postgres', host='localhost', password='postgres')
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
        sql.Identifier(DATABASE_NAME))
    )
    cur.execute(sql.SQL("CREATE DATABASE {}").format(
        sql.Identifier(DATABASE_NAME))
    )
    cur.close()
    con.close()


def init_mysql(_):
    con = mysql.connector.connect(user='root', host='localhost')
    cur = con.cursor()
    cur.execute("DROP DATABASE IF EXISTS {}".format(DATABASE_NAME))
    cur.execute("CREATE DATABASE {}".format(DATABASE_NAME))
    con.commit()
    cur.close()
    con.close()


# db_uris = (('sqlite:///' + SQLITE_DATABASE_FILE, init_sqlite),)
# if UNITTESTS_FULL_DATABASE_TEST:
#     db_uris += (
#         ('mysql://root@localhost:3306/' + DATABASE_NAME, init_mysql),
#         ('postgresql://postgres:postgres@localhost:5432/' + DATABASE_NAME, init_postgresql),
#     )


# @parameterized_class(('DATABASE_URI', 'init_fn'), db_uris)
class TestToolsCommandLineWallet(unittest.TestCase):

    def setUp(self):
        # self.init_fn()
        init_sqlite(self)
        self.python_executable = sys.executable
        self.clw_executable = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            '../bitcoinlib/tools/clw.py'))
        self.DATABASE_URI = SQLITE_DATABASE_FILE

    def test_tools_clw_create_wallet(self):
        cmd_wlt_create = '%s %s new -w test --passphrase "emotion camp sponsor curious bacon squeeze bean world ' \
                         'actual chicken obscure spray" -r -d %s' % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        cmd_wlt_delete = "%s %s -w test --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        output_wlt_create = "bc1qdv5tuzrluh4lzhnu59je9n83w4hkqjhgg44d5g"
        output_wlt_delete = "Wallet test has been removed"

        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'y')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))
        process = Popen(cmd_wlt_delete, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'test')
        self.assertIn(output_wlt_delete, normalize_string(poutput[0]))

    def test_tools_clw_create_multisig_wallet(self):
        key_list = [
            'tprv8ZgxMBicQKsPd1Q44tfDiZC98iYouKRC2CzjT3HGt1yYw2zuX2awTotzGAZQEAU9bi2M5MCj8iedP9MREPjUgpDEBwBgGi2C8eK'
            '5zNYeiX8',
            'tprv8ZgxMBicQKsPeUbMS6kswJc11zgVEXUnUZuGo3bF6bBrAg1ieFfUdPc9UHqbD5HcXizThrcKike1c4z6xHrz6MWGwy8L6YKVbgJ'
            'MeQHdWDp'
        ]
        cmd_wlt_create = "%s %s new -w testms -m 2 2 %s -r -n testnet -d %s -o 0" % \
                         (self.python_executable, self.clw_executable, ' '.join(key_list), self.DATABASE_URI)
        cmd_wlt_delete = "%s %s -w testms --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        output_wlt_create = "2NBrLTapyFqU4Wo29xG4QeEt8kn38KVWRR"
        output_wlt_delete = "Wallet testms has been removed"

        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'y')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))
        process = Popen(cmd_wlt_delete, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'testms')
        self.assertIn(output_wlt_delete, normalize_string(poutput[0]))

    def test_tools_clw_create_multisig_wallet_one_key(self):
        key_list = [
            'tprv8ZgxMBicQKsPd1Q44tfDiZC98iYouKRC2CzjT3HGt1yYw2zuX2awTotzGAZQEAU9bi2M5MCj8iedP9MREPjUgpDEBwBgGi2C8eK'
            '5zNYeiX8'
        ]
        cmd_wlt_create = "%s %s new -w testms1 -m 2 2 %s -r -n testnet -d %s -o 0" % \
                         (self.python_executable, self.clw_executable, ' '.join(key_list), self.DATABASE_URI)
        cmd_wlt_delete = "%s %s -w testms1 --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        output_wlt_create = "if you understood and wrote down your key: Receive address:"
        output_wlt_delete = "Wallet testms1 has been removed"

        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'yes')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))
        process = Popen(cmd_wlt_delete, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'testms1')
        self.assertIn(output_wlt_delete, normalize_string(poutput[0]))

    def test_tools_clw_create_multisig_wallet_error(self):
        cmd_wlt_create = "%s %s new -w testms2 -m 2 a -d %s" % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        output_wlt_create = "Number of signatures required (second argument) must be a numeric value"
        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'y')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))

    def test_tools_clw_transaction_with_script(self):
        cmd_wlt_create = '%s %s new -w test2 --passphrase "emotion camp sponsor curious bacon squeeze bean world ' \
                         'actual chicken obscure spray" -r -n bitcoinlib_test -d %s' % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        cmd_wlt_update = "%s %s -w test2 -x -d %s" % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        cmd_wlt_transaction = "%s %s -w test2 -d %s -s 21HVXMEdxdgjNzgfERhPwX4okXZ8WijHkvu 0.5 -f 100000 -p" % \
                              (self.python_executable, self.clw_executable, self.DATABASE_URI)
        cmd_wlt_delete = "%s %s -w test2 --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        output_wlt_create = "blt1qj0mgwyhxuw9p0ngj5kqnxhlrx8ypecqekm2gr7"
        output_wlt_transaction = 'Transaction pushed to network'
        output_wlt_delete = "Wallet test2 has been removed"

        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'y')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))

        process = Popen(cmd_wlt_update, stdout=PIPE, shell=True)
        process.communicate()

        process = Popen(cmd_wlt_transaction, stdout=PIPE, shell=True)
        poutput = process.communicate()
        self.assertIn(output_wlt_transaction, normalize_string(poutput[0]))

        process = Popen(cmd_wlt_delete, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'test2')
        self.assertIn(output_wlt_delete, normalize_string(poutput[0]))

    def test_tools_clw_create_litecoin_segwit_wallet(self):
        cmd_wlt_create = '%s %s new -w ltcsw --passphrase "lounge chief tip frog camera build trouble write end ' \
                         'sword order share" -d %s -j segwit -n litecoin -r' % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        cmd_wlt_delete = "%s %s -w ltcsw --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        output_wlt_create = "ltc1qgc7c2z56rr4lftg0fr8tgh2vknqc3yuydedu6m"
        output_wlt_delete = "Wallet ltcsw has been removed"

        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'y')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))
        process = Popen(cmd_wlt_delete, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'ltcsw')
        self.assertIn(output_wlt_delete, normalize_string(poutput[0]))

    def test_tools_clw_create_multisig_wallet_p2sh_segwit(self):
        key_list = [
            'YprvANkMzkodih9AKnvFGXTm8Fid3b6wDWoRq5GxmoFb8Rwoa4YsJvoHtbd6jFhCiCzG8Da3bFbkBeQq7Lz1YDAqufAZB5paBaZTEv8'
            'A1Yxfi5R',
            'YprvANkMzkodih9AJ6UamjW9rTWqBDMm5Be3M2cKybivd6V1MSMnKnGDkUXsVkz1hPKKNPFRZS9fFchRGKTgKdyTsppMuHjQQMVFBLY'
            'Ghp5MTsC',
            'YprvANkMzkodih9AKQ8evAkiDWCzpQsU6N1uasNtWznNj44Y2X6FJqkv9wcfavxVEkz9qru7VKRhzmQXqy562b9Tk4JGdsaVazByzmX'
            '7FW6wpKW'
        ]
        cmd_wlt_create = "%s %s new -w testms-p2sh-segwit -m 3 2 %s -r -j p2sh-segwit -d %s -o 0" % \
                         (self.python_executable, self.clw_executable, ' '.join(key_list), self.DATABASE_URI)
        cmd_wlt_delete = "%s %s -w testms-p2sh-segwit --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        output_wlt_create = "3MtNi5U2cjs3EcPizzjarSz87pU9DTANge"
        output_wlt_delete = "Wallet testms-p2sh-segwit has been removed"

        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'y')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))
        process = Popen(cmd_wlt_delete, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'testms-p2sh-segwit')
        self.assertIn(output_wlt_delete, normalize_string(poutput[0]))

    def test_tools_generate_key_quiet(self):
        cmd_generate_passphrase = "%s %s -gq --passphrase-strength 256" % \
                         (self.python_executable, self.clw_executable)
        process = Popen(cmd_generate_passphrase, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate()[0]
        self.assertEqual(len(poutput.split(b' ')), 24)

    def test_tools_wallet_create_from_key(self):
        phrase = ("hover rescue clock ocean strategy post melt banner anxiety phone pink paper enhance more "
                  "copy gate bag brass raise logic stone duck muffin conduct")
        cmd_wlt_create = "%s %s new -w wlt_from_key -c \"%s\" -d %s -y" % \
                         (self.python_executable, self.clw_executable, phrase, self.DATABASE_URI)
        output_wlt_create = "bc1qpylcrcyqa5wkwe2stzc6h7q0mhs5skxuas44w2"

        poutput = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))

    def test_tools_wallet_send_to_multi(self):
        send_str = ("-s blt1qzt90vqqjsqspuaegu9fh4e2htaxrgt0l76d9gz 0.1 "
                    "-s blt1qu825hm0a6ajg66j79x4tzkn56qmljjms97c5tp 1")
        cmd_wlt_create = "%s %s new -w wallet_send_to_multi -d %s -n bitcoinlib_test -yq" % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        cmd_wlt_update = "%s %s -w wallet_send_to_multi -d %s -x" % \
                         (self.python_executable, self.clw_executable, self.DATABASE_URI)
        cmd_wlt_send = "%s %s -w wallet_send_to_multi -d %s %s" % \
                        (self.python_executable, self.clw_executable, self.DATABASE_URI, send_str)

        Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        Popen(cmd_wlt_update, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        process = Popen(cmd_wlt_send, stdin=PIPE, stdout=PIPE, shell=True)
        self.assertIn(b"Transaction created", process.communicate()[0])

    def test_tools_wallet_empty(self):
        pk = ("zprvAWgYBBk7JR8GiejuVoZaVXtWf5zNawFbTH88uKao9qnZxBypJQNvh1tGHZghpfjUfSUiS7G7MmNw3cyakkNcNis3MjD4ic54n"
              "FY5LQxMszQ")
        cmd_wlt_create = "%s %s new -w wlt_create_and_empty -c %s -d %s -y" % \
                         (self.python_executable, self.clw_executable, pk, self.DATABASE_URI)
        output_wlt_create = "bc1qqnqkjpnmr5zsxar76wxqcntp28ltly0fz6crdg"
        poutput = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))

        cmd_wlt_empty = "%s %s -w wlt_create_and_empty -d %s --wallet-empty" % \
                        (self.python_executable, self.clw_executable, self.DATABASE_URI)
        poutput = Popen(cmd_wlt_empty, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        self.assertIn("Removed transactions and emptied wallet", normalize_string(poutput[0]))

        cmd_wlt_info = "%s %s -w wlt_create_and_empty -d %s -i" % \
                       (self.python_executable, self.clw_executable, self.DATABASE_URI)
        poutput = Popen(cmd_wlt_info, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        self.assertIn("- - Transactions Account 0 (0)", normalize_string(poutput[0]))
        self.assertNotIn(output_wlt_create, normalize_string(poutput[0]))


if __name__ == '__main__':
    unittest.main()
