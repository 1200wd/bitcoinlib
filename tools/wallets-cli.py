# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    Command line wallet manager. Use for testing and very basic (user unfriendly) wallet management
#
#    © 2018 January - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.wallets import HDWallet, wallets_list, wallet_exists
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import HDKey
from bitcoinlib.services.services import Service, ServiceError
try:
    import pyqrcode
    QRCODES_AVAILABLE = True
except:
    QRCODES_AVAILABLE = False

wallets_list = wallets_list()
print("Welcome to the Bitcoinlib Command line Wallet manager")
print("")


def wallet_open():
    print("Available wallets")
    for wn in wallets_list:
        if wn['parent_id']:
            continue
        print("[%d] %s %s %s" % (wn['id'], wn['name'], wn['network'], wn['owner']))
    search_wlt = input("\nEnter ID of wallet to open, a name for a new wallet or ENTER to exit: ")
    if not search_wlt:
        return False
    if search_wlt.isdigit():
        search_wlt = int(search_wlt)
    if wallet_exists(search_wlt):
        wlt = HDWallet(search_wlt)
        print("Opening wallet '%s'" % wlt.name)
        update_utxos(wlt)
        return wlt
    else:
        print("Create wallet", search_wlt)
        # TODO: Create 


def update_utxos(wlt):
    print("\nUpdating UTXOs")
    try:
        n_utxos = wlt.utxos_update()
        print("%d new utxo's found" % n_utxos)
    except:
        print("Error updating UTXO's")
        # print(e)


if __name__ == "__main__":
    while True:
        wlt = wallet_open()
        if not wlt:
            break
        while wlt is not None:
            srv = Service(network=wlt.network.network_name)
            print("\n== Wallet %s ==" % wlt.name)
            action = input("Wallet action? [U[pdate, [I]nfo, [S]end, [R]eceive, [C]lose: ").lower()
            if action == 'u':
                update_utxos(wlt)
            elif action == 'i':
                print(wlt.info())
            elif action == 's':
                wlt_balance = wlt.balance()
                if not wlt_balance:
                    print("Balance is 0, no UTXO's to spent")
                    continue
                to_addr = input("\nDestination address?: ")
                # TODO: check address
                update_utxos(wlt)
                amount = input("Amount in %s (max: %d)" % (wlt.network.currency_code, wlt_balance))
                estimated_fee = srv.estimatefee()
                user_fee = input("Fee in smallest denominator? [%d]" % estimated_fee)

            elif action == 'r':
                addr = wlt.get_key().address
                print("\nReceive address is %s" % addr)
                if QRCODES_AVAILABLE:
                    qrcode = pyqrcode.create(addr)
                    print(qrcode.terminal())
            elif action == 'c':
                wlt = None
