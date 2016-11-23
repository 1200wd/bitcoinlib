# -*- coding: utf-8 -*-
#
#    bitcoinlib wallets
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

from bitcoinlib.db import *
from bitcoinlib.keys import *


class Wallet:

    @staticmethod
    def from_key(key):
        # if key is not known add it
        k = Key(key)
        k.info()
        # c = conn.cursor()
        # c.execute('SELECT * FROM keys WHERE key=?', (key,))
        return Wallet

    def __init__(self, id=0):
        print(id)



if __name__ == '__main__':
    #
    # WALLETS EXAMPLES
    #

    wallet = Wallet.from_key('tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UX'
                             'F75r2dKePyA7irEvBoe4aAn52')

