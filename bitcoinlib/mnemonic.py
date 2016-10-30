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
import hashlib
from encoding import change_base

DEFAULT_LANGUAGE = 'english'

class Mnemonic:

    def __init__(self, language=DEFAULT_LANGUAGE):
        self._wordlist = []
        wldir = os.path.join(os.path.dirname(__file__), 'wordlist')
        with open('%s/%s.txt' % (wldir,language), 'r') as f:
            self._wordlist = [w.strip() for w in f.readlines()]

    @staticmethod
    def checksum(hexdata):
        if len(hexdata) % 8 > 0:
            raise ValueError('Data length in bits should be divisible by 32, but it is not (%d bytes = %d bits).' %
                             (len(hexdata), len(hexdata) * 8))
        data = change_base(hexdata, 16, 256)
        h = hashlib.sha256(data).hexdigest()
        b = bin(int(h, 16))[2:].zfill(256)[:len(data) * 8 // 32]
        return change_base(b, 2, 16)

    def word(self, index):
        return self._wordlist[index]

    def wordlist(self):
        return self._wordlist

    def generate(self, strength=128, include_checksum=True):
        data = change_base(os.urandom(strength // 8), 256, 16)
        if include_checksum:
            data = data + self.checksum(data)
        return self.to_mnemonic(data)

    def to_entropy(self, words, includes_checksum=True):
        wi = []
        for word in words:
            wi.append(self._wordlist.index(word))
        ent = change_base(wi, 2048, 16)
        if includes_checksum:
            # TODO: check checksum
            pass
        return ent

    def to_mnemonic(self, hexdata, add_checksum=True):
        if add_checksum:
            data = change_base(hexdata, 16, 256)
            hashhex = hashlib.sha256(data).hexdigest()
            binresult = bin(int(hexdata, 16))[2:].zfill(len(data) * 8) + \
                bin(int(hashhex, 16))[2:].zfill(256)[:len(data) * 8 // 32]
            wi = change_base(binresult, 2, 2048)
        else:
            wi = change_base(hexdata, 16, 2048)
        return ' '.join([self._wordlist[i] for i in wi])



if __name__ == '__main__':
    # entsize = 32
    # wpl = Mnemonic().generate(entsize)
    # print("Your password is: %s" % ' '.join(wpl))
    # print("A computer needs an avarage of %.2f tries to guess this password" % ((2 ** entsize) /2.0))
    # base = Mnemonic().to_entropy(wpl)
    # print("In HEX this is %s" % base)
    # print("Checksum is %s" % Mnemonic().checksum(base))
    # print("Convert back to base2048: %s" % Mnemonic().to_mnemonic(base))

    # Entropy input (128 bits) 0c1e24e5917779d297e14d45f14e1a1a
    # Mnemonic (12 words) army van defense carry jealous true garbage claim echo media make crunch
    # Seed (512 bits) 3338a6d2ee71c7f28eb5b882159634cd46a898463e9d2d0980f8e80dfbba5b0f
    #                 a0291e5fb888a599b44b93187be6ee3ab5fd3ead7dd646341b2cdb8d08d13bf7

    from binascii import unhexlify, hexlify
    pk = '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
    print pk, len(pk)
    words = Mnemonic().to_mnemonic(pk)
    print("Private key to mnemonic: %s" % words)