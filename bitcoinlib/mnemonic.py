# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    BIP0039 Mnemonic Key management
#    © 1200 Web Development <http://1200wd.com/>
#    2016 november
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
import sys
import hashlib
import hmac
from encoding import change_base
from pbkdf2 import PBKDF2
import unicodedata

PBKDF2_ROUNDS = 2048
DEFAULT_LANGUAGE = 'english'

class Mnemonic:
    """
    Implementation of BIP0039 for Mnemonic keys.

    Took parts of Pavol Rusnak Trezors implementation, see https://github.com/trezor/python-mnemonic
    """

    def __init__(self, language=DEFAULT_LANGUAGE):
        """
        Init Mnemonic class for defined language
        :param language: use specific wordlist
        :return:
        """
        self._wordlist = []
        wldir = os.path.join(os.path.dirname(__file__), 'wordlist')
        with open('%s/%s.txt' % (wldir,language), 'r') as f:
            self._wordlist = [w.strip() for w in f.readlines()]

    @classmethod
    def normalize_string(cls, txt):
        if isinstance(txt, str if sys.version < '3' else bytes):
            utxt = txt.decode('utf8')
        elif isinstance(txt, unicode if sys.version < '3' else str):
            utxt = txt
        else:
            raise TypeError("String value expected")

        return unicodedata.normalize('NFKD', utxt)

    @staticmethod
    def checksum(hexdata):
        """
        Gives checksum for given hexdata key

        :param hexdata: key string as hexadecimal
        :return: Checksum of key as hex
        """
        if len(hexdata) % 8 > 0:
            raise ValueError('Data length in bits should be divisible by 32, but it is not (%d bytes = %d bits).' %
                             (len(hexdata), len(hexdata) * 8))
        data = change_base(hexdata, 16, 256)
        hashhex = hashlib.sha256(data).hexdigest()
        binresult = bin(int(hashhex, 16))[2:].zfill(256)[:len(data) * 8 // 32]
        return change_base(binresult, 2, 16, output_even=0)

    @classmethod
    def to_seed(cls, words, passphrase=''):
        """
        Convert Mnemonic words to passphrase protected seed for HD Key

        :param words: Mnemonic passphrase as string
        :param passphrase: A password to
        :return: Hex Key
        """
        mnemonic = cls.normalize_string(words)
        passphrase = cls.normalize_string(passphrase)
        return PBKDF2(mnemonic, u'mnemonic' + passphrase,
                      iterations=PBKDF2_ROUNDS,
                      macmodule=hmac,
                      digestmodule=hashlib.sha512).read(64)

    def word(self, index):
        return self._wordlist[index]

    def wordlist(self):
        return self._wordlist

    def generate(self, strength=128, include_checksum=True):
        """
        Generate a Mnemonic key

        :param strength: Key strenght in number of bits
        :param include_checksum: Boolean to specify if checksum needs to be included
        :return: Mnemonic passphrase
        """
        data = change_base(os.urandom(strength // 8), 256, 16)
        if include_checksum:
            data = data + self.checksum(data)
        return self.to_mnemonic(data)

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

    def to_entropy(self, words, includes_checksum=True):
        """
        Convert Mnemonic words back to entrophy

        :param words: Mnemonic words as string of list of words
        :param includes_checksum: Boolean to specify if checksum is used
        :return: Hex entrophy string
        """
        if isinstance(words, str):
            words = words.split(' ')
        wi = []
        for word in words:
            wi.append(self._wordlist.index(word))
        ent = change_base(wi, 2048, 16, output_even=0)
        if includes_checksum:
            # binresult = bin(int(hexdata, 16))[2:].zfill(len(data) * 8) + \
            #         bin(int(hashhex, 16))[2:].zfill(256)[:len(data) * 8 // 32]
            # TODO: check checksum
            pass
        return ent


if __name__ == '__main__':
    #
    # SOME EXAMPLES
    #

    print "\nConvert hexadecimal to mnemonic"
    pk = '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
    words = Mnemonic().to_mnemonic(pk)
    print("Hex:               %s" % pk)
    print("Hex+checksum       %s" % pk + Mnemonic().checksum(pk))
    print("Mnemonic           %s" % words)
    print("Seed for HD Key    %s" % change_base(Mnemonic().to_seed(words, 'test'), 256, 16))
    print("Back to Hex        %s" % Mnemonic().to_entropy(words))

    # Generate a random Mnemonic HD Key
    print "\nGenerate a random Mnemonic HD Key"
    entsize = 32
    wpl = Mnemonic().generate(entsize)
    print("Your Mnemonic is   %s" % wpl)
    print("  (An avarage of %d tries is needed to brute-force this password)" % ((2 ** entsize) // 2))
    from keys import HDKey
    seed = change_base(Mnemonic().to_seed(wpl), 256, 16)
    hdk = HDKey().from_seed(seed)
    print("HD Key WIF is      %s" % hdk)
