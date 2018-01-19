# -*- cod   ing: utf-8 -*-
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
from bitcoinlib.wallets import HDWallet, wallets_list, wallet_exists, wallet_delete, WalletError
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.networks import Network
from bitcoinlib.keys import HDKey
from bitcoinlib.services.services import Service, ServiceError
try:
    import pyqrcode
    QRCODES_AVAILABLE = True
except:
    QRCODES_AVAILABLE = False

DEFAULT_NETWORK = 'bitcoin'


def parse_args():
    parser = argparse.ArgumentParser(description='BitcoinLib CLI')
    parser.add_argument('--wallet-name', '-w',
                        help="Name of wallet to create or open. Used to store your all your wallet keys "
                             "and will be printed on each paper wallet")
    parser.add_argument('--network', '-n', help="Specify 'bitcoin', 'testnet' or other supported network",
                        default=DEFAULT_NETWORK)
    parser.add_argument('--wallet-remove',
                        help="Name or ID of wallet to remove, all keys and related information will be deleted")
    parser.add_argument('--list-wallets', '-l', action='store_true',
                        help="List all known wallets in bitcoinlib database")
    parser.add_argument('--wallet-info', '-i', action='store_true',
                        help="Show wallet information")
    parser.add_argument('--passphrase', nargs="*", default=None,
                        help="Passphrase to recover or create a wallet")
    parser.add_argument('--passphrase-strength', type=float, default=128,
                        help="Number of bits for passphrase key")
    parser.add_argument('--receive', '-r', help="Show unused address to receive funds", action='store_true')
    parser.add_argument('--scan', '-s', action='store_true',
                        help="Scan and update wallet with all addresses, transactions and balances")
    group = parser.add_argument_group("Send / Create transaction")
    group.add_argument('--create-transaction', '-t',
                       help="Create transaction. Specify address followed by amount", nargs='*')
    group.add_argument('--fee', '-f', type=str,
                       help="Transaction fee")
    group.add_argument('--push', '-p', action='store_true',
                       help="Push created transaction to the network")

    pa = parser.parse_args()
    if pa.receive and pa.create_transaction:
        parser.error("Please select receive or create transaction option not both")
    if len(sys.argv) == 1:
        pa.list_wallets = True
    if pa.wallet_name and len(sys.argv) == 3:
        pa.wallet_info = True
    return pa


def create_wallet(wallet_name, args):
    print("\nCREATE wallet '%s' (%s network)" % (wallet_name, args.network))
    passphrase = args.passphrase
    if passphrase is None:
        inp_passphrase = Mnemonic('english').generate(args.passphrase_strength)
        print("\nYour mnemonic private key sentence is: %s" % inp_passphrase)
        print("\nPlease write down on paper and backup. With this key you can restore your wallet and all keasys")
        passphrase = inp_passphrase.split(' ')
        inp = input("\nType 'yes' if you understood and wrote down your key: ")
        if inp not in ['yes', 'Yes', 'YES']:
            print("Exiting...")
            sys.exit()
    elif not passphrase:
        passphrase = input("Enter Passphrase: ")
    if not isinstance(passphrase, list):
        passphrase = passphrase.split(' ')
    elif len(passphrase) == 1:
        passphrase = passphrase[0].split(' ')
    if len(passphrase) < 12:
        print("Please specify passphrase with 12 words or more")
        sys.exit()
    passphrase = ' '.join(passphrase)
    seed = binascii.hexlify(Mnemonic().to_seed(passphrase))
    hdkey = HDKey().from_seed(seed, network=args.network)
    return HDWallet.create(name=wallet_name, network=args.network, key=hdkey.wif())


def create_transaction(wlt, send_args, fee):
    output_arr = []
    while send_args:
        if len(send_args) == 1:
            raise ValueError("Invalid number of transaction input use <address1> <amount1> ... <address_n> <amount_n>")
        try:
            amount = int(send_args[1])
        except:
            print("Amount must be a numeric value. %s" % send_args[1])
            sys.exit()
        output_arr.append((send_args[0], amount))
        send_args = send_args[2:]
    try:
        fee = int(fee)
    except:
        print("Fee must be a numeric value. %s" % fee)
        sys.exit()
    return wlt.transaction_create(output_arr=output_arr, transaction_fee=fee)


if __name__ == '__main__':
    # --- Parse commandline arguments ---
    args = parse_args()
    # network_obj = Network(args.network)

    # List wallets, then exit
    if args.list_wallets:
        print("\nBitcoinlib wallets:")
        for w in wallets_list():
            if 'parent_id' in w and w['parent_id']:
                continue
            print("[%d] %s (%s) %s" % (w['id'], w['name'], w['network'], w['owner']))
        print("\n")
        sys.exit()

    # Delete specified wallet, then exit
    if args.wallet_remove:
        if not wallet_exists(args.wallet_remove):
            print("Wallet '%s' not found" % args.wallet_remove)
            sys.exit()
        inp = input("\nWallet '%s' with all keys and will be removed, without private key it cannot be restored."
                    "\nPlease retype exact name of wallet to proceed: " % args.wallet_remove)
        if inp == args.wallet_remove:
            if wallet_delete(args.wallet_remove, force=True):
                print("\nWallet %s has been removed" % args.wallet_remove)
            else:
                print("\nError when deleting wallet")
            sys.exit()

    wlt = None
    if not args.wallet_name:
        print("Please specify wallet name to perform an action")
    elif not args.wallet_name.isdigit() and not wallet_exists(args.wallet_name):
        if input("Wallet %s does not exist, create new wallet [yN]? " % args.wallet_name).lower() == 'y':
            wlt = create_wallet(args.wallet_name, args)
            args.wallet_info = True
    else:
        try:
            wlt = HDWallet(args.wallet_name)
            if args.passphrase is not None:
                print("WARNING: Using passphrase option for existing wallet ignored")
                args.wallet_info = True
        except WalletError as e:
            print("Could nog open wallet %s. %s" % (args.wallet_name, e.msg))
    if wlt is None:
        sys.exit()

    if args.wallet_info:
        print("Updating wallet")
        wlt.utxos_update()
        print("Wallet info for %s" % wlt.name)
        wlt.info()
        sys.exit()
    if args.receive:
        addr = wlt.get_key().address
        print("\nReceive address is %s" % addr)
        if QRCODES_AVAILABLE:
            qrcode = pyqrcode.create(addr)
            print(qrcode.terminal())
        else:
            print("Install qr code module to show QR codes: pip install pyqrcode")
    if args.scan:
        print("Scanning wallet: updating addresses, transactions and balances")
        print("Can take a while")
        wlt.scan()
    if args.create_transaction:
        t = create_transaction(wlt, args.create_transaction, args.fee)
        from pprint import pprint
        td = t.dict()
        print("Transaction created")
        print("Inputs")
        for ti in td['inputs']:
            print("-", ti['address'], ti['prev_hash'])
        print("Outputs")
        for to in td['outputs']:
            print("-", to['address'], to['amount'])
        if args.push:
            res = wlt.send(t)
            print("Send transaction result" % res)
        else:
            print("Transaction not send yet. Raw transaction to analyse or send online: ", t.raw_hex())


# # --- Create or open wallet ---
    # if wallet_exists(wallet_name):
    #     if args.recover_wallet_passphrase:
    #         print("\nWallet %s already exists. Please specify (not existing) wallet name for wallet to recover" %
    #               wallet_name)
    #         sys.exit()
    #     wallet = HDWallet(wallet_name)
    #     if wallet.network.network_name != args.network:
    #         print("\nNetwork setting (%s) ignored. Using network from defined wallet instead: %s" %
    #               (args.network, wallet.network.network_name))
    #         network = wallet.network.network_name
    #         network_obj = Network(network)
    #     print("\nOpen wallet '%s' (%s network)" % (wallet_name, network))
    # else:
    #     print("\nCREATE wallet '%s' (%s network)" % (wallet_name, network))
    #     if not args.recover_wallet_passphrase:
    #         words = Mnemonic('english').generate(args.passphrase_strength)
    #         print("\nYour mnemonic private key sentence is: %s" % words)
    #         print("\nPlease write down on paper and backup. With this key you can restore all paper wallets if "
    #               "something goes wrong during this process. You can / have to throw away this private key after "
    #               "the paper wallets are distributed.")
    #         inp = input("\nType 'yes' if you understood and wrote down your key: ")
    #         if inp not in ['yes', 'Yes', 'YES']:
    #             print("Exiting...")
    #             sys.exit()
    #     else:
    #         words = args.recover_wallet_passphrase
    #
    #     seed = binascii.hexlify(Mnemonic().to_seed(words))
    #     hdkey = HDKey().from_seed(seed, network=network)
    #     wallet = BulkPaperWallet.create(name=wallet_name, network=network, key=hdkey.wif())
    #     wallet.new_key("Input")
    #     wallet.new_account("Outputs", account_id=OUTPUT_ACCOUNT_ID)
    #
    # if args.recover_wallet_passphrase:
    #     print("Wallet recovered, now updating keys and balances...")
    #     stuff_updated = True
    #     while stuff_updated:
    #         for kn in range(0, 10):
    #             wallet.new_key(account_id=OUTPUT_ACCOUNT_ID)
    #             wallet.new_key_change(account_id=OUTPUT_ACCOUNT_ID)
    #         stuff_updated = wallet.utxos_update()
    #     wallet.info()
    #     sys.exit()
    #
    # # --- Estimate transaction fees ---
    # srv = Service(network=network)
    # if args.fee_per_kb:
    #     fee_per_kb = args.fee_per_kb
    # else:
    #     fee_per_kb = srv.estimatefee()
    #     if not srv.results:
    #         raise IOError("No response from services, could not determine estimated transaction fees. "
    #                       "You can use --fee-per-kb option to determine fee manually and avoid this error.")
    # tr_size = 100 + (1 * 150) + (len(outputs_arr) * 50)
    # estimated_fee = int((tr_size / 1024) * fee_per_kb)
    # if estimated_fee < 0:
    #     raise IOError("No valid response from any service provider, could not determine estimated transaction fees. "
    #                   "You can use --fee-per-kb option to determine fee manually and avoid this error.")
    # print("Estimated fee is for this transaction is %s (%d satoshis/kb)" %
    #       (network_obj.print_value(estimated_fee), fee_per_kb))
    # print("Total value of outputs is %s" % network_obj.print_value(total_amount))
    # total_transaction = total_amount + estimated_fee
    #

# wallets_list = wallets_list()
# print("Welcome to the Bitcoinlib Command line Wallet manager")
# print("")
#
#
# def wallet_open():
#     print("Available wallets")
#     for wn in wallets_list:
#         if wn['parent_id']:
#             continue
#         print("[%d] %s %s %s" % (wn['id'], wn['name'], wn['network'], wn['owner']))
#     search_wlt = input("\nEnter ID of wallet to open, a name for a new wallet or ENTER to exit: ")
#     if not search_wlt:
#         return False
#     if search_wlt.isdigit():
#         search_wlt = int(search_wlt)
#     if wallet_exists(search_wlt):
#         wlt = HDWallet(search_wlt)
#         print("Opening wallet '%s'" % wlt.name)
#         update_utxos(wlt)
#         return wlt
#     else:
#         print("Create wallet", search_wlt)
#         # TODO: Create
#
#
# def update_utxos(wlt):
#     print("\nUpdating UTXOs")
#     try:
#         n_utxos = wlt.utxos_update()
#         print("%d new utxo's found" % n_utxos)
#     except:
#         print("Error updating UTXO's")
#         # print(e)
#
#
# if __name__ == "__main__":
#     while True:
#         wlt = wallet_open()
#         if not wlt:
#             break
#         while wlt is not None:
#             srv = Service(network=wlt.network.network_name)
#             print("\n== Wallet %s ==" % wlt.name)
#             action = input("Wallet action? [U[pdate, [I]nfo, [S]end, [R]eceive, [C]lose: ").lower()
#             if action == 'u':
#                 update_utxos(wlt)
#             elif action == 'i':
#                 print(wlt.info())
#             elif action == 's':
#                 wlt_balance = wlt.balance()
#                 if not wlt_balance:
#                     print("Balance is 0, no UTXO's to spent")
#                     continue
#                 to_addr = input("\nDestination address?: ")
#                 # TODO: check address
#                 update_utxos(wlt)
#                 amount = input("Amount in %s (max: %d)" % (wlt.network.currency_code, wlt_balance))
#                 estimated_fee = srv.estimatefee()
#                 user_fee = input("Fee in smallest denominator? [%d]" % estimated_fee)
#
#             elif action == 'r':
#                 addr = wlt.get_key().address
#                 print("\nReceive address is %s" % addr)
#                 if QRCODES_AVAILABLE:
#                     qrcode = pyqrcode.create(addr)
#                     print(qrcode.terminal())
#             elif action == 'c':
#                 wlt = None
