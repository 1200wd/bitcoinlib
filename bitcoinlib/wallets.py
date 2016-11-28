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
    def from_key(name, wallet_id, key='', account_id=0, change=0, network='bitcoin', purpose=44):
        k = HDKey(key, network=network)
        # TODO: Check if wallet name and key are not in database yet

        wk = session.query(DbWalletKey).filter(or_(DbWalletKey.key==str(k.private()),
                                                   DbWalletKey.key_wif==k.extended_wif(),
                                                   DbWalletKey.address==k.public().address())).first()
        if wk:
            return HDWallet(wk.id)

        new_key = DbWalletKey(name=name, wallet_id=wallet_id, network=network, key=str(k.private()), purpose=purpose,
                              account_id=account_id, depth=k.depth(), change=change, address_index=k.child_index(),
                              key_wif=k.extended_wif(), address=k.public().address())
        session.add(new_key)
        session.commit()
        return HDWalletKey(new_key.id)

    def __init__(self, key_id):
        wk = session.query(DbWalletKey).filter_by(id=key_id).first()
        if wk:
            self.key_id = key_id
            self.name = wk.name
            self.wallet_id = wk.wallet_id
            self.network = wk.network
            self.key = wk.key
            self.account_id = wk.account_id
            self.depth = wk.depth
            self.change = wk.change
            self.address_index = wk.address_index
            self.key_wif = wk.key_wif
            self.address = wk.address
            self.purpose = wk.purpose
        else:
            raise WalletError("Key with id %s not found" % key_id)

    def path(self):
        # BIP43 + BIP44: m / purpose' / coin_type' / account' / change / address_index
        if self.key:
            p = "m"
        else:
            p = "M"
        if self.depth > 0:
            p += "/" + str(self.purpose) + "'"
        if self.depth > 1:
            p += "/" + str(networks.NETWORKS[self.network]['bip44_cointype']) + "'"
        if self.depth > 2:
            p += "/" + str(self.account_id) + "'"
        if self.depth > 3:
            p += "/" + str(self.change)
        if self.depth > 4:
            p += "/" + str(self.address_index)
        return p

    def info(self):
        print("--- Key ---")
        print(" ID                             %s" % self.key_id)
        print(" Name                           %s" % self.name)
        print(" Key WIF                        %s" % self.key_wif)
        print(" Network                        %s" % self.network)
        print(" Account ID                     %s" % self.account_id)
        print(" Depth                          %s" % self.depth)
        print(" Change                         %s" % self.change)
        print(" Address Index                  %s" % self.address_index)
        print(" Address                        %s" % self.address)
        print(" Path                           %s" % self.path())
        print("\n")


class HDWallet:

    @staticmethod
    def create(name, key='', owner='', network='bitcoin', account_id=0, change=0, purpose=44):
        if session.query(DbWallet).filter_by(name=name).count():
            raise WalletError("Wallet with name '%s' already exists" % name)
        new_wallet = DbWallet(name=name, owner=owner, network=network)
        session.add(new_wallet)
        session.commit()

        # Create new Master Key
        if not key:
            keyname = 'master'
        else:
            keyname = name + " key"
        m = HDWalletKey.from_key(key=key, name=keyname, wallet_id=new_wallet.id, network=network,
                                 account_id=account_id, change=change, purpose=purpose)
        new_wallet.main_key_id = m.key_id
        session.commit()

        return HDWallet(new_wallet.id)

    def __init__(self, wallet):
        if isinstance(wallet, int):
            w = session.query(DbWallet).filter_by(id=wallet).first()
        else:
            w = session.query(DbWallet).filter_by(name=wallet).first()
        if w:
            self.wallet_id = w.id
            self.name = w.name
            self.owner = w.owner
            self.network = w.network
            self.main_key_id = w.main_key_id
            self.key_cur = HDWalletKey(self.main_key_id)
        else:
            raise WalletError("Wallet '%s' not found, please specify correct wallet ID or name." % wallet)

    def info(self):
        print("=== WALLET ===")
        print(" ID                             %s" % self.wallet_id)
        print(" Name                           %s" % self.name)
        print(" Owner                          %s" % self.owner)
        print(" Network                        %s" % self.network)
        print("")

        print("= Main key =")
        self.key_cur.info()



if __name__ == '__main__':
    #
    # WALLETS EXAMPLES
    #

    # Create New Wallet and Generate a new Key
    try:
        wallet_new = HDWallet.create(name='Personal', owner='Lennart', network='testnet')
    except WalletError:
        wallet_new = HDWallet('Personal')
    wallet_new.info()

    # Create New Wallet with new imported Master Key on Bitcoin testnet3
    try:
        wallet_import = HDWallet.create(
            name='TestNetWallet',
            key='tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePy'
                'A7irEvBoe4aAn52',
            network='testnet')
    except WalletError:
        wallet_import = HDWallet("TestNetWallet")
    wallet_import.info()

    try:
        wallet_import2 = HDWallet.create(
            name='TestNetWallet2',
            key='xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREPSL39UNdE3BBDu76',
            network='bitcoin', account_id=2, change=2, purpose=0)
    except WalletError:
        wallet_import2 = HDWallet('TestNetWallet2')
    wallet_import2.info()

    # Get new Key for Imported Wallet
    # new_key = wallet_import.new_key()
