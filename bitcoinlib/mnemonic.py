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

    def generate(self, strength=128):
        data = os.urandom(strength // 8)
        return self.to_mnemonic(data)


    def to_entropy(self, words, base_to=16):
        wi = []
        for word in words:
            wi.append(self._wordlist.index(word))
        ent = change_base(wi, 2048, base_to)
        return ent

    def to_mnemonic(self, data):
        wi = change_base(data, 256, 2048)
        return [self._wordlist[i] for i in wi]


if __name__ == '__main__':
    entsize = 32
    mobj = Mnemonic()
    wpl = mobj.generate(entsize)
    print "Your password is: %s" % ' '.join(wpl)
    print "A computer needs an avarage of %.2f tries to guess this password" % ((2 ** entsize) /2.0)

    base = mobj.to_entropy(wpl, 256)
    print "In HEX this is %s" % change_base(base, 256, 16, 8)

    print "Convert back to base2048: %s" % mobj.to_mnemonic(base)