# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    CLW - Command Line Wallet manager
#    Create and manage BitcoinLib legacy, segwit single and multi-signature wallets from the commandline
#
#    © 2019 - 2024 January - 1200 Web Development <http://1200wd.com/>
#

import sys
import os
import argparse
import ast
from pprint import pprint
from bitcoinlib.wallets import Wallet, wallets_list, wallet_exists, wallet_delete, WalletError, wallet_empty
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey
from bitcoinlib.main import BITCOINLIB_VERSION
from bitcoinlib.config.config import DEFAULT_NETWORK
try:
    import pyqrcode
    QRCODES_AVAILABLE = True
except ImportError:
    QRCODES_AVAILABLE = False


# Show all errors in simple format without tracelog
def exception_handler(exception_type, exception, traceback):
    print("%s: %s" % (exception_type.__name__, exception))


sys.excepthook = exception_handler


def parse_args():
    parser = argparse.ArgumentParser(description='BitcoinLib command line wallet')
    parser.add_argument('--list-wallets', '-l', action='store_true',
                        help="List all known wallets in database")
    parser.add_argument('--generate-key', '-g', action='store_true', help="Generate a new masterkey, and"
                        " show passphrase, WIF and public account key. Can be used to create a new (multisig) wallet")
    parser.add_argument('--passphrase-strength', type=int, default=128,
                        help="Number of bits for passphrase key. Default is 128, lower is not advised but can "
                        "be used for testing. Set to 256 bits for more future-proof passphrases")
    parser.add_argument('--database', '-d',
                        help="URI of the database to use",)
    parser.add_argument('--wallet_name', '-w', nargs='?', default='',
                        help="Name of wallet to open. Provide wallet name or number when running wallet actions")
    parser.add_argument('--network', '-n',
                        help="Specify 'bitcoin', 'litecoin', 'testnet' or other supported network")
    parser.add_argument('--witness-type', '-j', metavar='WITNESS_TYPE', default=None,
                        help='Witness type of wallet: legacy, p2sh-segwit or segwit (default)')
    parser.add_argument('--yes', '-y', action='store_true', default=False,
                        help='Non-interactive mode, does not prompt for confirmation')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Quiet mode, no output writen to console')

    subparsers = parser.add_subparsers(required=False, dest='subparser_name')
    parser_new = subparsers.add_parser('new', description="Create new wallet")
    parser_new.add_argument('--wallet_name', '-w', nargs='?', default='', required=True,
                            help="Name of wallet to create or open. Provide wallet name or number when running wallet "
                            "actions")
    parser_new.add_argument('--password',
                            help='Password for BIP38 encrypted key. Use to create a wallet from a protected key')
    parser_new.add_argument('--network', '-n',
                            help="Specify 'bitcoin', 'litecoin', 'testnet' or other supported network")
    parser_new.add_argument('--passphrase', default=None, metavar="PASSPHRASE",
                            help="Passphrase to recover or create a wallet. Usually 12 or 24 words")
    parser_new.add_argument('--create-from-key', '-c', metavar='KEY',
                            help="Create a new wallet from specified key")
    parser_new.add_argument('--create-multisig', '-m', nargs='*', metavar='.',
                            help='[NUMBER_OF_SIGNATURES_REQUIRED, NUMBER_OF_SIGNATURES, KEY-1, KEY-2, ... KEY-N]'
                            'Specify number of signatures followed by the number of signatures required and '
                            'then a list of public or private keys for this wallet. Private keys will be '
                            'created if not provided in key list.'
                            '\nExample, create a 2-of-2 multisig wallet and provide 1 key and create another '
                            'key: -m 2 2 tprv8ZgxMBicQKsPd1Q44tfDiZC98iYouKRC2CzjT3HGt1yYw2zuX2awTotzGAZQ'
                            'EAU9bi2M5MCj8iedP9MREPjUgpDEBwBgGi2C8eK5zNYeiX8 tprv8ZgxMBicQKsPeUbMS6kswJc11zgV'
                            'EXUnUZuGo3bF6bBrAg1ieFfUdPc9UHqbD5HcXizThrcKike1c4z6xHrz6MWGwy8L6YKVbgJMeQHdWDp')
    parser_new.add_argument('--witness-type', '-j', metavar='WITNESS_TYPE', default=None,
                            help='Witness type of wallet: legacy, p2sh-segwit or segwit (default)')
    parser_new.add_argument('--cosigner-id', '-o', type=int, default=None,
                            help='Set this if wallet contains only public keys, more then one private key or if '
                            'you would like to create keys for other cosigners.')
    parser_new.add_argument('--database', '-d',
                            help="URI of the database to use",)
    parser_new.add_argument('--receive', '-r', action='store_true',
                            help="Show unused address to receive funds.")
    parser_new.add_argument('--yes', '-y', action='store_true', default=False,
                            help='Non-interactive mode, does not prompt for confirmation')
    parser_new.add_argument('--quiet', '-q', action='store_true',
                            help='Quiet mode, no output writen to console.')
    parser_new.add_argument('--disable-anti-fee-sniping', action='store_true', default=False,
                            help='Disable anti-fee-sniping, and set locktime in all transaction to zero.')

    group_wallet = parser.add_argument_group("Wallet Actions")
    group_wallet.add_argument('--wallet-remove', action='store_true',
                              help="Name or ID of wallet to remove, all keys and transactions will be deleted")
    group_wallet.add_argument('--wallet-info', '-i', action='store_true',
                              help="Show wallet information")
    group_wallet.add_argument('--update-utxos', '-x', action='store_true',
                              help="Update unspent transaction outputs (UTXO's) for this wallet")
    group_wallet.add_argument('--update-transactions', '-u', action='store_true',
                              help="Update all transactions and UTXO's for this wallet")
    group_wallet.add_argument('--wallet-empty', '-z', action='store_true',
                              help="Delete all keys and transactions from wallet, except for the masterkey(s). "
                                   "Use when updating fails or other errors occur. Please backup your database and "
                                   "masterkeys first. Update empty wallet again to restore your wallet.")
    group_wallet.add_argument('--receive', '-r', action='store_true',
                              help="Show unused address to receive funds.")
    group_wallet.add_argument('--cosigner-id', '-o', type=int, default=None,
                              help='Set this if wallet contains only public keys, more then one private key or if '
                              'you would like to create keys for other cosigners.')
    group_wallet.add_argument('--export-private', '-e', action='store_true',
                              help="Export private key for this wallet and exit")
    group_wallet.add_argument('--import-private', '-v',
                              help="Import private key in this wallet")

    group_transaction = parser.add_argument_group("Transactions")
    group_transaction.add_argument('--send', '-s', metavar=('ADDRESS', 'AMOUNT'), nargs=2,
                                   action='append',
                                   help="Create transaction to send amount to specified address. To send to "
                                        "multiple addresses, argument can be used multiple times.")
    group_transaction.add_argument('--number-of-change-outputs', type=int, default=1,
                                   help="Number of change outputs. Default is 1, increase for more privacy or "
                                        "to split funds")
    group_transaction.add_argument('--input-key-id', '-k', type=int, default=None,
                                   help="Use to create transaction with 1 specific key ID")
    group_transaction.add_argument('--sweep', metavar="ADDRESS",
                                   help="Sweep wallet, transfer all funds to specified address")
    group_transaction.add_argument('--fee', '-f', type=int, help="Transaction fee")
    group_transaction.add_argument('--fee-per-kb', '-b', type=int,
                                   help="Transaction fee in satoshi per kilobyte")
    group_transaction.add_argument('--push', '-p', action='store_true',
                                   help="Push created transaction to the network")
    group_transaction.add_argument('--import-tx', metavar="TRANSACTION",
                                   help="Import raw transaction hash or transaction dictionary in wallet and sign "
                                        "it with available key(s)")
    group_transaction.add_argument('--import-tx-file', '-a', metavar="FILENAME_TRANSACTION",
                                   help="Import transaction dictionary or raw transaction string from specified "
                                        "filename and sign it with available key(s)")
    group_transaction.add_argument('--rbf', action='store_true',
                                   help="Enable replace-by-fee flag. Allow to replace transaction with a new one "
                                        "with higher fees, to avoid transactions taking to long to confirm.")

    pa = parser.parse_args()

    if not pa.wallet_name:
        pa.list_wallets = True
    return pa


def get_passphrase(strength, interactive=False, quiet=False):
    passphrase = Mnemonic().generate(strength)
    if not quiet:
        print("Passphrase: %s" % passphrase)
        print("Please write down on paper and backup. With this key you can restore your wallet and all keys")
        if not interactive and input("\nType 'yes' if you understood and wrote down your key: ") not in ['yes', 'Yes', 'YES']:
            print("Exiting...")
            sys.exit()
    return passphrase


def create_wallet(wallet_name, args, db_uri, output_to):
    if args.network is None:
        args.network = DEFAULT_NETWORK
    print("CREATE wallet '%s' (%s network)" % (wallet_name, args.network), file=output_to)
    if args.create_multisig:
        if not isinstance(args.create_multisig, list) or len(args.create_multisig) < 2:
            raise WalletError("Please enter multisig creation parameter in the following format: "
                              "<number-of-signatures> <number-of-signatures-required> "
                              "<key-0> <key-1> [<key-2> ... <key-n>]")
        try:
            sigs_required = int(args.create_multisig[0])
        except ValueError:
            raise WalletError("Number of signatures required (first argument) must be a numeric value. %s" %
                     args.create_multisig[0])
        try:
            sigs_total = int(args.create_multisig[1])
        except ValueError:
            raise WalletError("Number of total signatures (second argument) must be a numeric value. %s" %
                     args.create_multisig[1])
        key_list = args.create_multisig[2:]
        keys_missing = sigs_total - len(key_list)
        if keys_missing < 0:
            raise WalletError("Invalid number of keys (%d required)" % sigs_total)
        if keys_missing:
            print("Not all keys provided, creating %d additional key(s)" % keys_missing, file=output_to)
            for _ in range(keys_missing):
                passphrase = get_passphrase(args.passphrase_strength, args.yes, args.quiet)
                key_list.append(HDKey.from_passphrase(passphrase, network=args.network))
        return Wallet.create(wallet_name, key_list, sigs_required=sigs_required, network=args.network,
                             cosigner_id=args.cosigner_id, db_uri=db_uri, witness_type=args.witness_type,
                             anti_fee_sniping=not(args.disable_anti_fee_sniping))
    elif args.create_from_key:
        from bitcoinlib.keys import get_key_format
        import_key = args.create_from_key
        kf = get_key_format(import_key)
        if kf['format'] == 'wif_protected':
            if not args.password:
                raise WalletError("This is a WIF protected key, please provide a password with the --password argument.")
            import_key, _ = HDKey._bip38_decrypt(import_key, args.password, args.network, args.witness_type)
        return Wallet.create(wallet_name, import_key, network=args.network, db_uri=db_uri,
                             witness_type=args.witness_type)
    else:
        passphrase = args.passphrase
        if passphrase is None:
            passphrase = get_passphrase(args.passphrase_strength, args.yes, args.quiet)
        if len(passphrase.split(' ')) < 3:
            raise WalletError("Please specify passphrase with 3 words or more. However less than 12 words is insecure!")
        hdkey = HDKey.from_passphrase(passphrase, network=args.network)
        return Wallet.create(wallet_name, hdkey, network=args.network, witness_type=args.witness_type,
                             password=args.password, db_uri=db_uri)


def create_transaction(wlt, send_args, args):
    output_arr = [(address, value) for [address, value] in send_args]
    return wlt.transaction_create(output_arr=output_arr, network=args.network, fee=args.fee, min_confirms=0,
                                  input_key_id=args.input_key_id,
                                  number_of_change_outputs=args.number_of_change_outputs,
                                  replace_by_fee=args.rbf)


def print_transaction(wt):
    pprint(wt.as_dict())


def main():
    args = parse_args()

    db_uri = args.database
    output_to = open(os.devnull, 'w') if args.quiet else sys.stdout
    wlt = None

    print("Command Line Wallet - BitcoinLib %s\n" % BITCOINLIB_VERSION, file=output_to)

    # --- General arguments ---
    # Generate key
    if args.generate_key:
        passphrase = get_passphrase(args.passphrase_strength, args.yes, args.quiet)
        hdkey = HDKey.from_passphrase(passphrase, witness_type=args.witness_type, network=args.network)
        if args.quiet:
            print(passphrase)
        else:
            print("Private Master key, to create multisig wallet on this machine:\n%s" % hdkey.wif_private())
        print("Public Master key, to share with other cosigner multisig wallets:\n%s" %
              hdkey.public_master(witness_type=args.witness_type, multisig=True).wif(), file=output_to)
        print("Network: %s" % hdkey.network.name, file=output_to)

    # List wallets
    elif args.list_wallets:
        print("BitcoinLib wallets:", file=sys.stdout)
        wallets = wallets_list(db_uri=db_uri)
        if not wallets:
            print("No wallets defined yet, use 'new' argument to create a new wallet. See clw new --help "
                  "for more info.")
        for w in wallets:
            if 'parent_id' in w and w['parent_id']:
                continue
            print("[%d] %s (%s) %s" % (w['id'], w['name'], w['network'], w['owner']))

    # Delete specified wallet
    elif args.wallet_remove:
        wallet_name = args.wallet_name
        if args.wallet_name.isdigit():
            wallet_name = int(args.wallet_name)
        if not wallet_exists(wallet_name, db_uri=db_uri):
            print("Wallet '%s' not found" % args.wallet_name, file=output_to)
        else:
            inp = wallet_name if (args.quiet or args.yes) else (
                input("Wallet '%s' with all keys and will be removed, without private key it cannot be restored."
                      "\nPlease retype exact name of wallet to proceed: " % args.wallet_name))
            if str(inp) == str(wallet_name):
                if wallet_delete(wallet_name, force=True, db_uri=db_uri):
                    print("Wallet %s has been removed" % wallet_name, file=output_to)
                else:
                    print("Error when deleting wallet", file=output_to)
            else:
                print("Specified wallet name incorrect", file=output_to)

    # Create or open wallet
    elif args.wallet_name:
        if args.subparser_name == 'new':
            if wallet_exists(args.wallet_name, db_uri=db_uri):
                print("Wallet with name '%s' already exists" % args.wallet_name, file=output_to)
            else:
                wlt = create_wallet(args.wallet_name, args, db_uri, output_to)
                args.wallet_info = True
        else:
            try:
                wlt = Wallet(args.wallet_name, db_uri=db_uri)
            except WalletError as e:
                print("Error: %s" % e.msg, file=output_to)

    if wlt is None:
        sys.exit()

    if args.network is None:
        args.network = wlt.network.name

    tx_import = None
    if not args.subparser_name:
        if args.import_private:
            if wlt.import_key(args.import_private):
                print("Private key imported", file=output_to)
            else:
                print("Failed to import key", file=output_to)
        elif args.wallet_empty:
            wallet_empty(args.wallet_name, args.database)
            print("Removed transactions and emptied wallet. Use --update-wallet option to update again.",
                  file=output_to)
        elif args.update_utxos:
            print("Updating wallet utxo's", file=output_to)
            wlt.utxos_update()
        elif args.update_transactions:
            print("Updating wallet transactions", file=output_to)
            wlt.scan(scan_gap_limit=3)
        elif args.export_private:
            if wlt.scheme == 'multisig':
                for w in wlt.cosigner:
                    if w.main_key and w.main_key.is_private:
                        print(w.main_key.wif)
            elif not wlt.main_key or not wlt.main_key.is_private:
                print("No private key available for this wallet", file=output_to)
            else:
                print(wlt.main_key.wif)
        elif args.import_tx_file or args.import_tx:
            if args.import_tx_file:
                try:
                    fn = args.import_tx_file
                    f = open(fn, "r")
                except FileNotFoundError:
                    print("File %s not found" % args.import_tx_file, file=output_to)
                    sys.exit()
                try:
                    tx_import = ast.literal_eval(f.read())
                except (ValueError, SyntaxError):
                    tx_import = f.read()
            elif args.import_tx:
                try:
                    tx_import = ast.literal_eval(args.import_tx)
                except (ValueError, SyntaxError):
                    tx_import = args.import_tx
            if tx_import:
                if isinstance(tx_import, dict):
                    wt = wlt.transaction_import(tx_import)
                else:
                    wt = wlt.transaction_import_raw(tx_import, network=args.network)
                wt.sign()
                if args.push:
                    res = wt.send()
                    if res:
                        if args.quiet:
                            print(wt.txid)
                        else:
                            print("Transaction pushed to network. Transaction ID: %s" % wt.txid)
                    else:
                        print("Error creating transaction: %s" % wt.error, file=output_to)
                wt.info()
                print("Signed transaction:", file=output_to)
                if not args.quiet:
                    print_transaction(wt)
        elif args.send:
            if args.fee_per_kb:
                raise WalletError("Fee-per-kb option not allowed with --send")
            try:
                wt = create_transaction(wlt, args.send, args)
            except WalletError as e:
                raise WalletError("Cannot create transaction: %s" % e.msg)
            wt.sign()
            print("Transaction created", file=output_to)
            wt.info()
            if args.push:
                wt.send()
                if wt.pushed:
                    if args.quiet:
                        print(wt.txid)
                    else:
                        print("Transaction pushed to network. Transaction ID: %s" % wt.txid)
                else:
                    print("Error creating transaction: %s" % wt.error, file=output_to)
            else:
                print("\nTransaction created but not sent yet. Transaction dictionary for export: ", file=output_to)
                if not args.quiet:
                    print_transaction(wt)
        elif args.sweep:
            broadcast = False
            print("Sweep wallet. Send all funds to %s" % args.sweep, file=output_to)
            if args.push:
                broadcast = True
            wt = wlt.sweep(args.sweep, broadcast=broadcast, network=args.network, fee_per_kb=args.fee_per_kb, fee=args.fee,
                           replace_by_fee=args.rbf)
            if not wt:
                raise WalletError("Error occurred when sweeping wallet: %s. Are UTXO's available and updated?" % wt)
            wt.info()
            if args.push:
                if wt.pushed:
                    if args.quiet:
                        print(wt.txid)
                    else:
                        print("Transaction pushed to network. Transaction ID: %s" % wt.txid)
                elif not wt:
                    print("Cannot sweep wallet, are UTXO's updated and available?", file=output_to)
                else:
                    print("Error sweeping wallet: %s" % wt.error, file=output_to)
            else:
                print("\nTransaction created but not sent yet. Transaction dictionary for export: ", file=output_to)
                print_transaction(wt)

    if args.receive and not (args.send or args.sweep):
        key = wlt.get_key(network=args.network, cosigner_id=args.cosigner_id)
        if args.quiet:
            print(key.address)
        else:
            print("Receive address: %s" % key.address)
        if QRCODES_AVAILABLE:
            qrcode = pyqrcode.create(key.address)
            print(qrcode.terminal(), file=output_to)
        else:
            print("Install qr code module to show QR codes: pip install pyqrcode", file=output_to)
    elif args.wallet_info:
        print("Wallet info for %s" % wlt.name, file=output_to)
        if not args.quiet:
            wlt.info()


if __name__ == '__main__':
    main()
