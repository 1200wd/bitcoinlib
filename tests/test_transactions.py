# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Unit Tests for Transaction Class
#    © 2017 January - 1200 Web Development <http://1200wd.com/>
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

import unittest
import os
import json

from bitcoinlib.transactions import *


class TestTransactions(unittest.TestCase):

    def setUp(self):
        workdir = os.path.dirname(__file__)
        with open('%s/%s' % (workdir, 'transactions_raw.json'), 'r') as f:
            d = json.load(f)
        self.rawtxs = d['transactions']

    def test_transactions_deserialize_raw(self):
        for r in self.rawtxs:
            t = Transaction.import_raw(r[1])
            self.assertEqual(len(t.inputs), r[2], msg="Incorrect numbers of inputs for tx '%s'" % r[0])
            self.assertEqual(len(t.outputs), r[3], msg="Incorrect numbers of outputs for tx '%s'" % r[0])

    def test_transactions_verify_signature(self):
        for r in self.rawtxs:
            t = Transaction.import_raw(r[1])
            # if len(t.inputs) < 5:
            self.assertTrue(t.verify(), msg="Can not verify transaction '%s'" % r[0])




