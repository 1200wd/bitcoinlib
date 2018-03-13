# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    Command line wallet manager. Use for testing and very basic (user unfriendly) wallet management
#
#    © 2018 January - 1200 Web Development <http://1200wd.com/>
#

import sys
import argparse
import binascii
from bitcoinlib.db import DEFAULT_DATABASE, DEFAULT_DATABASEDIR
from bitcoinlib.wallets import HDWallet, wallets_list, wallet_exists, wallet_delete, WalletError
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey
from bitcoinlib.services.services import Service
try:
    import pyqrcode
    QRCODES_AVAILABLE = True
except ImportError:
    QRCODES_AVAILABLE = False
try:
    input = raw_input
except NameError:
    pass

DEFAULT_NETWORK = 'bitcoin'


def parse_args():
    parser = argparse.ArgumentParser(description='BitcoinLib CLI')
    parser.add_argument('wallet_name', nargs='?', default='',
                        help="Name of wallet to create or open. Used to store your all your wallet keys "
                             "and will be printed on each paper wallet")
    parser.add_argument('--network', '-n',
                        help="Specify 'bitcoin', 'testnet' or other supported network")
    parser.add_argument('--database', '-d',
                        help="Name of specific database file to use",)
    parser.add_argument('--wallet-remove', action='store_true',
                        help="Name or ID of wallet to remove, all keys and related information will be deleted")
    parser.add_argument('--list-wallets', '-l', action='store_true',
                        help="List all known wallets in bitcoinlib database")
    parser.add_argument('--wallet-info', '-i', action='store_true',
                        help="Show wallet information")
    parser.add_argument('--passphrase', nargs="*", default=None,
                        help="Passphrase to recover or create a wallet. Usually 12 or 24 words")
    parser.add_argument('--passphrase-strength', type=float, default=128,
                        help="Number of bits for passphrase key")
    parser.add_argument('--create-multisig', '-m', nargs='*', metavar=('NUMBER_OF_SIGNATURES_REQUIRED', 'KEYS'),
                        help='Specificy number of signatures required followed by a list of signatures.'
                             '\nExample: -m 2 tprv8ZgxMBicQKsPd1Q44tfDiZC98iYouKRC2CzjT3HGt1yYw2zuX2awTotzGAZQEAU9bi2'
                             'M5MCj8iedP9MREPjUgpDEBwBgGi2C8eK5zNYeiX8 tprv8ZgxMBicQKsPeUbMS6kswJc11zgVEXUnUZuGo3bF'
                             '6bBrAg1ieFfUdPc9UHqbD5HcXizThrcKike1c4z6xHrz6MWGwy8L6YKVbgJMeQHdWDp')
    parser.add_argument('--receive', '-r', help="Show unused address to receive funds", nargs='?', type=int, const=1,
                        metavar=('NUMBER_OF_ADDRESSES'))
    parser.add_argument('--scan', '-s', action='store_true',
                        help="Scan and update wallet with all addresses, transactions and balances")
    group = parser.add_argument_group("Send / Create transaction")
    group.add_argument('--create-transaction', '-t', metavar=('ADDRESS_1', 'AMOUNT_1'),
                       help="Create transaction. Specify address followed by amount. Repeat for multiple outputs",
                       nargs='*')
    group.add_argument('--sweep', metavar="ADDRESS",
                       help="Sweep wallet, transfer all funds to specified address")
    group.add_argument('--fee', '-f', type=int,
                       help="Transaction fee")
    group.add_argument('--fee-per-kb', type=int, help="Transaction fee in sathosis (or smallest denominator) per "
                                                      "kilobyte")
    group.add_argument('--push', '-p', action='store_true',
                       help="Push created transaction to the network")

    pa = parser.parse_args()
    if pa.receive and pa.create_transaction:
        parser.error("Please select receive or create transaction option not both")
    if pa.wallet_name:
        pa.wallet_info = True
    else:
        pa.list_wallets = True
    return pa


def create_wallet(wallet_name, args, databasefile):
    if args.network is None:
        args.network = DEFAULT_NETWORK
    print("\nCREATE wallet '%s' (%s network)" % (wallet_name, args.network))
    if args.create_multisig:
        if not isinstance(args.create_multisig, list) or len(args.create_multisig) < 3:
            clw_exit("Please enter multisig creation parameter in the following format: "
                     "<number-of-signatures-required> <key-0> <key-1> [<key-2> ... <key-n>]")
        try:
            sigs_required = int(args.create_multisig[0])
        except ValueError:
            clw_exit("Number of signatures required (first argument) must be a numeric value. %s" %
                     args.create_multisig[0])
        key_list = args.create_multisig[1:]
        return HDWallet.create_multisig(name=wallet_name, key_list=key_list, sigs_required=sigs_required,
                                        network=args.network, databasefile=databasefile)
    else:
        passphrase = args.passphrase
        if passphrase is None:
            inp_passphrase = Mnemonic('english').generate(args.passphrase_strength)
            print("\nYour mnemonic private key sentence is: %s" % inp_passphrase)
            print("\nPlease write down on paper and backup. With this key you can restore your wallet and all keys")
            passphrase = inp_passphrase.split(' ')
            inp = input("\nType 'yes' if you understood and wrote down your key: ")
            if inp not in ['yes', 'Yes', 'YES']:
                clw_exit("Exiting...")
        elif not passphrase:
            passphrase = input("Enter Passphrase: ")
        if not isinstance(passphrase, list):
            passphrase = passphrase.split(' ')
        elif len(passphrase) == 1:
            passphrase = passphrase[0].split(' ')
        if len(passphrase) < 12:
            clw_exit("Please specify passphrase with 12 words or more")
        passphrase = ' '.join(passphrase)
        seed = binascii.hexlify(Mnemonic().to_seed(passphrase))
        hdkey = HDKey().from_seed(seed, network=args.network)
        return HDWallet.create(name=wallet_name, network=args.network, key=hdkey.wif(), databasefile=databasefile)


def create_transaction(wlt, send_args, fee, args):
    output_arr = []
    while send_args:
        if len(send_args) == 1:
            raise ValueError("Invalid number of transaction input use <address1> <amount1> ... <address_n> <amount_n>")
        try:
            amount = int(send_args[1])
        except ValueError:
            clw_exit("Amount must be a integer value: %s" % send_args[1])
        output_arr.append((send_args[0], amount))
        send_args = send_args[2:]
    return wlt.transaction_create(output_arr=output_arr, transaction_fee=args.fee, network=args.network, min_confirms=0)


def clw_exit(msg=None):
    if msg:
        print(msg)
    sys.exit()


if __name__ == '__main__':
    print("Command Line Wallet for BitcoinLib\n")
    # --- Parse commandline arguments ---
    args = parse_args()
    # network_obj = Network(args.network)

    databasefile = DEFAULT_DATABASE
    if args.database:
        databasefile = DEFAULT_DATABASEDIR + args.database

    # List wallets, then exit
    if args.list_wallets:
        print("Bitcoinlib wallets:")
        for w in wallets_list(databasefile=databasefile):
            if 'parent_id' in w and w['parent_id']:
                continue
            print("[%d] %s (%s) %s" % (w['id'], w['name'], w['network'], w['owner']))
        clw_exit()

    # Delete specified wallet, then exit
    if args.wallet_remove:
        if not wallet_exists(args.wallet_name, databasefile=databasefile):
            clw_exit("Wallet '%s' not found" % args.wallet_remove)
        inp = input("\nWallet '%s' with all keys and will be removed, without private key it cannot be restored."
                    "\nPlease retype exact name of wallet to proceed: " % args.wallet_name)
        if inp == args.wallet_name:
            if wallet_delete(args.wallet_name, force=True, databasefile=databasefile):
                clw_exit("\nWallet %s has been removed" % args.wallet_name)
            else:
                clw_exit("\nError when deleting wallet")
        else:
            clw_exit("\nSpecified wallet name incorrect")

    wlt = None
    if args.wallet_name and not args.wallet_name.isdigit() and \
            not wallet_exists(args.wallet_name, databasefile=databasefile):
        if input("Wallet %s does not exist, create new wallet [yN]? " % args.wallet_name).lower() == 'y':
            wlt = create_wallet(args.wallet_name, args, databasefile)
            args.wallet_info = True
    else:
        try:
            wlt = HDWallet(args.wallet_name, databasefile=databasefile)
            if args.passphrase is not None:
                print("WARNING: Using passphrase options for existing wallet ignored")
        except WalletError as e:
            clw_exit("Error: %s" % e.msg)
    if wlt is None:
        clw_exit("Could not open wallet %s" % args.wallet_name)

    if args.network is None:
        args.network = wlt.network.network_name

    if args.receive:
        keys = wlt.get_key(network=args.network, number_of_keys=args.receive)
        keys = [keys] if not isinstance(keys, list) else keys
        print("Receive address(es):")
        for key in keys:
            addr = key.address
            print(addr)
            if QRCODES_AVAILABLE:
                qrcode = pyqrcode.create(addr)
                print(qrcode.terminal())
        if not QRCODES_AVAILABLE:
            print("Install qr code module to show QR codes: pip install pyqrcode")
        clw_exit()
    if args.scan:
        print("Scanning wallet: updating addresses, transactions and balances")
        print("Can take a while")
        wlt.scan()
        print("Scanning complete, show wallet info")
        wlt.info()
        clw_exit()
    if args.create_transaction == []:
        clw_exit("Missing arguments for --create-transaction/-t option")
    if args.create_transaction:
        fee = args.fee
        if not fee:
            srv = Service(network=args.network)
            fee = srv.estimatefee()
        try:
            wt = create_transaction(wlt, args.create_transaction, fee, args)
        except WalletError as e:
            clw_exit("Cannot create transaction: %s" % e.msg)
        wt.sign()
        print("Transaction created")
        wt.info()
        if args.push:
            res = wt.send()
            if res:
                print("Transaction pushed to network. Transaction ID: %s" % wt.hash)
            else:
                print("Error creating transaction: %s" % wt.error)
        else:
            print("Transaction created but not send yet. Raw transaction to analyse or send online: ", wt.raw_hex())
        clw_exit()
    if args.sweep:
        if args.fee:
            clw_exit("Fee option not allowed with --sweep")
        offline = True
        print("Sweep wallet. Send all funds to %s" % args.sweep)
        if args.push:
            offline = False
        wt = wlt.sweep(args.sweep, offline=offline, network=args.network, fee_per_kb=args.fee_per_kb)
        if not wt:
            clw_exit("Error occurred when sweeping wallet: %s. Are UTXO's available and updated?" % wt)
        wt.info()
        if args.push:
            if wt and wt.pushed:
                print("Transaction pushed to network. Transaction ID: %s" % wt.hash)
            elif not wt:
                print("Cannot sweep wallet, are UTXO's updated and available?")
            else:
                print("Error sweeping wallet: %s" % wt.error)
        else:
            print("Transaction created but not send yet. Raw transaction to analyse or send online: ", wt.raw_hex())
        clw_exit()

    print("Updating wallet")
    wlt.utxos_update()
    print("Wallet info for %s" % wlt.name)
    wlt.info()
