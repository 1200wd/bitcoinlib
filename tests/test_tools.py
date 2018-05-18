# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Bitcoinlib Tools
#    © 2018 May - 1200 Web Development <http://1200wd.com/>
#

import os
import sys
import unittest
from subprocess import check_output
from bitcoinlib.encoding import normalize_string


DATABASEFILE_UNITTESTS = 'bitcoinlib.unittest.sqlite'


class TestToolsCommandLineWallet(unittest.TestCase):

    def setUp(self):
        if os.path.isfile(DATABASEFILE_UNITTESTS):
            os.remove(DATABASEFILE_UNITTESTS)
        self.python_executable = sys.executable
        self.clw_executable = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            '../bitcoinlib/tools/cli_wallet.py'))

    def test_tools_clw_create_wallet(self):
        cmd_wlt_create = "echo y | %s %s test --passphrase 'emotion camp sponsor curious bacon squeeze bean world " \
                         "actual chicken obscure spray' -r -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_delete = "echo test | %s %s test --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "Receive address(es):\n14guS7uQpEbgf1e8TDo1zTEURJW3NGPc9E"
        output_wlt_delete = "Wallet test has been removed"

        self.assertIn(output_wlt_create, normalize_string(check_output(cmd_wlt_create, shell=True)))
        self.assertIn(output_wlt_delete, normalize_string(check_output(cmd_wlt_delete, shell=True)))

    def test_tools_clw_create_multisig_wallet(self):
        key_list = [
            'tprv8ZgxMBicQKsPd1Q44tfDiZC98iYouKRC2CzjT3HGt1yYw2zuX2awTotzGAZQEAU9bi2M5MCj8iedP9MREPjUgpDEBwBgGi2C8eK'
            '5zNYeiX8',
            'tprv8ZgxMBicQKsPeUbMS6kswJc11zgVEXUnUZuGo3bF6bBrAg1ieFfUdPc9UHqbD5HcXizThrcKike1c4z6xHrz6MWGwy8L6YKVbgJ'
            'MeQHdWDp'
        ]
        cmd_wlt_create = "echo y | %s %s testms -m 2 2 %s -r -n testnet -d %s" % \
                         (self.python_executable, self.clw_executable, ' '.join(key_list), DATABASEFILE_UNITTESTS)
        cmd_wlt_delete = "echo testms | %s %s testms --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "Receive address(es):\n2N7QSKcsmWPP9anG7cdZvzBUbgTVrAK2MZ9"
        output_wlt_delete = "Wallet testms has been removed"

        self.assertIn(output_wlt_create, normalize_string(check_output(cmd_wlt_create, shell=True)))
        self.assertIn(output_wlt_delete, normalize_string(check_output(cmd_wlt_delete, shell=True)))

    def test_tools_clw_create_multisig_wallet_one_key(self):
        key_list = [
            'tprv8ZgxMBicQKsPd1Q44tfDiZC98iYouKRC2CzjT3HGt1yYw2zuX2awTotzGAZQEAU9bi2M5MCj8iedP9MREPjUgpDEBwBgGi2C8eK'
            '5zNYeiX8'
        ]
        cmd_wlt_create = "printf 'y\nyes' | %s %s testms1 -m 2 2 %s -r -n testnet -d %s" % \
                         (self.python_executable, self.clw_executable, ' '.join(key_list), DATABASEFILE_UNITTESTS)
        cmd_wlt_delete = "echo testms1 | %s %s testms1 --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "if you understood and wrote down your key: Receive address(es):"
        output_wlt_delete = "Wallet testms1 has been removed"

        self.assertIn(output_wlt_create, normalize_string(check_output(cmd_wlt_create, shell=True)))
        self.assertIn(output_wlt_delete, normalize_string(check_output(cmd_wlt_delete, shell=True)))

    def test_tools_clw_create_multisig_wallet_error(self):
        cmd_wlt_create = "printf 'y\nyes' | %s %s testms2 -m 2 a -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "Number of signatures required (second argument) must be a numeric value"
        self.assertIn(output_wlt_create, normalize_string(check_output(cmd_wlt_create, shell=True)))

    def test_tools_clw_transaction_with_script(self):
        python_executable = "cli-wallet"
        cmd_wlt_create = "echo y | %s test2 --passphrase 'emotion camp sponsor curious bacon squeeze bean world " \
                         "actual chicken obscure spray' -r -n bitcoinlib_test -d %s" % \
                         (python_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_update = "%s test2 -d %s" % \
                         (python_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_transaction = "%s test2 -d %s -t 21HVXMEdxdgjNzgfERhPwX4okXZ8WijHkvu 50000000 -f 100000 -p" % \
                         (python_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_delete = "echo test2 | %s test2 --wallet-remove -d %s" % \
                         (python_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "Receive address(es):\n21GPfxeCbBunsVev4uS6exPhqE8brPs1ZDF"
        output_wlt_transaction = b'Transaction pushed to network'
        output_wlt_delete = "Wallet test2 has been removed"

        self.assertIn(output_wlt_create, normalize_string(check_output(cmd_wlt_create, shell=True)))
        print(check_output(cmd_wlt_update, shell=True))
        self.assertIn(output_wlt_transaction, check_output(cmd_wlt_transaction, shell=True))
        self.assertIn(output_wlt_delete, normalize_string(check_output(cmd_wlt_delete, shell=True)))

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
