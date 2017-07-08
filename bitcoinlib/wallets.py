# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    WALLETS - HD wallet Class for key and transaction management
#    © 2017 July - 1200 Web Development <http://1200wd.com/>
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

import numbers
from itertools import groupby
from sqlalchemy import or_
from bitcoinlib.db import *
from bitcoinlib.encoding import pubkeyhash_to_addr
from bitcoinlib.keys import HDKey, check_network_and_key
from bitcoinlib.networks import Network, DEFAULT_NETWORK
from bitcoinlib.services.services import Service
from bitcoinlib.transactions import Transaction, serialize_multisig
from bitcoinlib.mnemonic import Mnemonic

_logger = logging.getLogger(__name__)


class WalletError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def list_wallets(databasefile=DEFAULT_DATABASE):
    """
    List Wallets from database
    
    :param databasefile: Location of Sqlite database. Leave empty to use default
    :type databasefile: str
    
    :return dict: Dictionary of wallets defined in database
    """

    session = DbInit(databasefile=databasefile).session
    wallets = session.query(DbWallet).all()
    wlst = []
    for w in wallets:
        wlst.append({
            'id': w.id,
            'name': w.name,
            'owner': w.owner,
            'network': w.network_name,
            'purpose': w.purpose,
            'balance': w.balance,
        })
    session.close()
    return wlst


def wallet_exists(wallet, databasefile=DEFAULT_DATABASE):
    """
    Check if Wallets is defined in database
    
    :param wallet: Wallet ID as integer or Wallet Name as string
    :type wallet: int, str
    :param databasefile: Location of Sqlite database. Leave empty to use default
    :type databasefile: str
    
    :return bool: True if wallet exists otherwise False
    """

    if wallet in [x['name'] for x in list_wallets(databasefile)]:
        return True
    if isinstance(wallet, int) and wallet in [x['id'] for x in list_wallets(databasefile)]:
        return True
    return False


def delete_wallet(wallet, databasefile=DEFAULT_DATABASE, force=False):
    """
    Delete wallet and associated keys from the database. If wallet has unspent outputs it raises a WalletError exception
    unless 'force=True' is specified
    
    :param wallet: Wallet ID as integer or Wallet Name as string
    :type wallet: int, str
    :param databasefile: Location of Sqlite database. Leave empty to use default
    :type databasefile: str
    :param force: If set to True wallet will be deleted even if unspent outputs are found. Default is False
    :type force: bool
    
    :return int: Number of rows deleted, so 1 if succesfull
    """

    session = DbInit(databasefile=databasefile).session
    if isinstance(wallet, int) or wallet.isdigit():
        w = session.query(DbWallet).filter_by(id=wallet)
    else:
        w = session.query(DbWallet).filter_by(name=wallet)
    if not w or not w.first():
        raise WalletError("Wallet '%s' not found" % wallet)

    # Delete keys from this wallet and update transactions (remove key_id)
    ks = session.query(DbKey).filter_by(wallet_id=w.first().id)
    for k in ks:
        if not force and k.balance:
            raise WalletError("Key %d (%s) still has unspent outputs. Use 'force=True' to delete this wallet" %
                              (k.id, k.address))
        session.query(DbTransactionOutput).filter_by(key_id=k.id).update({DbTransactionOutput.key_id: None})
        session.query(DbTransactionInput).filter_by(key_id=k.id).update({DbTransactionInput.key_id: None})
    ks.delete()

    res = w.delete()
    session.commit()
    session.close()
    _logger.info("Wallet '%s' deleted" % wallet)
    return res


def normalize_path(path):
    """ Normalize BIP0044 key path for HD keys. Using single quotes for hardened keys 

    :param path: BIP0044 key path 
    :type path: str
    :return str: Normalized BIP004 key path with single quotes
    """

    levels = path.split("/")
    npath = ""
    for level in levels:
        if not level:
            raise WalletError("Could not parse path. Index is empty.")
        nlevel = level
        if level[-1] in "'HhPp":
            nlevel = level[:-1] + "'"
        npath += nlevel + "/"
    if npath[-1] == "/":
        npath = npath[:-1]
    return npath


def parse_bip44_path(path):
    """
    Assumes a correct BIP0044 path and returns a dictionary with path items. See Bitcoin improvement proposals
    BIP0043 and BIP0044.
    
    Specify path in this format: m / purpose' / cointype' / account' / change / address_index.
    Path lenght must be between 1 and 6 (Depth between 0 and 5)
    
    :param path: BIP0044 path as string, with backslash (/) seperator. 
    :type path: str
    
    :return dict: Dictionary with path items: isprivate, purpose, cointype, account, change and address_index
    """

    pathl = normalize_path(path).split('/')
    if not 0 < len(pathl) <= 6:
        raise WalletError("Not a valid BIP0044 path. Path length (depth) must be between 1 and 6 not %d" % len(pathl))
    return {
        'isprivate': True if pathl[0] == 'm' else False,
        'purpose': '' if len(pathl) < 2 else pathl[1],
        'cointype': '' if len(pathl) < 3 else pathl[2],
        'account': '' if len(pathl) < 4 else pathl[3],
        'change': '' if len(pathl) < 5 else pathl[4],
        'address_index': '' if len(pathl) < 6 else pathl[5],
    }


class HDWalletKey:
    """
    Normally only used as attribute of HDWallet class. Contains HDKey object and extra information such as path and
    balance.
    
    All HDWalletKey are stored in a database
    """

    @staticmethod
    def from_key(name, wallet_id, session, key='', hdkey_object=None, account_id=0, network=None, change=0,
                 purpose=44, parent_id=0, path='m', key_type=None, tree_index=0):
        """
        Create HDWalletKey from a HDKey object or key
        
        :param name: New key name
        :type name: str
        :param wallet_id: ID of wallet where to store key
        :type wallet_id: int
        :param session: Required Sqlalchemy Session object
        :type session: sqlalchemy.orm.session.Session
        :param key: Optional key in any format accepted by the HDKey class
        :type key: str, int, byte, bytearray
        :param hdkey_object: Optional HDKey object to import, use this if available to save key derivation time
        :type hdkey_object: HDKey
        :param account_id: Account ID for specified key, default is 0
        :type account_id: int
        :param network: Network of specified key
        :type network: str
        :param change: Use 0 for normal key, and 1 for change key (for returned payments)
        :type change: int
        :param purpose: BIP0044 purpose field, default is 44
        :type purpose: int
        :param parent_id: Key ID of parent, default is 0 (no parent)
        :type parent_id: int
        :param path: BIP0044 path of given key, default is 'm' (masterkey)
        
        :return HDWalletKey: HDWalletKey object
        """

        if not hdkey_object:
            if network is None:
                network = DEFAULT_NETWORK
            k = HDKey(import_key=key, network=network)
        else:
            k = hdkey_object

        keyexists = session.query(DbKey).filter(DbKey.wif == k.wif()).first()
        if keyexists:
            _logger.warning("Key %s already exists" % (key or k.wif()))
            return HDWalletKey(keyexists.id, session, k)

        if key_type != 'single' and k.depth != len(path.split('/'))-1:
            if path == 'm' and k.depth == 3:
                # Create path when importing new account-key
                nw = Network(network)
                networkcode = nw.bip44_cointype
                path = "m/%d'/%s'/%d'" % (purpose, networkcode, account_id)
            else:
                raise WalletError("Key depth of %d does not match path lenght of %d for path %s" %
                                  (k.depth, len(path.split('/')) - 1, path))

        wk = session.query(DbKey).filter(or_(DbKey.key == k.key_hex,
                                             DbKey.wif == k.wif())).first()
        if wk:
            return HDWalletKey(wk.id, session, k)

        nk = DbKey(name=name, wallet_id=wallet_id, key=k.key_hex, purpose=purpose,
                   account_id=account_id, depth=k.depth, change=change, address_index=k.child_index,
                   wif=k.wif(), address=k.key.address(), parent_id=parent_id,
                   is_private=True, path=path, key_type=key_type, network_name=network, tree_index=tree_index)
        session.add(nk)
        session.commit()
        return HDWalletKey(nk.id, session, k)

    def __init__(self, key_id, session, hdkey_object=None):
        """
        Initialize HDWalletKey with specified ID, get information from database.
        
        :param key_id: ID of key as mentioned in database
        :type key_id: int
        :param session: Required Sqlalchemy Session object
        :type session: sqlalchemy.orm.session.Session
        :param hdkey_object: Optional HDKey object 
        :type hdkey_object: HDKey
        """

        wk = session.query(DbKey).filter_by(id=key_id).first()
        if wk:
            self._dbkey = wk
            self._hdkey_object = hdkey_object
            self.key_id = key_id
            self.name = wk.name
            self.wallet_id = wk.wallet_id
            self.key_hex = wk.key
            self.account_id = wk.account_id
            self.change = wk.change
            self.address_index = wk.address_index
            self.wif = wk.wif
            self.address = wk.address
            self._balance = wk.balance
            self.purpose = wk.purpose
            self.parent_id = wk.parent_id
            self.is_private = wk.is_private
            self.path = wk.path
            self.wallet = wk.wallet
            self.network_name = wk.network_name
            if not self.network_name:
                self.network_name = wk.wallet.network_name
            self.network = Network(self.network_name)
            self.depth = wk.depth
            self.key_type = wk.key_type
            self.tree_index = wk.tree_index
        else:
            raise WalletError("Key with id %s not found" % key_id)

    def __repr__(self):
        return "<HDWalletKey (name=%s, wif=%s, path=%s)>" % (self.name, self.wif, self.path)

    def key(self):
        """
        Get HDKey object for current HDWalletKey
        
        :return HDKey: 
        """

        if self._hdkey_object is None:
            self._hdkey_object = HDKey(import_key=self.wif, network=self.network_name)
        return self._hdkey_object

    def balance(self, fmt=''):
        """
        Get total of unspent outputs
        
        :param fmt: Specify 'string' to return a string in currency format
        :type fmt: str
        
        :return float, str: Key balance 
        """

        if fmt == 'string':
            return self.network.print_value(self._balance)
        else:
            return self._balance

    def fullpath(self, change=None, address_index=None, max_depth=5):
        """
        Full BIP0044 key path:
        - m / purpose' / coin_type' / account' / change / address_index
        
        :param change: Normal = 0, change =1
        :type change: int
        :param address_index: Index number of address (path depth 5)
        :type address_index: int
        :param max_depth: Maximum depth of output path. I.e. type 3 for account path
        :type max_depth: int
        
        :return list: Current key path 
        """

        if change is None:
            change = self.change
        if address_index is None:
            address_index = self.address_index
        if self.key_hex:
            p = ["m"]
        else:
            p = ["M"]
        p.append(str(self.purpose) + "'")
        p.append(str(self.network.bip44_cointype) + "'")
        p.append(str(self.account_id) + "'")
        p.append(str(change))
        p.append(str(address_index))
        return p[:max_depth]

    def info(self):
        """
        Output current key information to standard output
        
        """

        print("--- Key ---")
        print(" ID                             %s" % self.key_id)
        print(" Key Type                       %s" % self.key_type)
        print(" Is Private                     %s" % self.is_private)
        print(" Name                           %s" % self.name)
        print(" Key Hex                        %s" % self.key_hex)
        print(" Key WIF                        %s" % self.wif)
        print(" Account ID                     %s" % self.account_id)
        print(" Parent ID                      %s" % self.parent_id)
        print(" Depth                          %s" % self.depth)
        print(" Change                         %s" % self.change)
        print(" Address Index                  %s" % self.address_index)
        print(" Address                        %s" % self.address)
        print(" Path                           %s" % self.path)
        print(" Balance                        %s" % self.balance(fmt='string'))
        print("\n")


class HDWallet:
    """
    Class to create and manage keys Using the BIP0044 Hierarchical Deterministic wallet definitions, so you can 
    use one Masterkey to generate as much child keys as you want in a structured manner.
    
    You can import keys in many format such as WIF or extended WIF, bytes, hexstring, seeds or private key integer.
    For the Bitcoin network, Litecoin or any other network you define in the settings.
    
    Easily send and receive transactions. Compose transactions automatically or select unspent outputs.
    
    Each wallet name must be unique and can contain only one cointype and purpose, but practically unlimited
    accounts and addresses. 
    """

    @classmethod
    def create(cls, name, key='', owner='', network=None, account_id=0, purpose=44, databasefile=None):
        """
        Create HDWallet and insert in database. Generate masterkey or import key when specified. 
        
        Please mention account_id if you are using multiple accounts.
        
        :param name: Unique name of this Wallet
        :type name: str
        :param key: Masterkey to use for this wallet. Will be automatically created if not specified
        :type key: str, bytes, int, bytearray
        :param owner: Wallet owner for your own reference
        :type owner: str
        :param network: Network name, use default if not specified
        :type network: str
        :param account_id: Account ID, default is 0
        :type account_id: int
        :param purpose: BIP0044 purpose field, default is 44
        :type purpose: int
        :param databasefile: Location of database file. Leave empty to use default
        :type databasefile: str
        
        :return HDWallet: 
        """

        if databasefile is None:
            databasefile = DEFAULT_DATABASE
        session = DbInit(databasefile=databasefile).session
        if session.query(DbWallet).filter_by(name=name).count():
            raise WalletError("Wallet with name '%s' already exists" % name)
        else:
            _logger.info("Create new wallet '%s'" % name)
        if key:
            network = check_network_and_key(key, network)
            searchkey = session.query(DbKey).filter_by(wif=key).scalar()
            if searchkey:
                raise WalletError("Key already found in wallet %s" % searchkey.wallet.name)
        elif network is None:
            network = DEFAULT_NETWORK
        new_wallet = DbWallet(name=name, owner=owner, network_name=network, purpose=purpose)
        session.add(new_wallet)
        session.commit()
        new_wallet_id = new_wallet.id

        mk = HDWalletKey.from_key(key=key, name=name, session=session, wallet_id=new_wallet_id, network=network,
                                  account_id=account_id, purpose=purpose, key_type='bip44')
        if mk.depth > 4:
            raise WalletError("Cannot create new wallet with main key of depth 5 or more")
        new_wallet.main_key_id = mk.key_id
        session.commit()
        session.close()

        w = cls(new_wallet_id, databasefile=databasefile, main_key_object=mk.key())
        if mk.depth == 0:
            nw = Network(network)
            networkcode = nw.bip44_cointype
            path = ["%d'" % purpose, "%s'" % networkcode]
            w._create_keys_from_path(mk, path, name=name, wallet_id=new_wallet_id, network=network, session=session,
                                     account_id=account_id, purpose=purpose, basepath="m")
            w.new_account(account_id=account_id)
        return w

    def _create_keys_from_path(self, parent, path, wallet_id, account_id, network, session,
                               name='', basepath='', change=0, purpose=44, tree_index=0):
        """
        Create all keys for a given path.
        
        :param parent: Main parent key. Can be a BIP0044 master key, level 3 account key, or any other.
        :type parent: HDWalletKey
        :param path: Path of keys to generate, relative to given parent key
        :type path: list
        :param wallet_id: Wallet ID
        :type wallet_id: int
        :param account_id: Account ID
        :type account_id: int
        :param network: Network
        :type network: str
        :param session: Sqlalchemy session
        :type session: sqlalchemy.orm.session.Session
        :param name: Name for generated keys. Leave empty for default
        :type name: str
        :param basepath: Basepath of main parent key
        :type basepath: str
        :param change: Change = 1, or payment = 0. Default is 0.
        :type change: int
        :param purpose: BIP0044 purpose, default is 44.
        :type purpose: int
        
        :return HDWalletKey: 
        """

        # Initial checks and settings
        if not isinstance(parent, HDWalletKey):
            raise WalletError("Parent must be of type 'HDWalletKey'")
        if not isinstance(path, list):
            raise WalletError("Path must be of type 'list'")
        if len(basepath) and basepath[-1] != "/":
            basepath += "/"
        parent_id = 0
        nk = parent
        ck = nk.key()

        # Check for closest ancestor in wallet
        spath = basepath + '/'.join(path)
        rkey = None
        while spath and not rkey:
            rkey = self._session.query(DbKey).filter_by(wallet_id=wallet_id, path=spath, tree_index=tree_index).first()
            spath = '/'.join(spath.split("/")[:-1])
        if rkey is not None and rkey.path not in [basepath, basepath[:-1]]:
            path = (basepath + '/'.join(path)).replace(rkey.path + '/', '').split('/')
            basepath = rkey.path + '/'
            nk = self.key(rkey.id)
            ck = nk.key()

        # Create new keys from path
        for l in range(len(path)):
            pp = "/".join(path[:l+1])
            fullpath = basepath + pp
            ck = ck.subkey_for_path(path[l], network=network)
            nk = HDWalletKey.from_key(hdkey_object=ck, name=name, wallet_id=wallet_id, network=network,
                                      account_id=account_id, change=change, purpose=purpose, path=fullpath,
                                      parent_id=parent_id, session=session, tree_index=tree_index)
            self._key_objects.update({nk.key_id: nk})
            parent_id = nk.key_id
        _logger.info("New key(s) created for parent_id %d" % parent_id)
        return nk

    def __enter__(self):
        return self

    def __init__(self, wallet, databasefile=DEFAULT_DATABASE, main_key_object=None):
        """
        Open a wallet with given ID or name
        
        :param wallet: Wallet name or ID
        :type wallet: int, str
        :param databasefile: Location of database file. Leave empty to use default
        :type databasefile: str
        :param main_key_object: Pass main key object to save time
        :type main_key_object: HDWalletKey
        """

        self._session = DbInit(databasefile=databasefile).session
        if isinstance(wallet, int) or wallet.isdigit():
            w = self._session.query(DbWallet).filter_by(id=wallet).scalar()
        else:
            w = self._session.query(DbWallet).filter_by(name=wallet).scalar()
        if w:
            self._dbwallet = w
            self.wallet_id = w.id
            self._name = w.name
            self._owner = w.owner
            self.network = Network(w.network_name)
            self.purpose = w.purpose
            self._balance = w.balance
            self.main_key_id = w.main_key_id
            if main_key_object:
                self.main_key = HDWalletKey(self.main_key_id, session=self._session, hdkey_object=main_key_object)
            else:
                self.main_key = HDWalletKey(self.main_key_id, session=self._session)
            self.default_account_id = self.main_key.account_id
            _logger.info("Opening wallet '%s'" % self.name)
            self._key_objects = {
                self.main_key_id: self.main_key
            }
        else:
            raise WalletError("Wallet '%s' not found, please specify correct wallet ID or name." % wallet)

    def __exit__(self, exception_type, exception_value, traceback):
        self._session.close()

    def __repr__(self):
        return "<HDWallet (id=%d, name=%s, default_network=%s)>" % \
               (self.wallet_id, self.name, self.network.network_name)

    def _get_account_defaults(self, network=None, account_id=None):
        """
        Check parameter values for network and account ID, return defaults if no network or account ID is specified.
        If a network is specified but no account ID this method returns the first account ID it finds. 
        
        :param network: Network code, leave empty for default
        :type network: str
        :param account_id: Account ID, leave emtpy for default
        :type account_id: int
        
        :return: network code, account ID and DbKey instance of account ID key
        """

        if network is None:
            network = self.network.network_name
            if account_id is None:
                account_id = self.default_account_id
        qr = self._session.query(DbKey).\
            filter_by(wallet_id=self.wallet_id, purpose=self.purpose, depth=3, network_name=network)
        if account_id is not None:
            qr = qr.filter_by(account_id=account_id)
        acckey = qr.first()
        if len(qr.all()) > 1:
            _logger.warning("No account_id specified and more than one account found for this network %s. "
                            "Using a random account" % network)
        if not account_id and acckey:
            account_id = acckey.account_id
        return network, account_id, acckey

    def balance(self, as_string=False):
        """
        Get total of unspent outputs

        :param as_string: Set True to return a string in currency format. Default returns float.
        :type as_string: boolean
        
        :return float, str: Key balance 
        """
        if as_string:
            return self.network.print_value(self._balance)
        else:
            return self._balance

    @property
    def owner(self):
        """
        Get wallet Owner
        
        :return str: 
        """

        return self._owner

    @owner.setter
    def owner(self, value):
        """
        Set wallet Owner in database
        
        :param value: Owner
        :type value: str
        
        :return str: 
        """

        self._owner = value
        self._dbwallet.owner = value
        self._session.commit()

    @property
    def name(self):
        """
        Get wallet name
        
        :return str: 
        """

        return self._name

    @name.setter
    def name(self, value):
        """
        Set wallet name, update in database
        
        :param value: Name for this wallet
        :type value: str
        
        :return str: 
        """

        if wallet_exists(value):
            raise WalletError("Wallet with name '%s' already exists" % value)
        self._name = value
        self._dbwallet.name = value
        self._session.commit()

    def _get_latest_tree_index(self, network):
        return self._session.query(DbKey).filter_by(wallet_id=self.wallet_id, purpose=self.purpose,
                                                    network_name=network). \
            order_by(DbKey.tree_index.desc()).first().tree_index

    def import_key(self, key, account_id=0, name='', network=None, key_type='single'):
        """
        Add new non HD key to wallet. This key will have no path but are referred by a import_key sequence
        
        :param key: Key to import
        :type key: str, bytes, int, bytearray
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param name: Specify name for key, leave empty for default
        :type name: str
        :param network: Network name, method will try to extract from key if not specified. Raises warning if network could not be detected
        :type network: str
        :param key_type: Key type of imported key, can be single (unrelated to wallet, bip32, bip44 or master for new or extra master key import.
        :type key_type: str
        
        :return HDWalletKey: 
        """

        if network is None:
            network = check_network_and_key(key, default_network=self.network.network_name)
            if network not in self.network_list():
                raise WalletError("Network %s not available in this wallet, please create an account for this "
                                  "network first." % network)

        # TODO: If key has related key-path add to wallet (i.e. for restoring backup
        last_tree_index = self._get_latest_tree_index(network)
        tree_index = last_tree_index + 1
        ik_path = 'm'
        if key_type == 'single':
            # Create path for unrelated import keys
            last_import_key = self._session.query(DbKey).filter(DbKey.path.like("import_key_%")).\
                order_by(DbKey.path.desc()).first()
            if last_import_key:
                ik_path = "import_key_" + str(int(last_import_key.path[-5:]) + 1).zfill(5)
            else:
                ik_path = "import_key_00001"
            if not name:
                name = ik_path

        return HDWalletKey.from_key(
            key=key, name=name, wallet_id=self.wallet_id, network=network, key_type=key_type,
            account_id=account_id, purpose=self.purpose, session=self._session, path=ik_path, tree_index=tree_index)

    def create_multisig(self, key_list, n_required=None, name=''):
        if not isinstance(key_list, list):
            raise WalletError("Need list of keys to create multi-signature key structure")
        if len(key_list) < 2:
            raise WalletError("Key list must contain at least 2 keys")
        if n_required is None:
            n_required = len(key_list)
        if n_required > len(key_list):
            raise WalletError("Number of key required to sign is greater then number of keys provided")

        depth = 0
        last_tree_index = self._get_latest_tree_index(self.network.network_name)
        multisig_key = DbKey(name=name, wallet_id=self.wallet_id, purpose=self.purpose, account_id=0, depth=0,
                             change=0, address_index=0, parent_id=0, is_private=True, path='m',
                             key='multisig', wif='multisig', address='multisig', tree_index=last_tree_index,
                             key_type='multisig', network_name=self.network.network_name)
        self._session.add(multisig_key)
        self._session.commit()
        multisig_key_id = multisig_key.id
        tree_ids = []
        for k in key_list:
            # TODO: Check if key has same network, not already in wallet, used for other multisig etc
            if isinstance(k, (str, bytes, bytearray)):
                wkey = self.import_key(k, key_type='bip44')
                self.new_account(tree_index=wkey.tree_index)
            elif isinstance(k, HDWalletKey):
                wkey = k
            elif isinstance(k, HDKey):
                wkey = self.import_key(k.wif, key_type='bip44')
                self.new_account(tree_index=wkey.tree_index)
            elif isinstance(k, int):
                wkey = self.key(k)
            else:
                raise WalletError("Please use already existing HDWalletKey object / ID, HDKey object or "
                                  "private key in key list")
            # TODO: Add support for account keys (depth=3)
            if wkey.depth != 0:
                raise WalletError("Only use Masterkey with depth 0 as base for multisig key")
            tree_ids.append(wkey.tree_index)
        self._session.query(DbKey).filter(DbKey.tree_index.in_(tree_ids)).\
            update({DbKey.multisig_key_id: multisig_key_id}, synchronize_session='fetch')
        self._session.commit()

    def new_multisig_key(self, treeindex=None):
        multisig = serialize_multisig(publickeylist, n_required)
        pubkeyhash_to_addr(multisig)

    def new_key(self, name='', account_id=None, network=None, tree_index=0, change=0, max_depth=5):
        """
        Create a new HD Key derived from this wallet's masterkey. An account will be created for this wallet
        with index 0 if there is no account defined yet.
        
        :param name: Key name. Does not have to be unique but if you use it at reference you might chooce to enforce this. If not specified 'Key #' with an unique sequence number will be used
        :type name: str
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param change: Change (1) or payments (0). Default is 0
        :type change: int
        :param max_depth: Maximum path depth. Default for BIP0044 is 5, any other value is non-standard and might cause unexpected behavior
        :type max_depth: int
        
        :return HDWalletKey: 
        """

        network, account_id, acckey = self._get_account_defaults(network, account_id)

        # Get account key, create one if it doesn't exist
        if not acckey:
            acckey = self._session.query(DbKey). \
                filter_by(wallet_id=self.wallet_id, purpose=self.purpose, account_id=account_id,
                          depth=3, network_name=network, tree_index=tree_index).scalar()
        if not acckey:
            hk = self.new_account(account_id=account_id, network=network)
            if hk:
                acckey = hk._dbkey
        if not acckey:
            raise WalletError("No key found this wallet_id, network and purpose. "
                              "Is there a BIP32 Master key imported?")
        else:
            main_acc_key = self.key(acckey.id)

        # Determine new key ID
        prevkey = self._session.query(DbKey). \
            filter_by(wallet_id=self.wallet_id, purpose=self.purpose, network_name=network,
                      account_id=account_id, change=change, depth=max_depth, tree_index=tree_index). \
            order_by(DbKey.address_index.desc()).first()
        address_index = 0
        if prevkey:
            address_index = prevkey.address_index + 1

        # Compose key path and create new key
        newpath = [(str(change)), str(address_index)]
        bpath = main_acc_key.path + '/'
        # pathdepth = max_depth - self.main_key.depth
        if not name:
            if change:
                name = "Change %d" % address_index
            else:
                name = "Key %d" % address_index
        newkey = self._create_keys_from_path(
            main_acc_key, newpath, name=name, wallet_id=self.wallet_id,  account_id=account_id,
            change=change, network=network, purpose=self.purpose, basepath=bpath,
            session=self._session, tree_index=tree_index
        )
        return newkey

    def new_key_change(self, name='', account_id=0, network=None):
        """
        Create new key to receive change for a transaction. Calls new_key method with change=1.
        
        :param name: Key name. Default name is 'Change #' with an address index
        :type name: str
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
                
        :return HDWalletKey: 
        """

        return self.new_key(name=name, account_id=account_id, network=network, change=1)

    def get_key(self, account_id=None, network=None, change=0, depth_of_keys=5):
        """
        Get a unused key or create a new one if there are no unused keys. 
        Returns a key from this wallet which has no transactions linked to it.
        
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param change: Payment (0) or change key (1). Default is 0
        :type change: int
        :param depth_of_keys: Depth of account keys. Default is 5 according to BIP0032 standards
        :type depth_of_keys: int
        
        :return HDWalletKey: 
        """

        network, account_id, _ = self._get_account_defaults(network, account_id)
        dbkey = self._session.query(DbKey).\
            filter_by(wallet_id=self.wallet_id, account_id=account_id, network_name=network,
                      used=False, change=change, depth=depth_of_keys).\
            order_by(DbKey.id).first()
        if dbkey:
            return HDWalletKey(dbkey.id, session=self._session)
        else:
            return self.new_key(account_id=account_id, network=network, change=change)

    def get_key_change(self, account_id=None, network=None, depth_of_keys=5):
        """
        Get a unused change key or create a new one if there are no unused keys. 
        Wrapper for the get_key method
        
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param depth_of_keys: Depth of account keys. Default is 5 according to BIP0032 standards
        :type depth_of_keys: int
        
        :return HDWalletKey:  
        """

        return self.get_key(account_id=account_id, network=network, depth_of_keys=depth_of_keys)

    def new_account(self, name='', account_id=None, network=None, tree_index=0):
        """
        Create a new account with a childkey for payments and 1 for change.
        
        An account key can only be created if wallet contains a masterkey.
        
        :param name: Account Name. If not specified 'Account #" with the account_id will be used
        :type name: str
        :param account_id: Account ID. Default is last accounts ID + 1
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        
        :return HDWalletKey: 
        """

        if network is None:
            network = self.network.network_name

        # Determine account_id and name
        if account_id is None:
            account_id = 0
            qr = self._session.query(DbKey). \
                filter_by(wallet_id=self.wallet_id, purpose=self.purpose, network_name=network,
                          tree_index=tree_index). \
                order_by(DbKey.account_id.desc()).first()
            if qr:
                account_id = qr.account_id + 1
        if not name:
            name = 'Account #%d' % account_id
        if self.keys(account_id=account_id, depth=3, network=network, tree_index=tree_index):
            raise WalletError("Account with ID %d already exists for this wallet")

        # Get root key of new account
        res = self.keys(depth=2, network=network, tree_index=tree_index)
        if not res:
            try:
                # TODO: make this better...
                purposekey = self.key(self.keys(depth=1)[0].id)
                bip44_cointype = Network(network).bip44_cointype
                accrootkey_obj = self._create_keys_from_path(
                    purposekey, [str(bip44_cointype)], name=network, wallet_id=self.wallet_id, account_id=account_id,
                    network=network, purpose=self.purpose, tree_index=tree_index, basepath=purposekey.path,
                    session=self._session)
            except IndexError:
                raise WalletError("No key found for this wallet_id and purpose. Can not create new"
                                  "account for this wallet, is there a BIP32 Master key imported?")
        else:
            accrootkey = res[0]
            accrootkey_obj = self.key(accrootkey.id)

        # Create new account addresses and return main account key
        newpath = [str(account_id) + "'"]
        acckey = self._create_keys_from_path(
            accrootkey_obj, newpath, name=name, wallet_id=self.wallet_id,  account_id=account_id,
            network=network, purpose=self.purpose, basepath=accrootkey_obj.path, tree_index=tree_index,
            session=self._session
        )
        self._create_keys_from_path(
            acckey, ['0'], name=acckey.name + ' Payments', wallet_id=self.wallet_id, account_id=account_id,
            network=network, purpose=self.purpose, basepath=acckey.path, tree_index=tree_index,
            session=self._session)
        self._create_keys_from_path(
            acckey, ['1'], name=acckey.name + ' Change', wallet_id=self.wallet_id, account_id=account_id,
            network=network, purpose=self.purpose, basepath=acckey.path, tree_index=tree_index,
            session=self._session)
        return acckey

    def key_for_path(self, path, name='', account_id=0, change=0, enable_checks=True):
        """
        Create key with specified path. Can be used to create non-default (non-BIP0044) paths.
        
        Can cause problems if already used account ID's or address indexes are provided.
        
        :param path: Path string in m/#/#/# format. With quote (') or (p/P/h/H) character for hardened child key derivation
        :type path: str
        :param name: Key name to use
        :type name: str
        :param account_id: Account ID
        :type account_id: int
        :param change: Change 0 or 1
        :type change: int
        :param enable_checks: Use checks for valid BIP0044 path, default is True
        :type enable_checks: bool
        
        :return HDWalletKey: 
        """

        # Validate key path
        if path not in ['m', 'M'] and enable_checks:
            pathdict = parse_bip44_path(path)
            purpose = 0 if not pathdict['purpose'] else int(pathdict['purpose'].replace("'", ""))
            if purpose != self.purpose:
                raise WalletError("Cannot create key with different purpose field (%d) as existing wallet (%d)" % (
                purpose, self.purpose))
            cointype = 0 if not pathdict['cointype'] else int(pathdict['cointype'].replace("'", ""))
            if cointype != self.network.bip44_cointype:
                raise WalletError("Multiple cointypes per wallet are not supported at the moment. "
                                  "Cannot create key with different cointype field (%d) as existing wallet (%d)" % (
                                  cointype, self.network.bip44_cointype))
            if (pathdict['cointype'][-1] != "'" or pathdict['purpose'][-1] != "'"
                              or pathdict['account'][-1] != "'"):
                raise WalletError("Cointype, purpose and account must be hardened, see BIP43 and BIP44 definitions")
        if not name:
            name = self.name

        # Check for closest ancestor in wallet
        spath = normalize_path(path)
        rkey = None
        while spath and not rkey:
            rkey = self._session.query(DbKey).filter_by(path=spath, wallet_id=self.wallet_id).first()
            spath = '/'.join(spath.split("/")[:-1])

        # Key already found in db, return key
        if rkey.path == path:
            return self.key(rkey.id)

        parent_key = self.main_key
        subpath = path
        basepath = ''
        if rkey is not None:
            subpath = normalize_path(path).replace(rkey.path + '/', '')
            basepath = rkey.path
            if self.main_key.wif != rkey.wif:
                parent_key = self.key(rkey.id)
        newkey = self._create_keys_from_path(
            parent_key, subpath.split("/"), name=name, wallet_id=self.wallet_id,
            account_id=account_id, change=change,
            network=self.network.network_name, purpose=self.purpose, basepath=basepath, session=self._session)
        return newkey

    def keys(self, account_id=None, name=None, key_id=None, change=None, depth=None, network=None, tree_index=0,
             as_dict=False):
        """
        Search for keys in database. Include 0 or more of account_id, name, key_id, change and depth.
        
        Returns a list of DbKey object or dictionary object if as_dict is True
        
        :param account_id: Search for account ID 
        :type account_id: int
        :param name: Search for Name
        :type name: str
        :param key_id: Search for Key ID
        :type key_id: int
        :param change: Search for Change
        :type change: int
        :param depth: Only include keys with this depth
        :type depth: int
        :param network: Network name filter
        :type network: str
        :param as_dict: Return keys as dictionary objects. Default is False: DbKey objects
        
        :return list: List of Keys
        """

        qr = self._session.query(DbKey).filter_by(wallet_id=self.wallet_id, purpose=self.purpose, tree_index=tree_index)
        if network is not None:
            qr = qr.filter(DbKey.network_name == network)
        if account_id is not None:
            qr = qr.filter(DbKey.account_id == account_id)
            qr = qr.filter(DbKey.depth >= 3)
        if change is not None:
            qr = qr.filter(DbKey.change == change)
            qr = qr.filter(DbKey.depth > 4)
        if depth is not None:
            qr = qr.filter(DbKey.depth == depth)
        if name is not None:
            qr = qr.filter(DbKey.name == name)
        if key_id is not None:
            qr = qr.filter(DbKey.id == key_id)
        ret = as_dict and [x.__dict__ for x in qr.all()] or qr.all()
        qr.session.close()
        return ret

    def keys_networks(self, as_dict=False):
        """
        Get keys of defined networks for this wallet. Wrapper for the keys() method
        
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        
        """

        res = self.keys(depth=2, as_dict=as_dict)
        if not res:
            res = self.keys(depth=3, as_dict=as_dict)
        return res

    def keys_accounts(self, account_id=None, network=None, as_dict=False):
        """
        Get Database records of account key(s) with for current wallet. Wrapper for the keys() method.
        
        :param account_id: Search for Account ID
        :type account_id: int
        :param network: Network name filter
        :type network: str
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        """

        return self.keys(account_id, depth=3, network=network, as_dict=as_dict)

    def keys_addresses(self, account_id=None, network=None, as_dict=False):
        """
        Get address-keys of specified account_id for current wallet. Wrapper for the keys() methods.

        :param account_id: Account ID
        :type account_id: int
        :param network: Network name filter
        :type network: str
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        """

        return self.keys(account_id, depth=5, network=network, as_dict=as_dict)

    def keys_address_payment(self, account_id=None, network=None, as_dict=False):
        """
        Get payment addresses (change=0) of specified account_id for current wallet. Wrapper for the keys() methods.

        :param account_id: Account ID
        :type account_id: int
        :param network: Network name filter
        :type network: str
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        """

        return self.keys(account_id, depth=5, change=0, network=network, as_dict=as_dict)

    def keys_address_change(self, account_id=None, network=None, as_dict=False):
        """
        Get payment addresses (change=1) of specified account_id for current wallet. Wrapper for the keys() methods.

        :param account_id: Account ID
        :type account_id: int
        :param network: Network name filter
        :type network: str
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        """

        return self.keys(account_id, depth=5, change=1, network=network, as_dict=as_dict)

    def tree_ids(self):
        res = self._session.query(DbKey.tree_index).filter_by(wallet_id=self.wallet_id, parent_id=0).all()
        return list(set([x[0] for x in res]))

    def addresslist(self, account_id=None, network=None, depth=5, key_id=None, tree_index=0):
        """
        Get list of addresses defined in current wallet

        :param account_id: Account ID
        :type account_id: int
        :param network: Network name filter
        :type network: str
        :param depth: Filter by key depth
        :type depth: int
        :param key_id: Key ID to get address of just 1 key
        :type key_id: int
        
        :return list: List of address strings
        """

        addresslist = []
        for key in self.keys(account_id=account_id, depth=depth, network=network, key_id=key_id, tree_index=tree_index):
            addresslist.append(key.address)
        return addresslist

    def key(self, term):
        """
        Return single key with give ID or name as HDWalletKey object

        :param term: Search term can be key ID, key address, key WIF or key name
        :type term: int, str
        
        :return HDWalletKey: Single key as object
        """

        dbkey = None
        qr = self._session.query(DbKey).filter_by(wallet_id=self.wallet_id, purpose=self.purpose)
        if isinstance(term, numbers.Number):
            dbkey = qr.filter_by(id=term).scalar()
        if not dbkey:
            dbkey = qr.filter_by(address=term).first()
        if not dbkey:
            dbkey = qr.filter_by(wif=term).first()
        if not dbkey:
            dbkey = qr.filter_by(name=term).first()
        if dbkey:
            if dbkey.id in self._key_objects.keys():
                return self._key_objects[dbkey.id]
            else:
                return HDWalletKey(key_id=dbkey.id, session=self._session)
        else:
            raise KeyError("Key '%s' not found" % term)

    def accounts(self, network=None):
        """
        Get list of accounts for this wallet
        
        :param network: Network name filter
        :type network: str
                
        :return: List of keys as dictionary
        """

        wks = self.keys_accounts(network=network, as_dict=True)
        for wk in wks:
            if '_sa_instance_state' in wk:
                del wk['_sa_instance_state']
        return wks

    def networks(self):
        """
        Get list of networks used by this wallet
        
        :return: List of keys as dictionary
        """

        wks = self.keys_networks(as_dict=True)
        for wk in wks:
            if '_sa_instance_state' in wk:
                del wk['_sa_instance_state']
        return wks

    def network_list(self):
        """
        Wrapper for networks methods, returns a flat list with currently used
        networks for this wallet.
        
        :return: list 
        """

        return [x['network_name'] for x in self.networks()]

    def updatebalance_from_serviceprovider(self, account_id=None, network=None):
        """
        Update balance of currents account addresses using default Service objects getbalance method. Update total 
        wallet balance in database. 
        
        Please Note: Does not update UTXO's or the balance per key! For this use the 'updatebalance' method
        instead
        
        :param account_id: Account ID
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        
        :return: 
        """

        network, account_id, acckey = self._get_account_defaults(network, account_id)
        self._balance = Service(network=network).getbalance(self.addresslist(account_id=account_id, network=network))
        self._dbwallet.balance = self._balance
        self._session.commit()

    def updatebalance(self, account_id=None, network=None, key_id=None):
        """
        Update balance from UTXO's in database. To get most recent balance use 'updateutxos' method first.
        
        Also updates balance of wallet and keys in this wallet for the specified account or all accounts if
        no account is specified.
        
        :param account_id: Account ID filter
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param key_id: Key ID Filter
        :type key_id: int
        
        :return: 
        """

        network, account_id, acckey = self._get_account_defaults(network, account_id)

        # Get UTXO's and convert to dict with key_id and balance
        utxos = self.getutxos(account_id=account_id, network=network, key_id=key_id)
        utxos.sort(key=lambda x: x['key_id'])
        utxo_keys = []
        total_balance = 0
        for key, group in groupby(utxos, lambda x: x['key_id']):
            balance = sum(r['value'] for r in group)
            utxo_keys.append({
                    'id': key,
                    'balance': balance
            })
            total_balance += balance

        # Add keys with no UTXO's with 0 balance
        for key in self.keys(account_id=account_id, network=network, key_id=key_id):
            if key.id not in [x['key_id'] for x in utxos]:
                utxo_keys.append({
                    'id': key.id,
                    'balance': 0
                })

        # Bulk update database
        self._session.bulk_update_mappings(DbKey, utxo_keys)
        self._dbwallet.balance = total_balance
        self._balance = total_balance
        self._session.commit()
        _logger.info("Got balance for %d key. Total balance is %s" % (len(utxo_keys), total_balance))

    def updateutxos(self, account_id=None, network=None, key_id=None, depth=5):
        """
        Update UTXO's (Unspent Outputs) in database of given account using the default Service object.
        
        Delete old UTXO's which are spend and append new UTXO's to database.
        
        :param account_id: Account ID
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param key_id: Key ID to just update 1 key
        :type key_id: int
        :param depth: Only update keys with this depth, default is depth 5 according to BIP0048 standard. Set depth to None to update all keys of this wallet.
        :type depth: int
        
        :return int: Number of new UTXO's added 
        """

        network, account_id, acckey = self._get_account_defaults(network, account_id)

        # Get all UTXO's for this wallet from default Service object
        utxos = Service(network=network).\
            getutxos(self.addresslist(account_id=account_id, network=network, key_id=key_id, depth=depth))
        if utxos is False:
            raise WalletError("No response from any service provider, could not update UTXO's")
        count_utxos = 0

        # Get current UTXO's from database to compare with Service objects UTXO's
        current_utxos = self.getutxos(account_id=account_id, network=network, key_id=key_id)

        # Update spend UTXO's (not found in list) and mark key as used
        utxos_tx_hashes = [(x['tx_hash'], x['output_n']) for x in utxos]
        for current_utxo in current_utxos:
            if (current_utxo['tx_hash'], current_utxo['output_n']) not in utxos_tx_hashes:
                utxo_in_db = self._session.query(DbTransactionOutput).join(DbTransaction). \
                    filter(DbTransaction.hash == current_utxo['tx_hash']).filter(
                    DbTransactionOutput.output_n == current_utxo['output_n'])
                if utxo_in_db.count():
                    utxo_record = utxo_in_db.scalar()
                    utxo_record.spend = True
                # self._session.query(DbTransaction).filter(DbTransaction.hash == current_utxo['tx_hash']).\
                #     update({DbTransaction.spend: True})
                # self._session.query(DbKey).filter(DbKey.id == current_utxo['key_id']).update({DbKey.used: True})
            self._session.commit()

        # If UTXO is new, add to database otherwise update depth (confirmation count)
        for utxo in utxos:
            key = self._session.query(DbKey).filter_by(address=utxo['address']).scalar()
            if key and not key.used:
                key.used = True

            # Update confirmations in db if utxo was already imported
            # TODO: Add network filter (?)
            transaction_in_db = self._session.query(DbTransaction).filter_by(hash=utxo['tx_hash'])
            utxo_in_db = self._session.query(DbTransactionOutput).join(DbTransaction).\
                filter(DbTransaction.hash == utxo['tx_hash']).filter(DbTransactionOutput.output_n == utxo['output_n'])
            if utxo_in_db.count():
                utxo_record = utxo_in_db.scalar()
                utxo_record.key_id = key.id
                utxo_record.spend = False
                transaction_record = transaction_in_db.scalar()
                transaction_record.confirmations = utxo['confirmations']
            else:
                # Add transaction if not exist and then add output
                if not transaction_in_db.count():
                    new_tx = DbTransaction(hash=utxo['tx_hash'], confirmations=utxo['confirmations'])
                    self._session.add(new_tx)
                    self._session.commit()
                    tid = new_tx.id
                else:
                    tid = transaction_in_db.scalar().id

                new_utxo = DbTransactionOutput(transaction_id=tid,
                                               output_n=utxo['output_n'], value=utxo['value'],
                                               key_id=key.id,
                                               script=utxo['script'], spend=False)
                self._session.add(new_utxo)
                count_utxos += 1
            # TODO: Removing this gives errors??
            self._session.commit()

        _logger.info("Got %d new UTXOs for account %s" % (count_utxos, account_id))
        self._session.commit()
        self.updatebalance(account_id=account_id, key_id=key_id)
        return count_utxos

    def getutxos(self, account_id=None, network=None, min_confirms=0, key_id=None):
        """
        Get UTXO's (Unspent Outputs) from database. Use updateutxos method first for updated values
        
        :param account_id: Account ID
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param min_confirms: Minimal confirmation needed to include in output list
        :type min_confirms: int
        :param key_id: Key ID to just get 1 key
        :type key_id: int  
        :return list: List of transactions 
        """

        network, account_id, acckey = self._get_account_defaults(network, account_id)

        qr = self._session.query(DbTransactionOutput, DbKey.address, DbTransaction.confirmations, DbTransaction.hash).\
            join(DbTransaction).join(DbKey). \
            filter(DbTransactionOutput.spend.op("IS")(False),
                   DbKey.account_id == account_id,
                   DbKey.wallet_id == self.wallet_id,
                   DbKey.network_name == network,
                   DbTransaction.confirmations >= min_confirms)
        if key_id is not None:
            qr = qr.filter(DbKey.id == key_id)
        # print("qr:", qr, min_confirms, account_id, key_id, self._session)
        utxos = qr.order_by(DbTransaction.confirmations.desc()).all()
        res = []
        for utxo in utxos:
            u = utxo[0].__dict__
            if '_sa_instance_state' in u:
                del u['_sa_instance_state']
            u['address'] = utxo[1]
            u['confirmations'] = int(utxo[2])
            u['tx_hash'] = utxo[3]
            res.append(u)
        return res

    def send_to(self, to_address, amount, account_id=None, network=None, transaction_fee=None, min_confirms=4):
        """
        Create transaction and send it with default Service objects sendrawtransaction method
        
        :param to_address: Single output address
        :type to_address: str
        :param amount: Output is smallest denominator for this network (ie: Satoshi's for Bitcoin)
        :type amount: int
        :param account_id: Account ID, default is last used
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param transaction_fee: Fee to use for this transaction. Leave empty to automatically estimate.
        :type transaction_fee: int
        :param min_confirms: Minimal confirmation needed for an UTXO before it will included in inputs. Default is 4. Option is ignored if input_arr is provided.
        :type min_confirms: int
        
        :return str, list: Transaction ID or result array 
        """

        outputs = [(to_address, amount)]
        return self.send(outputs, account_id=account_id, network=network, transaction_fee=transaction_fee, min_confirms=min_confirms)

    @staticmethod
    def _select_inputs(amount, utxo_query=None):
        """
        Internal method used by create transaction to select best inputs (UTXO's) for a transaction. To get the
        least number of inputs
        
        Example of UTXO query:
            SELECT transactions.id AS transactions_id, transactions.key_id AS transactions_key_id, 
            transactions.tx_hash AS transactions_tx_hash, transactions.date AS transactions_date, 
            transactions.confirmations AS transactions_confirmations, transactions.output_n AS transactions_output_n, 
            transactions."index" AS transactions_index, transactions.value AS transactions_value, 
            transactions.script AS transactions_script, transactions.description AS transactions_description, 
            transactions.spend AS transactions_spend 
            FROM transactions JOIN keys ON keys.id = transactions.key_id 
            WHERE (transactions.spend IS ?) AND transactions.confirmations >= ? AND 
            keys.account_id = ? AND keys.wallet_id = ?
        
        :param amount: Amount to transfer
        :type amount: int
        :param utxo_query: List of outputs in SQLalchemy query format. Wallet and Account ID filter must be included already. 
        :type utxo_query: self._session.query
        
        :return list: List of selected UTXO 
        """

        if not utxo_query:
            return []

        # Try to find one utxo with exact amount or higher
        one_utxo = utxo_query.\
            filter(DbTransactionOutput.spend.op("IS")(False), DbTransactionOutput.value >= amount).\
            order_by(DbTransactionOutput.value).first()
        if one_utxo:
            return [one_utxo]

        # Otherwise compose of 2 or more lesser outputs
        lessers = utxo_query.\
            filter(DbTransactionOutput.spend.op("IS")(False), DbTransactionOutput.value < amount).\
            order_by(DbTransactionOutput.value.desc()).all()
        total_amount = 0
        selected_utxos = []
        for utxo in lessers:
            if total_amount < amount:
                selected_utxos.append(utxo)
                total_amount += utxo.value
        if total_amount < amount:
            return []
        return selected_utxos

    def send(self, output_arr, input_arr=None, account_id=None, network=None, transaction_fee=None, min_confirms=4):
        """
        Create new transaction with specified outputs and push it to the network. 
        Inputs can be specified but if not provided they will be selected from wallets utxo's.
        Output array is a list of 1 or more addresses and amounts.
        
        :param output_arr: List of output tuples with address and amount. Must contain at least one item. Example: [('mxdLD8SAGS9fe2EeCXALDHcdTTbppMHp8N', 5000000)] 
        :type output_arr: list 
        :param input_arr: List of inputs tuples with reference to a UTXO, a wallet key and value. The format is [(tx_hash, output_n, key_id, value)]
        :type input_arr: list
        :param account_id: Account ID
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param transaction_fee: Set fee manually, leave empty to calculate fees automatically. Set fees in smallest currency denominator, for example satoshi's if you are using bitcoins
        :type transaction_fee: int
        :param min_confirms: Minimal confirmation needed for an UTXO before it will included in inputs. Default is 4. Option is ignored if input_arr is provided.
        :type min_confirms: int
        
        :return str, list: Transaction ID or result array
        """

        # TODO: Add transaction_id as possible input in input_arr
        amount_total_output = 0
        network, account_id, acckey = self._get_account_defaults(network, account_id)

        # Create transaction and add outputs
        t = Transaction(network=network)
        if not isinstance(output_arr, list):
            raise WalletError("Output array must be a list of tuples with address and amount. "
                              "Use 'send_to' method to send to one address")
        for o in output_arr:
            amount_total_output += o[1]
            t.add_output(o[1], o[0])

        # Calculate fees
        srv = Service(network=network)
        fee = transaction_fee
        fee_per_kb = None
        fee_per_output = None
        if transaction_fee is None:
            fee_per_kb = srv.estimatefee()
            tr_size = 100 + (1 * 150) + (len(output_arr)+1 * 50)
            fee = int((tr_size / 1024) * fee_per_kb)
            fee_per_output = int((50 / 1024) * fee_per_kb)

        # Add inputs
        amount_total_input = 0
        if input_arr is None:
            utxo_query = self._session.query(DbTransactionOutput).join(DbTransaction).join(DbKey).\
                filter(DbKey.wallet_id == self.wallet_id,
                       DbKey. account_id == account_id,
                       DbTransactionOutput.spend.op("IS")(False),
                       DbTransaction.confirmations >= min_confirms)
            utxos = utxo_query.all()
            if not utxos:
                _logger.warning("Create transaction: No unspent transaction outputs found")
                return None
            input_arr = []
            selected_utxos = self._select_inputs(amount_total_output + fee, utxo_query)
            if not selected_utxos:
                raise WalletError("Not enough unspent transaction outputs found")
            for utxo in selected_utxos:
                amount_total_input += utxo.value
                input_arr.append((utxo.transaction.hash, utxo.output_n, utxo.key_id, utxo.value))
        else:
            for i in input_arr:
                amount_total_input += i[3]

        amount_change = int(amount_total_input - (amount_total_output + fee))
        # If change amount is smaller then estimated fee it will cost to send it then skip change
        if fee_per_output and amount_change < fee_per_output:
            amount_change = 0
        ck = None
        if amount_change:
            ck = self.get_key(account_id=account_id, network=network, change=1)
            t.add_output(amount_change, ck.address)

        # Add inputs
        sign_arr = []
        for inp in input_arr:
            key = self._session.query(DbKey).filter_by(id=inp[2]).scalar()
            if not key:
                raise WalletError("Key of UTXO %s not found in this wallet" % inp[0])
            k = HDKey(key.wif)
            id = t.add_input(inp[0], inp[1], public_key=k.public_byte)
            sign_arr.append((k.private_byte, id))

        # Sign inputs,
        for ti in sign_arr:
            t.sign(ti[0], ti[1])

        # Calculate exact estimated fees and update change output if necessary
        if transaction_fee is None and fee_per_kb and amount_change and ck is not None:
            # tr_size = len(t.raw())
            fee_exact = t.estimate_fee(fee_per_kb)
            if abs((fee - fee_exact) / fee_exact) > 0.10:  # Fee estimation more then 10% off
                _logger.info("Transaction fee not correctly estimated (est.: %d, real: %d). "
                             "Recreate transaction with correct fee" % (fee, fee_exact))
                return self.send(output_arr, input_arr, account_id=account_id, network=network,
                                 transaction_fee=fee_exact, min_confirms=min_confirms)

        # Verify transaction
        if not t.verify():
            raise WalletError("Cannot verify transaction. Create transaction failed")

        # Push it to the network
        res = srv.sendrawtransaction(t.raw_hex())
        if not res:
            raise WalletError("Could not send transaction: %s" % srv.errors)
        _logger.info("Successfully pushed transaction, result: %s" % res)

        # Update db: Update spend UTXO's, add transaction to database
        for inp in input_arr:
            utxos = self._session.query(DbTransactionOutput).join(DbTransaction).\
                filter(DbTransaction.hash == inp[0], DbTransactionOutput.output_n == inp[1]).all()
            for u in utxos:
                u.spend = True

        self._session.commit()
        if 'txid' in res:
            return res['txid']
        else:
            return res

    def sweep(self, to_address, account_id=None, network=None, max_utxos=999, min_confirms=1, fee_per_kb=None):
        """
        Sweep all unspent transaction outputs (UTXO's) and send them to one output address. 
        Wrapper for the send method.
        
        :param to_address: Single output address
        :type to_address: str
        :param account_id: Wallet's account ID
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param max_utxos: Limit maximum number of outputs to use. Default is 999
        :type max_utxos: int
        :param min_confirms: Minimal confirmations needed to include utxo
        :type min_confirms: int
        
        :return str, list: Transaction ID or result array
        """

        network, account_id, acckey = self._get_account_defaults(network, account_id)

        utxos = self.getutxos(account_id=account_id, network=network, min_confirms=min_confirms)
        utxos = utxos[0:max_utxos]
        input_arr = []
        total_amount = 0
        if not utxos:
            return False
        for utxo in utxos:
            input_arr.append((utxo['tx_hash'], utxo['output_n'], utxo['key_id'], utxo['value']))
            total_amount += utxo['value']
        srv = Service(network=network)
        if fee_per_kb is None:
            fee_per_kb = srv.estimatefee()
        tr_size = 125 + (len(input_arr) * 125)
        estimated_fee = int((tr_size / 1024) * fee_per_kb)
        return self.send([(to_address, total_amount-estimated_fee)], input_arr, network=network,
                         transaction_fee=estimated_fee, min_confirms=min_confirms)

    def info(self, detail=3):
        """
        Prints wallet information to standard output
        
        :param detail: Level of detail to show, can be 0, 1, 2 or 3
        :type detail: int

        """
        print("=== WALLET ===")
        print(" ID                             %s" % self.wallet_id)
        print(" Name                           %s" % self.name)
        print(" Owner                          %s" % self._owner)
        print(" Network                        %s" % self.network.description)
        print(" Balance                        %s" % self.balance(as_string=True))
        print("")

        if detail:
            print("= Main key =")
            self.main_key.info()
        if detail > 1:
            for tree_id in self.tree_ids():
                print("= Keys Overview - tree %d= " % tree_id)
                for nw in self.networks():
                    print("- Network: %s -" % nw['network_name'])
                    if detail < 3:
                        ds = [0, 3, 5]
                    else:
                        ds = range(6)
                    for d in ds:
                        for key in self.keys(depth=d, network=nw['network_name'], tree_index=tree_id):
                            print("%5s %-28s %-45s %-25s %25s" % (key.id, key.path, key.address, key.name,
                                                                  Network(key.network_name).print_value(key.balance)))
        print("\n")


if __name__ == '__main__':
    #
    # WALLETS EXAMPLES
    #

    # First recreate database to avoid already exist errors
    import os
    from pprint import pprint
    test_databasefile = 'bitcoinlib.test.sqlite'
    test_database = DEFAULT_DATABASEDIR + test_databasefile
    if os.path.isfile(test_database):
        os.remove(test_database)

    print("\n=== Most simple way to create Bitcoin Wallet ===")
    w = HDWallet.create('MyWallet', databasefile=test_database)
    w.new_key_change()
    w.new_key()
    w.info()

    print("\n=== Create new Testnet Wallet and generate a some new keys ===")
    with HDWallet.create(name='Personal', network='testnet', databasefile=test_database) as wallet:
        wallet.info(detail=3)
        wallet.new_account()
        new_key1 = wallet.new_key()
        new_key2 = wallet.new_key()
        new_key3 = wallet.new_key()
        new_key4 = wallet.new_key(change=1)
        new_key5 = wallet.key_for_path("m/44'/1'/100'/1200/1200")
        new_key6a = wallet.key_for_path("m/44'/1'/100'/1200/1201")
        new_key6b = wallet.key_for_path("m/44'/1'/100'/1200/1201")
        wallet.info(detail=3)
        donations_account = wallet.new_account()
        new_key8 = wallet.new_key(account_id=donations_account.account_id)
        wallet.info(detail=3)

    print("\n=== Create new Wallet with Testnet master key and account ID 99 ===")
    testnet_wallet = HDWallet.create(
        name='TestNetWallet',
        key='tprv8ZgxMBicQKsPeWn8NtYVK5Hagad84UEPEs85EciCzf8xYWocuJovxsoNoxZAgfSrCp2xa6DdhDrzYVE8UXF75r2dKePyA'
            '7irEvBoe4aAn52',
        network='testnet',
        account_id=99,
        databasefile=test_database)
    nk = testnet_wallet.new_key(account_id=99, name="Address #1")
    nk2 = testnet_wallet.new_key(account_id=99, name="Address #2")
    nkc = testnet_wallet.new_key_change(account_id=99, name="Change #1")
    nkc2 = testnet_wallet.new_key_change(account_id=99, name="Change #2")
    testnet_wallet.updateutxos()
    testnet_wallet.info(detail=3)

    # Three ways of getting the a HDWalletKey, with ID, address and name:
    # print(testnet_wallet.key(1).address)
    print(testnet_wallet.key('n3UKaXBRDhTVpkvgRH7eARZFsYE989bHjw').address)
    print(testnet_wallet.key('TestNetWallet').address)

    print("\n=== Import Account Bitcoin Testnet key with depth 3 ===")
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

    print("\n=== Create simple wallet and import some unrelated private keys ===")
    simple_wallet = HDWallet.create(
        name='Simple Wallet',
        key='L5fbTtqEKPK6zeuCBivnQ8FALMEq6ZApD7wkHZoMUsBWcktBev73',
        databasefile=test_database)
    simple_wallet.import_key('KxVjTaa4fd6gaga3YDDRDG56tn1UXdMF9fAMxehUH83PTjqk4xCs')
    simple_wallet.import_key('L3RyKcjp8kzdJ6rhGhTC5bXWEYnC2eL3b1vrZoduXMht6m9MQeHy')
    simple_wallet.updateutxos()
    simple_wallet.info(detail=3)
    del simple_wallet

    print("\n=== Create wallet with public key to generate addresses without private key ===")
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

    print("\n=== Create Litecoin wallet ===")
    litecoin_wallet = HDWallet.create(
        databasefile=test_database,
        name='Litecoin Wallet',
        network='litecoin')
    newkey = litecoin_wallet.new_key()
    litecoin_wallet.info(detail=3)
    del litecoin_wallet

    print("\n=== Create Litecoin testnet Wallet from Mnemonic Passphrase ===")
    # words = Mnemonic('english').generate()
    words = 'blind frequent camera goddess pottery repair skull year mistake wrist lonely mix'
    print("Generated Passphrase: %s" % words)
    seed = Mnemonic().to_seed(words)
    hdkey = HDKey().from_seed(seed, network='litecoin_testnet')
    wallet = HDWallet.create(name='Mnemonic Wallet', network='litecoin_testnet',
                             key=hdkey.wif(), databasefile=test_database)
    wallet.new_key("Input", 0)
    wallet.updateutxos()
    wallet.info(detail=3)

    print("\n=== Test import Litecoin key in Bitcoin wallet (should give error) ===")
    w = HDWallet.create(
        name='Wallet Error',
        databasefile=test_database)
    try:
        w.import_key(key='T43gB4F6k1Ly3YWbMuddq13xLb56hevUDP3RthKArr7FPHjQiXpp')
    except WalletError as e:
        print("Import litecoin key in bitcoin wallet gives an EXPECTED error: %s" % e)

    print("\n=== Normalize BIP48 key path ===")
    key_path = "m/44h/1'/0p/2000/1"
    print("Raw: %s, Normalized: %s" % (key_path, normalize_path(key_path)))

    print("\n=== Send test bitcoins to an address ===")
    wallet_import = HDWallet('TestNetWallet', databasefile=test_database)
    wallet_import.info(detail=3)
    wallet_import.updateutxos(99)
    print("\n= UTXOs =")
    utxos = wallet_import.getutxos(99)
    for utxo in utxos:
        print("%s %s (%d confirms)" % (
        utxo['address'], wallet_import.network.print_value(utxo['value']), utxo['confirmations']))
    res = wallet_import.send_to('mxdLD8SAGS9fe2EeCXALDHcdTTbppMHp8N', 100000, 99)
    print("Send transaction result:")
    pprint(res)

    print("\n=== List wallets & delete a wallet ===")
    print(','.join([w['name'] for w in list_wallets(databasefile=test_database)]))
    res = delete_wallet('Personal', databasefile=test_database, force=True)
    print(','.join([w['name'] for w in list_wallets(databasefile=test_database)]))
