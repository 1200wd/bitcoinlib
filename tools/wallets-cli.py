# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    Command line wallet manager. Use for testing and very basic (user unfriendly) wallet management
#
#    © 2018 January - 1200 Web Development <http://1200wd.com/>
#

import argparse
from bitcoinlib.wallets import HDWallet, wallets_list, wallet_exists
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey
from bitcoinlib.services.services import Service, ServiceError
try:
    import pyqrcode
    QRCODES_AVAILABLE = True
except:
    QRCODES_AVAILABLE = False

DEFAULT_WALLET_NAME = 'MyWallet'
DEFAULT_NETWORK = 'bitcoin'


def parse_args():
    parser = argparse.ArgumentParser(description='BitcoinLib CLI')
    parser.add_argument('--wallet-name', '-w', default=DEFAULT_WALLET_NAME,
                        help="Name of wallet to create or open. Used to store your all your wallet keys "
                             "and will be printed on each paper wallet")
    parser.add_argument('--network', '-n', help="Specify 'bitcoin', 'testnet' or other supported network",
                        default=DEFAULT_NETWORK)
    parser.add_argument('--wallet-remove',
                        help="Name of wallet to remove, all keys and related information will be deleted")
    parser.add_argument('--list-wallets', '-l', action='store_true',
                        help="List all known wallets in bitcoinlib database")
    parser.add_argument('--wallet-info', '-i', action='store_true',
                        help="Show wallet information")
    parser.add_argument('--recover-wallet-passphrase',
                        help="Passphrase - sequence of words - to recover and regenerate a previous wallet")
    parser.add_argument('--fee-per-kb', '-k', type=int,
                        help="Fee in Satoshi's per kilobyte")

    pa = parser.parse_args()
    if pa.outputs_repeat and pa.outputs is None:
        parser.error("--output_repeat requires --outputs")
    if not pa.wallet_remove and not pa.list_wallets and not pa.wallet_info and not pa.recover_wallet_passphrase \
            and not pa.test_pdf and not (pa.outputs or pa.outputs_import):
        parser.error("Either --outputs or --outputs-import should be specified")
    return pa


if __name__ == '__main__':
    # --- Parse commandline arguments ---
    args = parse_args()

    wallet_name = args.wallet_name
    network = args.network
    network_obj = Network(network)
    style_file = args.style
    template_file = args.template

    # List wallets, then exit
    if args.list_wallets:
        print("\nBitcoinlib wallets:")
        for w in wallets_list():
            print(w['name'])
        print("\n")
        sys.exit()

    if args.wallet_info:
        print("Wallet info for %s" % args.wallet_name)
        if wallet_exists(args.wallet_name):
            wallet = BulkPaperWallet(args.wallet_name)
            # wallet.utxos_update()
            wallet.info()
        else:
            raise ValueError("Wallet '%s' not found" % args.wallet_name)
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

    # --- Create or open wallet ---
    if wallet_exists(wallet_name):
        if args.recover_wallet_passphrase:
            print("\nWallet %s already exists. Please specify (not existing) wallet name for wallet to recover" %
                  wallet_name)
            sys.exit()
        wallet = BulkPaperWallet(wallet_name)
        if wallet.network.network_name != args.network:
            print("\nNetwork setting (%s) ignored. Using network from defined wallet instead: %s" %
                  (args.network, wallet.network.network_name))
            network = wallet.network.network_name
            network_obj = Network(network)
        print("\nOpen wallet '%s' (%s network)" % (wallet_name, network))
    else:
        print("\nCREATE wallet '%s' (%s network)" % (wallet_name, network))
        if not args.recover_wallet_passphrase:
            words = Mnemonic('english').generate(args.passphrase_strength)
            print("\nYour mnemonic private key sentence is: %s" % words)
            print("\nPlease write down on paper and backup. With this key you can restore all paper wallets if "
                  "something goes wrong during this process. You can / have to throw away this private key after "
                  "the paper wallets are distributed.")
            inp = input("\nType 'yes' if you understood and wrote down your key: ")
            if inp not in ['yes', 'Yes', 'YES']:
                print("Exiting...")
                sys.exit()
        else:
            words = args.recover_wallet_passphrase

        seed = binascii.hexlify(Mnemonic().to_seed(words))
        hdkey = HDKey().from_seed(seed, network=network)
        wallet = BulkPaperWallet.create(name=wallet_name, network=network, key=hdkey.wif())
        wallet.new_key("Input")
        wallet.new_account("Outputs", account_id=OUTPUT_ACCOUNT_ID)

    if args.recover_wallet_passphrase:
        print("Wallet recovered, now updating keys and balances...")
        stuff_updated = True
        while stuff_updated:
            for kn in range(0, 10):
                wallet.new_key(account_id=OUTPUT_ACCOUNT_ID)
                wallet.new_key_change(account_id=OUTPUT_ACCOUNT_ID)
            stuff_updated = wallet.utxos_update()
        wallet.info()
        sys.exit()

    # --- Estimate transaction fees ---
    srv = Service(network=network)
    if args.fee_per_kb:
        fee_per_kb = args.fee_per_kb
    else:
        fee_per_kb = srv.estimatefee()
        if not srv.results:
            raise IOError("No response from services, could not determine estimated transaction fees. "
                          "You can use --fee-per-kb option to determine fee manually and avoid this error.")
    tr_size = 100 + (1 * 150) + (len(outputs_arr) * 50)
    estimated_fee = int((tr_size / 1024) * fee_per_kb)
    if estimated_fee < 0:
        raise IOError("No valid response from any service provider, could not determine estimated transaction fees. "
                      "You can use --fee-per-kb option to determine fee manually and avoid this error.")
    print("Estimated fee is for this transaction is %s (%d satoshis/kb)" %
          (network_obj.print_value(estimated_fee), fee_per_kb))
    print("Total value of outputs is %s" % network_obj.print_value(total_amount))
    total_transaction = total_amount + estimated_fee


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
