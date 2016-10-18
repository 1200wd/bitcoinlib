# -*- coding: utf-8 -*-
#
#    bitcoinlib mnemonic.py
#    Copyright (C) 2016 October 
#    1200 Web Development
#    http://1200wd.com/
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
from encoding import change_base

DEFAULT_LANGUAGE = 'dutch'

class Mnemonic:

    def __init__(self, language=DEFAULT_LANGUAGE):
        wldir = os.path.join(os.path.dirname(__file__), 'wordlist')
        with open('%s/%s.txt' % (wldir,language), 'r') as f:
            self._wordlist = [w.strip() for w in f.readlines()]

    def word(self, index):
        return self._wordlist[index]

    def wordlist(self):
        return self._wordlist


if __name__ == '__main__':
    import random
    wordlist = Mnemonic().wordlist()
    maxsize = change_base('FFFFFFFFFF', 16, 10)
    rand = random.SystemRandom().randint(maxsize /2, maxsize)
    passline = change_base(rand, 16, 2048, output_as_list=True)
    wpl = [wordlist[i] for i in passline]
    print "Your password is: %s" % ' '.join(wpl)
    print "You need an avarage of %.0f tries to guess this password" % (maxsize/4)