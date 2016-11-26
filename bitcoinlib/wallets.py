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

from sqlalchemy import or_

from bitcoinlib.db import *
from bitcoinlib.keys import HDKey
from bitcoinlib.config import networks

class WalletError(Exception):
    pass


class HDWalletKey:

    @staticmethod
    def import_key(key, name, wallet_id, account_id=0, change=0, owner='', network='bitcoin'):
        k = HDKey(key)
        # Check if wallet name and key are not in database yet

        wk = session.query(DbWalletKey).filter(or_(DbWalletKey.key==str(k.private()),
                                                   DbWalletKey.key_wif==k.extended_wif(),
                                                   DbWalletKey.address==k.public().address())).first()
        if wk:
            return HDWallet(wk.id)

        new_key = DbWalletKey(name=name, wallet_id=wallet_id, network=network, key=str(k.private()),
                              account_id=account_id, depth=k.depth(), change=change, address_index=k.child_index(),
                              key_wif=k.extended_wif(), address=k.public().address())
        session.add(new_key)
        session.commit()
        return HDWallet(new_key.id)

    def path(self):
        coin_type = networks.NETWORKS[self.network]['bip44_cointype']
        p = "m/44'/"

# rbts1415
class HDWallet:

    @staticmethod
    def create(name, owner=''):
        if session.query(DbWallet).filter_by(name=name).count():
            raise WalletError("Wallet with name '%s' already exists" % name)
        new_wallet = DbWallet(name=name, owner=owner)
        session.add(new_wallet)
        session.commit()
        # Create new Master Key
        return HDWallet(new_wallet.id)

    def __init__(self, wallet_id):
        w = session.query(DbWallet).filter_by(wallet_id=self.wallet_id).first()
        if w:
            self.wallet_id = wallet_id
            self.name = w.name
            self.owner = w.owner
            self.network = w.network
        else:
            raise WalletError("Wallet with id %s not found" % wallet_id)

    def info(self):
        pass

    def current_key(self):
        pass

    # m / purpose' / coin_type' / account' / change / address_index
    def new_key(self):
        pass


if __name__ == '__main__':
    #
    # WALLETS EXAMPLES
    #

    # Create New Wallet with new imported Master Key on Bitcoin testnet3
    # wallet_import = HDWallet.from_key('tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6Ddh'
    #                                   'DrzYVE8UXF75r2dKePyA7irEvBoe4aAn52', 'TestNetWallet', network='testnet')
    # wallet_import2 = HDWallet.from_key('xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQ'
    #                                    'jgPie1rFSruoUihUZREPSL39UNdE3BBDu76', 'TestNetWallet', network='bitcoin')

    # Create New Wallet and Generate a new Key
    wallet_new = HDWallet.create(name='Personal', owner='Lennart')

    # Get new Key for Imported Wallet
    # new_key = wallet_import.new_key()
