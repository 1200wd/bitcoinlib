# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Bitcoinlib Tools
#    © 2018 May - 1200 Web Development <http://1200wd.com/>
#

import os
import sys
import unittest
from subprocess import Popen, PIPE
from bitcoinlib.encoding import normalize_string
from bitcoinlib.db import DEFAULT_DATABASEDIR


DATABASEFILE_UNITTESTS = 'bitcoinlib.unittest.sqlite'


class TestToolsCommandLineWallet(unittest.TestCase):

    def setUp(self):
        full_db_filename = os.path.join(DEFAULT_DATABASEDIR, DATABASEFILE_UNITTESTS)
        if os.path.isfile(full_db_filename):
            os.remove(full_db_filename)
        self.python_executable = sys.executable
        self.clw_executable = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            '../bitcoinlib/tools/cli_wallet.py'))

    def test_tools_clw_create_wallet(self):
        cmd_wlt_create = '%s %s test --passphrase "emotion camp sponsor curious bacon squeeze bean world ' \
                         'actual chicken obscure spray" -r -d %s' % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_delete = "%s %s test --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "14guS7uQpEbgf1e8TDo1zTEURJW3NGPc9E"
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
        cmd_wlt_create = "%s %s testms -m 2 2 %s -r -n testnet -d %s" % \
                         (self.python_executable, self.clw_executable, ' '.join(key_list), DATABASEFILE_UNITTESTS)
        cmd_wlt_delete = "%s %s testms --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "2N7QSKcsmWPP9anG7cdZvzBUbgTVrAK2MZ9"
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
        cmd_wlt_create = "%s %s testms1 -m 2 2 %s -r -n testnet -d %s" % \
                         (self.python_executable, self.clw_executable, ' '.join(key_list), DATABASEFILE_UNITTESTS)
        cmd_wlt_delete = "%s %s testms1 --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "if you understood and wrote down your key: Receive address(es):"
        output_wlt_delete = "Wallet testms1 has been removed"

        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'y\nyes')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))
        process = Popen(cmd_wlt_delete, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'testms1')
        self.assertIn(output_wlt_delete, normalize_string(poutput[0]))

    def test_tools_clw_create_multisig_wallet_error(self):
        cmd_wlt_create = "%s %s testms2 -m 2 a -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "Number of signatures required (second argument) must be a numeric value"
        process = Popen(cmd_wlt_create, stdin=PIPE, stdout=PIPE, shell=True)
        poutput = process.communicate(input=b'y')
        self.assertIn(output_wlt_create, normalize_string(poutput[0]))

    def test_tools_clw_transaction_with_script(self):
        python_executable = "cli-wallet"
        cmd_wlt_create = '%s test2 --passphrase "emotion camp sponsor curious bacon squeeze bean world ' \
                         'actual chicken obscure spray" -r -n bitcoinlib_test -d %s' % \
                         (python_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_update = "%s test2 -d %s" % \
                         (python_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_transaction = "%s test2 -d %s -t 21HVXMEdxdgjNzgfERhPwX4okXZ8WijHkvu 50000000 -f 100000 -p" % \
                         (python_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_delete = "%s test2 --wallet-remove -d %s" % \
                         (python_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "21GPfxeCbBunsVev4uS6exPhqE8brPs1ZDF"
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


    # FIXME: Doesn't work on Travis + Also tested with test_tools_clw_transaction_with_script
    # def test_tools_cli_wallet(self):
    #     from bitcoinlib.tools.cli_wallet import main
    #     import io
    #     from contextlib import redirect_stdout
    #     f = io.StringIO()
    #     with redirect_stdout(f):
    #         try:
    #             main()
    #         except SystemExit:
    #             pass
    #     out = f.getvalue()
    #     self.assertIn("Command Line Wallet for BitcoinLib", out)



if __name__ == '__main__':
    unittest.main()
