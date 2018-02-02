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


DATABASEFILE_UNITTESTS = 'bitcoinlib.unittest.sqlite'


class TestToolsCommandLineWallet(unittest.TestCase):

    def setUp(self):
        self.python_executable = sys.executable
        self.clw_executable = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tools/clw.py'))

    def test_tools_create_wallet(self):
        cmd_wlt_create = "echo y | %s %s test --passphrase 'emotion camp sponsor curious bacon squeeze bean world " \
                         "actual chicken obscure spray' -r -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_delete = "echo test | %s %s test --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "Receive address is 14guS7uQpEbgf1e8TDo1zTEURJW3NGPc9E"
        output_wlt_delete = "Wallet test has been removed"

        self.assertIn(output_wlt_create, normalize_string(check_output(cmd_wlt_create, shell=True)))
        self.assertIn(output_wlt_delete, normalize_string(check_output(cmd_wlt_delete, shell=True)))

    def test_tools_transaction(self):
        cmd_wlt_create = "echo y | %s %s test2 --passphrase 'emotion camp sponsor curious bacon squeeze bean world " \
                         "actual chicken obscure spray' -r -n bitcoinlib_test -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_update = "%s %s test2 -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_transaction = "%s %s test2 -d %s -t 21HVXMEdxdgjNzgfERhPwX4okXZ8WijHkvu 50000000 -f 100000" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        cmd_wlt_delete = "echo test2 | %s %s test2 --wallet-remove -d %s" % \
                         (self.python_executable, self.clw_executable, DATABASEFILE_UNITTESTS)
        output_wlt_create = "Receive address is 21GPfxeCbBunsVev4uS6exPhqE8brPs1ZDF"
        output_wlt_transaction = b'01000000011955e2bca098d8bf17f0982a117ad26a98343378dedda988caf7c4a49693a03d00000000' \
                                 b'00ffffffff0280f0fa02000000001976a914d96e214c31c0f34f8d4daaf01aa88647bbd6d33388ace0' \
                                 b'69f902000000001976a9142f825bb62ed9237e98083f841b80657d3df0961b88ac00000000'
        output_wlt_delete = "Wallet test2 has been removed"

        self.assertIn(output_wlt_create, normalize_string(check_output(cmd_wlt_create, shell=True)))
        check_output(cmd_wlt_update, shell=True)
        print(check_output(cmd_wlt_transaction, shell=True))
        self.assertIn(output_wlt_transaction, check_output(cmd_wlt_transaction, shell=True))
        self.assertIn(output_wlt_delete, normalize_string(check_output(cmd_wlt_delete, shell=True)))


if __name__ == '__main__':
    unittest.main()
