# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Bump transaction fee of a wallet transaction
#
#    © 2024 June - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.wallets import wallet_create_or_open


# Create wallet and transaction
w = wallet_create_or_open("wallet_transaction_bumpfee_example", network='bitcoinlib_test')
w.get_key()
w.utxos_update()

t = w.send_to('blt1q855uwmunslpe0vv83na78v8tuxw9knhvn4g3mq', 2000000, fee=10000)
print(f"Transaction fee before: {t.fee}")

# Bump fee with standard advised amount
t.bumpfee()
print(f"Transaction fee after bump #1: {t.fee}")

# Duplicate fee
t.bumpfee(extra_fee = t.fee*2)
print(f"Transaction fee after bump #2: {t.fee}")

# Raise fee with 0.1%. Raises error...:
print("Error when raising fee with 0,1%")
t.bumpfee(t.fee*1.001)

