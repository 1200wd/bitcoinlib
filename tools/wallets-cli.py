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
    search_wlt = input("\nEnter ID of wallet to open or enter a name for a new wallet: ")

    if search_wlt.isdigit():
        search_wlt = int(search_wlt)
    if wallet_exists(search_wlt):
        return HDWallet(search_wlt)
    else:
        print("Create wallet", search_wlt)
        # TODO


if __name__ == "__main__":
    while True:
        wlt = wallet_open()
        while wlt is not None:
            print("Wallet %s" % wlt.name)
            action = input("\nWallet action? [I]nfo, [S]end, [R]eceive, [W]allet setup [C]lose: ").lower()
            if action == 'i':
                print(wlt.info())
            elif action == 'c':
                wlt = None
4