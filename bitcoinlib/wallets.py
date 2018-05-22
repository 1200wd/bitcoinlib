# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    WALLETS - HD wallet Class for key and transaction management
#    © 2018 April - 1200 Web Development <http://1200wd.com/>
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
from copy import deepcopy
import struct
import random
from sqlalchemy import or_
from itertools import groupby
from operator import itemgetter
from bitcoinlib.db import *
from bitcoinlib.encoding import pubkeyhash_to_addr, to_hexstring, script_to_pubkeyhash, to_bytes
from bitcoinlib.keys import HDKey, check_network_and_key
from bitcoinlib.networks import Network, DEFAULT_NETWORK
from bitcoinlib.services.services import Service
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.transactions import Transaction, serialize_multisig_redeemscript, Output, Input, SIGHASH_ALL

_logger = logging.getLogger(__name__)


class WalletError(Exception):
    """
    Handle Wallet class Exceptions

    """
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def wallets_list(databasefile=DEFAULT_DATABASE):
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
            'scheme': w.scheme,
            'main_key_id': w.main_key_id,
            'parent_id': w.parent_id,
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

    if wallet in [x['name'] for x in wallets_list(databasefile)]:
        return True
    if isinstance(wallet, int) and wallet in [x['id'] for x in wallets_list(databasefile)]:
        return True
    return False


def wallet_create_or_open(name, key='', owner='', network=None, account_id=0, purpose=44, scheme='bip44',
                          parent_id=None, sort_keys=False, password='', databasefile=DEFAULT_DATABASE):
    """
    Create a wallet with specified options if it doesn't exist, otherwise just open

    See Wallets class create method for option documentation

    """
    if wallet_exists(name, databasefile=databasefile):
        return HDWallet(name, databasefile=databasefile)
    else:
        return HDWallet.create(name, key, owner, network, account_id, purpose, scheme, parent_id, sort_keys,
                               password, databasefile)


def wallet_create_or_open_multisig(
        name, key_list, sigs_required=None, owner='', network=None, account_id=0,
        purpose=45, multisig_compressed=True, sort_keys=False, databasefile=DEFAULT_DATABASE):
    """
    Create a wallet with specified options if it doesn't exist, otherwise just open

    See Wallets class create method for option documentation

    """
    if wallet_exists(name, databasefile=databasefile):
        return HDWallet(name, databasefile=databasefile)
    else:
        return HDWallet.create_multisig(name, key_list, sigs_required, owner, network, account_id, purpose,
                                        multisig_compressed, sort_keys, databasefile)


def wallet_delete(wallet, databasefile=DEFAULT_DATABASE, force=False):
    """
    Delete wallet and associated keys and transactions from the database. If wallet has unspent outputs it raises a
    WalletError exception unless 'force=True' is specified
    
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
    wallet_id = w.first().id

    # Delete keys from this wallet and update transactions (remove key_id)
    ks = session.query(DbKey).filter_by(wallet_id=wallet_id)
    for k in ks:
        if not force and k.balance:
            raise WalletError("Key %d (%s) still has unspent outputs. Use 'force=True' to delete this wallet" %
                              (k.id, k.address))
        session.query(DbTransactionOutput).filter_by(key_id=k.id).update({DbTransactionOutput.key_id: None})
        session.query(DbTransactionInput).filter_by(key_id=k.id).update({DbTransactionInput.key_id: None})
        session.query(DbKeyMultisigChildren).filter_by(parent_id=k.id).delete()
        session.query(DbKeyMultisigChildren).filter_by(child_id=k.id).delete()
    ks.delete()

    # Delete transactions from this wallet (remove wallet_id)
    session.query(DbTransaction).filter_by(wallet_id=wallet_id).update({DbTransaction.wallet_id: None})

    res = w.delete()
    session.commit()
    session.close()

    # Delete co-signer wallets if this is a multisig wallet
    for cw in session.query(DbWallet).filter_by(parent_id=wallet_id).all():
        wallet_delete(cw.id, databasefile=databasefile, force=force)

    _logger.info("Wallet '%s' deleted" % wallet)

    return res


def wallet_empty(wallet, databasefile=DEFAULT_DATABASE):
    session = DbInit(databasefile=databasefile).session
    if isinstance(wallet, int) or wallet.isdigit():
        w = session.query(DbWallet).filter_by(id=wallet)
    else:
        w = session.query(DbWallet).filter_by(name=wallet)
    if not w or not w.first():
        raise WalletError("Wallet '%s' not found" % wallet)
    wallet_id = w.first().id

    # Delete keys from this wallet and update transactions (remove key_id)
    ks = session.query(DbKey).filter(DbKey.wallet_id == wallet_id, DbKey.depth > 3)
    for k in ks:
        session.query(DbTransactionOutput).filter_by(key_id=k.id).update({DbTransactionOutput.key_id: None})
        session.query(DbTransactionInput).filter_by(key_id=k.id).update({DbTransactionInput.key_id: None})
        session.query(DbKeyMultisigChildren).filter_by(parent_id=k.id).delete()
        session.query(DbKeyMultisigChildren).filter_by(child_id=k.id).delete()
    ks.delete()

    # Delete transactions from this wallet (remove wallet_id)
    session.query(DbTransaction).filter_by(wallet_id=wallet_id).update({DbTransaction.wallet_id: None})

    session.commit()
    session.close()

    _logger.info("All keys and transactions from wallet '%s' deleted" % wallet)

    return True


def wallet_delete_if_exists(wallet, databasefile=DEFAULT_DATABASE, force=False):
    """
    Delete wallet and associated keys from the database. If wallet has unspent outputs it raises a WalletError exception
    unless 'force=True' is specified. If wallet wallet does not exist return False

    :param wallet: Wallet ID as integer or Wallet Name as string
    :type wallet: int, str
    :param databasefile: Location of Sqlite database. Leave empty to use default
    :type databasefile: str
    :param force: If set to True wallet will be deleted even if unspent outputs are found. Default is False
    :type force: bool

    :return int: Number of rows deleted, so 1 if succesfull
    """

    if wallet_exists(wallet, databasefile):
        return wallet_delete(wallet, databasefile, force)
    return False


def normalize_path(path):
    """ Normalize BIP0044 key path for HD keys. Using single quotes for hardened keys 

    :param path: BIP0044 key path 
    :type path: str

    :return str: Normalized BIP0044 key path with single quotes
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
    Path length must be between 1 and 6 (Depth between 0 and 5)
    
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
    def from_key(name, wallet_id, session, key='', account_id=0, network=None, change=0,
                 purpose=44, parent_id=0, path='m', key_type=None):
        """
        Create HDWalletKey from a HDKey object or key
        
        :param name: New key name
        :type name: str
        :param wallet_id: ID of wallet where to store key
        :type wallet_id: int
        :param session: Required Sqlalchemy Session object
        :type session: sqlalchemy.orm.session.Session
        :param key: Optional key in any format accepted by the HDKey class
        :type key: str, int, byte, bytearray, HDKey
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
        :type path: str
        :param key_type: Type of key, single or BIP44 type
        :type key_type: str

        :return HDWalletKey: HDWalletKey object
        """

        if isinstance(key, HDKey):
            k = key
        else:
            if network is None:
                network = DEFAULT_NETWORK
            k = HDKey(import_key=key, network=network)

        keyexists = session.query(DbKey).filter(DbKey.wallet_id == wallet_id, DbKey.wif == k.wif()).first()
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
                raise WalletError("Key depth of %d does not match path length of %d for path %s" %
                                  (k.depth, len(path.split('/')) - 1, path))

        wk = session.query(DbKey).filter(DbKey.wallet_id == wallet_id,
                                         or_(DbKey.public == k.public_hex,
                                             DbKey.wif == k.wif())).first()
        if wk:
            return HDWalletKey(wk.id, session, k)

        nk = DbKey(name=name, wallet_id=wallet_id, public=k.public_hex, private=k.private_hex, purpose=purpose,
                   account_id=account_id, depth=k.depth, change=change, address_index=k.child_index,
                   wif=k.wif(), address=k.key.address(), parent_id=parent_id, compressed=k.compressed,
                   is_private=k.isprivate, path=path, key_type=key_type, network_name=network)
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
            # self.key_hex = wk.key
            self.key_public = wk.public
            self.key_private = wk.private
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
            self.compressed = wk.compressed
        else:
            raise WalletError("Key with id %s not found" % key_id)

    def __repr__(self):
        return "<HDWalletKey(key_id=%d, name=%s, wif=%s, path=%s)>" % (self.key_id, self.name, self.wif, self.path)

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
        if self.is_private:
            p = ["m"]
        else:
            p = ["M"]
        p.append(str(self.purpose) + "'")
        p.append(str(self.network.bip44_cointype) + "'")
        p.append(str(self.account_id) + "'")
        p.append(str(change))
        p.append(str(address_index))
        return p[:max_depth]

    def dict(self):
        """
        Return current key information as dictionary

        """

        return {
            'id': self.key_id,
            'key_type': self.key_type,
            'is_private': self.is_private,
            'name': self.name,
            'key_private': self.key_private,
            'key_public': self.key_public,
            'wif': self.wif,
            'account_id':  self.account_id,
            'parent_id': self.parent_id,
            'depth': self.depth,
            'change': self.change,
            'address_index': self.address_index,
            'address': self.address,
            'path': self.path,
            'balance': self.balance(),
            'balance_str': self.balance(fmt='string')
        }


class HDWalletTransaction(Transaction):
    """
    Normally only used as attribute of HDWallet class. Child of Transaction object with extra reference to
    wallet and database object.

    All HDWalletTransaction items are stored in a database
    """

    def __init__(self, hdwallet, *args, **kwargs):
        """
        Initialize HDWalletTransaction object with reference to a HDWallet object

        :param hdwallet: HDWallet object, wallet name or ID
        :type hdWallet: HDwallet, str, int
        :param args: Arguments for HDWallet parent class
        :type args: args
        :param kwargs: Keyword arguments for HDWallet parent class
        :type kwargs: kwargs
        """
        assert isinstance(hdwallet, HDWallet)
        self.hdwallet = hdwallet
        self.pushed = False
        self.error = None
        self.response_dict = None
        Transaction.__init__(self, *args, **kwargs)

    def __repr__(self):
        return "<HDWalletTransaction(input_count=%d, output_count=%d, status=%s, network=%s)>" % \
               (len(self.inputs), len(self.outputs), self.status, self.network.network_name)

    @classmethod
    def from_transaction(cls, hdwallet, t):
        """
        Create HDWalletTransaction object from Transaction object

        :param hdwallet: HDWallet object, wallet name or ID
        :type hdwallet: HDwallet, str, int
        :param t: Specify Transaction object
        :type t: Transaction

        :return HDWalletClass:
        """
        return cls(hdwallet=hdwallet, inputs=t.inputs, outputs=t.outputs, locktime=t.locktime, version=t.version,
                   network=t.network.network_name, fee=t.fee, fee_per_kb=t.fee_per_kb, size=t.size,
                   hash=t.hash, date=t.date, confirmations=t.confirmations, block_height=t.block_height,
                   block_hash=t.block_hash, input_total=t.input_total, output_total=t.output_total,
                   rawtx=t.rawtx, status=t.status, coinbase=t.coinbase, verified=t.verified, flag=t.flag)

    def sign(self, keys=None, index_n=0, hash_type=SIGHASH_ALL):
        """
        Sign this transaction. Use existing keys from wallet or use keys argument for extra keys.

        :param keys: Extra private keys to sign the transaction
        :type keys: HDKey, str
        :param index_n: Transaction index_n to sign
        :type index_n: int
        :param hash_type: Hashtype to use, default is SIGHASH_ALL
        :type hash_type: int

        :return bool: True is successfully signed
        """
        priv_key_list_arg = []
        if keys:
            if not isinstance(keys, list):
                keys = [keys]
            for priv_key in keys:
                if isinstance(priv_key, HDKey):
                    priv_key_list_arg.append(priv_key)
                else:
                    priv_key_list_arg.append(HDKey(priv_key, network=self.network.network_name))
        for ti in self.inputs:
            priv_key_list = deepcopy(priv_key_list_arg)
            for k in ti.keys:
                if k.isprivate:
                    if isinstance(k, HDKey):
                        hdkey = k
                    else:
                        hdkey = HDKey(k, network=self.network.network_name)
                    if hdkey not in priv_key_list:
                        priv_key_list.append(k)
                elif self.hdwallet.cosigner:
                    # Check if private key is available in wallet
                    cosign_wallet_ids = [w.wallet_id for w in self.hdwallet.cosigner]
                    db_pk = self.hdwallet._session.query(DbKey).filter_by(public=k.public_hex, is_private=True). \
                        filter(DbKey.wallet_id.in_(cosign_wallet_ids + [self.hdwallet.wallet_id])).first()
                    if db_pk:
                        priv_key_list.append(HDKey(db_pk.wif, network=self.network.network_name))
            Transaction.sign(self, priv_key_list, ti.index_n, hash_type)
        self.verify()
        self.error = ""
        return True

    def send(self, offline=False):
        """
        Verify and push transaction to network. Update UTXO's in database after successfull send

        :param offline: Just return the transaction object and do not send it when offline = True. Default is False
        :type offline: bool

        :return bool: Returns True if succesfully pushed to the network

        """

        self.error = None
        # if not self.verified:
        #     self.sign()
        if not self.verified and not self.verify():
            self.error = "Cannot verify transaction"
            return False

        if offline:
            return False

        srv = Service(network=self.network.network_name)
        res = srv.sendrawtransaction(self.raw_hex())
        if not res:
            self.error = "Cannot send transaction. %s" % srv.errors
            return False
        if 'txid' in res:
            _logger.info("Successfully pushed transaction, result: %s" % res)
            self.hash = res['txid']
            self.status = 'unconfirmed'
            self.confirmations = 0
            self.pushed = True
            self.response_dict = srv.results
            self.save()

            # Update db: Update spent UTXO's, add transaction to database
            for inp in self.inputs:
                tx_hash = to_hexstring(inp.prev_hash)
                utxos = self.hdwallet._session.query(DbTransactionOutput).join(DbTransaction).\
                    filter(DbTransaction.hash == tx_hash,
                           DbTransactionOutput.output_n == inp.output_n_int,
                           DbTransactionOutput.spent.op("IS")(False)).all()
                for u in utxos:
                    u.spent = True

            self.hdwallet._session.commit()
            self.hdwallet._balance_update(network=self.network.network_name)
            return True

        return False

    def save(self):
        """
        Save this transaction to database

        :return int: Transaction ID
        """

        sess = self.hdwallet._session
        # If tx_hash is unknown add it to database, else update
        db_tx_query = sess.query(DbTransaction). \
            filter(DbTransaction.wallet_id == self.hdwallet.wallet_id, DbTransaction.hash == self.hash)
        db_tx = db_tx_query.scalar()
        if not db_tx:
            db_tx_query = sess.query(DbTransaction). \
                filter(DbTransaction.wallet_id.is_(None), DbTransaction.hash == self.hash)
            db_tx = db_tx_query.first()
            if db_tx:
                db_tx.wallet_id = self.hdwallet.wallet_id

        if not db_tx:
            new_tx = DbTransaction(
                wallet_id=self.hdwallet.wallet_id, hash=self.hash, block_height=self.block_height,
                size=self.size, confirmations=self.confirmations, date=self.date, fee=self.fee, status=self.status,
                input_total=self.input_total, output_total=self.output_total, network_name=self.network.network_name,
                raw=self.raw_hex(), block_hash=self.block_hash)
            sess.add(new_tx)
            sess.commit()
            tx_id = new_tx.id
        else:
            tx_id = db_tx.id
            db_tx.block_height = self.block_height if self.block_height else db_tx.block_height
            db_tx.confirmations = self.confirmations if self.confirmations else db_tx.confirmations
            db_tx.date = self.date if self.date else db_tx.date
            db_tx.fee = self.fee if self.fee else db_tx.fee
            db_tx.status = self.status if self.status else db_tx.status
            db_tx.input_total = self.input_total if self.input_total else db_tx.input_total
            db_tx.output_total = self.output_total if self.output_total else db_tx.output_total
            db_tx.network_name = self.network.network_name if self.network.network_name else db_tx.network_name
            sess.commit()

        assert tx_id
        for ti in self.inputs:
            tx_key = sess.query(DbKey).filter_by(wallet_id=self.hdwallet.wallet_id, address=ti.address).scalar()
            key_id = None
            if tx_key:
                key_id = tx_key.id
                tx_key.used = True
            tx_input = sess.query(DbTransactionInput). \
                filter_by(transaction_id=tx_id, index_n=ti.index_n).scalar()
            if not tx_input:
                index_n = ti.index_n
                if index_n is None:
                    last_index_n = sess.query(DbTransactionInput.index_n).\
                        filter_by(transaction_id=tx_id). \
                        order_by(DbTransactionInput.index_n.desc()).first()
                    index_n = 0
                    if last_index_n:
                        index_n = last_index_n[0] + 1

                new_tx_item = DbTransactionInput(
                    transaction_id=tx_id, output_n=ti.output_n_int, key_id=key_id, value=ti.value,
                    prev_hash=to_hexstring(ti.prev_hash), index_n=index_n, double_spend=ti.double_spend,
                    script=to_hexstring(ti.unlocking_script), script_type=ti.script_type)
                sess.add(new_tx_item)
            elif key_id:
                tx_input.key_id = key_id
                if ti.value:
                    tx_input.value = ti.value
                if ti.prev_hash:
                    tx_input.prev_hash = to_hexstring(ti.prev_hash)
                if ti.unlocking_script:
                    tx_input.script = to_hexstring(ti.unlocking_script)

            sess.commit()
        for to in self.outputs:
            tx_key = sess.query(DbKey).\
                filter_by(wallet_id=self.hdwallet.wallet_id, address=to.address).scalar()
            key_id = None
            if tx_key:
                key_id = tx_key.id
                tx_key.used = True
            spent = to.spent
            tx_output = sess.query(DbTransactionOutput). \
                filter_by(transaction_id=tx_id, output_n=to.output_n).scalar()
            if not tx_output:
                new_tx_item = DbTransactionOutput(
                    transaction_id=tx_id, output_n=to.output_n, key_id=key_id, value=to.value, spent=spent,
                    script=to_hexstring(to.lock_script), script_type=to.script_type)
                sess.add(new_tx_item)
            elif key_id:
                tx_output.key_id = key_id
                tx_output.spent = spent if spent is not None else tx_output.spent
            sess.commit()
        return tx_id

    def info(self):
        """
        Print Wallet transaction information to standard output. Include send information.

        """
        Transaction.info(self)
        print("Pushed to network: %s" % self.pushed)
        print("Wallet: %s" % self.hdwallet.name)
        self.pushed = False
        if self.error:
            print("Send errors: %s" % self.error)


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
    def create(cls, name, key='', owner='', network=None, account_id=0, purpose=44, scheme='bip44', parent_id=None,
               sort_keys=True, password='', databasefile=None):
        """
        Create HDWallet and insert in database. Generate masterkey or import key when specified. 
        
        Please mention account_id if you are using multiple accounts.
        
        :param name: Unique name of this Wallet
        :type name: str
        :param key: Masterkey to use for this wallet. Will be automatically created if not specified. Can contain all key formats accepted by the HDKey object, a HDKey object or BIP39 passphrase
        :type key: str, bytes, int, bytearray
        :param owner: Wallet owner for your own reference
        :type owner: str
        :param network: Network name, use default if not specified
        :type network: str
        :param account_id: Account ID, default is 0
        :type account_id: int
        :param purpose: BIP44 purpose field, default is 44
        :type purpose: int
        :param scheme: Key structure type, i.e. BIP44, single or multisig
        :type scheme: str
        :param parent_id: Parent Wallet ID used for multisig wallet structures
        :type parent_id: int
        :param sort_keys: Sort keys according to BIP45 standard (used for multisig keys)
        :type sort_keys: bool
        :param password: Password to protect passphrase, only used if a passphrase is supplied in the 'key' argument.
        :type password: str
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
        if name.isdigit():
            raise WalletError("Wallet name '%s' invalid, please include letter characters" % name)
        if isinstance(key, HDKey):
            network = key.network.network_name
        elif key:
            # If key consists of several words assume it is a passphrase and convert it to a HDKey object
            if len(key.split(" ")) > 1:
                if not network:
                    raise WalletError("Please specify network when using passphrase to create a key")
                key = HDKey().from_seed(Mnemonic().to_seed(key, password), network=network)
            else:
                network = check_network_and_key(key, network)
                key = HDKey(key, network=network)
        elif network is None:
            network = DEFAULT_NETWORK
        if not name:
            raise WalletError("Please enter wallet name")

        new_wallet = DbWallet(name=name, owner=owner, network_name=network, purpose=purpose, scheme=scheme,
                              sort_keys=sort_keys, parent_id=parent_id)
        session.add(new_wallet)
        session.commit()
        new_wallet_id = new_wallet.id

        if scheme == 'bip44':
            mk = HDWalletKey.from_key(key=key, name=name, session=session, wallet_id=new_wallet_id, network=network,
                                      account_id=account_id, purpose=purpose, key_type='bip32')
            if mk.depth > 4:
                raise WalletError("Cannot create new wallet with main key of depth 5 or more")
            new_wallet.main_key_id = mk.key_id
            session.commit()

            w = cls(new_wallet_id, databasefile=databasefile, main_key_object=mk.key())
            if mk.depth == 0:
                nw = Network(network)
                networkcode = nw.bip44_cointype
                path = ["%d'" % purpose, "%s'" % networkcode]
                w._create_keys_from_path(mk, path, name=name, wallet_id=new_wallet_id, network=network, session=session,
                                         account_id=account_id, purpose=purpose, basepath="m")
                w.new_account(account_id=account_id)
        elif scheme == 'multisig':
            w = cls(new_wallet_id, databasefile=databasefile)
        elif scheme == 'single':
            mk = HDWalletKey.from_key(key=key, name=name, session=session, wallet_id=new_wallet_id, network=network,
                                      account_id=account_id, purpose=purpose, key_type='single')
            new_wallet.main_key_id = mk.key_id
            session.commit()
            w = cls(new_wallet_id, databasefile=databasefile, main_key_object=mk.key())
        else:
            raise WalletError("Wallet with scheme %s not supported at the moment" % scheme)

        session.close()
        return w

    @classmethod
    def create_multisig(cls, name, key_list, sigs_required=None, owner='', network=None, account_id=0, purpose=45,
                        multisig_compressed=True, sort_keys=True, databasefile=None):
        """
        Create a multisig wallet with specified name and list of keys. The list of keys can contain 2 or more
        public or private keys. For every key a cosigner wallet will be created with a BIP44 key structure or a
        single key depending on the key_type.

        :param name: Unique name of this Wallet
        :type name: str
        :param key_list: List of keys in HDKey format or any other format supported by HDKey class
        :type key_list: list
        :param sigs_required: Number of signatures required for validation. For example 2 for 2-of-3 multisignature. Default is all keys must signed
        :type sigs_required: int
        :type owner: str
        :param network: Network name, use default if not specified
        :type network: str
        :param account_id: Account ID, default is 0
        :type account_id: int
        :param purpose: BIP44 purpose field, default is 44
        :type purpose: int
        :param multisig_compressed: Use compressed multisig keys for this wallet. Default is True
        :type multisig_compressed: bool
        :param sort_keys: Sort keys according to BIP45 standard (used for multisig keys)
        :type sort_keys: bool
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
            _logger.info("Create new multisig wallet '%s'" % name)
        if not isinstance(key_list, list):
            raise WalletError("Need list of keys to create multi-signature key structure")
        if len(key_list) < 2:
            raise WalletError("Key list must contain at least 2 keys")
        if sigs_required is None:
            sigs_required = len(key_list)
        if sigs_required > len(key_list):
            raise WalletError("Number of keys required to sign is greater then number of keys provided")

        hdpm = cls.create(name=name, owner=owner, network=network, account_id=account_id,
                          purpose=purpose, scheme='multisig', sort_keys=sort_keys, databasefile=databasefile)
        hdpm.multisig_compressed = multisig_compressed
        co_id = 0
        hdpm.cosigner = []
        hdkey_list = []
        for cokey in key_list:
            if not isinstance(cokey, HDKey):
                if len(cokey.split(' ')) > 5:
                    k = HDKey().from_passphrase(cokey, network=network)
                else:
                    k = HDKey(cokey, network=network)
                hdkey_list.append(k)
            else:
                hdkey_list.append(cokey)
        if sort_keys:
            hdkey_list.sort(key=lambda x: x.public_byte)
        for cokey in hdkey_list:
            if hdpm.network.network_name != cokey.network.network_name:
                raise WalletError("Network for key %s (%s) is different then network specified: %s/%s" %
                                  (cokey.wif(), cokey.network.network_name, network, hdpm.network.network_name))
            scheme = 'bip44'
            wn = name + '-cosigner-%d' % co_id
            if cokey.key_type == 'single':
                scheme = 'single'
            w = cls.create(name=wn, key=cokey, owner=owner, network=network, account_id=account_id,
                           purpose=purpose, parent_id=hdpm.wallet_id, databasefile=databasefile, scheme=scheme)
            hdpm.cosigner.append(w)
            co_id += 1

        hdpm.multisig_n_required = sigs_required
        hdpm.sort_keys = sort_keys
        session.query(DbWallet).filter(DbWallet.id == hdpm.wallet_id).\
            update({DbWallet.multisig_n_required: sigs_required})
        session.commit()
        session.close_all()
        return hdpm

    def _create_keys_from_path(self, parent, path, wallet_id, account_id, network, session,
                               name='', basepath='', change=0, purpose=44):
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
        :param purpose: Purpose field according to BIP32 definition, default is 44 for BIP44.
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
        nk = parent
        ck = nk.key()

        # Check for closest ancestor in wallet
        spath = basepath + '/'.join(path)
        rkey = None
        while spath and not rkey:
            rkey = self._session.query(DbKey).filter_by(wallet_id=wallet_id, path=spath).first()
            spath = '/'.join(spath.split("/")[:-1])
        if rkey is not None and rkey.path not in [basepath, basepath[:-1]]:
            path = (basepath + '/'.join(path)).replace(rkey.path + '/', '').split('/')
            basepath = rkey.path + '/'
            nk = self.key(rkey.id)
            ck = nk.key()

        parent_id = nk.key_id
        # Create new keys from path
        for l in range(len(path)):
            pp = "/".join(path[:l+1])
            fullpath = basepath + pp
            ck = ck.subkey_for_path(path[l], network=network)
            nk = HDWalletKey.from_key(key=ck, name=name, wallet_id=wallet_id, network=network,
                                      account_id=account_id, change=change, purpose=purpose, path=fullpath,
                                      parent_id=parent_id, session=session)
            self._key_objects.update({nk.key_id: nk})
            parent_id = nk.key_id
        _logger.info("New key(s) created for parent_id %d" % parent_id)
        return nk

    def __enter__(self):
        return self

    def __init__(self, wallet, databasefile=DEFAULT_DATABASE, session=None, main_key_object=None):
        """
        Open a wallet with given ID or name
        
        :param wallet: Wallet name or ID
        :type wallet: int, str
        :param databasefile: Location of database file. Leave empty to use default
        :type databasefile: str
        :param session: Sqlalchemy session
        :type session: sqlalchemy.orm.session.Session
        :param main_key_object: Pass main key object to save time
        :type main_key_object: HDKey
        """

        if session:
            self._session = session
        else:
            dbinit = DbInit(databasefile=databasefile)
            self._session = dbinit.session
            self._engine = dbinit.engine
        self.databasefile = databasefile
        if isinstance(wallet, int) or wallet.isdigit():
            db_wlt = self._session.query(DbWallet).filter_by(id=wallet).scalar()
        else:
            db_wlt = self._session.query(DbWallet).filter_by(name=wallet).scalar()
        if db_wlt:
            self._dbwallet = db_wlt
            self.wallet_id = db_wlt.id
            self._name = db_wlt.name
            self._owner = db_wlt.owner
            self.network = Network(db_wlt.network_name)
            self.purpose = db_wlt.purpose
            self.scheme = db_wlt.scheme
            self._balance = None
            self._balances = []
            self.main_key_id = db_wlt.main_key_id
            self.main_key = None
            self.default_account_id = 0
            self.multisig_n_required = db_wlt.multisig_n_required
            self.multisig_compressed = None
            co_sign_wallets = self._session.query(DbWallet).\
                filter(DbWallet.parent_id == self.wallet_id).order_by(DbWallet.name).all()
            self.cosigner = [HDWallet(w.id, databasefile=databasefile) for w in co_sign_wallets]
            self.sort_keys = db_wlt.sort_keys
            if main_key_object:
                self.main_key = HDWalletKey(self.main_key_id, session=self._session, hdkey_object=main_key_object)
            elif db_wlt.main_key_id:
                self.main_key = HDWalletKey(self.main_key_id, session=self._session)
            if self.main_key:
                self.default_account_id = self.main_key.account_id
            _logger.info("Opening wallet '%s'" % self.name)
            self._key_objects = {
                self.main_key_id: self.main_key
            }
        else:
            raise WalletError("Wallet '%s' not found, please specify correct wallet ID or name." % wallet)

    def __exit__(self, exception_type, exception_value, traceback):
        self._session.close()

    def __del__(self):
        try:
            if self._dbwallet.parent_id:
                return
        except:
            pass
        self._session.close()

    def __repr__(self):
        return "<HDWallet(name=%s, databasefile=\"%s\")>" % \
               (self.name, self.databasefile)

    def _get_account_defaults(self, network=None, account_id=None, key_id=None):
        """
        Check parameter values for network and account ID, return defaults if no network or account ID is specified.
        If a network is specified but no account ID this method returns the first account ID it finds. 
        
        :param network: Network code, leave empty for default
        :type network: str
        :param account_id: Account ID, leave emtpy for default
        :type account_id: int
        :param key_id: Key ID to just update 1 key
        :type key_id: int
        
        :return: network code, account ID and DbKey instance of account ID key
        """

        if key_id:
            kobj = self.key(key_id)
            network = kobj.network_name
            account_id = kobj.account_id
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
        if account_id is None:
            if acckey:
                account_id = acckey.account_id
            else:
                account_id = 0
        return network, account_id, acckey

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

    def key_add_private(self, wallet_key, private_key):
        """
        Change public key in wallet to private key in current HDWallet object and in database

        :param wallet_key: Key object of wallet
        :type wallet_key: HDWalletKey
        :param private_key: Private key wif or HDKey object
        :type private_key: HDKey, str

        :return HDWalletKey:
        """
        assert isinstance(wallet_key, HDWalletKey)
        if not isinstance(private_key, HDKey):
            private_key = HDKey(private_key, network=self.network.network_name)
        wallet_key.is_private = True
        wallet_key.wif = private_key.wif()
        wallet_key.private = private_key.private_hex
        self._session.query(DbKey).filter(DbKey.id == wallet_key.key_id).update(
                {DbKey.is_private: True, DbKey.private: private_key.private_hex, DbKey.wif: private_key.wif()})
        self._session.commit()
        return wallet_key

    def import_master_key(self, hdkey, name='Masterkey (imported)'):
        """
        Import (another) masterkey in this wallet

        :param hdkey: Private key
        :type hdkey: HDKey, str
        :param name: Key name of masterkey
        :type name: str

        :return HDKey: Main key as HDKey object
        """
        network, account_id, acckey = self._get_account_defaults()

        if not isinstance(hdkey, HDKey):
            hdkey = HDKey(hdkey)
        if not isinstance(self.main_key, HDWalletKey):
            raise WalletError("Main wallet key is not an HDWalletKey instance. Type %s" % type(self.main_key))
        if not hdkey.isprivate or hdkey.depth != 0:
            raise WalletError("Please supply a valid private BIP32 master key with key depth 0")
        if self.main_key.depth != 3 or self.main_key.is_private or self.main_key.key_type != 'bip32':
            raise WalletError("Current main key is not a valid BIP32 public account key")
        if self.main_key.wif != hdkey.account_key(purpose=self.purpose).wif_public():
            raise WalletError("This key does not correspond to current main account key")
        if not (self.network.network_name == self.main_key.network.network_name == hdkey.network.network_name):
            raise WalletError("Network of Wallet class, main account key and the imported private key must use "
                              "the same network")

        self.main_key = HDWalletKey.from_key(
            key=hdkey.wif(), name=name, session=self._session, wallet_id=self.wallet_id, network=network,
            account_id=account_id, purpose=self.purpose, key_type='bip32')
        self.main_key_id = self.main_key.key_id
        network_code = self.network.bip44_cointype
        path = ["%d'" % self.purpose, "%s'" % network_code]
        self._create_keys_from_path(
            self.main_key, path, name=name, wallet_id=self.wallet_id, network=network, session=self._session,
            account_id=account_id, purpose=self.purpose, basepath="m")

        self._key_objects = {
            self.main_key_id: self.main_key
        }
        # FIXME: Use wallet object for this (integrate self._db and self)
        self._session.query(DbWallet).filter(DbWallet.id == self.wallet_id).\
            update({DbWallet.main_key_id: self.main_key_id})
        self._session.commit()
        return self.main_key

    def import_key(self, key, account_id=0, name='', network=None, purpose=44, key_type=None):
        """
        Add new single key to wallet.
        
        :param key: Key to import
        :type key: str, bytes, int, bytearray
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param name: Specify name for key, leave empty for default
        :type name: str
        :param network: Network name, method will try to extract from key if not specified. Raises warning if network could not be detected
        :type network: str
        :param purpose: BIP definition used, default is BIP44
        :type purpose: int
        :param key_type: Key type of imported key, can be single (unrelated to wallet, bip32, bip44 or master for new or extra master key import. Default is 'single'
        :type key_type: str
        
        :return HDWalletKey: 
        """

        if self.scheme != 'bip44' and self.scheme != 'multisig':
            raise WalletError("Keys can only be imported to a BIP44 or Multisig type wallet, create a new wallet "
                              "instead")
        if isinstance(key, HDKey):
            network = key.network.network_name
            hdkey = key
        else:
            if network is None:
                network = check_network_and_key(key, default_network=self.network.network_name)
                if network not in self.network_list():
                    raise WalletError("Network %s not available in this wallet, please create an account for this "
                                      "network first." % network)

            hdkey = HDKey(key, network=network, key_type=key_type)

        if self.scheme == 'bip44':
            if self.main_key and self.main_key.depth == 3 and \
                    hdkey.isprivate and hdkey.depth == 0 and self.scheme == 'bip44':
                hdkey.key_type = 'bip32'
                return self.import_master_key(hdkey, name)

            if key_type is None:
                hdkey.key_type = 'single'
                key_type = 'single'

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

            mk = HDWalletKey.from_key(
                key=hdkey, name=name, wallet_id=self.wallet_id, network=network, key_type=key_type,
                account_id=account_id, purpose=purpose, session=self._session, path=ik_path)
            return mk
        else:
            account_key = hdkey.account_multisig_key().wif_public()
            for w in self.cosigner:
                if w.main_key.wif == account_key:
                    if w.main_key.depth != 3:
                        _logger.debug("Private key probably already known. Key depth of wallet key must be 3 but is "
                                      "%d" % w.main_key.depth)
                        continue
                    _logger.debug("Import new private cosigner key in this multisig wallet: %s" % account_key)
                    return w.import_master_key(hdkey)

    def new_key(self, name='', account_id=None, network=None, change=0, max_depth=5):
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

        if self.scheme == 'single':
            return self.main_key

        network, account_id, acckey = self._get_account_defaults(network, account_id)
        if self.scheme == 'bip44':
            # Get account key, create one if it doesn't exist
            if not acckey:
                acckey = self._session.query(DbKey). \
                    filter_by(wallet_id=self.wallet_id, purpose=self.purpose, account_id=account_id,
                              depth=3, network_name=network).scalar()
            if not acckey:
                if account_id is None:
                    account_id = 0
                hk = self.new_account(account_id=account_id, network=network)
                if hk:
                    acckey = hk._dbkey
            if not acckey:
                raise WalletError("No key found this wallet_id, network and purpose. "
                                  "Is there a master key imported?")
            else:
                main_acc_key = self.key(acckey.id)

            # Determine new key ID
            prevkey = self._session.query(DbKey). \
                filter_by(wallet_id=self.wallet_id, purpose=self.purpose, network_name=network,
                          account_id=account_id, change=change, depth=max_depth). \
                order_by(DbKey.address_index.desc()).first()
            address_index = 0
            if prevkey:
                address_index = prevkey.address_index + 1

            # Compose key path and create new key
            newpath = [(str(change)), str(address_index)]
            bpath = main_acc_key.path + '/'
            if not name:
                if change:
                    name = "Change %d" % address_index
                else:
                    name = "Key %d" % address_index
            newkey = self._create_keys_from_path(
                main_acc_key, newpath, name=name, wallet_id=self.wallet_id,  account_id=account_id,
                change=change, network=network, purpose=self.purpose, basepath=bpath, session=self._session
            )
            return newkey
        elif self.scheme == 'multisig':
            if self.network.network_name != network:
                raise WalletError("Multiple networks is currently not supported for multisig")
            if not self.multisig_n_required:
                raise WalletError("Multisig_n_required not set, cannot create new key")
            if account_id is None:
                account_id = 0
            co_sign_wallets = self._session.query(DbWallet).\
                filter(DbWallet.parent_id == self.wallet_id).order_by(DbWallet.name).all()

            public_keys = []
            for csw in co_sign_wallets:
                w = HDWallet(csw.id, session=self._session)
                wk = w.new_key(change=change, max_depth=max_depth, network=network)
                public_keys.append({
                    'key_id': wk.key_id,
                    'public_key_uncompressed': wk.key().key.public_uncompressed(),
                    'public_key': wk.key().key.public(),
                    'depth': wk.depth,
                    'path': wk.path
                })
            if self.sort_keys:
                public_keys.sort(key=lambda x: x['public_key'])
            public_key_list = [x['public_key'] for x in public_keys]
            public_key_ids = [str(x['key_id']) for x in public_keys]
            depths = [x['depth'] for x in public_keys]
            depth = 5 if len(set(depths)) != 1 else depths[0]

            # Calculate redeemscript and address and add multisig key to database
            redeemscript = serialize_multisig_redeemscript(public_key_list, n_required=self.multisig_n_required)
            address = pubkeyhash_to_addr(script_to_pubkeyhash(redeemscript),
                                         versionbyte=Network(network).prefix_address_p2sh)
            if len(set([x['path'] for x in public_keys])) == 1:
                path = public_keys[0]['path']
            else:
                path = "multisig-%d-of-" % self.multisig_n_required + '/'.join(public_key_ids)
            if not name:
                name = "Multisig Key " + '/'.join(public_key_ids)
            multisig_key = DbKey(
                name=name, wallet_id=self.wallet_id, purpose=self.purpose, account_id=account_id,
                depth=depth, change=change, address_index=0, parent_id=0, is_private=False, path=path,
                public=to_hexstring(redeemscript), wif='multisig-%s' % address, address=address,
                key_type='multisig', network_name=network)
            self._session.add(multisig_key)
            self._session.commit()
            for child_id in public_key_ids:
                self._session.add(DbKeyMultisigChildren(key_order=public_key_ids.index(child_id),
                                                        parent_id=multisig_key.id, child_id=child_id))
            self._session.commit()
            return HDWalletKey(multisig_key.id, session=self._session)

    def new_key_change(self, name='', account_id=None, network=None):
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

    def scan(self, scan_gap_limit=10, account_id=None, change=None, network=None, _keys_ignore=None,
             _recursion_depth=0):
        """
        Generate new keys for this wallet and scan for UTXO's.

        :param scan_gap_limit: Amount of new keys and change keys (addresses) created for this wallet
        :type scan_gap_limit: int
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param change: Filter by change addresses. Set to True to include only change addresses, False to only include regular addresses. None (default) to disable filter and include both
        :param network: Network name. Leave empty for default network
        :type network: str

        :return:
        """

        if _keys_ignore is None:
            _keys_ignore = []

        if _recursion_depth > 10:
            raise WalletError("UTXO scanning has reached a recursion depth of more then 10")
        if self.scheme != 'bip44' and self.scheme != 'multisig':
            raise WalletError("The wallet scan() method is only available for BIP44 wallets")

        # FIXME: This removes to much UTXO's, used keys are not scanned...
        # if not _recursion_depth:
        #     # Mark all UTXO's for this wallet as spend
        #     utxos = self._session.query(DbTransactionOutput).join(DbTransaction).join(DbKey). \
        #         filter(DbTransaction.wallet_id == self.wallet_id)
        #     if account_id is not None:
        #         utxos.filter(DbKey.account_id == account_id)
        #     for utxo_record in utxos.all():
        #         utxo_record.spent = True
        #     self._session.commit()

        _recursion_depth += 1
        if change != 1:
            scanned_keys = self.get_key(account_id, network, number_of_keys=scan_gap_limit)
            new_key_ids = [k.key_id for k in scanned_keys]
            nr_new_txs = 0
            new_key_ids = list(set(new_key_ids) - set(_keys_ignore))
            n_highest_updated = 0
            for new_key_id in new_key_ids:
                n_new = self.transactions_update(change=0, key_id=new_key_id)
                if n_new:
                    n_highest_updated = new_key_id if n_new and n_highest_updated < new_key_id else n_highest_updated
                nr_new_txs += n_new
            for key_id in [key_id for key_id in new_key_ids if key_id < n_highest_updated]:
                self._session.query(DbKey).filter_by(id=key_id).update({'used': True})
            self._session.commit()

            _keys_ignore += new_key_ids
            if nr_new_txs:
                self.scan(scan_gap_limit, account_id, change=0, network=network, _keys_ignore=_keys_ignore,
                          _recursion_depth=_recursion_depth)
        if change != 0:
            scanned_keys_change = self.get_key(account_id, network, change=1, number_of_keys=scan_gap_limit)
            new_key_ids = [k.key_id for k in scanned_keys_change]
            nr_new_txs = 0
            new_key_ids = list(set(new_key_ids) - set(_keys_ignore))
            n_highest_updated = 0
            for new_key_id in new_key_ids:
                n_new = self.transactions_update(change=1, key_id=new_key_id)
                if n_new:
                    n_highest_updated = new_key_id if n_new and n_highest_updated < new_key_id else n_highest_updated
                nr_new_txs += n_new
            for key_id in [key_id for key_id in new_key_ids if key_id < n_highest_updated]:
                self._session.query(DbKey).filter_by(id=key_id).update({'used': True})
            self._session.commit()

            _keys_ignore += new_key_ids
            if nr_new_txs:
                self.scan(scan_gap_limit, account_id, change=1, network=network, _keys_ignore=_keys_ignore,
                          _recursion_depth=_recursion_depth)

    def get_key(self, account_id=None, network=None, number_of_keys=1, change=0, depth_of_keys=5):
        """
        Get a unused key or create a new one if there are no unused keys. 
        Returns a key from this wallet which has no transactions linked to it.
        
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param number_of_keys: Number of keys to return. Default is 1
        :type number_of_keys: int
        :param change: Payment (0) or change key (1). Default is 0
        :type change: int
        :param depth_of_keys: Depth of account keys. Default is 5 according to BIP44 standards
        :type depth_of_keys: int
        
        :return HDWalletKey: 
        """

        network, account_id, _ = self._get_account_defaults(network, account_id)
        keys_depth = depth_of_keys
        last_used_qr = self._session.query(DbKey).\
            filter_by(wallet_id=self.wallet_id, account_id=account_id, network_name=network,
                      used=True, change=change, depth=keys_depth).\
            order_by(DbKey.id.desc()).first()
        last_used_key_id = 0
        if last_used_qr:
            last_used_key_id = last_used_qr.id
        dbkey = self._session.query(DbKey).\
            filter_by(wallet_id=self.wallet_id, account_id=account_id, network_name=network,
                      used=False, change=change, depth=keys_depth).filter(DbKey.id > last_used_key_id).\
            order_by(DbKey.id.desc()).all()
        key_list = []
        for i in range(number_of_keys):
            if dbkey:
                dk = dbkey.pop()
                nk = HDWalletKey(dk.id, session=self._session)
            else:
                nk = self.new_key(account_id=account_id, network=network, change=change, max_depth=depth_of_keys)
            key_list.append(nk)
        if len(key_list) == 1:
            return key_list[0]
        else:
            return key_list

    def get_keys(self, account_id=None, network=None, change=0, depth_of_keys=5):
        """
        Get a unused key or create a new one if there are no unused keys.
        Returns a key from this wallet which has no transactions linked to it.

        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param change: Payment (0) or change key (1). Default is 0
        :type change: int
        :param depth_of_keys: Depth of account keys. Default is 5 according to BIP44 standards
        :type depth_of_keys: int

        :return HDWalletKey:
        """

        network, account_id, _ = self._get_account_defaults(network, account_id)
        keys_depth = depth_of_keys
        if self.scheme == 'multisig':
            keys_depth = 0
        dbkeys = self._session.query(DbKey). \
            filter_by(wallet_id=self.wallet_id, account_id=account_id, network_name=network,
                      used=False, change=change, depth=keys_depth). \
            order_by(DbKey.id).all()
        unusedkeys = []
        for dk in dbkeys:
            unusedkeys.append(HDWalletKey(dk.id, session=self._session))
        return unusedkeys

    def get_key_change(self, account_id=None, network=None, number_of_keys=1, depth_of_keys=5):
        """
        Get a unused change key or create a new one if there are no unused keys. 
        Wrapper for the get_key method
        
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param number_of_keys: Number of keys to return. Default is 1
        :type number_of_keys: int
        :param depth_of_keys: Depth of account keys. Default is 5 according to BIP44 standards
        :type depth_of_keys: int
        
        :return HDWalletKey:  
        """

        return self.get_key(account_id=account_id, network=network, change=1, number_of_keys=number_of_keys,
                            depth_of_keys=depth_of_keys)

    def new_account(self, name='', account_id=None, network=None):
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

        if self.scheme != 'bip44':
            raise WalletError("We can only create new accounts for a wallet with a BIP44 key scheme")
        if self.main_key.depth != 0 or self.main_key.is_private is False:
            raise WalletError("A master private key of depth 0 is needed to create new accounts (%s)" %
                              self.main_key.wif)

        if network is None:
            network = self.network.network_name

        # Determine account_id and name
        if account_id is None:
            account_id = 0
            qr = self._session.query(DbKey). \
                filter_by(wallet_id=self.wallet_id, purpose=self.purpose, network_name=network). \
                order_by(DbKey.account_id.desc()).first()
            if qr:
                account_id = qr.account_id + 1
        if not name:
            name = 'Account #%d' % account_id
        if self.keys(account_id=account_id, depth=3, network=network):
            raise WalletError("Account with ID %d already exists for this wallet" % account_id)
        if name in [k.name for k in self.keys(network=network)]:
            raise WalletError("Account or key with name %s already exists for this wallet" % name)

        # Get root key of new account
        res = self.keys(depth=2, network=network)
        if not res:
            try:
                purposekey = self.key(self.keys(depth=1)[0].id)
                bip44_cointype = Network(network).bip44_cointype
                duplicate_cointypes = [Network(x).network_name for x in self.network_list() if
                                       Network(x).bip44_cointype == bip44_cointype]
                if duplicate_cointypes:
                    raise WalletError("Can not create new account for network %s with same BIP44 cointype: %s" %
                                      (network, duplicate_cointypes))
                accrootkey_obj = self._create_keys_from_path(
                    purposekey, ["%s'" % str(bip44_cointype)], name=network, wallet_id=self.wallet_id,
                    account_id=account_id, network=network, purpose=self.purpose, basepath=purposekey.path,
                    session=self._session)
            except IndexError:
                raise WalletError("No key found for this wallet_id and purpose. Can not create new"
                                  "account for this wallet, is there a master key imported?")
        else:
            accrootkey = res[0]
            accrootkey_obj = self.key(accrootkey.id)

        # Create new account addresses and return main account key
        newpath = [str(account_id) + "'"]
        acckey = self._create_keys_from_path(
            accrootkey_obj, newpath, name=name, wallet_id=self.wallet_id,  account_id=account_id,
            network=network, purpose=self.purpose, basepath=accrootkey_obj.path, session=self._session
        )
        self._create_keys_from_path(
            acckey, ['0'], name=acckey.name + ' Payments', wallet_id=self.wallet_id, account_id=account_id,
            network=network, purpose=self.purpose, basepath=acckey.path,  session=self._session)
        self._create_keys_from_path(
            acckey, ['1'], name=acckey.name + ' Change', wallet_id=self.wallet_id, account_id=account_id,
            network=network, purpose=self.purpose, basepath=acckey.path, session=self._session)
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
                raise WalletError("Cannot create key with different purpose field (%d) as existing wallet (%d)" %
                                  (purpose, self.purpose))
            cointype = int(pathdict['cointype'].replace("'", ""))
            wallet_cointypes = [Network(nw).bip44_cointype for nw in self.network_list()]
            if cointype not in wallet_cointypes:
                raise WalletError("Network / cointype %s not available in this wallet, please create an account for "
                                  "this network first. Or disable BIP checks." % cointype)
            if pathdict['cointype'][-1] != "'" or pathdict['purpose'][-1] != "'" or pathdict['account'][-1] != "'":
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
        if rkey and rkey.path == path:
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

    def keys(self, account_id=None, name=None, key_id=None, change=None, depth=None, used=None, is_private=None,
             has_balance=None, is_active=True, network=None, as_dict=False):
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
        :param used: Only return used or unused keys
        :type used: bool
        :param is_private: Only return private keys
        :type is_private: bool
        :param has_balance: Only include keys with a balance or without a balance, default is both
        :type has_balance: bool
        :param is_active: Hide inactive keys. Only include active keys with either a balance or which are unused, default is True
        :type is_active: bool
        :param network: Network name filter
        :type network: str
        :param as_dict: Return keys as dictionary objects. Default is False: DbKey objects
        
        :return list: List of Keys
        """

        qr = self._session.query(DbKey).filter_by(wallet_id=self.wallet_id).order_by(DbKey.id)
        if network is not None:
            qr = qr.filter(DbKey.network_name == network)
        if account_id is not None:
            qr = qr.filter(DbKey.account_id == account_id)
            if self.scheme == 'bip44' and depth is None:
                qr = qr.filter(DbKey.depth >= 3)
        if change is not None:
            qr = qr.filter(DbKey.change == change)
            if self.scheme == 'bip44' and depth is None:
                qr = qr.filter(DbKey.depth > 4)
        if depth is not None:
            qr = qr.filter(DbKey.depth == depth)
        if name is not None:
            qr = qr.filter(DbKey.name == name)
        if key_id is not None:
            qr = qr.filter(DbKey.id == key_id)
            is_active = False
        elif used is not None:
            qr = qr.filter(DbKey.used == used)
        if is_private is not None:
            qr = qr.filter(DbKey.is_private == is_private)
        if has_balance is True and is_active is True:
            raise WalletError("Cannot use has_balance and hide_unused parameter together")
        if has_balance is not None:
            if has_balance:
                qr = qr.filter(DbKey.balance != 0)
            else:
                qr = qr.filter(DbKey.balance == 0)
        if is_active:  # Unused keys and keys with a balance
            qr = qr.filter(or_(DbKey.balance != 0, DbKey.used == False))
        ret = as_dict and [x.__dict__ for x in qr.all()] or qr.all()
        qr.session.close()
        return ret

    def keys_networks(self, used=None, as_dict=False):
        """
        Get keys of defined networks for this wallet. Wrapper for the keys() method

        :param used: Only return used or unused keys
        :type used: bool
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        
        """

        if self.scheme != 'bip44':
            raise WalletError("The 'keys_network' method can only be used with BIP44 type wallets")
        res = self.keys(depth=2, used=used, as_dict=as_dict)
        if not res:
            res = self.keys(depth=3, used=used, as_dict=as_dict)
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

    def keys_addresses(self, account_id=None, used=None, network=None, depth=5, as_dict=False):
        """
        Get address-keys of specified account_id for current wallet. Wrapper for the keys() methods.

        :param account_id: Account ID
        :type account_id: int
        :param used: Only return used or unused keys
        :type used: bool
        :param network: Network name filter
        :type network: str
        :param depth: Filter by key depth. Default for BIP44 and multisig is 5
        :type depth: int
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        """

        return self.keys(account_id, depth=depth, used=used, network=network, as_dict=as_dict)

    def keys_address_payment(self, account_id=None, used=None, network=None, as_dict=False):
        """
        Get payment addresses (change=0) of specified account_id for current wallet. Wrapper for the keys() methods.

        :param account_id: Account ID
        :type account_id: int
        :param used: Only return used or unused keys
        :type used: bool
        :param network: Network name filter
        :type network: str
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        """

        return self.keys(account_id, depth=5, change=0, used=used, network=network, as_dict=as_dict)

    def keys_address_change(self, account_id=None, used=None, network=None, as_dict=False):
        """
        Get payment addresses (change=1) of specified account_id for current wallet. Wrapper for the keys() methods.

        :param account_id: Account ID
        :type account_id: int
        :param used: Only return used or unused keys
        :type used: bool
        :param network: Network name filter
        :type network: str
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        """

        return self.keys(account_id, depth=5, change=1, used=used, network=network, as_dict=as_dict)

    def addresslist(self, account_id=None, used=None, network=None, change=None, depth=5, key_id=None):
        """
        Get list of addresses defined in current wallet

        :param account_id: Account ID
        :type account_id: int
        :param used: Only return used or unused keys
        :type used: bool, None
        :param network: Network name filter
        :type network: str
        :param change: Only include change addresses or not. Default is None which returns both
        :param depth: Filter by key depth
        :type depth: int
        :param key_id: Key ID to get address of just 1 key
        :type key_id: int
        
        :return list: List of address strings
        """

        addresslist = []
        for key in self.keys(account_id=account_id, depth=depth, used=used, network=network, change=change,
                             key_id=key_id, is_active=False):
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

    def account(self, account_id):
        """
        Returns wallet key of specific BIP44 account.

        Account keys have a BIP44 path depth of 3 and have the format m/purpose'/network'/account'

        I.e: Use account(0).key().wif_public() to get wallet's public account key

        :param account_id: ID of account. Default is 0
        :type account_id: int

        :return HDWalletKey:

        """
        qr = self._session.query(DbKey).\
            filter_by(wallet_id=self.wallet_id, purpose=self.purpose, network_name=self.network.network_name,
                      account_id=account_id, depth=3).scalar()
        if not qr:
            raise WalletError("Account with ID %d not found in this wallet" % account_id)
        key_id = qr.id
        return HDWalletKey(key_id, session=self._session)

    def accounts(self, network=None):
        """
        Get list of accounts for this wallet
        
        :param network: Network name filter
        :type network: str
                
        :return list: List of accounts as HDWalletKey objects
        """

        accounts = []
        if self.scheme == 'multisig':
            for wlt in self.cosigner:
                if wlt.main_key.is_private:
                    accounts.append(HDWalletKey(wlt.main_key.key_id, self._session))
        else:
            wks = self.keys_accounts(network=network)

            for wk in wks:
                accounts.append(HDWalletKey(wk.id, self._session))
        return accounts

    def networks(self):
        """
        Get list of networks used by this wallet
        
        :return: List of networks as dictionary
        """

        if self.scheme == 'bip44':
            wks = self.keys_networks(as_dict=True)
            for wk in wks:
                if '_sa_instance_state' in wk:
                    del wk['_sa_instance_state']
            return wks
        else:
            return [self.network.__dict__]

    def network_list(self, field='network_name'):
        """
        Wrapper for networks methods, returns a flat list with currently used
        networks for this wallet.
        
        :return: list 
        """

        return [x[field] for x in self.networks()]

    def balance_update_from_serviceprovider(self, account_id=None, network=None):
        """
        Update balance of currents account addresses using default Service objects getbalance method. Update total 
        wallet balance in database. 
        
        Please Note: Does not update UTXO's or the balance per key! For this use the 'updatebalance' method
        instead
        
        :param account_id: Account ID. Leave empty for default account
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        
        :return: 
        """

        network, account_id, acckey = self._get_account_defaults(network, account_id)
        balance = Service(network=network).getbalance(self.addresslist(account_id=account_id, network=network))
        if balance:
            new_balance = {
                'account_id': account_id,
                'network': network,
                'balance': balance
            }
            old_balance_item = [bi for bi in self._balances if bi['network'] == network and bi['account_id'] == account_id]
            if old_balance_item:
                item_n = self._balances.index(old_balance_item[0])
                self._balances[item_n] = new_balance
            else:
                self._balances.append(new_balance)
        return balance

    def balance(self, account_id=None, network=None, as_string=False):
        """
        Get total of unspent outputs

        :param account_id: Account ID filter
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param as_string: Set True to return a string in currency format. Default returns float.
        :type as_string: boolean

        :return float, str: Key balance
        """

        self._balance_update(account_id, network)
        network, account_id, _ = self._get_account_defaults(network, account_id)

        balance = 0
        b_res = [b['balance'] for b in self._balances if b['account_id'] == account_id and b['network'] == network]
        if len(b_res):
            balance = b_res[0]
        if as_string:
            return Network(network).print_value(balance)
        else:
            return balance

    def _balance_update(self, account_id=None, network=None, key_id=None, min_confirms=0):
        """
        Update balance from UTXO's in database. To get most recent balance update UTXO's first.
        
        Also updates balance of wallet and keys in this wallet for the specified account or all accounts if
        no account is specified.
        
        :param account_id: Account ID filter
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param key_id: Key ID Filter
        :type key_id: int
        :param min_confirms: Minimal confirmations needed to include in balance (default = 1)
        :type min_confirms: int

        :return: Updated balance
        """

        qr = self._session.query(DbTransactionOutput, func.sum(DbTransactionOutput.value), DbKey.network_name,
                                 DbKey.account_id).\
            join(DbTransaction).join(DbKey). \
            filter(DbTransactionOutput.spent.op("IS")(False),
                   DbTransaction.wallet_id == self.wallet_id,
                   DbTransaction.confirmations >= min_confirms)
        if account_id is not None:
            qr = qr.filter(DbKey.account_id == account_id)
        if network is not None:
            qr = qr.filter(DbKey.network_name == network)
        if key_id is not None:
            qr = qr.filter(DbKey.id == key_id)
        utxos = qr.group_by(DbTransactionOutput.key_id).all()

        key_values = [
            {
                'id': utxo[0].key_id,
                'network': utxo[2],
                'account_id': utxo[3],
                'balance': utxo[1]
            }
            for utxo in utxos
        ]

        grouper = itemgetter("network", "account_id")
        balance_list = []
        for key, grp in groupby(sorted(key_values, key=grouper), grouper):
            nw_acc_dict = dict(zip(["network", "account_id"], key))
            nw_acc_dict["balance"] = sum(item["balance"] for item in grp)
            balance_list.append(nw_acc_dict)

        # Add keys with no UTXO's with 0 balance
        for key in self.keys(account_id=account_id, network=network, key_id=key_id):
            if key.id not in [utxo[0].key_id for utxo in utxos]:
                key_values.append({
                    'id': key.id,
                    'account_id': key.account_id,
                    'balance': 0
                })

        if not key_id:
            for bl in balance_list:
                bl_item = [b for b in self._balances if
                           b['network'] == bl['network'] and b['account_id'] == bl['account_id']]
                if not bl_item:
                    self._balances.append(bl)
                    continue
                lx = self._balances.index(bl_item[0])
                self._balances[lx].update(bl)

        self._balance = sum([b['balance'] for b in balance_list if b['network'] == self.network.network_name])

        # Bulk update database
        self._session.bulk_update_mappings(DbKey, key_values)
        self._session.commit()
        _logger.info("Got balance for %d key(s)" % len(key_values))
        return self._balances

    def utxos_update(self, account_id=None, used=None, networks=None, key_id=None, depth=None, change=None,
                     utxos=None, update_balance=True):
        """
        Update UTXO's (Unspent Outputs) in database of given account using the default Service object.
        
        Delete old UTXO's which are spent and append new UTXO's to database.

        For usage on an offline PC, you can import utxos with the utxos parameter as a list of dictionaries:
        [{
            'address': 'n2S9Czehjvdmpwd2YqekxuUC1Tz5ZdK3YN',
            'script': '',
            'confirmations': 10,
            'output_n': 1,
            'tx_hash': '9df91f89a3eb4259ce04af66ad4caf3c9a297feea5e0b3bc506898b6728c5003',
            'value': 8970937
        }]

        :param account_id: Account ID
        :type account_id: int
        :param used: Only check for UTXO for used or unused keys. Default is both
        :type used: bool
        :param networks: Network name filter as string or list of strings. Leave empty to update all used networks in wallet
        :type networks: str, list
        :param key_id: Key ID to just update 1 key
        :type key_id: int
        :param depth: Only update keys with this depth, default is depth 5 according to BIP0048 standard. Set depth to None to update all keys of this wallet.
        :type depth: int
        :param change: Only update change or normal keys, default is both (None)
        :type change: int
        :param utxos: List of unspent outputs in dictionary format specified in this method DOC header
        :type utxos: list
        :param update_balance: Option to disable balance update after fetching UTXO's, used when utxos_update method is called several times in a row. Default is True
        :type update_balance: bool
        :return int: Number of new UTXO's added 
        """

        if key_id:
            kobj = self.key(key_id)
            networks = [kobj.network_name]
            account_id = kobj.account_id
        if networks is None:
            networks = self.network_list()
        elif not isinstance(networks, list):
            networks = [networks]
        elif len(networks) != 1 and utxos is not None:
            raise WalletError("Please specify maximum 1 network when passing utxo's")

        count_utxos = 0
        for network in networks:
            if account_id is None:
                accounts = [k.account_id for k in self.accounts(network=network)]
                if not accounts:
                    accounts = [self.default_account_id]
            else:
                accounts = [account_id]
            for account_id in accounts:
                _, _, acckey = self._get_account_defaults(network, account_id, key_id)
                # TODO: implement bip45/67/electrum/?
                schemes_key_depth = {
                    'bip44': 5,
                    'single': 0,
                    'electrum': 4,
                    'multisig': 0
                }
                if depth is None:
                    if self.scheme == 'bip44' or self.scheme == 'multisig':
                        depth = 5
                    else:
                        depth = 0

                if utxos is None:
                    # Get all UTXO's for this wallet from default Service object
                    addresslist = self.addresslist(account_id=account_id, used=used, network=network, key_id=key_id,
                                                   change=change, depth=depth)
                    random.shuffle(addresslist)
                    srv = Service(network=network)
                    utxos = srv.getutxos(addresslist)
                    if utxos is False:
                        raise WalletError("No response from any service provider, could not update UTXO's. "
                                          "Errors: %s" % srv.errors)

                # Get current UTXO's from database to compare with Service objects UTXO's
                current_utxos = self.utxos(account_id=account_id, network=network, key_id=key_id)

                # Update spent UTXO's (not found in list) and mark key as used
                utxos_tx_hashes = [(x['tx_hash'], x['output_n']) for x in utxos]
                for current_utxo in current_utxos:
                    if (current_utxo['tx_hash'], current_utxo['output_n']) not in utxos_tx_hashes:
                        utxo_in_db = self._session.query(DbTransactionOutput).join(DbTransaction). \
                            filter(DbTransaction.hash == current_utxo['tx_hash'],
                                   DbTransactionOutput.output_n == current_utxo['output_n'])
                        for utxo_record in utxo_in_db.all():
                            utxo_record.spent = True
                    self._session.commit()

                # If UTXO is new, add to database otherwise update depth (confirmation count)
                for utxo in utxos:
                    key = self._session.query(DbKey).\
                        filter_by(wallet_id=self.wallet_id, address=utxo['address']).scalar()
                    if not key:
                        raise WalletError("Key with address %s not found in this wallet" % utxo['address'])
                    key.used = True
                    status = 'unconfirmed'
                    if utxo['confirmations']:
                        status = 'confirmed'

                    # Update confirmations in db if utxo was already imported
                    # TODO: Add network filter (?)
                    transaction_in_db = self._session.query(DbTransaction).filter_by(wallet_id=self.wallet_id,
                                                                                     hash=utxo['tx_hash'])
                    utxo_in_db = self._session.query(DbTransactionOutput).join(DbTransaction).\
                        filter(DbTransaction.wallet_id == self.wallet_id,
                               DbTransaction.hash == utxo['tx_hash'],
                               DbTransactionOutput.output_n == utxo['output_n'])
                    if utxo_in_db.count():
                        utxo_record = utxo_in_db.scalar()
                        if not utxo_record.key_id:
                            count_utxos += 1
                        utxo_record.key_id = key.id
                        utxo_record.spent = False
                        transaction_record = transaction_in_db.scalar()
                        transaction_record.confirmations = utxo['confirmations']
                        transaction_record.status = status
                    else:
                        # Add transaction if not exist and then add output
                        if not transaction_in_db.count():
                            new_tx = DbTransaction(wallet_id=self.wallet_id, hash=utxo['tx_hash'], status=status,
                                                   confirmations=utxo['confirmations'])
                            self._session.add(new_tx)
                            self._session.commit()
                            tid = new_tx.id
                        else:
                            tid = transaction_in_db.scalar().id

                        new_utxo = DbTransactionOutput(transaction_id=tid,  output_n=utxo['output_n'], value=utxo['value'],
                                                       key_id=key.id, script=utxo['script'], spent=False)
                        self._session.add(new_utxo)
                        count_utxos += 1

                    self._session.commit()

                _logger.info("Got %d new UTXOs for account %s" % (count_utxos, account_id))
                self._session.commit()
                if update_balance:
                    self._balance_update(account_id=account_id, network=network, key_id=key_id, min_confirms=0)
                utxos = None
        return count_utxos

    def utxos(self, account_id=None, network=None, min_confirms=0, key_id=None):
        """
        Get UTXO's (Unspent Outputs) from database. Use utxos_update method first for updated values
        
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

        network, account_id, acckey = self._get_account_defaults(network, account_id, key_id)

        qr = self._session.query(DbTransactionOutput, DbKey.address, DbTransaction.confirmations, DbTransaction.hash,
                                 DbKey.network_name).\
            join(DbTransaction).join(DbKey). \
            filter(DbTransactionOutput.spent.op("IS")(False),
                   DbKey.account_id == account_id,
                   DbTransaction.wallet_id == self.wallet_id,
                   DbKey.network_name == network,
                   DbTransaction.confirmations >= min_confirms)
        if key_id is not None:
            qr = qr.filter(DbKey.id == key_id)
        utxos = qr.order_by(DbTransaction.confirmations.desc()).all()
        res = []
        for utxo in utxos:
            u = utxo[0].__dict__
            if '_sa_instance_state' in u:
                del u['_sa_instance_state']
            u['address'] = utxo[1]
            u['confirmations'] = int(utxo[2])
            u['tx_hash'] = utxo[3]
            u['network_name'] = utxo[4]
            res.append(u)
        return res

    def transactions_update(self, account_id=None, used=None, network=None, key_id=None, depth=None, change=None):
        """
        Update wallets transaction from service providers. Get all transactions for known keys in this wallet.
        The balances and unspent outputs (UTXO's) are updated as well, but for large wallets use the utxo_update
        method if possible.

        :param account_id: Account ID
        :type account_id: int
        :param used: Only update used or unused keys, specify None to update both. Default is None
        :type used: bool, None
        :param network: Network name. Leave empty for default network
        :type network: str
        :param key_id: Key ID to just update 1 key
        :type key_id: int
        :param depth: Only update keys with this depth, default is depth 5 according to BIP0048 standard. Set depth to None to update all keys of this wallet.
        :type depth: int
        :param change: Only update change or normal keys, default is both (None)
        :type change: int

        :return bool: True if all transactions are updated

        """

        network, account_id, acckey = self._get_account_defaults(network, account_id, key_id)
        if depth is None:
            if self.scheme == 'bip44':
                depth = 5
            elif self.scheme == 'multisig':
                depth = 5
                account_id = None
            else:
                depth = 0
        addresslist = self.addresslist(account_id=account_id, used=used, network=network, key_id=key_id,
                                       change=change, depth=depth)
        srv = Service(network=network)
        txs = srv.gettransactions(addresslist)
        if txs is False:
            raise WalletError("No response from any service provider, could not update transactions")
        utxo_set = set()
        for t in txs:
            wt = HDWalletTransaction.from_transaction(self, t)
            wt.save()
            utxos = [(to_hexstring(ti.prev_hash), ti.output_n_int) for ti in wt.inputs]
            utxo_set.update(utxos)

        for utxo in list(utxo_set):
            tos = self._session.query(DbTransactionOutput).join(DbTransaction).\
                filter(DbTransaction.hash == utxo[0], DbTransactionOutput.output_n == utxo[1],
                       DbTransactionOutput.spent.op("IS")(False)).all()
            for u in tos:
                u.spent = True
        self._session.commit()
        self._balance_update(account_id=account_id, network=network, key_id=key_id, min_confirms=0)

        return len(txs)

    def transactions(self, account_id=None, network=None, include_new=False, key_id=None):
        """
        :param account_id: Filter by Account ID. Leave empty for default account_id
        :type account_id: int
        :param network: Filter by network name. Leave empty for default network
        :type network: str
        :param include_new: Also include new and incomplete transactions in list. Default is False
        :type include_new: bool
        :param key_id: Filter by key ID
        :type key_id: int

        :return list: List of transactions as dictionary
        """

        network, account_id, acckey = self._get_account_defaults(network, account_id, key_id)

        qr = self._session.query(DbTransactionInput, DbKey.address, DbTransaction.confirmations,
                                 DbTransaction.hash, DbKey.network_name, DbTransaction.status). \
            join(DbTransaction).join(DbKey). \
            filter(DbKey.account_id == account_id,
                   DbTransaction.wallet_id == self.wallet_id,
                   DbKey.network_name == network)
        if key_id is not None:
            qr = qr.filter(DbKey.id == key_id)
        if not include_new:
            qr = qr.filter(or_(DbTransaction.status == 'confirmed', DbTransaction.status == 'unconfirmed'))

        txs = qr.all()

        qr = self._session.query(DbTransactionOutput, DbKey.address, DbTransaction.confirmations,
                                 DbTransaction.hash, DbKey.network_name, DbTransaction.status). \
            join(DbTransaction).join(DbKey). \
            filter(DbKey.account_id == account_id,
                   DbTransaction.wallet_id == self.wallet_id,
                   DbKey.network_name == network)
        if not include_new:
            qr = qr.filter(or_(DbTransaction.status == 'confirmed', DbTransaction.status == 'unconfirmed'))

        if key_id is not None:
            qr = qr.filter(DbKey.id == key_id)
        txs += qr.all()

        txs = sorted(txs, key=lambda k: (k[2], pow(10, 20)-k[0].transaction_id, k[3]), reverse=True)

        res = []
        for tx in txs:
            u = tx[0].__dict__
            if '_sa_instance_state' in u:
                del u['_sa_instance_state']
            u['address'] = tx[1]
            u['confirmations'] = int(tx[2])
            u['tx_hash'] = tx[3]
            u['network_name'] = tx[4]
            u['status'] = tx[5]
            if 'index_n' in u:
                u['value'] = -u['value']
            res.append(u)
        return res

    def transaction_create(self, output_arr, input_arr=None, account_id=None, network=None, fee=None,
                           min_confirms=0, max_utxos=None):
        """
            Create new transaction with specified outputs. 
            Inputs can be specified but if not provided they will be selected from wallets utxo's.
            Output array is a list of 1 or more addresses and amounts.

            :param output_arr: List of output tuples with address and amount. Must contain at least one item. Example: [('mxdLD8SAGS9fe2EeCXALDHcdTTbppMHp8N', 5000000)] 
            :type output_arr: list 
            :param input_arr: List of inputs tuples with reference to a UTXO, a wallet key and value. The format is [(tx_hash, output_n, key_ids, value, signatures, unlocking_script, address)]
            :type input_arr: list
            :param account_id: Account ID
            :type account_id: int
            :param network: Network name. Leave empty for default network
            :type network: str
            :param fee: Set fee manually, leave empty to calculate fees automatically. Set fees in smallest currency denominator, for example satoshi's if you are using bitcoins
            :type fee: int
            :param min_confirms: Minimal confirmation needed for an UTXO before it will included in inputs. Default is 0 confirmations. Option is ignored if input_arr is provided.
            :type min_confirms: int
            :param max_utxos: Maximum number of UTXO's to use. Set to 1 for optimal privacy. Default is None: No maximum
            :type max_utxos: int

            :return HDWalletTransaction: object
        """

        def _select_inputs(amount, variance=0):
            utxo_query = self._session.query(DbTransactionOutput).join(DbTransaction).join(DbKey). \
                filter(DbTransaction.wallet_id == self.wallet_id, DbKey.account_id == account_id,
                       DbKey.network_name == network,
                       DbTransactionOutput.spent.op("IS")(False), DbTransaction.confirmations >= min_confirms). \
                order_by(DbTransaction.confirmations.desc())
            utxos = utxo_query.all()
            if not utxos:
                raise WalletError("Create transaction: No unspent transaction outputs found")

            # TODO: Find 1 or 2 UTXO's with exact amount +/- self.network.dust_amount

            # Try to find one utxo with exact amount
            one_utxo = utxo_query.filter(DbTransactionOutput.spent.op("IS")(False),
                                         DbTransactionOutput.value >= amount,
                                         DbTransactionOutput.value <= amount + variance).first()
            if one_utxo:
                return [one_utxo]

            # Try to find one utxo with higher amount
            one_utxo = utxo_query. \
                filter(DbTransactionOutput.spent.op("IS")(False), DbTransactionOutput.value >= amount).\
                order_by(DbTransactionOutput.value).first()
            if one_utxo:
                return [one_utxo]
            elif max_utxos and max_utxos <= 1:
                _logger.info("No single UTXO found with requested amount, use higher 'max_utxo' setting to use "
                             "multiple UTXO's")
                return []

            # Otherwise compose of 2 or more lesser outputs
            lessers = utxo_query. \
                filter(DbTransactionOutput.spent.op("IS")(False), DbTransactionOutput.value < amount).\
                order_by(DbTransactionOutput.value.desc()).all()
            total_amount = 0
            selected_utxos = []
            for utxo in lessers[:max_utxos]:
                if total_amount < amount:
                    selected_utxos.append(utxo)
                    total_amount += utxo.value
            if total_amount < amount:
                return []
            return selected_utxos

        def _objects_by_key_id(key_id):
            key = self._session.query(DbKey).filter_by(id=key_id).scalar()
            if not key:
                raise WalletError("Key '%s' not found in this wallet" % key_id)
            if key.key_type == 'multisig':
                inp_keys = []
                for ck in key.multisig_children:
                    # TODO:  CHECK THIS
                    inp_keys.append(HDKey(ck.child_key.wif, network=ck.child_key.network_name).key)
                script_type = 'p2sh_multisig'
            elif key.key_type in ['bip32', 'single']:
                inp_keys = HDKey(key.wif, compressed=key.compressed, network=key.network_name).key
                script_type = 'p2pkh'
            else:
                raise WalletError("Input key type %s not supported" % key.key_type)
            return inp_keys, script_type, key

        amount_total_output = 0
        network, account_id, acckey = self._get_account_defaults(network, account_id)

        if input_arr and max_utxos and len(input_arr) > max_utxos:
            raise WalletError("Input array contains %d UTXO's but max_utxos=%d parameter specified" %
                              (len(input_arr), max_utxos))

        # Create transaction and add outputs
        transaction = HDWalletTransaction(hdwallet=self, network=network)
        if not isinstance(output_arr, list):
            raise WalletError("Output array must be a list of tuples with address and amount. "
                              "Use 'send_to' method to send to one address")
        for o in output_arr:
            if isinstance(o, Output):
                transaction.outputs.append(o)
                amount_total_output += o.value
            else:
                amount_total_output += o[1]
                transaction.add_output(o[1], o[0])

        srv = Service(network=network)
        transaction.fee_per_kb = None
        if fee is None:
            if not input_arr:
                transaction.fee_per_kb = srv.estimatefee()
                fee_estimate = (transaction.estimate_size() / 1024.0 * transaction.fee_per_kb)
            else:
                fee_estimate = 0
        else:
            fee_estimate = fee

        # Add inputs
        amount_total_input = 0
        if input_arr is None:
            selected_utxos = _select_inputs(amount_total_output + fee_estimate, self.network.dust_amount)
            if not selected_utxos:
                raise WalletError("Not enough unspent transaction outputs found")
            for utxo in selected_utxos:
                amount_total_input += utxo.value
                inp_keys, script_type, key = _objects_by_key_id(utxo.key_id)
                transaction.add_input(utxo.transaction.hash, utxo.output_n, keys=inp_keys, script_type=script_type,
                                      sigs_required=self.multisig_n_required, sort=self.sort_keys,
                                      compressed=key.compressed, value=utxo.value)
        else:
            for inp in input_arr:
                if isinstance(inp, Input):
                    prev_hash = inp.prev_hash
                    output_n = inp.output_n
                    key_id = None
                    value = inp.value
                    signatures = inp.signatures
                    unlocking_script = inp.unlocking_script
                    address = inp.address
                else:
                    prev_hash = inp[0]
                    output_n = inp[1]
                    key_id = None if len(inp) <= 2 else inp[2]
                    value = 0 if len(inp) <= 3 else inp[3]
                    signatures = None if len(inp) <= 4 else inp[4]
                    unlocking_script = b'' if len(inp) <= 5 else inp[5]
                    address = '' if len(inp) <= 6 else inp[6]
                # Get key_ids, value from Db if not specified
                if not (key_id and value):
                    if not isinstance(output_n, int):
                        output_n = struct.unpack('>I', output_n)[0]
                    inp_utxo = self._session.query(DbTransactionOutput).join(DbTransaction).join(DbKey). \
                        filter(DbTransaction.wallet_id == self.wallet_id,
                               DbTransaction.hash == to_hexstring(prev_hash),
                               DbTransactionOutput.output_n == output_n).first()
                    if inp_utxo:
                        key_id = inp_utxo.key_id
                        value = inp_utxo.value
                    else:
                        _logger.info("UTXO %s not found in this wallet. Please update UTXO's if othis is not an "
                                     "offline wallet" % to_hexstring(prev_hash))
                        key_id = self._session.query(DbKey.id).\
                            filter(DbKey.wallet_id == self.wallet_id, DbKey.address == address).scalar()
                        if not key_id:
                            raise WalletError("UTXO %s and key with address %s not found in this wallet" % (
                                to_hexstring(prev_hash), address))
                        if not value:
                            raise WalletError("Input value is zero for address %s. Import or update UTXO's first "
                                              "or import transaction as dictionary" % address)

                amount_total_input += value
                inp_keys, script_type, key = _objects_by_key_id(key_id)
                transaction.add_input(prev_hash, output_n, keys=inp_keys, script_type=script_type,
                                      sigs_required=self.multisig_n_required, sort=self.sort_keys,
                                      compressed=key.compressed, value=value, signatures=signatures,
                                      unlocking_script=unlocking_script)

        # Calculate fees
        transaction.fee = fee
        fee_per_output = None
        tr_size = transaction.estimate_size()
        if fee is None:
            if not input_arr:
                transaction.fee_per_kb = srv.estimatefee()
                if transaction.fee_per_kb is False:
                    raise WalletError("Could not estimate transaction fees, please specify fees manually")
                transaction.fee = int((tr_size / 1024.0) * transaction.fee_per_kb)
                fee_per_output = int((50 / 1024.0) * transaction.fee_per_kb)
            else:
                if amount_total_output and amount_total_input:
                    fee = False
                else:
                    transaction.fee = 0

        if fee is False:
            transaction.change = 0
            transaction.fee = int(amount_total_input - amount_total_output)
        else:
            transaction.change = int(amount_total_input - (amount_total_output + transaction.fee))

        if transaction.change < 0:
            raise WalletError("Total amount of outputs is greater then total amount of inputs")
        # Skip change if amount is smaller then the dust limit or estimated fee
        if (fee_per_output and transaction.change < fee_per_output) or transaction.change < self.network.dust_amount:
            transaction.fee += transaction.change
            transaction.change = 0
        if transaction.change:
            ck = self.get_key(account_id=account_id, network=network, change=1)
            on = transaction.add_output(transaction.change, ck.address)
            transaction.outputs[on].key_id = ck.key_id
            amount_total_output += transaction.change

        # TODO: Extra check for ridiculous fees
        # if (amount_total_input - amount_total_output) > tr_size * MAXIMUM_FEE_PER_KB

        return transaction

    def transaction_import(self, t):
        """
        Import a Transaction into this wallet. Link inputs to wallet keys if possible and return HDWalletTransaction
        object. Only imports Transaction objects or dictionaries, use transaction_import_raw method to import a
        raw transaction.

        :param t: A Transaction object or dictionary
        :type t: Transaction, dict

        :return HDWalletTransaction:

        """
        if isinstance(t, Transaction):
            rt = self.transaction_create(t.outputs, t.inputs, fee=t.fee, network=t.network.network_name)
        elif isinstance(t, dict):
            output_arr = []
            for o in t['outputs']:
                output_arr.append((o['address'], int(o['value'])))
            input_arr = []

            for i in t['inputs']:
                signatures = [to_bytes(sig) for sig in i['signatures']]
                script = b'' if 'script' not in i else i['script']
                address = '' if 'address' not in i else i['address']
                input_arr.append((i['prev_hash'], i['output_n'], None, int(i['value']), signatures, script,
                                  address))
            rt = self.transaction_create(output_arr, input_arr, fee=t['fee'], network=t['network'])
        else:
            raise WalletError("Import transaction must be of type Transaction or dict")
        rt.verify()
        return rt

    def transaction_import_raw(self, raw_tx, network=None):
        """
        Import a raw transaction. Link inputs to wallet keys if possible and return HDWalletTransaction object

        :param raw_tx: Raw transaction
        :type raw_tx: str, bytes
        :param network: Network name. Leave empty for default network
        :type network: str

        :return HDWalletTransaction:

        """
        if network is None:
            network = self.network.network_name
        t_import = Transaction.import_raw(raw_tx, network=network)
        rt = self.transaction_create(t_import.outputs, t_import.inputs, network=network)
        rt.verify()
        return rt

    def send(self, output_arr, input_arr=None, account_id=None, network=None, fee=None, min_confirms=0,
             priv_keys=None, max_utxos=None, offline=False):
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
        :param fee: Set fee manually, leave empty to calculate fees automatically. Set fees in smallest currency denominator, for example satoshi's if you are using bitcoins
        :type fee: int
        :param min_confirms: Minimal confirmation needed for an UTXO before it will included in inputs. Default is 0. Option is ignored if input_arr is provided.
        :type min_confirms: int
        :param priv_keys: Specify extra private key if not available in this wallet
        :type priv_keys: HDKey, list
        :param max_utxos: Maximum number of UTXO's to use. Set to 1 for optimal privacy. Default is None: No maximum
        :type max_utxos: int
        :param offline: Just return the transaction object and do not send it when offline = True. Default is False
        :type offline: bool

        :return HDWalletTransaction:
        """

        network, account_id, _ = self._get_account_defaults(network, account_id)
        if input_arr and max_utxos and len(input_arr) > max_utxos:
            raise WalletError("Input array contains %d UTXO's but max_utxos=%d parameter specified" %
                              (len(input_arr), max_utxos))

        transaction = self.transaction_create(output_arr, input_arr, account_id, network, fee,
                                              min_confirms, max_utxos)
        transaction.sign(priv_keys)
        # Calculate exact estimated fees and update change output if necessary
        if fee is None and transaction.fee_per_kb and transaction.change:
            fee_exact = transaction.calculate_fee()
            # Recreate transaction if fee estimation more then 10% off
            if fee_exact and abs((transaction.fee - fee_exact) / float(fee_exact)) > 0.10:
                _logger.info("Transaction fee not correctly estimated (est.: %d, real: %d). "
                             "Recreate transaction with correct fee" % (transaction.fee, fee_exact))
                transaction = self.transaction_create(output_arr, input_arr, account_id, network, fee_exact,
                                                      min_confirms, max_utxos)
                transaction.sign(priv_keys)

        transaction.send(offline)
        return transaction

    def send_to(self, to_address, amount, account_id=None, network=None, fee=None, min_confirms=0,
                priv_keys=None, offline=False):
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
        :param fee: Fee to use for this transaction. Leave empty to automatically estimate.
        :type fee: int
        :param min_confirms: Minimal confirmation needed for an UTXO before it will included in inputs. Default is 0. Option is ignored if input_arr is provided.
        :type min_confirms: int
        :param priv_keys: Specify extra private key if not available in this wallet
        :type priv_keys: HDKey, list
        :param offline: Just return the transaction object and do not send it when offline = True. Default is False
        :type offline: bool

        :return HDWalletTransaction:
        """

        outputs = [(to_address, amount)]
        return self.send(outputs, account_id=account_id, network=network, fee=fee,
                         min_confirms=min_confirms, priv_keys=priv_keys, offline=offline)

    def sweep(self, to_address, account_id=None, input_key_id=None, network=None, max_utxos=999, min_confirms=0,
              fee_per_kb=None, offline=False):
        """
        Sweep all unspent transaction outputs (UTXO's) and send them to one output address. 
        Wrapper for the send method.
        
        :param to_address: Single output address
        :type to_address: str
        :param account_id: Wallet's account ID
        :type account_id: int
        :param input_key_id: Limit sweep to UTXO's with this key_id
        :type input_key_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param max_utxos: Limit maximum number of outputs to use. Default is 999
        :type max_utxos: int
        :param min_confirms: Minimal confirmations needed to include utxo
        :type min_confirms: int
        :param fee_per_kb: Fee per kilobyte transaction size, leave empty to get estimated fee costs from Service provider.
        :type fee_per_kb: int
        :param offline: Just return the transaction object and do not send it when offline = True. Default is False
        :type offline: bool

        :return HDWalletTransaction:
        """

        network, account_id, acckey = self._get_account_defaults(network, account_id)

        utxos = self.utxos(account_id=account_id, network=network, min_confirms=min_confirms, key_id=input_key_id)
        utxos = utxos[0:max_utxos]
        input_arr = []
        total_amount = 0
        if not utxos:
            raise WalletError("Cannot sweep wallet, no UTXO's found")
        for utxo in utxos:
            # Skip dust transactions
            if utxo['value'] < self.network.dust_amount:
                continue
            input_arr.append((utxo['tx_hash'], utxo['output_n'], utxo['key_id'], utxo['value']))
            total_amount += utxo['value']
        srv = Service(network=network)
        if fee_per_kb is None:
            fee_per_kb = srv.estimatefee()
        tr_size = 125 + (len(input_arr) * 125)
        estimated_fee = int((tr_size / 1024.0) * fee_per_kb)
        return self.send([(to_address, total_amount-estimated_fee)], input_arr, network=network,
                         fee=estimated_fee, min_confirms=min_confirms, offline=offline)

    def info(self, detail=3):
        """
        Prints wallet information to standard output
        
        :param detail: Level of detail to show. Specify a number between 0 and 4, with 0 low detail and 4 highest detail
        :type detail: int

        """
        print("=== WALLET ===")
        print(" ID                             %s" % self.wallet_id)
        print(" Name                           %s" % self.name)
        print(" Owner                          %s" % self._owner)
        print(" Scheme                         %s" % self.scheme)
        if self.scheme == 'multisig':
            print(" Multisig Wallet IDs            %s" % str([w.wallet_id for w in self.cosigner]).strip('[]'))
        print(" Main network                   %s" % self.network.network_name)

        if self.scheme == 'multisig':
            print("\n= Multisig Public Account Keys =")
            for mk in [w.main_key for w in self.cosigner]:
                print("%5s %-70s %-10s" % (mk.key_id, mk.key().account_multisig_key().wif_public(),
                                           "main" if mk.is_private else "cosigner"))
            print("For 'main' keys a private master key is available in this wallet to sign transactions.")

        if detail and self.main_key:
            print("\n= Wallet Master Key =")
            print(" ID                             %s" % self.main_key_id)
            print(" Private                        %s" % self.main_key.is_private)
            print(" Depth                          %s" % self.main_key.depth)

        balances = self._balance_update()
        if detail > 1:
            for nw in self.networks():
                print("\n- NETWORK: %s -" % nw['network_name'])
                print("- - Keys")
                if detail < 3:
                    ds = [0, 3, 5]
                else:
                    ds = range(6)
                for d in ds:
                    is_active = True
                    if detail > 3:
                        is_active = False
                    for key in self.keys(depth=d, network=nw['network_name'], is_active=is_active):
                        print("%5s %-28s %-45s %-25s %25s" % (key.id, key.path, key.address, key.name,
                                                              Network(key.network_name).print_value(key.balance)))

                if detail > 2:
                    include_new = False
                    if detail > 3:
                        include_new = True
                    for account in self.accounts(network=nw['network_name']):
                        print("\n- - Transactions (Account %d, %s)" % (account.account_id, account.key().wif_public()))
                        for t in self.transactions(include_new=include_new, account_id=account.account_id,
                                                   network=nw['network_name']):
                            spent = ""
                            if 'spent' in t and t['spent'] is False:
                                spent = "U"
                            status = ""
                            if t['status'] not in ['confirmed', 'unconfirmed']:
                                status = t['status']
                            print("%4d %64s %36s %8d %13d %s %s" % (t['transaction_id'], t['tx_hash'], t['address'],
                                                                    t['confirmations'], t['value'], spent, status))
        print("\n= Balance Totals (includes unconfirmed) =")
        for na_balance in balances:
            print("%-20s %-20s %20s" % (na_balance['network'], "(Account %s)" % na_balance['account_id'],
                  Network(na_balance['network']).print_value(na_balance['balance'])))
        print("\n")

    def dict(self, detail=3):
        """
        Return wallet information in dictionary format

        :param detail: Level of detail to show, can be 0, 1, 2 or 3
        :type detail: int

        :return dict:
        """

        if detail > 1:
            for nw in self.networks():
                print("- Network: %s -" % nw['network_name'])
                if detail < 3:
                    ds = [0, 3, 5]
                else:
                    ds = range(6)
                for d in ds:
                    for key in self.keys(depth=d, network=nw['network_name']):
                        print("%5s %-28s %-45s %-25s %25s" % (key.id, key.path, key.address, key.name,
                                                              Network(key.network_name).print_value(key.balance)))

        return {
            'wallet_id': self.wallet_id,
            'name': self.name,
            'owner': self._owner,
            'scheme': self.scheme,
            'main_network': self.network.network_name,
            'main_balance': self.balance(),
            'main_balance_str': self.balance(as_string=True),
            'balances': self._balances,
            'default_account_id': self.default_account_id,
            'multisig_n_required': self.multisig_n_required,
            'multisig_compressed': self.multisig_compressed,
            'cosigner_wallet_ids': [w.wallet_id for w in self.cosigner],
            'cosigner_mainkey_wifs': [w.main_key.wif for w in self.cosigner],
            'sort_keys': self.sort_keys,
            'main_key_id': self.main_key_id
        }
