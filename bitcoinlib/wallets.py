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
    def from_key(name, wallet_id, key='', account_id=0, change=0, network='bitcoin', purpose=44, parent_id=0, path='m'):
        k = HDKey(import_key=key, network=network)
        # TODO: Check if wallet name and key are not in database yet

        wk = session.query(DbWalletKey).filter(or_(DbWalletKey.key==str(k.private()),
                                                   DbWalletKey.key_wif==k.extended_wif(),
                                                   DbWalletKey.address==k.public().address())).first()
        if wk:
            return HDWalletKey(wk.id)

        new_key = DbWalletKey(name=name, wallet_id=wallet_id, network=network, key=str(k.private()), purpose=purpose,
                              account_id=account_id, depth=k.depth(), change=change, address_index=k.child_index(),
                              key_wif=k.extended_wif(), address=k.public().address(), parent_id=parent_id,
                              is_private=True, path=path)
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
            self.change = wk.change
            self.address_index = wk.address_index
            self.key_wif = wk.key_wif
            self.address = wk.address
            self.purpose = wk.purpose
            self.parent_id = wk.parent_id
            self.is_private = wk.is_private
            self.path = wk.path
            self.k = HDKey(import_key = self.key_wif)
            self.depth = wk.depth
        else:
            raise WalletError("Key with id %s not found" % key_id)

    def subkey_for_path(self, path):
        k = None
        if self.path() in 'Mm':
            k = self.k.subkey_for_path(path)

        if isinstance(k, HDKey):
            return False

    def fullpath(self, change=None, address_index=None):
        # BIP43 + BIP44: m / purpose' / coin_type' / account' / change / address_index
        if change is None:
            change = self.change
        if address_index is None:
            address_index = self.address_index
        if self.key:
            p = ["m"]
        else:
            p = ["M"]
        p.append(str(self.purpose) + "'")
        p.append(str(networks.NETWORKS[self.network]['bip44_cointype']) + "'")
        p.append(str(self.account_id) + "'")
        p.append(str(change))
        p.append(str(address_index))
        return p

    def info(self):
        print("--- Key ---")
        print(" ID                             %s" % self.key_id)
        print(" Is Private                     %s" % self.is_private)
        print(" Name                           %s" % self.name)
        print(" Key WIF                        %s" % self.key_wif)
        print(" Network                        %s" % self.network)
        print(" Account ID                     %s" % self.account_id)
        print(" Parent ID                      %s" % self.parent_id)
        print(" Depth                          %s" % self.depth)
        print(" Change                         %s" % self.change)
        print(" Address Index                  %s" % self.address_index)
        print(" Address                        %s" % self.address)
        print(" Path                           %s" % self.path)
        print("\n")


class HDWallet:

    @classmethod
    def create(cls, name, key='', owner='', network='bitcoin', account_id=0, purpose=44):
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
                                 account_id=account_id, purpose=purpose)
        new_wallet.main_key_id = m.key_id
        session.commit()

        # Create rest of Wallet Structure
        path = m.fullpath()
        cls._create_keys_from_path(m, path, wallet_id=new_wallet.id, network=network,
                                    account_id=account_id, change=0, purpose=purpose)
        path = m.fullpath(change=1)
        cls._create_keys_from_path(m, path, wallet_id=new_wallet.id, network=network,
                                    account_id=account_id, change=1, purpose=purpose)
        return HDWallet(new_wallet.id)

    @staticmethod
    def _create_keys_from_path(masterkey, path, wallet_id, network, account_id, basepath='', change=0, purpose=44):
        parent_id = 0
        for l in range(1, len(path)+1):
            pp = "/".join(path[:l])
            ckwif = masterkey.k.subkey_for_path(pp).extended_wif()
            nk = HDWalletKey.from_key(key=ckwif, name=pp, wallet_id=wallet_id, network=network,
                                      account_id=account_id, change=change, purpose=purpose, path=basepath+pp,
                                      parent_id=parent_id)
            parent_id = nk.key_id
        return parent_id

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
            self.main_key = HDWalletKey(self.main_key_id)
        else:
            raise WalletError("Wallet '%s' not found, please specify correct wallet ID or name." % wallet)

    def new_key(self, name='', account_id=0, change=0, purpose=44):
        # Find main account key
        acckey = session.query(DbWalletKey). \
            filter_by(wallet_id=self.wallet_id, purpose=purpose, network=self.network,
                      account_id=account_id, change=0, depth=3).first()
        prevkey = session.query(DbWalletKey). \
            filter_by(wallet_id=self.wallet_id, purpose=purpose, network=self.network,
                      account_id=account_id, change=change, depth=5). \
            order_by(DbWalletKey.address_index.desc()).first()
        if not acckey:
            raise WalletError("No account key found for account %d" % account_id)
        if not prevkey:
            raise WalletError("No child key found for account %d and change %d" % (account_id, change))

        address_index = prevkey.address_index + 1
        accwk = HDWalletKey(acckey.id)
        newpath = [str(change), str(address_index)]
        bpath = accwk.path + '/'
        newkey = self._create_keys_from_path(accwk, newpath, wallet_id=self.wallet_id, network=self.network,
                                             account_id=account_id, change=change, purpose=purpose, basepath=bpath)
        newwkey = HDWalletKey(newkey)
        newwkey.name = name
        session.commit()
        return newwkey

    def info(self, detail=0):
        print("=== WALLET ===")
        print(" ID                             %s" % self.wallet_id)
        print(" Name                           %s" % self.name)
        print(" Owner                          %s" % self.owner)
        print(" Network                        %s" % self.network)
        print("")

        if detail:
            print("= Main key =")
            self.main_key.info()
        if detail == 2:
            print("= Keys Overview = ")



if __name__ == '__main__':
    #
    # WALLETS EXAMPLES
    #

    import os
    os.remove(DATABASEFILE)
    Base.metadata.create_all(engine)

    # Create New Wallet and Generate a new Key
    wallet = HDWallet.create(name='Personal', owner='Lennart', network='testnet')
    wallet.info()

    new_key = wallet.new_key("Voor Pizza!")
    new_key.info()

    new_key = wallet.new_key("Voor meer Pizza!")
    new_key.info()

    new_key = wallet.new_key("Voor nog meer f#$%!^g Pizza!")
    new_key.info()

    new_key = wallet.new_key("Pizza change coins", change=1)
    new_key.info()

    # Create New Wallet with new imported Master Key on Bitcoin testnet3
    wallet_import = HDWallet.create(
        name='TestNetWallet',
        key='tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePy'
            'A7irEvBoe4aAn52',
        network='testnet',
        account_id=251)
    wallet_import.info()
    print(wallet_import.main_key.fullpath())

    wallet_import2 = HDWallet.create(
        name='Company Wallet',
        key='xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREP'
            'SL39UNdE3BBDu76',
        network='bitcoin',
        account_id=2, purpose=0)
    wallet_import2.info(detail=1)

    session.close()
