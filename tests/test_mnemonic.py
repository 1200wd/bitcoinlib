# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Key, Encoding and Mnemonic Class
#    © 2016 November - 1200 Web Development <http://1200wd.com/>
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

import os
import unittest
import json

from bitcoinlib.keys import HDKey
from bitcoinlib.encoding import change_base
from bitcoinlib.mnemonic import Mnemonic


# From Copyright (c) 2013 Pavol Rusnak <https://github.com/trezor/python-mnemonic>
class TestMnemonics(unittest.TestCase):

    def _check_list(self, language, vectors):
        mnemo = Mnemonic(language)
        for v in vectors:
            if v[0]:
                phrase = mnemo.to_mnemonic(v[0])
            else:
                phrase = v[1]
            seed = change_base(mnemo.to_seed(phrase, v[4]), 256, 16)
            # print("Test %s => %s" % (v[0], phrase))
            self.assertEqual(v[1], phrase)
            self.assertEqual(v[2], seed)
            k = HDKey.from_seed(seed)
            self.assertEqual(k.wif(), v[3])

    def test_vectors(self):
        workdir = os.path.dirname(__file__)
        with open('%s/%s' % (workdir, 'mnemonics_tests.json'), 'r') as f:
            vectors = json.load(f)
        for lang in vectors.keys():
            self._check_list(lang, vectors[lang])

    # TODO tests for sanitize_mnemonic, detect language etc


if __name__ == '__main__':
    unittest.main()
