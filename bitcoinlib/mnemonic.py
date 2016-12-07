# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    BIP0039 Mnemonic Key management
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
import sys
import hashlib
import hmac
from pbkdf2 import PBKDF2
import unicodedata

from bitcoinlib.encoding import change_base

PBKDF2_ROUNDS = 2048
DEFAULT_LANGUAGE = 'english'
WORDLIST_DIR = os.path.join(os.path.dirname(__file__), 'wordlist')


class Mnemonic:
    """
    Implementation of BIP0039 for Mnemonic keys.

    Took parts of Pavol Rusnak Trezors implementation, see https://github.com/trezor/python-mnemonic
    """

    def __init__(self, language=DEFAULT_LANGUAGE):
        """
        Init Mnemonic class and read wordlist of specified language
        :param language: use specific wordlist
        :return:
        """
        self._wordlist = []
        with open('%s/%s.txt' % (WORDLIST_DIR, language), 'r') as f:
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
        Calculates checksum for given hexdata key

        :param hexdata: key string as hexadecimal
        :return: Checksum of key as hex
        """
        if len(hexdata) % 8 > 0:
            raise ValueError('Data length in bits should be divisible by 32, but it is not (%d bytes = %d bits).' %
                             (len(hexdata), len(hexdata) * 8))
        # data = self.normalize_string(change_base(hexdata, 16, 256))
        data = change_base(hexdata, 16, 256)
        hashhex = hashlib.sha256(data).hexdigest()
        return change_base(hashhex, 16, 2, 256)[:len(data) * 8 // 32]

    def to_seed(self, words, passphrase=''):
        """
        Use Mnemonic words and passphrase to create a seed

        :param words: Mnemonic passphrase as string
        :param passphrase: A password to
        :return: Hex Key
        """
        words = self.sanitize_mnemonic(words)
        mnemonic = self.normalize_string(words)
        passphrase = passphrase.encode()
        return PBKDF2(mnemonic, b'mnemonic' + passphrase,
                      iterations=PBKDF2_ROUNDS,
                      macmodule=hmac,
                      digestmodule=hashlib.sha512).read(64)

    def word(self, index):
        return self._wordlist[index]

    def wordlist(self):
        return self._wordlist

    def generate(self, strength=128, add_checksum=True):
        """
        Generate a Mnemonic key

        :param strength: Key strenght in number of bits
        :param add_checksum: Boolean to specify if checksum needs to be included
        :return: Mnemonic passphrase
        """
        data = change_base(os.urandom(strength // 8), 256, 16)
        return self.to_mnemonic(data, add_checksum=add_checksum)

    def to_mnemonic(self, hexdata, add_checksum=True):
        if add_checksum:
            binresult = change_base(hexdata, 16, 2, len(hexdata) * 4) + self.checksum(hexdata)
            wi = change_base(binresult, 2, 2048)
        else:
            wi = change_base(hexdata, 16, 2048)
        return self.normalize_string(' '.join([self._wordlist[i] for i in wi]))

    def to_entropy(self, words, includes_checksum=True):
        """
        Convert Mnemonic words back to entrophy

        :param words: Mnemonic words as string of list of words
        :param includes_checksum: Boolean to specify if checksum is used
        :return: Hex entrophy string
        """
        words = self.sanitize_mnemonic(words)
        if isinstance(words, (str, unicode if sys.version < '3' else str)):
            words = words.split(' ')
        wi = []
        for word in words:
            wi.append(self._wordlist.index(word))
        ent = change_base(wi, 2048, 16, output_even=0)
        if includes_checksum:
            binresult = change_base(ent, 16, 2, len(ent) * 4)
            ent = change_base(binresult[:-len(binresult) // 33], 2, 16)

            # Check checksum
            checksum = binresult[-len(binresult) // 33:]
            if checksum != self.checksum(ent):
                raise Warning("Invalid checksum %s for entropy %s" % (checksum, ent))

        return ent

    def detect_language(self, words):
        words = self.normalize_string(words)
        if isinstance(words, (str, unicode if sys.version < '3' else bytes)):
            words = words.split(' ')

        wlcount = {}
        for fn in os.listdir(WORDLIST_DIR):
            if fn.endswith(".txt"):
                with open('%s/%s' % (WORDLIST_DIR, fn), 'r') as f:
                    wordlist = [w.strip() for w in f.readlines()]
                    language = fn.split('.')[0]
                    wlcount[language] = 0
                    for word in words:
                        if sys.version < '3':
                            word = word.encode('utf-8')
                        if word in wordlist:
                            wlcount[language] += 1
        detlang = max(wlcount.keys(), key=(lambda key: wlcount[key]))
        if wlcount[detlang] > 0:
            return detlang
        else:
            raise Warning("Could not detect language of Mnemonic sentence %s" % words)

    def sanitize_mnemonic(self, words):
        words = self.normalize_string(words)
        language = self.detect_language(words)
        if isinstance(words, (str, unicode if sys.version < '3' else bytes)):
            words = words.split(' ')
        with open('%s/%s.txt' % (WORDLIST_DIR, language), 'r') as f:
            wordlist = [w.strip() for w in f.readlines()]
            for word in words:
                if sys.version < '3':
                    word = word.encode('utf-8')
                if word not in wordlist:
                    raise Warning("Unrecognised word %s in mnemonic sentence" % word.encode('utf8'))
        return ' '.join(words)


if __name__ == '__main__':
    #
    # SOME EXAMPLES
    #

    from bitcoinlib.keys import HDKey

    # Convert hexadecimal to mnemonic and back again to hex
    print("\nConvert hexadecimal to mnemonic and back again to hex")
    pk = '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
    words = Mnemonic().to_mnemonic(pk)
    print("Hex                %s" % pk)
    print("Checksum bin       %s" % Mnemonic().checksum(pk))
    print("Mnemonic           %s" % words)
    print(Mnemonic().to_seed(words, 'test'))
    print("Seed for HD Key    %s" % change_base(Mnemonic().to_seed(words, 'test'), 256, 16))
    print("Back to Hex        %s" % Mnemonic().to_entropy(words))

    # Generate a random Mnemonic HD Key
    print("\nGenerate a random Mnemonic HD Key")
    entsize = 128
    words = Mnemonic('english').generate(entsize)
    print("Your Mnemonic is   %s" % words)
    print("  (An avarage of %d tries is needed to brute-force this password)" % ((2 ** entsize) // 2))
    seed = change_base(Mnemonic().to_seed(words), 256, 16)
    hdk = HDKey().from_seed(seed)
    print("Seed for HD Key    %s" % change_base(seed, 256, 16))
    print("HD Key WIF is      %s" % hdk)

    # Generate a key from a Mnemonic sentence
    print("\nGenerate a key from a Mnemonic sentence")
    words = "type fossil omit food supply enlist move perfect direct grape clean diamond"
    print("Your Mnemonic is   %s" % words)
    seed = change_base(Mnemonic().to_seed(words), 256, 16)
    hdk = HDKey().from_seed(seed)
    print("Seed for HD Key    %s" % change_base(seed, 256, 16))
    print("HD Key WIF is      %s" % hdk)

    # Let's talk Spanish
    print("\nGenerate a key from a Spanish Mnemonic sentence")
    words = "laguna afirmar talón resto peldaño deuda guerra dorado catorce avance oasis barniz"
    print("Your Mnemonic is   %s" % words)
    seed = change_base(Mnemonic().to_seed(words), 256, 16)
    hdk = HDKey().from_seed(seed)
    print("Seed for HD Key    %s" % change_base(seed, 256, 16))
    print("HD Key WIF is      %s" % hdk)

    # Want some Chinese?
    print("\nGenerate a key from a Chinese Mnemonic sentence")
    words = "信 收 曉 捐 炭 祖 瘋 原 強 則 岩 蓄"
    print("Your Mnemonic is   %s" % words)
    seed = change_base(Mnemonic().to_seed(words), 256, 16)
    hdk = HDKey().from_seed(seed)
    print("Seed for HD Key    %s" % change_base(seed, 256, 16))
    print("HD Key WIF is      %s" % hdk)

    # Spanish Unicode mnemonic sentence
    print("\nGenerate a key from a Spanish UNICODE Mnemonic sentence")
    words = u"guion cruz envío papel otoño percha hazaña salir joya gorra íntimo actriz"
    print("Your Mnemonic is   %s" % words)
    seed = change_base(Mnemonic().to_seed(words, '1200 web development'), 256, 16)
    hdk = HDKey().from_seed(seed)
    print("Seed for HD Key    %s" % change_base(seed, 256, 16))
    print("HD Key WIF is      %s" % hdk)

    # And Japanese
    print("\nGenerate a key from a Japanese UNICODE Mnemonic sentence")
    words = "あじわう　ちしき　たわむれる　おくさま　しゃそう　うんこう　ひてい　みほん　たいほ　てのひら　りこう　わかれる　かいすいよく　こもん　ねもと"
    print("Your Mnemonic is   %s" % words)
    seed = change_base(Mnemonic().to_seed(words, '1200 web development'), 256, 16)
    hdk = HDKey().from_seed(seed)
    print("Seed for HD Key    %s" % change_base(seed, 256, 16))
    print("HD Key WIF is      %s" % hdk)

    # And Japanese
    # --- not supported at the moment ---
    # print("\nGenerate a key from a Japanese UNICODE Mnemonic sentence")
    # words = "あじわう　ちしき　たわむれる　おくさま　しゃそう　うんこう　ひてい　みほん　たいほ　てのひら　りこう　わかれる　かいすいよく　" \
    #         "こもん　ねもと"
    # print("Your Mnemonic is   %s" % words)
    # seed = change_base(Mnemonic().to_seed(words, '1200 web development'), 256, 16)
    # hdk = HDKey().from_seed(seed)
    # print("Seed for HD Key    %s" % change_base(seed, 256, 16))
    # print("HD Key WIF is      %s" % hdk)
    # print("HD Key WIF <==>    xprv9s21ZrQH143K2dq9wumtjiDMnMqF56xswR5ZQDpQehp34zNtAEHCADTDt6RAEpxtsEwQbissfq2p4Hq9"
    #       "NY6Fbf7F5pRKkddcXoTsu5xWziU")

    # Japanese Json test
    # [
    #     "",
    #     "あじわう　ちしき　たわむれる　おくさま　しゃそう　うんこう　ひてい　みほん　たいほ　てのひら　りこう　わかれる　かいすいよく　こもん　"
    #     "ねもと",
    #     "6e0404f30a518af203d70ebc0b5839c04e70d671699ffaad9f0447592b59b68afae9d938db1834c0d1aeac3554212dfedf3c42f5a"
    #     "fd60740a308589518174e10",
    #     "xprv9s21ZrQH143K2dq9wumtjiDMnMqF56xswR5ZQDpQehp34zNtAEHCADTDt6RAEpxtsEwQbissfq2p4Hq9NY6Fbf7F5pRKkddcXoTsu"
    #     "5xWziU",
    #     "1200 web development"
    # ]
