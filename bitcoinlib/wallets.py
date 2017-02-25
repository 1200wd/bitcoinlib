# -*- coding: utf-8 -*-
#
#    bitcoinlib wallets
#    © 2017 January - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.services.services import Service
from bitcoinlib.transactions import Transaction

_logger = logging.getLogger(__name__)


class WalletError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def list_wallets(databasefile=DEFAULT_DATABASE):
    session = DbInit(databasefile=databasefile).session
    wallets = session.query(DbWallet).all()
    wlst = []
    for w in wallets:
        wlst.append({
            'id': w.id,
            'name': w.name,
            'owner': w.owner,
            'network': w.network.name,
            'purpose': w.purpose,
            'balance': w.balance,
        })
    session.close()
    return wlst


def delete_wallet(wallet, databasefile=DEFAULT_DATABASE):
    session = DbInit(databasefile=databasefile).session
    if isinstance(wallet, int) or wallet.isdigit():
        w = session.query(DbWallet).filter_by(id=wallet)
    else:
        w = session.query(DbWallet).filter_by(name=wallet)
    if not w or not w.first():
        raise WalletError("Wallet '%s' not found" % wallet)
    # Also delete all keys and transactions in this wallet
    ks = session.query(DbKey).filter_by(wallet_id=w.first().id)
    for k in ks:
        session.query(DbUtxo).filter_by(key_id=k.id).delete()
    ks.delete()
    res = w.delete()
    session.commit()
    session.close()
    return res


class HDWalletKey:

    @staticmethod
    def from_key(name, wallet_id, session, key='', hdkey_object=0, account_id=0, network='bitcoin', change=0,
                 purpose=44, parent_id=0, path='m'):
        # TODO: Test key and throw warning if invalid network, account_id etc
        if not hdkey_object:
            k = HDKey(import_key=key, network=network)
        else:
            k = hdkey_object
        keyexists = session.query(DbKey).filter(DbKey.key_wif == k.extended_wif()).all()
        if keyexists:
            raise WalletError("Key %s already exists" % (key or k.extended_wif()))

        if k.depth != len(path.split('/'))-1:
            if path == 'm' and k.depth == 3:
                # Create path when importing new account-key
                networkcode = networks.NETWORKS[network]['bip44_cointype']
                path = "m/%d'/%s'/%d'" % (purpose, networkcode, account_id)
            else:
                raise WalletError("Key depth of %d does not match path lenght of %d" %
                                  (k.depth, len(path.split('/')) - 1))

        wk = session.query(DbKey).filter(or_(DbKey.key == str(k.private()),
                                             DbKey.key_wif == k.extended_wif(),
                                             DbKey.address == k.public().address())).first()
        if wk:
            return HDWalletKey(wk.id, session)

        nk = DbKey(name=name, wallet_id=wallet_id, key=str(k.private()), purpose=purpose,
                   account_id=account_id, depth=k.depth, change=change, address_index=k.child_index,
                   key_wif=k.extended_wif(), address=k.public().address(), parent_id=parent_id,
                   is_private=True, path=path, key_type=k.key_type)
        session.add(nk)
        session.commit()
        return HDWalletKey(nk.id, session)

    @classmethod
    def from_key_object(cls, hdkey_object, name, wallet_id, session, account_id=0, network='bitcoin', change=0,
                        purpose=44, parent_id=0, path='m'):
        if not isinstance(hdkey_object, HDKey):
            raise WalletError("The hdkey_object variable must be a HDKey type")
        return cls.from_key(name=name, wallet_id=wallet_id, session=session,
                            hdkey_object=hdkey_object, account_id=account_id, network=network,
                            change=change, purpose=purpose, parent_id=parent_id, path=path)

    def __init__(self, key_id, session):
        wk = session.query(DbKey).filter_by(id=key_id).scalar()
        if wk:
            self.dbkey = wk
            self.key_id = key_id
            self.name = wk.name
            self.wallet_id = wk.wallet_id
            self.key = wk.key
            self.account_id = wk.account_id
            self.change = wk.change
            self.address_index = wk.address_index
            self.key_wif = wk.key_wif
            self.address = wk.address
            self.balance = wk.balance
            self.purpose = wk.purpose
            self.parent_id = wk.parent_id
            self.is_private = wk.is_private
            self.path = wk.path
            self.wallet = wk.wallet
            self.network = wk.wallet.network
            self.k = HDKey(import_key=self.key_wif, network=self.network.name)
            self.depth = wk.depth
            self.key_type = wk.key_type
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
        p.append(str(networks.NETWORKS[self.network.name]['bip44_cointype']) + "'")
        p.append(str(self.account_id) + "'")
        p.append(str(change))
        p.append(str(address_index))
        return p[:max_depth]

    def parent(self, session):
        return HDWalletKey(self.parent_id, session=session)

    def updatebalance(self):
        self.balance = Service(network=self.network.name).getbalance([self.address])
        self.dbkey.balance = self.balance

    def updateutxo(self):
        utxos = Service(network=self.network.name).getutxos([self.address])
        from pprint import pprint
        pprint(utxos)

    def info(self):
        print("--- Key ---")
        print(" ID                             %s" % self.key_id)
        print(" Key Type                       %s" % self.key_type)
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
        print(" Balance                        %s" % self.balance)
        print("\n")


class HDWallet:

    @classmethod
    def create(cls, name, key='', owner='', network='bitcoin', account_id=0, purpose=44,
               databasefile=DEFAULT_DATABASE):
        session = DbInit(databasefile=databasefile).session
        if session.query(DbWallet).filter_by(name=name).count():
            raise WalletError("Wallet with name '%s' already exists" % name)
        else:
            _logger.info("Create new wallet '%s'" % name)
        # if key and get_key_format(key) in ['wif', 'wif_compressed', 'wif_protected']:
        #     raise WalletError("Cannot create a HD Wallet from a simple private key. Create wallet first and then "
        #                       "import new Private key.")
        new_wallet = DbWallet(name=name, owner=owner, network_name=network, purpose=purpose)
        session.add(new_wallet)
        session.commit()
        new_wallet_id = new_wallet.id

        mk = HDWalletKey.from_key(key=key, name=name, session=session, wallet_id=new_wallet_id, network=network,
                                  account_id=account_id, purpose=purpose)
        if mk.k.depth > 4:
            raise WalletError("Cannot create new wallet with main key of depth 5 or more")
        new_wallet.main_key_id = mk.key_id
        session.commit()

        if mk.key_type == 'bip32':
            # Create rest of Wallet Structure
            depth = mk.k.depth+1
            path = mk.fullpath(max_depth=3)[depth:]
            basepath = '/'.join(mk.fullpath(max_depth=3)[:depth])
            if basepath and len(path) and path[:1] != '/':
                basepath += '/'
            cls._create_keys_from_path(mk, path, name=name, wallet_id=new_wallet.id, network=network, session=session,
                                       account_id=account_id, change=0, purpose=purpose, basepath=basepath)
        session.close()
        return HDWallet(new_wallet_id, databasefile=databasefile)

    @staticmethod
    def _create_keys_from_path(masterkey, path, wallet_id, account_id, network, session,
                               name='', basepath='', change=0, purpose=44):
        parent_id = 0
        for l in range(1, len(path)+1):
            pp = "/".join(path[:l])
            fullpath = basepath+pp
            if session.query(DbKey).filter_by(wallet_id=wallet_id, path=fullpath).all():
                continue
            ck = masterkey.k.subkey_for_path(pp)
            nk = HDWalletKey.from_key_object(ck, name=name, wallet_id=wallet_id, network=network,
                                             account_id=account_id, change=change, purpose=purpose, path=fullpath,
                                             parent_id=parent_id, session=session)
            parent_id = nk.key_id
        return parent_id

    def __enter__(self):
        return self

    def __init__(self, wallet, databasefile=DEFAULT_DATABASE):
        self.session = DbInit(databasefile=databasefile).session
        if isinstance(wallet, int) or wallet.isdigit():
            w = self.session.query(DbWallet).filter_by(id=wallet).scalar()
        else:
            w = self.session.query(DbWallet).filter_by(name=wallet).scalar()
        if w:
            self.dbwallet = w
            self.wallet_id = w.id
            self.name = w.name
            self.owner = w.owner
            self.network = w.network
            self.purpose = w.purpose
            self.balance = w.balance
            self.main_key_id = w.main_key_id
            self.main_key = HDWalletKey(self.main_key_id, session=self.session)
        else:
            raise WalletError("Wallet '%s' not found, please specify correct wallet ID or name." % wallet)

    def __exit__(self, exception_type, exception_value, traceback):
        self.session.close()

    def __del__(self):
        self.session.close()

    def import_key(self, key, account_id=None):
        return HDWalletKey.from_key(
            key=key, name=self.name, wallet_id=self.wallet_id, network=self.network.name,
            account_id=account_id, purpose=self.purpose, session=self.session)

    def import_hdkey_object(self, hdkey_object, account_id=None):
        return HDWalletKey.from_key_object(
            hdkey_object, name=self.name, wallet_id=self.wallet_id, network=self.network.name,
            account_id=account_id, purpose=self.purpose, session=self.session)

    def new_key(self, name='', account_id=0, change=0, max_depth=5):
        # Find main account key
        acckey = self.session.query(DbKey). \
            filter_by(wallet_id=self.wallet_id, purpose=self.purpose,
                      account_id=account_id, change=0, depth=3).scalar()
        prevkey = self.session.query(DbKey). \
            filter_by(wallet_id=self.wallet_id, purpose=self.purpose,
                      account_id=account_id, change=change, depth=5). \
            order_by(DbKey.address_index.desc()).first()

        address_index = 0
        if prevkey:
            address_index = prevkey.address_index + 1

        newpath = []
        if not acckey:
            acckey = self.session.query(DbKey). \
                filter(DbKey.wallet_id == self.wallet_id, DbKey.purpose == self.purpose, DbKey.depth == 2,
                       DbKey.parent_id != 0).scalar()
            newpath.append(str(account_id)+"'")
            if not acckey:
                raise WalletError("No key found this wallet_id, network and purpose. "
                                  "Is there a BIP32 Master key imported?")

        accwk = HDWalletKey(acckey.id, session=self.session)
        newpath.append(str(change))
        newpath.append(str(address_index))
        bpath = accwk.path + '/'
        pathdepth = max_depth-accwk.k.depth
        if not name:
            name = "Key %d" % address_index
        newkey = self._create_keys_from_path(accwk, newpath[:pathdepth], name=name, wallet_id=self.wallet_id,
                                             account_id=account_id, change=change, network=self.network.name,
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

    def key_for_path(self, path, name='', account_id=0, change=0):
        newkey = self.main_key.k.subkey_for_path(path)
        if not name:
            name = self.name
        nk = HDWalletKey.from_key_object(newkey, name=name, wallet_id=self.wallet_id,
                                         network=self.network, account_id=account_id, change=change,
                                         purpose=self.purpose, path=path, session=self.session)
        return nk

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

    def addresslist(self, account_id=None):
        addresslist = []
        for key in self.keys(account_id=account_id):
            addresslist.append(key.address)
        return addresslist

    def updatebalance(self, account_id=None):
        self.balance = Service(network=self.network.name).getbalance(self.addresslist(account_id=account_id))
        self.dbwallet.balance = self.balance
        self.session.commit()

    def updateutxos(self, account_id=None):
        utxos = Service(network=self.network.name).getutxos(self.addresslist(account_id=account_id))
        key_balances = {}
        for utxo in utxos:
            key = self.session.query(DbKey).filter_by(address=utxo['address']).scalar()
            if key.id in key_balances:
                key_balances[key.id] += float(utxo['value'])
            else:
                key_balances[key.id] = float(utxo['value'])

            # Skip if utxo was already imported
            if self.session.query(DbUtxo).filter_by(tx_hash=utxo['tx_hash']).count():
                continue

            new_utxo = DbUtxo(key_id=key.id, tx_hash=utxo['tx_hash'], confirmations=utxo['confirmations'],
                              output_n=utxo['output_n'], index=utxo['index'], value=utxo['value'],
                              script=utxo['script'])
            self.session.add(new_utxo)
        for kb in key_balances:
            getkey = self.session.query(DbKey).filter_by(id=kb).scalar()
            getkey.balance = key_balances[kb]
        self.session.commit()

    def send(self, to_address, amount, account_id=None, fee=None):
        outputs = [(to_address, amount)]
        self.create_transaction(outputs, account_id=account_id, fee=fee)

    @staticmethod
    def _select_inputs(amount, utxo_query=None):
        if not utxo_query:
            return None

        DENOMINATOR = pow(10, 8)

        # Try to find one utxo with exact amount or higher
        one_utxo = utxo_query.filter(DbUtxo.value*DENOMINATOR >= amount).order_by(DbUtxo.value).first()
        if one_utxo:
            return [one_utxo]

        # Otherwise compose of 2 or more lesser outputs
        lessers = utxo_query.filter(DbUtxo.value*DENOMINATOR < amount).order_by(DbUtxo.value.desc()).all()
        total_amount = 0
        selected_utxos = []
        for utxo in lessers:
            if total_amount < amount:
                selected_utxos.append(utxo)
                total_amount += utxo.value*DENOMINATOR
        if total_amount < amount:
            return None
        return selected_utxos

    def create_transaction(self, output_arr, input_arr=None, account_id=None, fee=None):
        total_amount = 0
        t = Transaction(network=self.network.name)
        for o in output_arr:
            total_amount += o[1]
            t.add_output(o[1], o[0])

        qr = self.session.query(DbUtxo)
        if account_id is not None:
            qr.filter(DbKey.account_id == account_id)
        utxos = qr.all()
        if not utxos:
            return None

        # TODO: Estimate fees
        if fee is None:
            fee = 100000

        if input_arr is None:
            input_arr = []
            selected_utxos = self._select_inputs(total_amount + fee, qr)
            for utxo in selected_utxos:
                input_arr.append((utxo.tx_hash, utxo.output_n, utxo.key_id))

        # Add inputs
        sign_arr = []
        for inp in input_arr:
            key = self.session.query(DbKey).filter_by(id=inp[2]).scalar()
            k = HDKey(key.key_wif)
            id = t.add_input(inp[0], inp[1], public_key=k.public().public_byte())
            sign_arr.append((k.private().private_byte(), id))

        # Sign inputs
        for ti in sign_arr:
            t.sign(ti[0], ti[1])

        # Verify transaction
        t.verify()

        # TODO: Send transaction
        from pprint import pprint
        pprint(t.get())

    def info(self, detail=0):
        print("=== WALLET ===")
        print(" ID                             %s" % self.wallet_id)
        print(" Name                           %s" % self.name)
        print(" Owner                          %s" % self.owner)
        print(" Network                        %s" % self.network.description)
        print(" Balance                        %s" % self.balance)
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
    # if os.path.isfile(test_database):
    #     os.remove(test_database)

    # -- Create New Wallet and Generate a some new Keys --
    if False:
        with HDWallet.create(name='Personal', network='testnet', databasefile=test_database) as wallet:
            wallet.info(detail=3)
            wallet.new_account()
            new_key1 = wallet.new_key()
            new_key2 = wallet.new_key()
            new_key3 = wallet.new_key()
            new_key4 = wallet.new_key(change=1)
            wallet.key_for_path('m/0/0')
            donations_account = wallet.new_account()
            new_key5 = wallet.new_key(account_id=donations_account.account_id)
            wallet.info(detail=3)

    # -- Create New Wallet with Testnet master key and account ID 99 --
    if True:
        # wallet_import = HDWallet.create(
        #     name='TestNetWallet',
        #     key='tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePyA'
        #         '7irEvBoe4aAn52',
        #     network='testnet',
        #     databasefile=test_database)
        # wallet_import.new_account(account_id=99)
        # nk = wallet_import.new_key(account_id=99, name="Faucet gift")
        # nk2 = wallet_import.new_key(account_id=99, name="Send to test")
        # nkc = wallet_import.new_key_change(account_id=99, name="Faucet gift (Change)")
        # wallet_import.updateutxos()
        # wallet_import.info(detail=3)

        wallet_import = HDWallet('TestNetWallet')
        # Send to test
        wallet_import.send('mxdLD8SAGS9fe2EeCXALDHcdTTbppMHp8N', 20000000)

    # -- Import Account Bitcoin Testnet key with depth 3
    if False:
        accountkey = 'tprv8h4wEmfC2aSckSCYa68t8MhL7F8p9xAy322B5d6ipzY5ZWGGwksJMoajMCqd73cP4EVRygPQubgJPu9duBzPn3QV' \
                     '8Y7KbKUnaMzxnnnsSvh'
        wallet_import2 = HDWallet.create(
            databasefile=test_database,
            name='Account Import',
            key=accountkey,
            network='testnet',
            account_id=99)
        wallet_import2.info(detail=3)
        del wallet_import2

    # -- Create New Wallet with account (depth=3) private key on bitcoin network and purpose 0 --
    if False:
        wallet_import2 = HDWallet.create(
            name='Company Wallet',
            key='xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjAN'
                'TtpgP4mLTj34bhnZX7UiM',
            network='bitcoin',
            account_id=2, purpose=0,
            databasefile=test_database)
        wallet_import2.info(detail=3)
        del wallet_import2

    # -- Create simple wallet with just some private keys --
    if False:
        simple_wallet = HDWallet.create(
            name='Simple Wallet',
            key='L5fbTtqEKPK6zeuCBivnQ8FALMEq6ZApD7wkHZoMUsBWcktBev73',
            databasefile=test_database)
        simple_wallet.import_key('KxVjTaa4fd6gaga3YDDRDG56tn1UXdMF9fAMxehUH83PTjqk4xCs')
        simple_wallet.import_key('L3RyKcjp8kzdJ6rhGhTC5bXWEYnC2eL3b1vrZoduXMht6m9MQeHy')
        simple_wallet.updateutxos()
        simple_wallet.info(detail=3)
        del simple_wallet

    # -- Create online wallet to generate addresses without private key
    if False:
        pubkey = 'tpubDDkyPBhSAx8DFYxx5aLjvKH6B6Eq2eDK1YN76x1WeijE8eVUswpibGbv8zJjD6yLDHzVcqWzSp2fWVFhEW9XnBssFqM' \
                 'wt9SrsVeBeqfBbR3'
        pubwal = HDWallet.create(
            databasefile=test_database,
            name='Import Public Key Wallet',
            key=pubkey,
            network='testnet',
            account_id=0)
        newkey = pubwal.new_key()
        pubwal.info(detail=3)
        del pubwal

    # -- Litecoin wallet
    if False:
        litecoin_wallet = HDWallet.create(
            databasefile=test_database,
            name='Litecoin Wallet',
            network='litecoin')
        newkey = litecoin_wallet.new_key()
        litecoin_wallet.info(detail=3)
        del litecoin_wallet

    # -- List wallets & delete a wallet
    # print(','.join([w['name'] for w in list_wallets(databasefile=test_database)]))
    # delete_wallet(1, databasefile=test_database)
    # print(','.join([w['name'] for w in list_wallets(databasefile=test_database)]))
