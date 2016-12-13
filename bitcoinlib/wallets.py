# -*- coding: utf-8 -*-
#
#    bitcoinlib wallets
#    © 2016 December - 1200 Web Development <http://1200wd.com/>
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
    def from_key(name, wallet_id, session, key='', account_id=0, network='bitcoin', change=0, purpose=44, parent_id=0,
                 path='m'):
        k = HDKey(import_key=key, network=network)
        # TODO: Check if wallet name and key are not in database yet

        if k.depth() != len(path.split('/'))-1:
            if path == 'm' and k.depth() == 3:
                # Create path when importing new account-key
                networkcode = networks.NETWORKS[network]['bip44_cointype']
                path = "m/%d'/%d'/%d'" % (purpose, networkcode, account_id)
            else:
                raise WalletError("Key depth of %d does not match path lenght of %d" %
                                  (k.depth(), len(path.split('/')) - 1))

        wk = session.query(DbKey).filter(or_(DbKey.key == str(k.private()),
                                             DbKey.key_wif == k.extended_wif(),
                                             DbKey.address == k.public().address())).first()
        if wk:
            return HDWalletKey(wk.id, session)

        nk = DbKey(name=name, wallet_id=wallet_id, key=str(k.private()), purpose=purpose,
                   account_id=account_id, depth=k.depth(), change=change, address_index=k.child_index(),
                   key_wif=k.extended_wif(), address=k.public().address(), parent_id=parent_id,
                   is_private=True, path=path)
        session.add(nk)
        session.commit()
        return HDWalletKey(nk.id, session)

    def __init__(self, key_id, session):
        wk = session.query(DbKey).filter_by(id=key_id).scalar()
        if wk:
            self.key_id = key_id
            self.name = wk.name
            self.wallet_id = wk.wallet_id
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
            self.network = wk.wallet.network
            self.k = HDKey(import_key=self.key_wif, network=self.network)
            self.depth = wk.depth
        else:
            raise WalletError("Key with id %s not found" % key_id)

    def fullpath(self, change=None, address_index=None, max_depth=5):
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
        return p[:max_depth]

    def parent(self, session):
        return HDWalletKey(self.parent_id, session=session)

    def getbalance(self):
        from bitcoinlib.services.blockexplorer import BlockExplorerClient
        bec = BlockExplorerClient()
        return bec.getbalance(self.address)

    def info(self):
        print("--- Key ---")
        print(" ID                             %s" % self.key_id)
        print(" Is Private                     %s" % self.is_private)
        print(" Name                           %s" % self.name)
        print(" Key WIF                        %s" % self.key_wif)
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
    def create(cls, name, key='', owner='', network='bitcoin', account_id=0, purpose=44,
               databasefile=DEFAULT_DATABASE):
        session = DbInit(databasefile=databasefile).session
        if session.query(DbWallet).filter_by(name=name).count():
            raise WalletError("Wallet with name '%s' already exists" % name)
        new_wallet = DbWallet(name=name, owner=owner, network=network, purpose=purpose)
        session.add(new_wallet)
        session.commit()

        mk = HDWalletKey.from_key(key=key, name=name, session=session, wallet_id=new_wallet.id, network=network,
                                  account_id=account_id, purpose=purpose)
        if mk.k.depth() > 4:
            raise WalletError("Cannot create new wallet with main key of depth 5 or more")
        new_wallet.main_key_id = mk.key_id
        session.commit()

        # Create rest of Wallet Structure
        depth = mk.k.depth()+1
        path = mk.fullpath(max_depth=3)[depth:]
        basepath = '/'.join(mk.fullpath(max_depth=3)[:depth])
        if basepath and len(path) and path[:1] != '/':
            basepath += '/'
        cls._create_keys_from_path(mk, path, name=name, wallet_id=new_wallet.id, network=network, session=session,
                                   account_id=account_id, change=0, purpose=purpose, basepath=basepath)
        session.close()
        return HDWallet(new_wallet.id, databasefile=databasefile)

    @staticmethod
    def _create_keys_from_path(masterkey, path, wallet_id, account_id, network, session,
                               name='', basepath='', change=0, purpose=44):
        parent_id = 0
        for l in range(1, len(path)+1):
            pp = "/".join(path[:l])
            ck = masterkey.k.subkey_for_path(pp)
            nk = HDWalletKey.from_key(key=ck.extended_wif(), name=name, wallet_id=wallet_id, network=network,
                                      account_id=account_id, change=change, purpose=purpose, path=basepath+pp,
                                      parent_id=parent_id, session=session)
            parent_id = nk.key_id
        return parent_id

    def __init__(self, wallet, databasefile=DEFAULT_DATABASE):
        self.session = DbInit(databasefile=databasefile).session
        if isinstance(wallet, int):
            w = self.session.query(DbWallet).filter_by(id=wallet).scalar()
        else:
            w = self.session.query(DbWallet).filter_by(name=wallet).scalar()
        if w:
            self.wallet_id = w.id
            self.name = w.name
            self.owner = w.owner
            self.network = w.network
            self.purpose = w.purpose
            self.main_key_id = w.main_key_id
            self.main_key = HDWalletKey(self.main_key_id, session=self.session)
        else:
            raise WalletError("Wallet '%s' not found, please specify correct wallet ID or name." % wallet)

    def __del__(self):
        pass
        # TODO close db
        
    def new_key(self, name='', account_id=0, change=0, max_depth=5):
        # Find main account key
        acckey = self.session.query(DbKey). \
            filter_by(wallet_id=self.wallet_id, purpose=self.purpose, account_id=account_id, change=0, depth=3).scalar()
        prevkey = self.session.query(DbKey). \
            filter_by(wallet_id=self.wallet_id, purpose=self.purpose, account_id=account_id, change=change, depth=5). \
            order_by(DbKey.address_index.desc()).first()

        address_index = 0
        if prevkey:
            address_index = prevkey.address_index + 1

        newpath = []
        if not acckey:
            acckey = self.session.query(DbKey). \
                filter_by(wallet_id=self.wallet_id, purpose=self.purpose, depth=2).scalar()
            newpath.append(str(account_id)+"'")
            if not acckey:
                raise WalletError("No key found this wallet_id, network and purpose. Is there a Master key imported?")

        accwk = HDWalletKey(acckey.id, session=self.session)
        newpath.append(str(change))
        newpath.append(str(address_index))
        bpath = accwk.path + '/'
        pathdepth = max_depth-accwk.k.depth()
        if not name:
            name = "Key %d" % address_index
        newkey = self._create_keys_from_path(accwk, newpath[:pathdepth], name=name, wallet_id=self.wallet_id,
                                             account_id=account_id, change=change, network=self.network,
                                             purpose=self.purpose, basepath=bpath, session=self.session)
        return HDWalletKey(newkey, session=self.session)

    def new_key_change(self, name='', account_id=0):
        return self.new_key(name=name, account_id=account_id, change=1)

    def new_account(self, name='', account_id=0):
        if self.keys(account_id=account_id):
            last_id = self.session.query(DbKey). \
                filter_by(wallet_id=self.wallet_id, purpose=self.purpose). \
                order_by(DbKey.account_id.desc()).first().account_id
            account_id = last_id + 1
        if not name:
            name = 'Account #%d' % account_id
        if self.keys(account_id=account_id):
            raise WalletError("Account with ID %d already exists for this wallet")
        ret = self.new_key(name=name, account_id=account_id, max_depth=4)
        self.new_key(name=name, account_id=account_id, max_depth=4, change=1)
        return ret.parent(session=self.session)

    def keys(self, account_id=None, change=None, depth=None, as_dict=False):
        qr = self.session.query(DbKey).filter_by(wallet_id=self.wallet_id, purpose=self.purpose)
        if account_id is not None:
            qr = qr.filter(DbKey.account_id == account_id)
            qr = qr.filter(DbKey.depth > 3)
        if change is not None:
            qr = qr.filter(DbKey.change == change)
            qr = qr.filter(DbKey.depth > 4)
        if depth is not None:
            qr = qr.filter(DbKey.depth == depth)
        return as_dict and [x.__dict__ for x in qr.all()] or qr.all()

    def accounts(self, account_id, as_dict=False):
        return self.keys(account_id, depth=3, as_dict=as_dict)

    def keys_addresses(self, account_id, as_dict=False):
        return self.keys(account_id, depth=5, as_dict=as_dict)

    def keys_address_payment(self, account_id, as_dict=False):
        return self.keys(account_id, depth=5, change=0, as_dict=as_dict)

    def keys_address_change(self, account_id, as_dict=False):
        return self.keys(account_id, depth=5, change=1, as_dict=as_dict)

    def getbalance(self, account_id=None):
        from bitcoinlib.services.blockexplorer import BlockExplorerClient
        addresslist = []
        for key in self.keys(account_id=account_id):
            addresslist.append(key.address)
        bec = BlockExplorerClient().getbalances(addresslist)
        return bec

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
        if detail > 1:
            print("= Keys Overview = ")
            if detail < 3:
                ds = [0, 3, 5]
            else:
                ds = range(0, 6)
            for d in ds:
                for key in self.keys(depth=d):
                    print("%5s %-28s %-45s %s" % (key.id, key.path, key.address, key.name))
        print("\n")


if __name__ == '__main__':
    #
    # WALLETS EXAMPLES
    #

    # First recreate database to avoid already exist errors
    import os
    test_databasefile = 'bitcoinlib.test.sqlite'
    test_database = DEFAULT_DATABASEDIR + test_databasefile
    if os.path.isfile(test_database):
        os.remove(test_database)

    # -- Create New Wallet and Generate a some new Keys --
    wallet = HDWallet.create(name='Personal', network='testnet', databasefile=test_database)
    wallet.new_account()
    new_key1 = wallet.new_key()
    new_key2 = wallet.new_key()
    new_key3 = wallet.new_key()
    new_key4 = wallet.new_key(change=1)
    donations_account = wallet.new_account()
    new_key5 = wallet.new_key(account_id=donations_account.account_id)
    wallet.info(detail=3)

    # -- Create New Wallet with Testnet master key and account ID 251 --
    wallet_import = HDWallet.create(
        name='TestNetWallet',
        key='tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePyA'
            '7irEvBoe4aAn52',
        network='testnet',
        databasefile=test_database)
    wallet_import.new_account(account_id=99)
    nk = wallet_import.new_key(account_id=99, name="Faucet gift")
    wallet_import.new_key_change(account_id=99, name="Faucet gift (Change)")
    wallet_import.info(detail=3)
    print("Balance %s" % wallet_import.getbalance())

    # -- Import Account Bitcoin Testnet key with depth 3
    accountkey = 'tprv8h4wEmfC2aSckSCYa68t8MhL7F8p9xAy322B5d6ipzY5ZWGGwksJMoajMCqd73cP4EVRygPQubgJPu9duBzPn3QV' \
                 '8Y7KbKUnaMzx9nnsSvh'
    wallet_import = HDWallet.create(
        databasefile=test_database,
        name='test_wallet_import_account',
        key=accountkey,
        network='testnet',
        account_id=99)
    wallet_import.info(detail=3)

    # -- Create New Wallet with account (depth=3) private key on bitcoin network and purpose 0 --
    wallet_import2 = HDWallet.create(
        name='Company Wallet',
        key='xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjAN'
            'TtpgP4mLTj34bhnZX7UiM',
        network='bitcoin',
        account_id=2, purpose=0,
        databasefile=test_database)
    wallet_import2.info(detail=3)

    # -- Create online wallet to generate addresses without private key
    pubkey = 'tpubDDkyPBhSAx8DFYxx5aLjvKH6B6Eq2eDK1YN76x1WeijE8eVUswpibGbv8zJjD6yLDHzVcqWzSp2fWVFhEW9XnBssFqM' \
             'wt9SrsVeBeqfBbR3'
    pubwal = HDWallet.create(
        databasefile=test_database,
        name='test_wallet_import_public_wallet',
        key=pubkey,
        network='testnet',
        account_id=0)
    newkey = pubwal.new_key()
    pubwal.info(detail=3)

    # -- Litecoin wallet
    litecoin_wallet = HDWallet.create(
        databasefile=test_database,
        name='litecoin_wallet',
        network='litecoin')
    newkey = litecoin_wallet.new_key()
    litecoin_wallet.info(detail=3)
