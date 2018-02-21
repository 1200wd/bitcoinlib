# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Creating and Using Cryptocurrency Wallets
#
#    © 2017 November - 1200 Web Development <http://1200wd.com/>
#

from pprint import pprint
from bitcoinlib.services.services import *


# Tests for specific provider
srv = Service(network='bitcoin', providers=['estimatefee'])
print("Estimated bitcoin transaction fee:", srv.estimatefee(1000))

# Get Balance and UTXO's for given bitcoin testnet3 addresses
addresslst = ['mfvFzusKPZzGBAhS69AWvziRPjamtRhYpZ', 'mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2']
srv = Service(network='testnet', min_providers=5)
print("Getbalance, first result only: %s" % srv.getbalance(addresslst))
print("\nAll results as dict:")
pprint(srv.results)
print("\nUTXOs list:")
pprint(srv.getutxos(addresslst))

# GET Raw Transaction data for given Transaction ID
t = 'd3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955'
print("\nGET Raw Transaction:")
pprint(Service(network='testnet', min_providers=2).getrawtransaction(t))

# DECODE Raw Transaction
rt = '0100000001573ae2bb133f88cba0a96e9cf6179810a9fbdc2dc550c123b80c1ae1fc354855000000006b48304502200204f394bd46' \
     '324d677cf94768be99f5f7a0225545d1c9a1250a644873109b11022100a7e0d741705f3ea4fee169fa1b7907ecc54a26927e74f1f0' \
     'e339a824e55ee256012103e428723c145e61c35c070da86faadaf0fab21939223a5e6ce3e1cfd76bad133dffffffff02404b4c0000' \
     '0000001976a914ac19d3fd17710e6b9a331022fe92c693fdf6659588ac88e3bf0b000000001976a91463c98ad8e6b43c9b68fd81b2' \
     '02bb7266e439b1b988ac00000000'
print("\nDECODE Raw Transaction:")
pprint(Service(network='testnet').decoderawtransaction(rt))

# SEND Raw Transaction data (UTXO's already spent, so should give 'missing inputs' error)
rt = '010000000108004b4c0394a211d4ec0d344b70bf1e3b1ce1731d11d1d30279ab0c0f6d9fd7000000006c493046022100ab18a72f7' \
     '87e4c8ea5d2f983b99df28d27e13482b91fd6d48701c055af92f525022100d1c26b8a779896a53a026248388896501e724e46407f' \
     '14a4a1b6478d3293da24012103e428723c145e61c35c070da86faadaf0fab21939223a5e6ce3e1cfd76bad133dffffffff0240420' \
     'f00000000001976a914bbaeed8a02f64c9d40462d323d379b8f27ad9f1a88ac905d1818000000001976a914046858970a72d33817' \
     '474c0e24e530d78716fc9c88ac00000000'
print("\nSEND Raw Transaction:")
srv = Service(network='testnet')
if srv.sendrawtransaction(rt):
    print("Transaction send, result: ")
    pprint(srv.results)
else:
    print("Transaction could not be send, errors:")
    pprint(srv.errors)

# Get current estimated networks fees
print("\nCurrent estimated networks fees:")
srv = Service(min_providers=10)
srv.estimatefee(5)
pprint(srv.results)

# Test address with huge number of UTXO's
# addresslst = '16ZbpCEyVVdqu8VycWR8thUL2Rd9JnjzHt'
# addresslst = '1KwA4fS4uVuCNjCtMivE7m5ATbv93UZg8V'
# srv = Service(network='bitcoin', min_providers=10)
# utxos = srv.getutxos(addresslst)
# results = srv.results
# for res in results:
#     print(res, len(results[res]))

# Get transactions by hash
srv = Service()
res = srv.gettransaction('2ae77540ec3ef7b5001de90194ed0ade7522239fe0fc57c12c772d67274e2700')
pprint(res)
