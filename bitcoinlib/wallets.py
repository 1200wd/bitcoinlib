# -*- coding: utf-8 -*-
#    BitcoinLib - Python Cryptocurrency Library
#    WALLETS - HD wallet Class for Key and Transaction management
#    © 2016 - 2019 February - 1200 Web Development <http://1200wd.com/>
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
import random
from sqlalchemy import or_
from itertools import groupby
from operator import itemgetter
import json

from bitcoinlib.db import *
from bitcoinlib.encoding import to_hexstring, to_bytes, EncodingError
from bitcoinlib.keys import HDKey, check_network_and_key, Address, path_expand, BKeyError
from bitcoinlib.networks import Network
from bitcoinlib.services.services import Service
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.transactions import Transaction, serialize_multisig_redeemscript, Output, Input, \
    get_unlocking_script_type

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


def wallet_create_or_open(
        name, keys='', owner='', network=None, account_id=0, purpose=None, scheme='bip32', sort_keys=True,
        password='', witness_type='legacy', encoding=None, multisig=None, sigs_required=None, cosigner_id=None,
        key_path=None, databasefile=DEFAULT_DATABASE):
    """
    Create a wallet with specified options if it doesn't exist, otherwise just open

    See Wallets class create method for option documentation
    """
    if wallet_exists(name, databasefile=databasefile):
        return HDWallet(name, databasefile=databasefile)
    else:
        return HDWallet.create(name, keys, owner, network, account_id, purpose, scheme, sort_keys,
                               password, witness_type, encoding, multisig, sigs_required, cosigner_id,
                               key_path, databasefile=databasefile)


@deprecated  # In version 0.4.5
def wallet_create_or_open_multisig(
        name, keys, sigs_required=None, owner='', network=None, account_id=0, purpose=None, sort_keys=True,
        witness_type='legacy', encoding=None, cosigner_id=None, key_path=None, databasefile=DEFAULT_DATABASE):
    """
    Deprecated since version 0.4.5, use wallet_create_or_open instead

    Create a wallet with specified options if it doesn't exist, otherwise just open

    See Wallets class create method for option documentation
    """
    if wallet_exists(name, databasefile=databasefile):
        return HDWallet(name, databasefile=databasefile)
    else:
        return HDWallet.create(name, keys, owner, network, account_id, purpose, 'bip32', sort_keys,
                               '', witness_type, encoding, True, sigs_required, cosigner_id,
                               key_path, databasefile=databasefile)


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
    """
    Remove all generated keys and transactions from wallet. Does not delete the wallet itself or the masterkey,
    so everything can be recreated.

    :param wallet: Wallet ID as integer or Wallet Name as string
    :type wallet: int, str
    :param databasefile: Location of Sqlite database. Leave empty to use default
    :type databasefile: str

    :return bool: True if succesfull
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
    """
    Normalize BIP0044 key path for HD keys. Using single quotes for hardened keys

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


@deprecated
def parse_bip44_path(path):
    """
    Assumes a correct BIP0044 path and returns a dictionary with path items. See Bitcoin improvement proposals
    BIP0043 and BIP0044.
    
    Specify path in this format: m / purpose' / cointype' / account' / change / address_index.
    Path length must be between 1 and 6 (Depth between 0 and 5)
    
    :param path: BIP0044 path as string, with backslash (/) seperator. 
    :type path: str
    
    :return dict: Dictionary with path items: is_private, purpose, cointype, account, change and address_index
    """

    pathl = normalize_path(path).split('/')
    if not 0 < len(pathl) <= 6:
        raise WalletError("Not a valid BIP0044 path. Path length (depth) must be between 1 and 6 not %d" % len(pathl))
    return {
        'is_private': True if pathl[0] == 'm' else False,
        'purpose': '' if len(pathl) < 2 else pathl[1],
        'cointype': '' if len(pathl) < 3 else pathl[2],
        'account': '' if len(pathl) < 4 else pathl[3],
        'change': '' if len(pathl) < 5 else pathl[4],
        'address_index': '' if len(pathl) < 6 else pathl[5],
    }


class HDWalletKey(object):
    """
    Normally only used as attribute of HDWallet class. Contains HDKey class, and adds extra information such as
    key ID, name, path and balance.
    
    All HDWalletKey are stored in a database
    """

    @staticmethod
    def from_key(name, wallet_id, session, key='', account_id=0, network=None, change=0, purpose=44, parent_id=0,
                 path='m', key_type=None, encoding=None, witness_type='legacy', multisig=False, cosigner_id=None):
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
        :param encoding: Encoding used for address, i.e.: base58 or bech32. Default is base58
        :type encoding: str
        :param witness_type: Witness type used when creating transaction script: legacy, p2sh-segwit or segwit.
        :type witness_type: str
        :param multisig: Specify if key is part of multisig wallet, used for create keys and key representations such as WIF and addreses
        :type multisig: bool
        :param cosigner_id: Set this if you would like to create keys for other cosigners.
        :type cosigner_id: int

        :return HDWalletKey: HDWalletKey object
        """

        key_is_address = False
        if isinstance(key, HDKey):
            k = key
            if network is None:
                network = k.network.name
        elif isinstance(key, Address):
            k = key
            key_is_address = True
            if network is None:
                network = k.network.name
        else:
            if network is None:
                network = DEFAULT_NETWORK
            k = HDKey(import_key=key, network=network)
        if not encoding and witness_type:
            encoding = get_encoding_from_witness(witness_type)
        script_type = script_type_default(witness_type, multisig)

        if not key_is_address:
            keyexists = session.query(DbKey).\
                filter(DbKey.wallet_id == wallet_id,
                       DbKey.wif == k.wif(witness_type=witness_type, multisig=multisig, is_private=True)).first()
            if keyexists:
                _logger.warning("Key already exists in this wallet. Key ID: %d" % keyexists.id)
                return HDWalletKey(keyexists.id, session, k)

            if key_type != 'single' and k.depth != len(path.split('/'))-1:
                if path == 'm' and k.depth > 1:
                    path = "M"

            wk = session.query(DbKey).filter(
                DbKey.wallet_id == wallet_id, DbKey.wif == k.wif(
                    witness_type=witness_type, multisig=multisig, is_private=True)).first()
            address = k.address(encoding=encoding, script_type=script_type)
            if wk:
                return HDWalletKey(wk.id, session, k)
            else:  # Look for public version of key, and convert to private if possible
                wk = session.query(DbKey).filter(
                    DbKey.wallet_id == wallet_id,
                    or_(DbKey.public == k.public_hex,
                        DbKey.wif == k.wif(witness_type=witness_type, multisig=multisig, is_private=False),
                        DbKey.address == address)).first()
                if wk:
                    wk.wif = k.wif(witness_type=witness_type, multisig=multisig, is_private=True)
                    wk.is_private = True
                    wk.private = k.private_hex
                    wk.public = k.public_hex
                    wk.path = path
                    session.commit()
                    return HDWalletKey(wk.id, session, k)

            nk = DbKey(name=name, wallet_id=wallet_id, public=k.public_hex, private=k.private_hex, purpose=purpose,
                       account_id=account_id, depth=k.depth, change=change, address_index=k.child_index,
                       wif=k.wif(witness_type=witness_type, multisig=multisig, is_private=True), address=address,
                       parent_id=parent_id, compressed=k.compressed, is_private=k.is_private, path=path,
                       key_type=key_type, network_name=network, encoding=encoding, cosigner_id=cosigner_id)
        else:
            keyexists = session.query(DbKey).\
                filter(DbKey.wallet_id == wallet_id,
                       DbKey.address == k.address).first()
            if keyexists:
                _logger.warning("Key with ID %s already exists" % keyexists.id)
                return HDWalletKey(keyexists.id, session, k)
            nk = DbKey(name=name, wallet_id=wallet_id, purpose=purpose,
                       account_id=account_id, depth=k.depth, change=change, address=k.address,
                       parent_id=parent_id, compressed=k.compressed, is_private=False, path=path,
                       key_type=key_type, network_name=network, encoding=encoding, cosigner_id=cosigner_id)

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
        :param hdkey_object: Optional HDKey object. Specify HDKey object if available for performance
        :type hdkey_object: HDKey

        """

        self._session = session
        wk = session.query(DbKey).filter_by(id=key_id).first()
        if wk:
            self._dbkey = wk
            self._hdkey_object = hdkey_object
            self.key_id = key_id
            self._name = wk.name
            self.wallet_id = wk.wallet_id
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
            self.encoding = wk.encoding
            self.cosigner_id = wk.cosigner_id
            self.used = wk.used
        else:
            raise WalletError("Key with id %s not found" % key_id)

    def __repr__(self):
        return "<HDWalletKey(key_id=%d, name=%s, wif=%s, path=%s)>" % (self.key_id, self.name, self.wif, self.path)

    @property
    def name(self):
        """
        Return name of wallet

        :return str:
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Set key name, update in database

        :param value: Name for this key
        :type value: str

        :return str:
        """

        self._name = value
        self._dbkey.name = value
        self._session.commit()

    def key(self):
        """
        Get HDKey object for current HDWalletKey

        :return HDKey:
        """

        if self.key_type == 'multisig':
            raise WalletError("HDWalletKey of type multisig has no single hdkey object, use cosigner attribute")
        if self._hdkey_object is None:
            self._hdkey_object = HDKey(import_key=self.wif, network=self.network_name, )
        return self._hdkey_object

    def balance(self, fmt=''):
        """
        Get total value of unspent outputs
        
        :param fmt: Specify 'string' to return a string in currency format
        :type fmt: str
        
        :return float, str: Key balance 
        """

        if fmt == 'string':
            return self.network.print_value(self._balance)
        else:
            return self._balance

    def as_dict(self):
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
            'encoding': self.encoding,
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
        witness_type = 'legacy'
        if hdwallet.witness_type in ['segwit', 'p2sh-segwit']:
            witness_type = 'segwit'
        Transaction.__init__(self, witness_type=witness_type, *args, **kwargs)

    def __repr__(self):
        return "<HDWalletTransaction(input_count=%d, output_count=%d, status=%s, network=%s)>" % \
               (len(self.inputs), len(self.outputs), self.status, self.network.name)

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
                   network=t.network.name, fee=t.fee, fee_per_kb=t.fee_per_kb, size=t.size,
                   hash=t.hash, date=t.date, confirmations=t.confirmations, block_height=t.block_height,
                   block_hash=t.block_hash, input_total=t.input_total, output_total=t.output_total,
                   rawtx=t.rawtx, status=t.status, coinbase=t.coinbase, verified=t.verified, flag=t.flag)

    def sign(self, keys=None, index_n=0, multisig_key_n=None, hash_type=SIGHASH_ALL):
        """
        Sign this transaction. Use existing keys from wallet or use keys argument for extra keys.

        :param keys: Extra private keys to sign the transaction
        :type keys: HDKey, str
        :param index_n: Transaction index_n to sign
        :type index_n: int
        :param multisig_key_n: Index number of key for multisig input for segwit transactions. Leave empty if not known. If not specified all possibilities will be checked
        :type multisig_key_n: int
        :param hash_type: Hashtype to use, default is SIGHASH_ALL
        :type hash_type: int

        :return None:
        """
        priv_key_list_arg = []
        if keys:
            key_paths = list(set([ti.key_path for ti in self.inputs]))
            if not isinstance(keys, list):
                keys = [keys]
            for priv_key in keys:
                if not isinstance(priv_key, HDKey):
                    priv_key = HDKey(priv_key, network=self.network.name)
                if not key_paths or priv_key.depth != 0 or priv_key.key_type == "single":
                    priv_key_list_arg.append((None, priv_key))
                else:
                    for key_path in key_paths:
                        priv_key_list_arg.append((key_path, priv_key.subkey_for_path(key_path)))
        for ti in self.inputs:
            priv_key_list = []
            for (key_path, priv_key) in priv_key_list_arg:
                if not key_path or key_path == ti.key_path:
                    priv_key_list.append(priv_key)
            for k in ti.keys:
                if k.is_private:
                    if isinstance(k, HDKey):
                        hdkey = k
                    else:
                        hdkey = HDKey(k, network=self.network.name)
                    if hdkey not in priv_key_list:
                        priv_key_list.append(hdkey)
                elif self.hdwallet.cosigner:
                    # Check if private key is available in wallet
                    cosign_wallet_ids = [w.wallet_id for w in self.hdwallet.cosigner]
                    db_pk = self.hdwallet._session.query(DbKey).filter_by(public=k.public_hex, is_private=True). \
                        filter(DbKey.wallet_id.in_(cosign_wallet_ids + [self.hdwallet.wallet_id])).first()
                    if db_pk:
                        priv_key_list.append(HDKey(db_pk.wif, network=self.network.name))
            Transaction.sign(self, priv_key_list, ti.index_n, multisig_key_n, hash_type)
        self.verify()
        self.error = ""

    def send(self, offline=False):
        """
        Verify and push transaction to network. Update UTXO's in database after successfull send

        :param offline: Just return the transaction object and do not send it when offline = True. Default is False
        :type offline: bool

        :return None:

        """

        self.error = None
        if not self.verified and not self.verify():
            self.error = "Cannot verify transaction"
            return None

        if offline:
            return None

        srv = Service(network=self.network.name, providers=self.hdwallet.providers)
        res = srv.sendrawtransaction(self.raw_hex())
        if not res:
            self.error = "Cannot send transaction. %s" % srv.errors
            return None
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
            self.hdwallet._balance_update(network=self.network.name)
            return None

        self.error = "Transaction not send, unknown response from service providers"

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
                input_total=self.input_total, output_total=self.output_total, network_name=self.network.name,
                block_hash=self.block_hash, raw=self.rawtx)
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
            db_tx.network_name = self.network.name if self.network.name else db_tx.name
            db_tx.raw = self.rawtx if self.rawtx else db_tx.raw
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
        if self.error:
            print("Errors: %s" % self.error)
        print("\n")


class HDWallet(object):
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
    def _create(cls, name, key, owner, network, account_id, purpose, scheme, parent_id, sort_keys,
                witness_type, encoding, multisig, sigs_required, cosigner_id, key_path, databasefile):

        if databasefile is None:
            databasefile = DEFAULT_DATABASE
        session = DbInit(databasefile=databasefile).session
        if session.query(DbWallet).filter_by(name=name).count():
            raise WalletError("Wallet with name '%s' already exists" % name)
        else:
            _logger.info("Create new wallet '%s'" % name)
        if not name:
            raise WalletError("Please enter wallet name")

        if not isinstance(key_path, list):
            key_path = key_path.split('/')
        key_depth = 1 if not key_path else len(key_path) - 1
        base_path = 'm'
        if hasattr(key, 'depth'):
            if key.depth is None:
                key.depth = key_depth
            if key.depth > 0:
                hardened_keys = [x for x in key_path if x[-1:] == "'"]
                if hardened_keys:
                    depth_public_master = key_path.index(hardened_keys[-1])
                    if depth_public_master != key.depth:
                        raise WalletError("Depth of provided public master key %d does not correspond with key path "
                                          "%s. Did you provide correct witness_type and multisig attribute?" %
                                          (key.depth, key_path))
                key_path = ['M'] + key_path[key.depth+1:]
                base_path = 'M'

        if isinstance(key_path, list):
            key_path = '/'.join(key_path)
        new_wallet = DbWallet(name=name, owner=owner, network_name=network, purpose=purpose, scheme=scheme,
                              sort_keys=sort_keys, witness_type=witness_type, parent_id=parent_id, encoding=encoding,
                              multisig=multisig, multisig_n_required=sigs_required, cosigner_id=cosigner_id,
                              key_path=key_path)
        session.add(new_wallet)
        session.commit()
        new_wallet_id = new_wallet.id

        if scheme == 'bip32' and multisig and parent_id is None:
            w = cls(new_wallet_id, databasefile=databasefile)
        elif scheme == 'bip32':
            mk = HDWalletKey.from_key(key=key, name=name, session=session, wallet_id=new_wallet_id, network=network,
                                      account_id=account_id, purpose=purpose, key_type='bip32', encoding=encoding,
                                      witness_type=witness_type, multisig=multisig, path=base_path)
            if mk.depth > 5:
                raise WalletError("Cannot create new wallet with main key of depth 5 or more")
            new_wallet.main_key_id = mk.key_id
            session.commit()

            w = cls(new_wallet_id, databasefile=databasefile, main_key_object=mk.key())
            w.key_for_path([0, 0], account_id=account_id, cosigner_id=cosigner_id)
        elif scheme == 'single':
            if not key:
                key = HDKey(network=network, depth=key_depth)
            mk = HDWalletKey.from_key(key=key, name=name, session=session, wallet_id=new_wallet_id, network=network,
                                      account_id=account_id, purpose=purpose, key_type='single', encoding=encoding,
                                      witness_type=witness_type, multisig=multisig)
            new_wallet.main_key_id = mk.key_id
            session.commit()
            w = cls(new_wallet_id, databasefile=databasefile, main_key_object=mk.key())
        else:
            raise WalletError("Wallet with scheme %s not supported at the moment" % scheme)

        session.close()
        return w

    @classmethod
    def create(cls, name, keys=None, owner='', network=None, account_id=0, purpose=0, scheme='bip32',
               sort_keys=True, password='', witness_type=None, encoding=None, multisig=None, sigs_required=None,
               cosigner_id=None, key_path=None, databasefile=None):
        """
        Create HDWallet and insert in database. Generate masterkey or import key when specified.

        When only a name is specified an legacy HDWallet with a single masterkey is created with standard p2wpkh
        scripts.

        To create a multi signature wallet specify multiple keys (private or public) and provide the sigs_required
        argument if it different then len(keys)

        To create a native segwit wallet use the option witness_type = 'segwit' and for old style addresses and p2sh
        embedded segwit script us 'ps2h-segwit' as witness_type.
        
        Please mention account_id if you are using multiple accounts.
        
        :param name: Unique name of this Wallet
        :type name: str
        :param keys: Masterkey to or list of keys to use for this wallet. Will be automatically created if not specified. One or more keys are obligatory for multisig wallets. Can contain all key formats accepted by the HDKey object, a HDKey object or BIP39 passphrase
        :type keys: str, bytes, int, bytearray
        :param owner: Wallet owner for your own reference
        :type owner: str
        :param network: Network name, use default if not specified
        :type network: str
        :param account_id: Account ID, default is 0
        :type account_id: int
        :param purpose: BIP43 purpose field, will be derived from witness_type and multisig by default
        :type purpose: int
        :param scheme: Key structure type, i.e. BIP32 or single
        :type scheme: str
        :param sort_keys: Sort keys according to BIP45 standard (used for multisig keys)
        :type sort_keys: bool
        :param password: Password to protect passphrase, only used if a passphrase is supplied in the 'key' argument.
        :type password: str
        :param witness_type: Specify witness type, default is 'legacy'. Use 'segwit' for native segregated witness wallet, or 'p2sh-segwit' for legacy compatible wallets
        :type witness_type: str
        :param encoding: Encoding used for address generation: base58 or bech32. Default is derive from wallet and/or witness type
        :type encoding: str
        :param multisig: Multisig wallet or child of a multisig wallet, default is None / derive from number of keys.
        :type multisig: bool
        :param sigs_required: Number of signatures required for validation if using a multisignature wallet. For example 2 for 2-of-3 multisignature. Default is all keys must signed
        :type sigs_required: int
        :param cosigner_id: Set this if wallet contains only public keys or if you would like to create keys for other cosigners.
        :type cosigner_id: int
        :param key_path: Key path for multisig wallet, use to create your own non-standard key path. Key path must
        follow the following rules:
        * Path start with masterkey (m) and end with change / address_index
        * If accounts are used, the account level must be 3. I.e.: m/purpose/coin_type/account/
        * All keys must be hardened, except for change, address_index or cosigner_id
        * Max length of path is 8 levels
        :type key_path: list, str
        :param databasefile: Location of database file. Leave empty to use default
        :type databasefile: str
        
        :return HDWallet: 
        """

        if multisig is None:
            if keys and isinstance(keys, list) and len(keys) > 1:
                multisig = True
            else:
                multisig = False
        if scheme not in ['bip32', 'single']:
            raise WalletError("Only bip32 or single key scheme's are supported at the moment")
        if witness_type not in [None, 'legacy', 'p2sh-segwit', 'segwit']:
            raise WalletError("Witness type %s not supported at the moment" % witness_type)
        if name.isdigit():
            raise WalletError("Wallet name '%s' invalid, please include letter characters" % name)

        if multisig:
            if password:
                raise WalletError("Password protected multisig wallets not supported")
            if scheme != 'bip32':
                raise WalletError("Multisig wallets should use bip32 scheme not %s" % scheme)
            if sigs_required is None:
                sigs_required = len(keys)
            if sigs_required > len(keys):
                raise WalletError("Number of keys required to sign is greater then number of keys provided")
        elif not isinstance(keys, list):
            keys = [keys]

        hdkey_list = []
        if keys and isinstance(keys, list) and sort_keys:
            keys.sort(key=lambda x: ('0' if isinstance(x, HDKey) else '1'))
        for key in keys:
            if isinstance(key, HDKey):
                network = key.network.name
                if witness_type is None:
                    witness_type = key.witness_type
            elif key:
                # If key consists of several words assume it is a passphrase and convert it to a HDKey object
                if len(key.split(" ")) > 1:
                    if not network:
                        raise WalletError("Please specify network when using passphrase to create a key")
                    key = HDKey.from_seed(Mnemonic().to_seed(key, password), network=network)
                else:
                    try:
                        key = HDKey(key, network=network)
                    except BKeyError:
                        try:
                            scheme = 'single'
                            key = Address.import_address(key, encoding=encoding, network=network)
                        except EncodingError:
                            pass
                    # else:
                    if network is None:
                        network = key.network.name
                    elif network != key.network.name:
                        raise BKeyError("Specified key %s is from different network then specified: %s" %
                                        (key.network.name, network))
                    if witness_type is None:
                        witness_type = key.witness_type
            hdkey_list.append(key)

        if network is None:
            network = DEFAULT_NETWORK
        if witness_type is None:
            witness_type = 'legacy'
        if (network == 'dash' or network == 'dash_testnet') and witness_type != 'legacy':
            raise WalletError("Segwit is not supported for Dash wallets")

        if not key_path:
            if scheme == 'single':
                key_path = ['m']
                purpose = 0
            else:
                ks = [k for k in WALLET_KEY_STRUCTURES if k['witness_type'] == witness_type and
                      k['multisig'] == multisig and k['purpose'] is not None]
                if len(ks) > 1:
                    raise WalletError("Please check definitions in WALLET_KEY_STRUCTURES. Multiple options found for "
                                      "witness_type - multisig combination")
                if ks and not purpose:
                    purpose = ks[0]['purpose']
                if ks and not encoding:
                    encoding = ks[0]['encoding']
                key_path = ks[0]['key_path']
        else:
            if purpose is None:
                purpose = 0
        if not encoding:
            encoding = get_encoding_from_witness(witness_type)

        if multisig:
            key = ''
        else:
            key = hdkey_list[0]

        hdpm = cls._create(name, key, owner=owner, network=network, account_id=account_id, purpose=purpose,
                           scheme=scheme, parent_id=None, sort_keys=sort_keys, witness_type=witness_type,
                           encoding=encoding, multisig=multisig, sigs_required=sigs_required, cosigner_id=cosigner_id,
                           key_path=key_path, databasefile=databasefile)

        if multisig:
            if sort_keys:
                hdkey_list.sort(key=lambda x: x.public_byte)
            cos_prv_lst = [hdkey_list.index(cw) for cw in hdkey_list if cw.is_private]
            if cosigner_id is None:
                hdpm.cosigner_id = 0 if not cos_prv_lst else cos_prv_lst[0]
            wlt_cos_id = 0
            for cokey in hdkey_list:
                if hdpm.network.name != cokey.network.name:
                    raise WalletError("Network for key %s (%s) is different then network specified: %s/%s" %
                                      (cokey.wif(is_private=False), cokey.network.name, network, hdpm.network.name))
                scheme = 'bip32'
                wn = name + '-cosigner-%d' % wlt_cos_id
                if cokey.key_type == 'single':
                    scheme = 'single'
                    # Adjust key depth of main wallet if main key is a single private key
                    if cokey.is_private:
                        hdpm.key_depth = cokey.depth

                w = cls._create(name=wn, key=cokey, owner=owner, network=network, account_id=account_id,
                                purpose=hdpm.purpose, scheme=scheme, parent_id=hdpm.wallet_id, sort_keys=sort_keys,
                                witness_type=hdpm.witness_type, encoding=encoding, multisig=True,
                                sigs_required=None, cosigner_id=wlt_cos_id, key_path=key_path,
                                databasefile=databasefile)
                hdpm.cosigner.append(w)
                wlt_cos_id += 1

        return hdpm

    @classmethod
    def create_multisig(cls, name, keys, sigs_required=None, owner='', network=None, account_id=0, purpose=None,
                        sort_keys=True, witness_type='legacy', encoding=None, key_path=None, cosigner_id=None,
                        databasefile=None):
        """
        Create a multisig wallet with specified name and list of keys. The list of keys can contain 2 or more
        public or private keys. For every key a cosigner wallet will be created with a BIP44 key structure or a
        single key depending on the key_type.

        :param name: Unique name of this Wallet
        :type name: str
        :param keys: List of keys in HDKey format or any other format supported by HDKey class
        :type keys: list
        :param sigs_required: Number of signatures required for validation. For example 2 for 2-of-3 multisignature. Default is all keys must signed
        :type sigs_required: int
        :type owner: str
        :param network: Network name, use default if not specified
        :type network: str
        :param account_id: Account ID, default is 0
        :type account_id: int
        :param purpose: BIP44 purpose field, default is 44
        :type purpose: int
        :param sort_keys: Sort keys according to BIP45 standard (used for multisig keys)
        :type sort_keys: bool
        :param witness_type: Specify wallet type, default is legacy. Use 'segwit' for segregated witness wallet.
        :type witness_type: str
        :param encoding: Encoding used for address generation: base58 or bech32. Default is derive from wallet and/or witness type
        :type encoding: str
        :param key_path: Key path for multisig wallet, use to create your own non-standard key path. Key path must
        follow the following rules:
        * Path start with masterkey (m) and end with change / address_index
        * If accounts are used, the account level must be 3. I.e.: m/purpose/coin_type/account/
        * All keys must be hardened, except for change, address_index or cosigner_id
        * Max length of path is 8 levels
        :type key_path: list, str
        :param cosigner_id: Set this if wallet contains only public keys or if you would like to create keys for other cosigners.
        :type cosigner_id: int
        :param databasefile: Location of database file. Leave empty to use default
        :type databasefile: str

        :return HDWallet:

        """

        return cls.create(name, keys=keys, owner=owner, network=network, account_id=account_id, purpose=purpose,
                          sort_keys=sort_keys, witness_type=witness_type, encoding=encoding, multisig=True,
                          sigs_required=sigs_required, cosigner_id=cosigner_id, key_path=key_path,
                          databasefile=databasefile)

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
            self._default_account_id = db_wlt.default_account_id
            self.multisig_n_required = db_wlt.multisig_n_required
            co_sign_wallets = self._session.query(DbWallet).\
                filter(DbWallet.parent_id == self.wallet_id).order_by(DbWallet.name).all()
            self.cosigner = [HDWallet(w.id, databasefile=databasefile) for w in co_sign_wallets]
            self.sort_keys = db_wlt.sort_keys
            if db_wlt.main_key_id:
                self.main_key = HDWalletKey(self.main_key_id, session=self._session, hdkey_object=main_key_object)
            if self.main_key and self._default_account_id is None:
                self._default_account_id = self.main_key.account_id
            _logger.info("Opening wallet '%s'" % self.name)
            self._key_objects = {
                self.main_key_id: self.main_key
            }
            self.providers = None
            self.witness_type = db_wlt.witness_type
            self.encoding = db_wlt.encoding
            self.multisig = db_wlt.multisig
            self.cosigner_id = db_wlt.cosigner_id
            self.script_type = script_type_default(self.witness_type, self.multisig, locking_script=True)
            self.key_path = db_wlt.key_path.split('/')
            self.depth_public_master = 0
            self.parent_id = db_wlt.parent_id
            if self.main_key and self.main_key.depth > 0:
                self.depth_public_master = self.main_key.depth
                self.key_depth = self.depth_public_master + len(self.key_path) - 1
            else:
                hardened_keys = [x for x in self.key_path if x[-1:] == "'"]
                if hardened_keys:
                    self.depth_public_master = self.key_path.index(hardened_keys[-1])
                self.key_depth = len(self.key_path) - 1
        else:
            raise WalletError("Wallet '%s' not found, please specify correct wallet ID or name." % wallet)

    def __exit__(self, exception_type, exception_value, traceback):
        self._session.close()

    # REMOVED - Gives database errors, assume it's done automatically
    # def __del__(self):
    #     try:
    #         if self._session:
    #             if self._dbwallet and self._dbwallet.parent_id:
    #                 return
    #             self._session.close()
    #     except Exception:
    #         pass

    def __repr__(self):
        return "<HDWallet(name=%s, databasefile=\"%s\")>" % \
               (self.name, self.databasefile)

    def __str__(self):
        return self.name

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
            network = self.network.name
        if account_id is None and network == self.network.name:
            account_id = self.default_account_id
        qr = self._session.query(DbKey).\
            filter_by(wallet_id=self.wallet_id, purpose=self.purpose, depth=self.depth_public_master,
                      network_name=network)
        if account_id is not None:
            qr = qr.filter_by(account_id=account_id)
        acckey = qr.first()
        if len(qr.all()) > 1 and "account'" in self.key_path:
            _logger.warning("No account_id specified and more than one account found for this network %s. "
                            "Using a random account" % network)
        if account_id is None:
            if acckey:
                account_id = acckey.account_id
            else:
                account_id = 0
        return network, account_id, acckey

    @property
    def default_account_id(self):
        return self._default_account_id

    @default_account_id.setter
    def default_account_id(self, value):
        self._default_account_id = value
        self._dbwallet = self._session.query(DbWallet).filter(DbWallet.id == self.wallet_id). \
            update({DbWallet.default_account_id: value})
        self._session.commit()

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
        self._dbwallet = self._session.query(DbWallet).filter(DbWallet.id == self.wallet_id).\
            update({DbWallet.owner: value})
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
        self._session.query(DbWallet).filter(DbWallet.id == self.wallet_id).update({DbWallet.name: value})
        self._session.commit()

    def default_network_set(self, network):
        if not isinstance(network, Network):
            network = Network(network)
        self.network = network
        self._session.query(DbWallet).filter(DbWallet.id == self.wallet_id).\
            update({DbWallet.network_name: network.name})
        self._session.commit()

    @deprecated  # Since 0.4.5 - Use import_key, to import private key for known public key
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
            private_key = HDKey(private_key, network=self.network.name)
        wallet_key.is_private = True
        wallet_key.wif = private_key.wif(is_private=True)
        wallet_key.private = private_key.private_hex
        self._session.query(DbKey).filter(DbKey.id == wallet_key.key_id).update(
                {DbKey.is_private: True, DbKey.private: private_key.private_hex,
                 DbKey.wif: private_key.wif(is_private=True)})
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
        if not hdkey.is_private or hdkey.depth != 0:
            raise WalletError("Please supply a valid private BIP32 master key with key depth 0")
        if self.main_key.is_private:
            raise WalletError("Main key is already a private key, cannot import key")
        if (self.main_key.depth != 1 and self.main_key.depth != 3 and self.main_key.depth != 4) or \
                self.main_key.key_type != 'bip32':
            raise WalletError("Current main key is not a valid BIP32 public master key")
        pm = self.public_master()
        if pm and self.main_key.wif != pm.wif:
            raise WalletError("This key does not correspond to current public master key")
        if not (self.network.name == self.main_key.network.name == hdkey.network.name):
            raise WalletError("Network of Wallet class, main account key and the imported private key must use "
                              "the same network")

        hdkey.key_type = 'bip32'
        ks = [k for k in WALLET_KEY_STRUCTURES if
              k['witness_type'] == self.witness_type and k['multisig'] == self.multisig and k['purpose'] is not None]
        if len(ks) > 1:
            raise WalletError("Please check definitions in WALLET_KEY_STRUCTURES. Multiple options found for "
                              "witness_type - multisig combination")
        self.key_path = ks[0]['key_path']
        self.main_key = HDWalletKey.from_key(
            key=hdkey, name=name, session=self._session, wallet_id=self.wallet_id, network=network,
            account_id=account_id, purpose=self.purpose, key_type='bip32', witness_type=self.witness_type)
        self.main_key_id = self.main_key.key_id
        self._key_objects.update({self.main_key_id: self.main_key})
        self._session.query(DbWallet).filter(DbWallet.id == self.wallet_id).\
            update({DbWallet.main_key_id: self.main_key_id})

        for key in self.keys(is_private=False):
            kp = key.path.split("/")
            if kp and kp[0] == 'M':
                kp = self.key_path[:self.depth_public_master+1] + kp[1:]
            self.key_for_path(kp, recreate=True)

        self._session.commit()
        return self.main_key

    def import_key(self, key, account_id=0, name='', network=None, purpose=44, key_type=None):
        """
        Add new single key to wallet.
        
        :param key: Key to import
        :type key: str, bytes, int, bytearray, HDKey, Address
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

        if self.scheme not in ['bip32', 'single']:
            raise WalletError("Keys can only be imported to a BIP32 or single type wallet, create a new wallet "
                              "instead")
        if isinstance(key, (HDKey, Address)):
            network = key.network.name
            hdkey = key
            if network not in self.network_list():
                raise WalletError("Network %s not found in this wallet" % network)
        else:
            if len(key.split(" ")) > 1:
                if network is None:
                    network = self.network
                hdkey = HDKey.from_seed(Mnemonic().to_seed(key), network=network)
            else:
                if network is None:
                    network = check_network_and_key(key, default_network=self.network.name)
                if network not in self.network_list():
                    raise WalletError("Network %s not available in this wallet, please create an account for this "
                                      "network first." % network)
                hdkey = HDKey(key, network=network, key_type=key_type)

        if not self.multisig:
            if self.main_key and self.main_key.depth == self.depth_public_master and \
                    not isinstance(hdkey, Address) and hdkey.is_private and hdkey.depth == 0 and self.scheme == 'bip32':
                return self.import_master_key(hdkey, name)

            if key_type is None:
                hdkey.key_type = 'single'
                key_type = 'single'

            ik_path = 'm'
            if key_type == 'single':
                # Create path for unrelated import keys
                hdkey.depth = self.key_depth
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
                account_id=account_id, purpose=purpose, session=self._session, path=ik_path,
                witness_type=self.witness_type)
            self._key_objects.update({mk.key_id: mk})
            if mk.key_id == self.main_key.key_id:
                self.main_key = mk
            return mk
        else:
            account_key = hdkey.public_master(witness_type=self.witness_type, multisig=True).wif()
            for w in self.cosigner:
                if w.main_key.key().wif_public() == account_key:
                    _logger.debug("Import new private cosigner key in this multisig wallet: %s" % account_key)
                    return w.import_master_key(hdkey)
            raise WalletError("Unknown key: Can only import a private key for a known public key in multisig wallets")

    def _new_key_multisig(self, public_keys, name, account_id, change, cosigner_id, network, address_index):
        if self.sort_keys:
            public_keys.sort(key=lambda pubk: pubk.key_public)
        public_key_list = [pubk.key_public for pubk in public_keys]
        public_key_ids = [str(x.key_id) for x in public_keys]

        # Calculate redeemscript and address and add multisig key to database
        redeemscript = serialize_multisig_redeemscript(public_key_list, n_required=self.multisig_n_required)
        script_type = 'p2sh'
        if self.witness_type == 'p2sh-segwit':
            script_type = 'p2sh_p2wsh'
        address = Address(redeemscript, encoding=self.encoding, script_type=script_type, network=network).address
        already_found_key = self._session.query(DbKey).filter_by(wallet_id=self.wallet_id, address=address).first()
        if already_found_key:
            return self.key(already_found_key.id)
        path = [pubk.path for pubk in public_keys if pubk.wallet.cosigner_id == self.cosigner_id][0]
        depth = self.cosigner[self.cosigner_id].main_key.depth + len(path.split("/")) - 1
        if not name:
            name = "Multisig Key " + '/'.join(public_key_ids)

        multisig_key = DbKey(
            name=name, wallet_id=self.wallet_id, purpose=self.purpose, account_id=account_id,
            depth=depth, change=change, address_index=address_index, parent_id=0, is_private=False, path=path,
            public=to_hexstring(redeemscript), wif='multisig-%s' % address, address=address, cosigner_id=cosigner_id,
            key_type='multisig', network_name=network)
        self._session.add(multisig_key)
        self._session.commit()
        for child_id in public_key_ids:
            self._session.add(DbKeyMultisigChildren(key_order=public_key_ids.index(child_id), parent_id=multisig_key.id,
                                                    child_id=int(child_id)))
        self._session.commit()
        return self.key(multisig_key.id)

    def new_key(self, name='', account_id=None, change=0, cosigner_id=None, network=None):
        """
        Create a new HD Key derived from this wallet's masterkey. An account will be created for this wallet
        with index 0 if there is no account defined yet.
        
        :param name: Key name. Does not have to be unique but if you use it at reference you might chooce to enforce this. If not specified 'Key #' with an unique sequence number will be used
        :type name: str
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param change: Change (1) or payments (0). Default is 0
        :type change: int
        :param cosigner_id: Cosigner ID for key path
        :type cosigner_id: int
        :param network: Network name. Leave empty for default network
        :type network: str

        :return HDWalletKey: 
        """

        if self.scheme == 'single':
            return self.main_key

        network, account_id, _ = self._get_account_defaults(network, account_id)
        if network != self.network.name and "coin_type'" not in self.key_path:
            raise WalletError("Multiple networks not supported by wallet key structure")
        if self.multisig:
            if not self.multisig_n_required:
                raise WalletError("Multisig_n_required not set, cannot create new key")
        if cosigner_id is None:
            cosigner_id = self.cosigner_id

        # Determine new key ID
        prevkey = self._session.query(DbKey).\
            filter_by(wallet_id=self.wallet_id, purpose=self.purpose, network_name=network, account_id=account_id,
                      change=change, cosigner_id=cosigner_id, depth=self.key_depth).\
            order_by(DbKey.address_index.desc()).first()
        address_index = 0
        if prevkey:
            address_index = prevkey.address_index + 1

        return self.key_for_path([change, address_index], name=name, account_id=account_id, network=network,
                                 cosigner_id=cosigner_id)

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

    def scan(self, scan_gap_limit=3, account_id=None, change=None, network=None, _keys_ignore=None,
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
        if self.scheme != 'bip32' and self.scheme != 'multisig':
            raise WalletError("The wallet scan() method is only available for BIP32 wallets")
        if scan_gap_limit < 2:
            raise WalletError("Scan gap limit must be 2 or higher")

        # Update number of confirmations
        txs = self._session.query(DbTransaction). \
            filter(DbTransaction.wallet_id == self.wallet_id).filter(DbTransaction.status == 'confirmed').\
            filter(DbTransaction.block_height > 0)
        if account_id is not None:
            txs.filter(DbKey.account_id == account_id)
        srv = Service(network=self.network.name)
        current_block_height = srv.block_count()
        for tx in txs:
            tx.confirmations = current_block_height - tx.block_height
        if txs.count():
            self._session.commit()

        # Check unconfirmed
        utxos = self._session.query(DbTransactionOutput).join(DbTransaction). \
            filter(DbTransaction.wallet_id == self.wallet_id).filter(DbTransaction.status == 'unconfirmed')
        if account_id is not None:
            utxos.filter(DbKey.account_id == account_id)
        txids = list(set([utxo.transaction.hash for utxo in utxos]))
        self.transactions_update_by_txids(txids)

        # Check UTXO's
        utxos = self._session.query(DbTransactionOutput).join(DbTransaction). \
            filter(DbTransaction.wallet_id == self.wallet_id).filter(DbTransactionOutput.spent.op("IS")(False))
        if account_id is not None:
            utxos.filter(DbKey.account_id == account_id)
        txids = list(set([utxo.transaction.hash for utxo in utxos]))
        self.transactions_update_by_txids(txids)

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

    def get_key(self, account_id=None, network=None, cosigner_id=None, number_of_keys=1, change=0):
        """
        Get a unused key or create a new one if there are no unused keys. 
        Returns a key from this wallet which has no transactions linked to it.
        
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param cosigner_id: Cosigner ID for key path
        :type cosigner_id: int
        :param number_of_keys: Number of keys to return. Default is 1
        :type number_of_keys: int
        :param change: Payment (0) or change key (1). Default is 0
        :type change: int

        :return HDWalletKey: 
        """

        network, account_id, _ = self._get_account_defaults(network, account_id)
        last_used_qr = self._session.query(DbKey).\
            filter_by(wallet_id=self.wallet_id, account_id=account_id, network_name=network,
                      used=True, change=change, depth=self.key_depth).\
            order_by(DbKey.id.desc()).first()
        last_used_key_id = 0
        if last_used_qr:
            last_used_key_id = last_used_qr.id
        dbkey = self._session.query(DbKey).\
            filter_by(wallet_id=self.wallet_id, account_id=account_id, network_name=network,
                      used=False, change=change, depth=self.key_depth).filter(DbKey.id > last_used_key_id).\
            order_by(DbKey.id.desc()).all()
        key_list = []
        for i in range(number_of_keys):
            if dbkey:
                dk = dbkey.pop()
                nk = self.key(dk.id)
            else:
                nk = self.new_key(account_id=account_id, change=change, cosigner_id=cosigner_id, network=network)
            key_list.append(nk)
        if len(key_list) == 1:
            return key_list[0]
        else:
            return key_list

    def get_key_change(self, account_id=None, network=None, number_of_keys=1):
        """
        Get a unused change key or create a new one if there are no unused keys. 
        Wrapper for the get_key method
        
        :param account_id: Account ID. Default is last used or created account ID.
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param number_of_keys: Number of keys to return. Default is 1
        :type number_of_keys: int

        :return HDWalletKey:  
        """

        return self.get_key(account_id=account_id, network=network, change=1, number_of_keys=number_of_keys)

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

        if self.scheme != 'bip32':
            raise WalletError("We can only create new accounts for a wallet with a BIP32 key scheme")
        if self.main_key and (self.main_key.depth != 0 or self.main_key.is_private is False):
            raise WalletError("A master private key of depth 0 is needed to create new accounts (depth: %d)" %
                              self.main_key.depth)
        if "account'" not in self.key_path:
            raise WalletError("Accounts are not supported for this wallet. Account not found in key path %s" %
                              self.key_path)
        if network is None:
            network = self.network.name
        elif network != self.network.name and "coin_type'" not in self.key_path:
            raise WalletError("Multiple networks not supported by wallet key structure")

        duplicate_cointypes = [Network(x).name for x in self.network_list() if Network(x).name != network and
                               Network(x).bip44_cointype == Network(network).bip44_cointype]
        if duplicate_cointypes:
            raise WalletError("Can not create new account for network %s with same BIP44 cointype: %s" %
                              (network, duplicate_cointypes))

        # Determine account_id and name
        if account_id is None:
            account_id = 0
            qr = self._session.query(DbKey). \
                filter_by(wallet_id=self.wallet_id, purpose=self.purpose, network_name=network). \
                order_by(DbKey.account_id.desc()).first()
            if qr:
                account_id = qr.account_id + 1
        if self.keys(account_id=account_id, depth=self.depth_public_master, network=network):
            raise WalletError("Account with ID %d already exists for this wallet" % account_id)

        acckey = self.key_for_path([], level_offset=self.depth_public_master-self.key_depth, account_id=account_id,
                                   name=name, network=network)
        self.key_for_path([0, 0], network=network, account_id=account_id)
        self.key_for_path([1, 0], network=network, account_id=account_id)
        return acckey

    def path_expand(self, path, level_offset=None, account_id=None, cosigner_id=0, address_index=None, change=0,
                    network=DEFAULT_NETWORK):
        """
        Create key path. Specify part of key path and path settings

        :param path: Part of path, for example [0, 2] for change=0 and address_index=2
        :type path: list, str
        :param level_offset: Just create part of path. For example -2 means create path with the last 2 items (change, address_index) or 1 will return the master key 'm'
        :type level_offset: int
        :param account_id: Account ID
        :type account_id: int
        :param cosigner_id: ID of cosigner
        :type cosigner_id: int
        :param address_index: Index of key, normally provided to 'path' argument
        :type address_index: int
        :param change: Change key = 1 or normal = 0, normally provided to 'path' argument
        :type change: int
        :param network: Network name. Leave empty for default network
        :type network: str

        :return list:
        """
        network, account_id, _ = self._get_account_defaults(network, account_id)
        return path_expand(path, self.key_path, level_offset, account_id=account_id, cosigner_id=cosigner_id,
                           address_index=address_index, change=change, purpose=self.purpose,
                           witness_type=self.witness_type, network=network)

    def key_for_path(self, path, level_offset=None, name=None, account_id=None, cosigner_id=None,
                     address_index=0, change=0, network=None, recreate=False):
        """
        Return key for specified path. Derive all wallet keys in path if they not already exists

        >>> w = HDWallet.create('key_for_path_example')
        >>> w.key_for_path([0, 0])
        <HDWalletKey(key_id=750, name=address index 0, wif=xprv...4Vk2, path=m/44'/0'/0'/0/0)>

        >>> w.key_for_path([], level_offset=-2)
        <HDWalletKey(key_id=748, name=account 0, wif=xprv...aMo, path=m/44'/0'/0')>

        >>> w.key_for_path([], w.depth_public_master + 1)
        <HDWalletKey(key_id=748, name=account 0, wif=xprv...aMo, path=m/44'/0'/0')>

        Arguments provided in 'path' take precedence over other arguments. The address_index argument is ignored:
        >>> w.key_for_path([0, 10], address_index=1000)
        <HDWalletKey(key_id=751, name=address index 0, wif=xprv...k2Mo, path=m/44'/0'/0'/0/10)>

        :param path: Part of key path, i.e. [0, 0] for [change=0, address_index=0]
        :type path: list, str
        :param level_offset: Just create part of path, when creating keys. For example -2 means create path with the last 2 items (change, address_index) or 1 will return the master key 'm'
        :type level_offset: int
        :param name: Specify key name for latest/highest key in structure
        :type name: str
        :param account_id: Account ID
        :type account_id: int
        :param cosigner_id: ID of cosigner
        :type cosigner_id: int
        :param address_index: Index of key, normally provided to 'path' argument
        :type address_index: int
        :param change: Change key = 1 or normal = 0, normally provided to 'path' argument
        :type change: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param recreate: Recreate key, even if already found in wallet. Can be used to update public key with private key info
        :type recreate: bool

        :return HDWalletKey:
        """

        network, account_id, _ = self._get_account_defaults(network, account_id)
        cosigner_id = cosigner_id if cosigner_id is not None else self.cosigner_id
        level_offset_key = level_offset
        if level_offset and self.main_key and level_offset > 0:
            level_offset_key = level_offset - self.main_key.depth

        fullpath = path_expand(path, self.key_path, level_offset_key, account_id=account_id, cosigner_id=cosigner_id,
                               purpose=self.purpose, address_index=address_index, change=change,
                               witness_type=self.witness_type, network=network)

        if self.multisig and self.cosigner:
            public_keys = []
            for wlt in self.cosigner:
                if wlt.scheme == 'single':
                    wk = wlt.main_key
                else:
                    wk = wlt.key_for_path(path, level_offset=level_offset, account_id=account_id, name=name,
                                          cosigner_id=cosigner_id, network=network, recreate=recreate)
                public_keys.append(wk)
            return self._new_key_multisig(public_keys, name, account_id, change, cosigner_id, network, address_index)

        # Check for closest ancestor in wallet\
        wpath = fullpath
        if self.main_key.depth and fullpath and fullpath[0] != 'M':
            wpath = ["M"] + fullpath[self.main_key.depth + 1:]
        dbkey = None
        while wpath and not dbkey:
            qr = self._session.query(DbKey).filter_by(path=normalize_path('/'.join(wpath)), wallet_id=self.wallet_id)
            if recreate:
                qr = qr.filter_by(is_private=True)
            dbkey = qr.first()
            wpath = wpath[:-1]
        if not dbkey:
            _logger.warning("No master or public master key found in this wallet")
            return None
        else:
            topkey = self.key(dbkey.id)

        # Key already found in db, return key
        if dbkey and dbkey.path == normalize_path('/'.join(fullpath)) and not recreate:
            return topkey
        else:
            # Create 1 or more keys add them to wallet
            nk = None
            parent_id = topkey.key_id
            ck = topkey.key()
            newpath = topkey.path
            n_items = len(str(dbkey.path).split('/'))
            for lvl in fullpath[n_items:]:
                ck = ck.subkey_for_path(lvl, network=network)
                newpath += '/' + lvl
                if not account_id:
                    account_id = 0 if "account'" not in self.key_path or self.key_path.index("account'") >= len(
                        fullpath) \
                        else int(fullpath[self.key_path.index("account'")][:-1])
                change = None if "change" not in self.key_path or self.key_path.index("change") >= len(fullpath) \
                    else int(fullpath[self.key_path.index("change")])
                if name and len(fullpath) == len(newpath.split('/')):
                    key_name = name
                else:
                    key_name = "%s %s" % (self.key_path[len(newpath.split('/'))-1], lvl)
                    key_name = key_name.replace("'", "").replace("_", " ")
                nk = HDWalletKey.from_key(key=ck, name=key_name, wallet_id=self.wallet_id, account_id=account_id,
                                          change=change, purpose=self.purpose, path=newpath, parent_id=parent_id,
                                          encoding=self.encoding, witness_type=self.witness_type,
                                          cosigner_id=cosigner_id, network=network, session=self._session)
                self._key_objects.update({nk.key_id: nk})
                parent_id = nk.key_id
            return nk

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
            if self.scheme == 'bip32' and depth is None:
                qr = qr.filter(DbKey.depth >= 3)
        if change is not None:
            qr = qr.filter(DbKey.change == change)
            if self.scheme == 'bip32' and depth is None:
                qr = qr.filter(DbKey.depth > self.key_depth - 1)
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
        keys = qr.order_by(DbKey.depth).all()
        if as_dict:
            keys = [x.__dict__ for x in keys]
            keys2 = []
            for key in keys:
                keys2.append({k: v for (k, v) in key.items() if k[:1] != '_' and k != 'wallet'})
            return keys2
        qr.session.close()
        return keys

    def keys_networks(self, used=None, as_dict=False):
        """
        Get keys of defined networks for this wallet. Wrapper for the keys() method

        :param used: Only return used or unused keys
        :type used: bool
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        
        """

        if self.scheme != 'bip32':
            raise WalletError("The 'keys_network' method can only be used with BIP32 type wallets")
        try:
            depth = self.key_path.index("coin_type'")
        except ValueError:
            return []
        if self.multisig and self.cosigner:
            _logger.warning("No network keys available for multisig wallet, use networks() method for list of networks")
        return self.keys(depth=depth, used=used, as_dict=as_dict)

    def keys_accounts(self, account_id=None, network=DEFAULT_NETWORK, as_dict=False):
        """
        Get Database records of account key(s) with for current wallet. Wrapper for the keys() method.
        
        Returns nothing if no account keys are available for instance in multisig or single account wallets. In this case use accounts() method instead.
        
        :param account_id: Search for Account ID
        :type account_id: int
        :param network: Network name filter
        :type network: str
        :param as_dict: Return as dictionary or DbKey object. Default is False: DbKey objects
        :type as_dict: bool
        
        :return list: DbKey or dictionaries
        """

        return self.keys(account_id, depth=self.depth_public_master, network=network, as_dict=as_dict)

    def keys_addresses(self, account_id=None, used=None, network=None, depth=None, as_dict=False):
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

        if depth is None:
            depth = self.key_depth
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

        return self.keys(account_id, depth=self.key_depth, change=0, used=used, network=network, as_dict=as_dict)

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

        return self.keys(account_id, depth=self.key_depth, change=1, used=used, network=network, as_dict=as_dict)

    def addresslist(self, account_id=None, used=None, network=None, change=None, depth=None, key_id=None):
        """
        Get list of addresses defined in current wallet

        :param account_id: Account ID
        :type account_id: int
        :param used: Only return used or unused keys
        :type used: bool, None
        :param network: Network name filter
        :type network: str
        :param change: Only include change addresses or not. Default is None which returns both
        :param depth: Filter by key depth. Default is None for standard key depth. Use -1 to show all keys
        :type depth: int
        :param key_id: Key ID to get address of just 1 key
        :type key_id: int
        
        :return list: List of address strings
        """

        addresslist = []
        if depth is None:
            depth = self.key_depth
        elif depth == -1:
            depth = None
        for key in self.keys(account_id=account_id, depth=depth, used=used, network=network, change=change,
                             key_id=key_id, is_active=False):
            addresslist.append(key.address)
        return addresslist

    def key(self, term):
        """
        Return single key with given ID or name as HDWalletKey object

        :param term: Search term can be key ID, key address, key WIF or key name
        :type term: int, str
        
        :return HDWalletKey: Single key as object
        """

        dbkey = None
        qr = self._session.query(DbKey).filter_by(wallet_id=self.wallet_id)
        if self.purpose:
            qr = qr.filter_by(purpose=self.purpose)
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
                hdwltkey = HDWalletKey(key_id=dbkey.id, session=self._session)
                self._key_objects.update({dbkey.id: hdwltkey})
                return hdwltkey
        else:
            raise KeyError("Key '%s' not found" % term)

    def account(self, account_id):
        """
        Returns wallet key of specific BIP44 account.

        Account keys have a BIP44 path depth of 3 and have the format m/purpose'/network'/account'

        I.e: Use account(0).key().wif_public() to get wallet's public master key

        :param account_id: ID of account. Default is 0
        :type account_id: int

        :return HDWalletKey:
        """

        if "account'" not in self.key_path:
            raise WalletError("Accounts are not supported for this wallet. Account not found in key path %s" %
                              self.key_path)
        if self.multisig:
            raise WalletError("Accounts not supported for multisig wallets")
        qr = self._session.query(DbKey).\
            filter_by(wallet_id=self.wallet_id, purpose=self.purpose, network_name=self.network.name,
                      account_id=account_id, depth=3).scalar()
        if not qr:
            raise WalletError("Account with ID %d not found in this wallet" % account_id)
        key_id = qr.id
        return self.key(key_id)

    def accounts(self, network=DEFAULT_NETWORK):
        """
        Get list of accounts for this wallet
        
        :param network: Network name filter. Default filter is DEFAULT_NETWORK
        :type network: str
                
        :return list: List of accounts as HDWalletKey objects
        """

        if self.multisig and self.cosigner:
            accounts = [wk.account_id for wk in self.cosigner[self.cosigner_id].keys_accounts(network=network)]
        else:
            accounts = [wk.account_id for wk in self.keys_accounts(network=network)]
        if not accounts:
            accounts = [self.default_account_id]
        return accounts

    def networks(self, as_dict=False):
        """
        Get list of networks used by this wallet

        :param as_dict: Return as dictionary or as Network objects, default is Network objects
        :type as_dict: bool

        :return list of (Network, dict):
        """

        nw_list = [self.network]
        if self.multisig and self.cosigner:
            keys_qr = self._session.query(DbKey.network_name).\
                filter_by(wallet_id=self.wallet_id, depth=self.key_depth).\
                group_by(DbKey.network_name).all()
            nw_list += [Network(nw[0]) for nw in keys_qr]
        elif self.main_key.key_type != 'single':
            wks = self.keys_networks()
            for wk in wks:
                nw_list.append(Network(wk.network_name))

        networks = []
        nw_list = list(set(nw_list))
        for nw in nw_list:
            if as_dict:
                nw = nw.__dict__
                if '_sa_instance_state' in nw:
                    del nw['_sa_instance_state']
            networks.append(nw)

        return networks

    def network_list(self, field='name'):
        """
        Wrapper for networks methods, returns a flat list with currently used
        networks for this wallet.
        
        :return list of str:
        """

        return [getattr(x, field) for x in self.networks()]

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

        :return int: Total balance
        """

        balance = Service(network=network, providers=self.providers).getbalance(self.addresslist(account_id=account_id,
                                                                                                 network=network))
        network, account_id, acckey = self._get_account_defaults(network, account_id)
        if balance:
            new_balance = {
                'account_id': account_id,
                'network': network,
                'balance': balance
            }
            old_balance_item = [bi for bi in self._balances if bi['network'] == network and
                                bi['account_id'] == account_id]
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

        self._balance = sum([b['balance'] for b in balance_list if b['network'] == self.network.name])

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

        single_key = None
        if key_id:
            single_key = self._session.query(DbKey).filter_by(id=key_id).scalar()
            networks = [single_key.network_name]
            account_id = single_key.account_id
        if networks is None:
            networks = self.network_list()
        elif not isinstance(networks, list):
            networks = [networks]
        elif len(networks) != 1 and utxos is not None:
            raise WalletError("Please specify maximum 1 network when passing utxo's")

        count_utxos = 0
        for network in networks:
            if account_id is None and not self.multisig:
                accounts = self.accounts(network=network)
            else:
                accounts = [account_id]
            for account_id in accounts:
                if depth is None:
                    depth = self.key_depth

                if utxos is None:
                    # Get all UTXO's for this wallet from default Service object
                    addresslist = self.addresslist(account_id=account_id, used=used, network=network, key_id=key_id,
                                                   change=change, depth=depth)
                    random.shuffle(addresslist)
                    srv = Service(network=network, providers=self.providers)
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
                    key = single_key
                    if not single_key:
                        key = self._session.query(DbKey).\
                            filter_by(wallet_id=self.wallet_id, address=utxo['address']).scalar()
                    if not key:
                        raise WalletError("Key with address %s not found in this wallet" % utxo['address'])
                    key.used = True
                    status = 'unconfirmed'
                    if utxo['confirmations']:
                        status = 'confirmed'

                    # Update confirmations in db if utxo was already imported
                    transaction_in_db = self._session.query(DbTransaction).\
                        filter_by(wallet_id=self.wallet_id, hash=utxo['tx_hash'], network_name=self.network.name)
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
                        if transaction_in_db.count():
                            transaction_record = transaction_in_db.scalar()
                            transaction_record.confirmations = utxo['confirmations']
                            transaction_record.status = status
                    else:
                        # Add transaction if not exist and then add output
                        if not transaction_in_db.count():
                            block_height = None
                            if block_height in utxo and utxo['block_height']:
                                block_height = utxo['block_height']
                            new_tx = DbTransaction(wallet_id=self.wallet_id, hash=utxo['tx_hash'], status=status,
                                                   block_height=block_height,
                                                   confirmations=utxo['confirmations'], network_name=self.network.name)
                            self._session.add(new_tx)
                            self._session.commit()
                            tid = new_tx.id
                        else:
                            tid = transaction_in_db.scalar().id

                        script_type = script_type_default(self.witness_type, multisig=self.multisig,
                                                          locking_script=True)
                        new_utxo = DbTransactionOutput(transaction_id=tid,  output_n=utxo['output_n'],
                                                       value=utxo['value'], key_id=key.id, script=utxo['script'],
                                                       script_type=script_type, spent=False)
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

    def utxo_add(self, address, value, tx_hash, output_n, confirmations=0, script=''):
        """
        Add a single UTXO to the wallet database. To update all utxo's use utxos_update method.

        Use this method for testing, offline wallets or if you wish to override standard method of retreiving UTXO's

        This method does not check if UTXO exists or is still spendable.

        [{
            'address': 'n2S9Czehjvdmpwd2YqekxuUC1Tz5ZdK3YN',
            'script': '',
            'confirmations': 10,
            'output_n': 1,
            'tx_hash': '9df91f89a3eb4259ce04af66ad4caf3c9a297feea5e0b3bc506898b6728c5003',
            'value': 8970937
        }]

        :param address: Address of Unspent Output. Address should be available in wallet
        :type address: str
        :param value: Value of output in sathosis or smallest denominator for type of currency
        :type value: int
        :param tx_hash: Transaction hash or previous output as hex-string
        :type tx_hash: str
        :param output_n: Output number of previous transaction output
        :type output_n: int
        :param confirmations: Number of confirmations. Default is 0, unconfirmed
        :type confirmations: int
        :param script: Locking script of previous output as hex-string
        :type script: str

        :return int: Number of new UTXO's added, so 1 if successful
        """

        utxo = {
            'address': address,
            'script': script,
            'confirmations': confirmations,
            'output_n': output_n,
            'tx_hash': tx_hash,
            'value': value
        }
        return self.utxos_update(utxos=[utxo])

    def transactions_update_by_txids(self, txids):
        if not isinstance(txids, list):
            txids = [txids]
        txids = list(set(txids))

        txs = []
        srv = Service(network=self.network.name, providers=self.providers)
        for txid in txids:
            txs.append(srv.gettransaction(txid))

        # TODO: Avoid duplicate code in this method and transaction_update()
        utxo_set = set()
        for t in txs:
            wt = HDWalletTransaction.from_transaction(self, t)
            wt.save()
            utxos = [(to_hexstring(ti.prev_hash), ti.output_n_int) for ti in wt.inputs]
            utxo_set.update(utxos)

        for utxo in list(utxo_set):
            tos = self._session.query(DbTransactionOutput).join(DbTransaction). \
                filter(DbTransaction.hash == utxo[0], DbTransactionOutput.output_n == utxo[1],
                       DbTransactionOutput.spent.op("IS")(False)).all()
            for u in tos:
                u.spent = True
        self._session.commit()
        # self._balance_update(account_id=account_id, network=network, key_id=key_id)

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
            depth = self.key_depth
        addresslist = self.addresslist(account_id=account_id, used=used, network=network, key_id=key_id,
                                       change=change, depth=depth)
        srv = Service(network=network, providers=self.providers)
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
        self._balance_update(account_id=account_id, network=network, key_id=key_id)

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

    def _objects_by_key_id(self, key_id):
        key = self._session.query(DbKey).filter_by(id=key_id).scalar()
        if not key:
            raise WalletError("Key '%s' not found in this wallet" % key_id)
        if key.key_type == 'multisig':
            inp_keys = [HDKey(ck.child_key.wif, network=ck.child_key.network_name) for ck in key.multisig_children]
        elif key.key_type in ['bip32', 'single']:
            if not key.wif:
                raise WalletError("WIF of key is empty cannot create HDKey")
            inp_keys = [HDKey(key.wif, compressed=key.compressed, network=key.network_name)]
        else:
            raise WalletError("Input key type %s not supported" % key.key_type)
        return inp_keys, key

    def select_inputs(self, amount, variance=None, account_id=None, network=None, min_confirms=0, max_utxos=None,
                      return_input_obj=True):
        """
        Select available inputs for given amount

        :param amount: Total value of inputs to select
        :type amount: int
        :param variance: Allowed difference in total input value. Default is dust amount of selected network.
        :type variance: int
        :param account_id: Account ID
        :type account_id: int
        :param network: Network name. Leave empty for default network
        :type network: str
        :param min_confirms: Minimal confirmation needed for an UTXO before it will included in inputs. Default is 0 confirmations. Option is ignored if input_arr is provided.
        :type min_confirms: int
        :param max_utxos: Maximum number of UTXO's to use. Set to 1 for optimal privacy. Default is None: No maximum
        :type max_utxos: int
        :param return_input_obj: Return inputs as Input class object. Default is True
        :type return_input_obj: bool

        :return list of DbTransactionOutput, Input: List of previous outputs
        """

        network, account_id, _ = self._get_account_defaults(network, account_id)
        if variance is None:
            variance = self.network.dust_amount

        utxo_query = self._session.query(DbTransactionOutput).join(DbTransaction).join(DbKey). \
            filter(DbTransaction.wallet_id == self.wallet_id, DbKey.account_id == account_id,
                   DbKey.network_name == network, DbKey.public != '',
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
        selected_utxos = []
        if one_utxo:
            selected_utxos = [one_utxo]
        else:
            # Try to find one utxo with higher amount
            one_utxo = utxo_query. \
                filter(DbTransactionOutput.spent.op("IS")(False), DbTransactionOutput.value >= amount).\
                order_by(DbTransactionOutput.value).first()
            if one_utxo:
                selected_utxos = [one_utxo]
            elif max_utxos and max_utxos <= 1:
                _logger.info("No single UTXO found with requested amount, use higher 'max_utxo' setting to use "
                             "multiple UTXO's")
                return []

        # Otherwise compose of 2 or more lesser outputs
        if not selected_utxos:
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
        if not return_input_obj:
            return selected_utxos
        else:
            inputs = []
            for utxo in selected_utxos:
                # amount_total_input += utxo.value
                inp_keys, key = self._objects_by_key_id(utxo.key_id)
                multisig = False if len(inp_keys) < 2 else True
                script_type = get_unlocking_script_type(utxo.script_type, multisig=multisig)
                inputs.append(Input(utxo.transaction.hash, utxo.output_n, keys=inp_keys, script_type=script_type,
                              sigs_required=self.multisig_n_required, sort=self.sort_keys,
                              compressed=key.compressed, value=utxo.value))
            return inputs

    def transaction_create(self, output_arr, input_arr=None, account_id=None, network=None, fee=None,
                           min_confirms=0, max_utxos=None, locktime=0):
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
        :param locktime: Transaction level locktime. Locks the transaction until a specified block (value from 1 to 5 million) or until a certain time (Timestamp in seconds after 1-jan-1970). Default value is 0 for transactions without locktime
        :type locktime: int

        :return HDWalletTransaction: object
        """

        amount_total_output = 0
        network, account_id, acckey = self._get_account_defaults(network, account_id)

        if input_arr and max_utxos and len(input_arr) > max_utxos:
            raise WalletError("Input array contains %d UTXO's but max_utxos=%d parameter specified" %
                              (len(input_arr), max_utxos))

        # Create transaction and add outputs
        transaction = HDWalletTransaction(hdwallet=self, network=network, locktime=locktime)
        if not isinstance(output_arr, list):
            raise WalletError("Output array must be a list of tuples with address and amount. "
                              "Use 'send_to' method to send to one address")
        for o in output_arr:
            if isinstance(o, Output):
                transaction.outputs.append(o)
                amount_total_output += o.value
            else:
                amount_total_output += o[1]
                addr = o[0]
                if isinstance(addr, HDWalletKey):
                    addr = addr.key()
                transaction.add_output(o[1], addr)

        srv = Service(network=network, providers=self.providers)
        transaction.fee_per_kb = None
        if fee is None:
            if not input_arr:
                transaction.fee_per_kb = srv.estimatefee()
                fee_estimate = (transaction.estimate_size(add_change_output=True) / 1024.0 * transaction.fee_per_kb)
                if fee_estimate < self.network.fee_min:
                    fee_estimate = self.network.fee_min
            else:
                fee_estimate = 0
        else:
            fee_estimate = fee

        # Add inputs
        sequence = 0xffffffff
        if 0 < transaction.locktime < 0xffffffff:
            sequence = 0xfffffffe
        amount_total_input = 0
        if input_arr is None:
            selected_utxos = self.select_inputs(amount_total_output + fee_estimate, self.network.dust_amount,
                                                account_id, network, min_confirms, max_utxos, False)
            if not selected_utxos:
                logger.warning("Not enough unspent transaction outputs found")
                return False
            for utxo in selected_utxos:
                amount_total_input += utxo.value
                inp_keys, key = self._objects_by_key_id(utxo.key_id)
                multisig = False if isinstance(inp_keys, list) and len(inp_keys) < 2 else True
                unlock_script_type = get_unlocking_script_type(utxo.script_type, self.witness_type, multisig=multisig)
                transaction.add_input(utxo.transaction.hash, utxo.output_n, keys=inp_keys,
                                      script_type=unlock_script_type, sigs_required=self.multisig_n_required,
                                      sort=self.sort_keys, compressed=key.compressed, value=utxo.value,
                                      address=utxo.key.address, sequence=sequence,
                                      key_path=utxo.key.path, witness_type=self.witness_type)
                # FIXME: Missing locktime_cltv=locktime_cltv, locktime_csv=locktime_csv (?)
        else:
            for inp in input_arr:
                locktime_cltv = None
                locktime_csv = None
                unlocking_script_unsigned = None
                unlocking_script_type = ''
                if isinstance(inp, Input):
                    prev_hash = inp.prev_hash
                    output_n = inp.output_n
                    key_id = None
                    value = inp.value
                    signatures = inp.signatures
                    unlocking_script = inp.unlocking_script
                    unlocking_script_unsigned = inp.unlocking_script_unsigned
                    unlocking_script_type = inp.script_type
                    address = inp.address
                    sequence = inp.sequence
                    locktime_cltv = inp.locktime_cltv
                    locktime_csv = inp.locktime_csv
                elif isinstance(inp, DbTransactionOutput):
                    prev_hash = inp.transaction.hash
                    output_n = inp.output_n
                    key_id = inp.key_id
                    value = inp.value
                    signatures = None
                    # FIXME: This is probably not an unlocking_script
                    unlocking_script = inp.script
                    unlocking_script_type = get_unlocking_script_type(inp.script_type)
                    address = inp.key.address
                else:
                    prev_hash = inp[0]
                    output_n = inp[1]
                    key_id = None if len(inp) <= 2 else inp[2]
                    value = 0 if len(inp) <= 3 else inp[3]
                    signatures = None if len(inp) <= 4 else inp[4]
                    unlocking_script = b'' if len(inp) <= 5 else inp[5]
                    address = '' if len(inp) <= 6 else inp[6]
                # Get key_ids, value from Db if not specified
                if not (key_id and value and unlocking_script_type):
                    if not isinstance(output_n, int):
                        output_n = struct.unpack('>I', output_n)[0]
                    inp_utxo = self._session.query(DbTransactionOutput).join(DbTransaction).join(DbKey). \
                        filter(DbTransaction.wallet_id == self.wallet_id,
                               DbTransaction.hash == to_hexstring(prev_hash),
                               DbTransactionOutput.output_n == output_n).first()
                    if inp_utxo:
                        key_id = inp_utxo.key_id
                        value = inp_utxo.value
                        address = inp_utxo.key.address
                        unlocking_script_type = get_unlocking_script_type(inp_utxo.script_type, multisig=self.multisig)
                        # witness_type = inp_utxo.witness_type
                    else:
                        _logger.info("UTXO %s not found in this wallet. Please update UTXO's if this is not an "
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
                inp_keys, key = self._objects_by_key_id(key_id)
                transaction.add_input(prev_hash, output_n, keys=inp_keys, script_type=unlocking_script_type,
                                      sigs_required=self.multisig_n_required, sort=self.sort_keys,
                                      compressed=key.compressed, value=value, signatures=signatures,
                                      unlocking_script=unlocking_script, address=address,
                                      unlocking_script_unsigned=unlocking_script_unsigned,
                                      sequence=sequence, locktime_cltv=locktime_cltv, locktime_csv=locktime_csv,
                                      witness_type=self.witness_type, key_path=key.path)
        # Calculate fees
        transaction.fee = fee
        fee_per_output = None
        transaction.size = transaction.estimate_size(add_change_output=True)
        if fee is None:
            if not input_arr:
                if not transaction.fee_per_kb:
                    transaction.fee_per_kb = srv.estimatefee()
                if transaction.fee_per_kb < self.network.fee_min:
                    transaction.fee_per_kb = self.network.fee_min
                transaction.fee = int((transaction.size / 1024.0) * transaction.fee_per_kb)
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

        # Skip change if amount is smaller then the dust limit or estimated fee
        if (fee_per_output and transaction.change < fee_per_output) or transaction.change <= self.network.dust_amount:
            transaction.fee += transaction.change
            transaction.change = 0
        if transaction.change < 0:
            raise WalletError("Total amount of outputs is greater then total amount of inputs")
        if transaction.change:
            ck = self.get_key(account_id=account_id, network=network, change=1)
            on = transaction.add_output(transaction.change, ck.address, encoding=self.encoding)
            transaction.outputs[on].key_id = ck.key_id
            amount_total_output += transaction.change

        if not transaction.fee_per_kb:
            transaction.fee_per_kb = int((transaction.fee * 1024.0) / transaction.size)
        if transaction.fee_per_kb < self.network.fee_min:
            raise WalletError("Fee per kB of %d is lower then minimal network fee of %d" %
                              (transaction.fee_per_kb, self.network.fee_min))
        elif transaction.fee_per_kb > self.network.fee_max:
            raise WalletError("Fee per kB of %d is higher then maximum network fee of %d" %
                              (transaction.fee_per_kb, self.network.fee_max))

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
            rt = self.transaction_create(t.outputs, t.inputs, fee=t.fee, network=t.network.name)
            if t.size:
                rt.size = t.size
            else:
                rt.size = len(t.raw())
            rt.fee_per_kb = int((rt.fee / rt.size) * 1024)
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
            network = self.network.name
        t_import = Transaction.import_raw(raw_tx, network=network)
        rt = self.transaction_create(t_import.outputs, t_import.inputs, network=network)
        rt.verify()
        rt.size = len(raw_tx)
        rt.fee_per_kb = int((rt.fee / rt.size) * 1024)
        return rt

    def send(self, output_arr, input_arr=None, account_id=None, network=None, fee=None, min_confirms=0,
             priv_keys=None, max_utxos=None, locktime=0, offline=False):
        """
        Create new transaction with specified outputs and push it to the network. 
        Inputs can be specified but if not provided they will be selected from wallets utxo's.
        Output array is a list of 1 or more addresses and amounts.
        
        :param output_arr: List of output tuples with address and amount. Must contain at least one item. Example: [('mxdLD8SAGS9fe2EeCXALDHcdTTbppMHp8N', 5000000)]. Address can be an address string, Address object, HDKey object or HDWalletKey object
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
        :param locktime: Transaction level locktime. Locks the transaction until a specified block (value from 1 to 5 million) or until a certain time (Timestamp in seconds after 1-jan-1970). Default value is 0 for transactions without locktime
        :type locktime: int
        :param offline: Just return the transaction object and do not send it when offline = True. Default is False
        :type offline: bool

        :return HDWalletTransaction:
        """

        network, account_id, _ = self._get_account_defaults(network, account_id)
        if input_arr and max_utxos and len(input_arr) > max_utxos:
            raise WalletError("Input array contains %d UTXO's but max_utxos=%d parameter specified" %
                              (len(input_arr), max_utxos))

        transaction = self.transaction_create(output_arr, input_arr, account_id, network, fee,
                                              min_confirms, max_utxos, locktime)
        if not transaction:
            return False
        transaction.sign(priv_keys)
        # Calculate exact estimated fees and update change output if necessary
        if fee is None and transaction.fee_per_kb and transaction.change:
            fee_exact = transaction.calculate_fee()
            # Recreate transaction if fee estimation more then 10% off
            if fee_exact and abs((transaction.fee - fee_exact) / float(fee_exact)) > 0.10:
                _logger.info("Transaction fee not correctly estimated (est.: %d, real: %d). "
                             "Recreate transaction with correct fee" % (transaction.fee, fee_exact))
                transaction = self.transaction_create(output_arr, input_arr, account_id, network, fee_exact,
                                                      min_confirms, max_utxos, locktime)
                transaction.sign(priv_keys)

        transaction.fee_per_kb = int((transaction.fee / transaction.size) * 1024)
        transaction.send(offline)
        return transaction

    def send_to(self, to_address, amount, account_id=None, network=None, fee=None, min_confirms=0,
                priv_keys=None, locktime=0, offline=False):
        """
        Create transaction and send it with default Service objects sendrawtransaction method

        :param to_address: Single output address as string Address object, HDKey object or HDWalletKey object
        :type to_address: str, Address, HDKey, HDWalletKey
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
        :param locktime: Transaction level locktime. Locks the transaction until a specified block (value from 1 to 5 million) or until a certain time (Timestamp in seconds after 1-jan-1970). Default value is 0 for transactions without locktime
        :type locktime: int
        :param offline: Just return the transaction object and do not send it when offline = True. Default is False
        :type offline: bool

        :return HDWalletTransaction:
        """

        outputs = [(to_address, amount)]
        return self.send(outputs, account_id=account_id, network=network, fee=fee,
                         min_confirms=min_confirms, priv_keys=priv_keys, locktime=locktime, offline=offline)

    def sweep(self, to_address, account_id=None, input_key_id=None, network=None, max_utxos=999, min_confirms=0,
              fee_per_kb=None, fee=None, locktime=0, offline=False):
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
        :param fee_per_kb: Fee per kilobyte transaction size, leave empty to get estimated fee costs from Service provider. This option is ignored when the 'fee' option is specified
        :type fee_per_kb: int
        :param fee: Total transaction fee in smallest denominator (i.e. satoshis). Leave empty to get estimated fee from service providers.
        :type fee: int
        :param locktime: Transaction level locktime. Locks the transaction until a specified block (value from 1 to 5 million) or until a certain time (Timestamp in seconds after 1-jan-1970). Default value is 0 for transactions without locktime
        :type locktime: int
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
            if utxo['value'] <= self.network.dust_amount:
                continue
            input_arr.append((utxo['tx_hash'], utxo['output_n'], utxo['key_id'], utxo['value']))
            total_amount += utxo['value']
        srv = Service(network=network, providers=self.providers)

        if not fee:
            if fee_per_kb is None:
                fee_per_kb = srv.estimatefee()
            tr_size = 125 + (len(input_arr) * 125)
            fee = int((tr_size / 1024.0) * fee_per_kb)
        return self.send([(to_address, total_amount-fee)], input_arr, network=network,
                         fee=fee, min_confirms=min_confirms, locktime=locktime, offline=offline)

    def wif(self, is_private=False, account_id=0):
        """
        Return Wallet Import Format string for master private or public key which can be used to import key and
        recreate wallet in other software.

        A list of keys will be exported for a multisig wallet.

        :param is_private: Export public or private key
        :type is_private: Public or private, default is True
        :param account_id: Account ID of key to export
        :type account_id: bool

        :return list, str:
        """
        if not self.multisig or not self.cosigner:
            if is_private and self.main_key:
                return self.main_key.wif
            else:
                return self.public_master(account_id=account_id).key().\
                    wif(is_private=is_private, witness_type=self.witness_type, multisig=self.multisig)
        else:
            wiflist = []
            for cs in self.cosigner:
                wiflist.append(cs.wif(is_private=is_private))
            return wiflist

    def public_master(self, account_id=None, name=None, network=None):
        """
        Return public master key(s) for this wallet. Use to import in other wallets to sign transactions or create keys.

        For a multisig wallet all public master keys are return as list.

        Returns private key information if available.

        :param account_id: Account ID of key to export
        :type account_id: int
        :param name: Optional name for account key
        :type name: str
        :param network: Network name. Leave empty for default network
        :type network: str

        :return list of HDWalletKey, HDWalletKey:
        """
        if self.main_key and self.main_key.key_type == 'single':
            return self.main_key
        elif not self.cosigner:
            depth = -self.key_depth + self.depth_public_master
            return self.key_for_path([], depth, name=name, account_id=account_id, network=network,
                                     cosigner_id=self.cosigner_id)
        else:
            pm_list = []
            for cs in self.cosigner:
                pm_list.append(cs.public_master(account_id, name, network))
            return pm_list

    def info(self, detail=3):
        """
        Prints wallet information to standard output
        
        :param detail: Level of detail to show. Specify a number between 0 and 5, with 0 low detail and 5 highest detail
        :type detail: int
        """

        print("=== WALLET ===")
        print(" ID                             %s" % self.wallet_id)
        print(" Name                           %s" % self.name)
        print(" Owner                          %s" % self.owner)
        print(" Scheme                         %s" % self.scheme)
        print(" Multisig                       %s" % self.multisig)
        if self.multisig:
            print(" Multisig Wallet IDs            %s" % str([w.wallet_id for w in self.cosigner]).strip('[]'))
        print(" Witness type                   %s" % self.witness_type)
        print(" Main network                   %s" % self.network.name)

        if self.multisig:
            print("\n= Multisig Public Master Keys =")
            for cs in self.cosigner:
                print("%5s %-70s %-10s" % (cs.main_key.key_id, cs.wif(is_private=False),
                                           "main" if cs.main_key.is_private else "cosigner"))
            print("For main keys a private master key is available in this wallet to sign transactions.")

        if detail and self.main_key:
            print("\n= Wallet Master Key =")
            print(" ID                             %s" % self.main_key_id)
            print(" Private                        %s" % self.main_key.is_private)
            print(" Depth                          %s" % self.main_key.depth)

        balances = self._balance_update()
        if detail > 1:
            for nw in self.networks():
                print("\n- NETWORK: %s -" % nw.name)
                print("- - Keys")
                if detail < 4:
                    ds = [self.key_depth]
                elif detail < 5:
                    if self.purpose == 45:
                        ds = [0, self.key_depth]
                    else:
                        ds = [0, self.depth_public_master, self.key_depth]
                else:
                    ds = range(8)
                for d in ds:
                    is_active = True
                    if detail > 3:
                        is_active = False
                    for key in self.keys(depth=d, network=nw.name, is_active=is_active):
                        print("%5s %-28s %-45s %-25s %25s" % (key.id, key.path, key.address, key.name,
                                                              Network(key.network_name).print_value(key.balance)))

                if detail > 2:
                    include_new = False
                    if detail > 3:
                        include_new = True
                    if self.multisig:
                        for t in self.transactions(include_new=include_new, account_id=0, network=nw.name):
                            print("\n- - Transactions")
                            spent = ""
                            if 'spent' in t and t['spent'] is False:
                                spent = "U"
                            status = ""
                            if t['status'] not in ['confirmed', 'unconfirmed']:
                                status = t['status']
                            print("%4d %64s %36s %8d %13d %s %s" % (t['transaction_id'], t['tx_hash'], t['address'],
                                                                    t['confirmations'], t['value'], spent, status))
                    else:
                        accounts = self.accounts(network=nw.name)
                        if not accounts:
                            accounts = [0]
                        for account_id in accounts:
                            print("\n- - Transactions Account %d" % account_id)
                            for t in self.transactions(include_new=include_new, account_id=account_id,
                                                       network=nw.name):
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

    def as_dict(self):
        """
        Return wallet information in dictionary format

        :param detail: Level of detail to show, from 0 to 6. With 0 no details and 6 most details
        :type detail: int

        :return dict:
        """

        keys = []
        transactions = []
        for nw in self.networks():
            for key in self.keys(network=nw['network_name'], as_dict=True):
                keys.append(key)

            if self.multisig:
                for t in self.transactions(include_new=True, account_id=0, network=nw['network_name']):
                    transactions.append(t)
            else:
                accounts = self.accounts(network=nw['network_name'])
                if not accounts:
                    accounts = [0]
                for account in accounts:
                    if account == 0:
                        account_id = 0
                    else:
                        account_id = account.account_id
                    for t in self.transactions(include_new=True, account_id=account_id, network=nw['network_name']):
                        transactions.append(t)

        return {
            'wallet_id': self.wallet_id,
            'name': self.name,
            'owner': self._owner,
            'scheme': self.scheme,
            'witness_type': self.witness_type,
            'main_network': self.network.name,
            'main_balance': self.balance(),
            'main_balance_str': self.balance(as_string=True),
            'balances': self._balances,
            'default_account_id': self.default_account_id,
            'multisig_n_required': self.multisig_n_required,
            'cosigner_wallet_ids': [w.wallet_id for w in self.cosigner],
            'cosigner_mainkey_wifs': [w.main_key.wif for w in self.cosigner],
            'sort_keys': self.sort_keys,
            'main_key_id': self.main_key_id,
            'encoding': self.encoding,
            'keys': keys,
            'transactions': transactions,
        }

    def as_json(self):
        """
        Get current key as json formatted string

        :return str:
        """
        adict = self.as_dict()
        return json.dumps(adict, indent=4)
