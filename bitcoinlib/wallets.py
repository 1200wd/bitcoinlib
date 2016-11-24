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
from bitcoinlib.keys import HDKey

from sqlalchemy import or_

class WalletError(Exception):
    pass


class HDWallet:

    @staticmethod
    def from_key(key, name, wallet_id=0, owner='', network='bitcoin'):
        k = HDKey(key)
        # Check if wallet name and key are not in database yet
        w = session.query(DbWallet).filter_by(name=name).first()
        if w:
            wallet_id = w.id
        wk = session.query(DbWalletKey).filter(or_(DbWalletKey.key==str(k.private()),
                                                   DbWalletKey.key_wif==k.extended_wif(),
                                                   DbWalletKey.address==k.public().address())).first()
        if wk:
            return HDWallet(w.id, wk.id)

        if not wallet_id:
            new_wallet = DbWallet(name=name, owner=owner)
            session.add(new_wallet)
            session.commit()
            wallet_id = new_wallet.id

        new_key = DbWalletKey(name=name, wallet_id=wallet_id, network=network, key=str(k.private()),
                              key_wif=k.extended_wif(), address=k.public().address())
        session.add(new_key)
        session.commit()
        return HDWallet(wallet_id, new_key.id)

    def __init__(self, wallet_id=0, key_id=0):
        print(wallet_id, key_id)

    def current_key(self):
        pass

    def new_key(self):
        pass

    def info(self):
        pass


if __name__ == '__main__':
    #
    # WALLETS EXAMPLES
    #

    # Create New Wallet with new imported Master Key on Bitcoin testnet3
    wallet_import = HDWallet.from_key('tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UX'
                               'F75r2dKePyA7irEvBoe4aAn52', 'TestNetWallet', network='testnet')

    # Create New Wallet and Generate a new Key
    wallet_new = HDWallet()

    # Get new Key for Imported Wallet
    new_key = wallet_import.new_key()
