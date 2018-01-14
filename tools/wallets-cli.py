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
        wlt.utxos_update()
        return wlt
    else:
        print("Create wallet", search_wlt)
        # TODO: Create 


if __name__ == "__main__":
    while True:
        wlt = wallet_open()
        if not wlt:
            break
        while wlt is not None:
            print("Wallet %s" % wlt.name)
            action = input("\nWallet action? [U[pdate, [I]nfo, [S]end, [R]eceive, [C]lose: ").lower()
            if action == 'u':
                print("\nUpdating UTXOs")
                n_utxos = wlt.utxos_update()
                print("%d new utxo's found" % n_utxos)
            elif action == 'i':
                print(wlt.info())
            elif action == 's':
                to_addr = input("\nDestination address?: ")
                # TODO: check address
                amount = input("Amount in %s (max: ")
            elif action == 'r':
                addr = wlt.get_key().address
                print("\nReceive address is %s" % addr)
                if QRCODES_AVAILABLE:
                    qrcode = pyqrcode.create(addr)
                    print(qrcode.terminal())
            elif action == 'c':
                wlt = None
