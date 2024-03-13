# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Bitcoinlib Tools
#    © 2018 - 2024 January - 1200 Web Development <http://1200wd.com/>
#

import ast
import os
import sys
import unittest
from subprocess import Popen, PIPE

try:
    import mysql.connector
    import psycopg
    from psycopg import sql
except ImportError:
    pass  # Only necessary when mysql or postgres is used

from bitcoinlib.db import BCL_DATABASE_DIR, session
from bitcoinlib.encoding import normalize_string

DATABASE_NAME = 'bitcoinlib_unittest'


def database_init(dbname=DATABASE_NAME):
    session.close_all_sessions()
    if os.getenv('UNITTEST_DATABASE') == 'postgresql':
        con = psycopg.connect(user='postgres', host='localhost', password='postgres', autocommit=True)
        cur = con.cursor()
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
            sql.Identifier(dbname))
        )
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(dbname))
        )
        cur.close()
        con.close()
        return 'postgresql+psycopg://postgres:postgres@localhost:5432/' + dbname
    elif os.getenv('UNITTEST_DATABASE') == 'mysql':
        con = mysql.connector.connect(user='root', host='localhost', password='root')
        cur = con.cursor()
        cur.execute("DROP DATABASE IF EXISTS {}".format(dbname))
        cur.execute("CREATE DATABASE {}".format(dbname))
        con.commit()
        cur.close()
        con.close()
        return 'mysql://root:root@localhost:3306/' + dbname
    else:
        dburi = os.path.join(str(BCL_DATABASE_DIR), '%s.sqlite' % dbname)
        if os.path.isfile(dburi):
            os.remove(dburi)
        return dburi


class TestToolsCommandLineWallet(unittest.TestCase):

    def setUp(self):
        self.python_executable = sys.executable
        self.clw_executable = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            '../bitcoinlib/tools/clw.py'))
        self.database_uri = database_init()

    def test_tools_clw_create_wallet(self):
        cmd_wlt_create = '%s %s new -w test --passphrase "emotion camp sponsor curious bacon squeeze bean world ' \
                         'actual chicken obscure spray" -r -d %s' % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_delete = "%s %s -w test --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
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
                         (self.python_executable, self.clw_executable, ' '.join(key_list), self.database_uri)
        print(cmd_wlt_create)
        cmd_wlt_delete = "%s %s -w testms --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
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
                         (self.python_executable, self.clw_executable, ' '.join(key_list), self.database_uri)
        cmd_wlt_delete = "%s %s -w testms1 --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        output_wlt_create = "if you understood and wrote down your key"
        output_wlt_delete = "Wallet testms1 has been removed"

        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'yes')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))
        process = Popen(cmd_wlt_delete, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'testms1')
        self.assertIn(output_wlt_delete, normalize_string(poutput[0]))

    def test_tools_clw_create_multisig_wallet_error(self):
        cmd_wlt_create = "%s %s new -w testms2 -m 2 a -d %s" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        output_wlt_create = "Number of total signatures (second argument) must be a numeric value"
        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'y')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))

    def test_tools_clw_transaction_with_script(self):
        cmd_wlt_create = '%s %s new -w test2 --passphrase "emotion camp sponsor curious bacon squeeze bean world ' \
                         'actual chicken obscure spray" -r -n bitcoinlib_test -d %s' % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_update = "%s %s -w test2 -x -d %s" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_transaction = "%s %s -w test2 -d %s -s 21HVXMEdxdgjNzgfERhPwX4okXZ8WijHkvu 0.5 -f 100000 -p" % \
                              (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_delete = "%s %s -w test2 --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
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
                         (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_delete = "%s %s -w ltcsw --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
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
        cmd_wlt_create = "%s %s new -w testms-p2sh-segwit -m 2 3 %s -r -j p2sh-segwit -d %s -o 0" % \
                         (self.python_executable, self.clw_executable, ' '.join(key_list), self.database_uri)
        cmd_wlt_delete = "%s %s -w testms-p2sh-segwit --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
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
                         (self.python_executable, self.clw_executable, phrase, self.database_uri)
        output_wlt_create = "bc1qpylcrcyqa5wkwe2stzc6h7q0mhs5skxuas44w2"

        poutput = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))

    def test_tools_wallet_send_to_multi(self):
        send_str = ("-s blt1qzt90vqqjsqspuaegu9fh4e2htaxrgt0l76d9gz 0.1 "
                    "-s blt1qu825hm0a6ajg66j79x4tzkn56qmljjms97c5tp 1")
        cmd_wlt_create = "%s %s new -w wallet_send_to_multi -d %s -n bitcoinlib_test -yq" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_update = "%s %s -w wallet_send_to_multi -d %s -x" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_send = "%s %s -w wallet_send_to_multi -d %s %s" % \
                        (self.python_executable, self.clw_executable, self.database_uri, send_str)

        Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        Popen(cmd_wlt_update, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        process = Popen(cmd_wlt_send, stdin=PIPE, stdout=PIPE, shell=True)
        self.assertIn(b"Transaction created", process.communicate()[0])

    def test_tools_wallet_empty(self):
        pk = ("zprvAWgYBBk7JR8GiejuVoZaVXtWf5zNawFbTH88uKao9qnZxBypJQNvh1tGHZghpfjUfSUiS7G7MmNw3cyakkNcNis3MjD4ic54n"
              "FY5LQxMszQ")
        cmd_wlt_create = "%s %s new -w wlt_create_and_empty -c %s -d %s -y" % \
                         (self.python_executable, self.clw_executable, pk, self.database_uri)
        output_wlt_create = "bc1qqnqkjpnmr5zsxar76wxqcntp28ltly0fz6crdg"
        poutput = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))

        cmd_wlt_empty = "%s %s -w wlt_create_and_empty -d %s --wallet-empty" % \
                        (self.python_executable, self.clw_executable, self.database_uri)
        poutput = Popen(cmd_wlt_empty, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        self.assertIn("Removed transactions and emptied wallet", normalize_string(poutput[0]))

        cmd_wlt_info = "%s %s -w wlt_create_and_empty -d %s -i" % \
                       (self.python_executable, self.clw_executable, self.database_uri)
        poutput = Popen(cmd_wlt_info, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        self.assertIn("- - Transactions Account 0 (0)", normalize_string(poutput[0]))
        self.assertNotIn(output_wlt_create, normalize_string(poutput[0]))

    def test_tools_wallet_sweep(self):
        cmd_wlt_create = "%s %s new -w wlt_sweep -d %s -n bitcoinlib_test -yq" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_update = "%s %s -w wlt_sweep -d %s -x" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_send = "%s %s -w wlt_sweep -d %s --sweep blt1qzt90vqqjsqspuaegu9fh4e2htaxrgt0l76d9gz -p" % \
                        (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_info = "%s %s -w wlt_sweep -d %s -i" % \
                        (self.python_executable, self.clw_executable, self.database_uri)
        Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        Popen(cmd_wlt_update, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        process = Popen(cmd_wlt_send, stdin=PIPE, stdout=PIPE, shell=True)
        self.assertIn(b"Transaction pushed to network", process.communicate()[0])
        process = Popen(cmd_wlt_info, stdin=PIPE, stdout=PIPE, shell=True)
        self.assertIn("-1.00000000 T   = Balance Totals (includes unconfirmed) =",
                      normalize_string(process.communicate()[0]).replace('\n', '').replace('\r', ''))

    def test_tools_wallet_multisig_cosigners(self):
        pk1 = ('BC12Se7KL1uS2bA6QNjPAjFirwyoB8bDA3EPLMwDex7D3fZrWG4pP2zUcyEPKpgXfcoxxhZQqWX7b57MBWVxjjioNvsfvnpJVT9'
               'XWVvHtmdyowDz')
        pk2 = ('BC12Se7KL1uS2bA6QQH1M6YkFGbNXoFSUavaE6EfMEmTrtSERw1JRCWf6Jj5tfoLhZopA4s2FSzqZqYTMpChvUvV9KdgtnJ1sFi'
               'B7SZVyHC31ybq')
        pk3 = ('BC12Se7KL1uS2bA6QNjZ8T9CzaubwGjTH3WTaZdDB45GVwNMt26ixhgk4L8zus4NxhKWez5xj6xiT7DkpsSnD363h8WEoR7b5d2'
               'u64ec4KeCXQKg')
        pub_key1 = ('BC11mYr7gRWJM1oBUFSkW8tPWVeb8bVv9kzjkjH7emfNnsSWVKLo24vopvN8vxud7VvFjYBvhCrEECC6mVTtE7imyytvkLT'
                    '9URKHJ3Crs1dSecKa')
        pub_key2 = ('BC11mYrAhSZGc4JJYubuRSJDjbeoi2BueBjggutvkC8AMv8v2vdKT9T1Tq5VmXgnmzdb2maK5VF5fnbpZR1yt5bJRNBAgJb'
                    'ZYXRnhWiS3jjHqgeZ')
        pub_key3 = ('BC11mYrL5yBtMgaYxHEUg3anvLX3gcLi8hbtwbjymReCgGiP6hYifVMi96M3ejtvZpZbDvetBfbzgRxmu22ZkqP2i7yhFge'
                    'mSkHp7BRhoDubrQvs')
        cmd_wlt_create1 = ("%s %s new -w wlt_multisig_2_3_A -m 2 3 %s %s %s -d %s -n bitcoinlib_test -q "
                           "--disable-anti-fee-sniping") % \
                          (self.python_executable, self.clw_executable, pk1, pub_key2, pub_key3, self.database_uri)
        Popen(cmd_wlt_create1, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        cmd_wlt_create2 = ("%s %s new -w wlt_multisig_2_3_B -m 2 3 %s %s %s -d %s -n bitcoinlib_test -q "
                           "--disable-anti-fee-sniping") % \
                          (self.python_executable, self.clw_executable, pub_key1, pub_key2, pk3, self.database_uri)
        print(cmd_wlt_create2)
        Popen(cmd_wlt_create2, stdin=PIPE, stdout=PIPE, shell=True).communicate()

        cmd_wlt_receive1 = "%s %s -w wlt_multisig_2_3_A -d %s -r -o 1 -q" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        output1 = Popen(cmd_wlt_receive1, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        cmd_wlt_receive2 = "%s %s -w wlt_multisig_2_3_B -d %s -r -o 1 -q" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        output2 = Popen(cmd_wlt_receive2, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        self.assertEqual(output1[0], output2[0])
        address = normalize_string(output1[0].strip(b'\n'))

        cmd_wlt_update1 = "%s %s -w wlt_multisig_2_3_A -d %s -x -o 1" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        Popen(cmd_wlt_update1, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        cmd_wlt_update2 = "%s %s -w wlt_multisig_2_3_B -d %s -x -o 1" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        Popen(cmd_wlt_update2, stdin=PIPE, stdout=PIPE, shell=True).communicate()

        create_tx = "%s %s -w wlt_multisig_2_3_A -d %s -s %s 0.5 -o 1" % \
                         (self.python_executable, self.clw_executable, self.database_uri, address)
        output = Popen(create_tx, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        tx_dict_str = '{' + normalize_string(output[0]).split('{', 1)[1]
        sign_tx =  "%s %s -w wlt_multisig_2_3_B -d %s -o 1 --import-tx \"%s\"" % \
                   (self.python_executable, self.clw_executable, self.database_uri,
                    tx_dict_str.replace('\r', '').replace('\n', ''))
        output = Popen(sign_tx, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        response = normalize_string(output[0])
        self.assertIn('12821f8ac330e4eddb9f87ea29456b31ec300e232d2c63880f669a9b15e3741f', response)
        self.assertIn('Signed transaction', response)
        self.assertIn("'verified': True,", response)

        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'import_test.tx')
        sign_import_tx_file = "%s %s -w wlt_multisig_2_3_B -d %s -o 1 --import-tx-file %s" % \
            (self.python_executable, self.clw_executable, self.database_uri, filename)
        output = Popen(sign_import_tx_file, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        response2 = normalize_string(output[0])
        self.assertIn('2e07be62d933f5b257ac066b874df651cd6e6763795c24036904024a2b44180b', response2)
        self.assertIn('239M1DxQuxJcMHtYBdG6A81bfXQrrCNa2rr', response2)
        self.assertIn('Signed transaction', response2)
        self.assertIn("'verified': True,", response2)

    def test_tools_transaction_options(self):
        cmd_wlt_create = "%s %s new -w test_tools_transaction_options -d %s -n bitcoinlib_test -yq" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_update = "%s %s -w test_tools_transaction_options -d %s -x" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        cmd_wlt_send = ("%s %s -w test_tools_transaction_options -d %s -s blt1qg7du8cs0scxccmfly7x252qurv7kwsy6rm4xr7 0.001 "
                        "--number-of-change-outputs 5") % \
                       (self.python_executable, self.clw_executable, self.database_uri)
        Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        Popen(cmd_wlt_update, stdin=PIPE, stdout=PIPE, shell=True).communicate()
        output = normalize_string(Popen(cmd_wlt_send, stdin=PIPE, stdout=PIPE, shell=True).communicate()[0])
        tx_dict_str = '{' + output.split('{', 1)[1]
        tx_dict = ast.literal_eval(tx_dict_str.replace('\r', '').replace('\n', ''))
        self.assertEqual(len(tx_dict['outputs']), 6)
        self.assertTrue(tx_dict['verified'])

        cmd_wlt_update2 = "%s %s -w test_tools_transaction_options -d %s -ix" % \
                         (self.python_executable, self.clw_executable, self.database_uri)
        output = normalize_string(Popen(cmd_wlt_update2, stdin=PIPE, stdout=PIPE, shell=True).communicate()[0])
        output_list = [i for i in output.split('Keys')[1].split(' ') if i != '']
        first_key_id = int(output_list[1])
        address = output_list[3]
        cmd_wlt_send2 = ("%s %s -w test_tools_transaction_options -d %s "
                        "-s blt1qdjre3yw9hnt53entkp6tflhg34y4sp999emjnk 0.5 -k %d") % \
                       (self.python_executable, self.clw_executable, self.database_uri, first_key_id)
        output = normalize_string(Popen(cmd_wlt_send2, stdin=PIPE, stdout=PIPE, shell=True).communicate()[0])
        self.assertIn(address, output)
        self.assertIn("Transaction created", output)


if __name__ == '__main__':
    unittest.main()
