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


class Mnemonic:

    def __init__(self, language='english'):
        dir = os.path.join(os.path.dirname(__file__), 'wordlist')
        f = open('%s/%s.txt' % (dir,language))
        self._wordlist = {}
        i = 0
        for word in f.readlines():
            self._wordlist.update({
                i: word,
            })
            i += 1

    def word(self, index):
        return self._wordlist[index]

    def wordlist(self):
        return self._wordlist


if __name__ == '__main__':
    wl = Mnemonic()
    print wl.wordlist()