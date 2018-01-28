# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Bitcoinlib Tools
#    © 2018 January - 1200 Web Development <http://1200wd.com/>
#

import os
import sys
import unittest
from subprocess import check_output
from bitcoinlib.encoding import normalize_string


class TestToolsCommandLineWallet(unittest.TestCase):

    def test_format_wif_uncompressed(self):
        python_executable = sys.executable
        clw_executable = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tools/clw.py'))
        cmd_wlt_create = "echo y | %s %s test --passphrase 'emotion camp sponsor curious bacon squeeze bean world " \
                         "actual chicken obscure spray' -r" % (python_executable, clw_executable)
        cmd_wlt_delete = "echo test | %s %s --wallet-remove test" % (python_executable, clw_executable)
        output_wlt_create = "Receive address is 14guS7uQpEbgf1e8TDo1zTEURJW3NGPc9E"
        output_wlt_delete = "Wallet test has been removed"

        self.assertIn(output_wlt_create, normalize_string(check_output(cmd_wlt_create, shell=True)))
        self.assertIn(output_wlt_delete, normalize_string(check_output(cmd_wlt_delete, shell=True)))


if __name__ == '__main__':
    unittest.main()
