# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Transaction Class examples
#
#    © 2017 - 2020 July - 1200 Web Development <http://1200wd.com/>
#

from pprint import pprint
from bitcoinlib.transactions import *


#
# Create transactions
#

print("\n=== Create and sign transaction with add_input, add_output methods ===")
print("(Based on http://bitcoin.stackexchange.com/questions/3374/how-to-redeem-a-basic-tx/24580)")
t = Transaction()
prev_tx = 'f2b3eb2deb76566e7324307cd47c35eeb88413f971d88519859b1834307ecfec'
ki = Key(0x18E14A7B6A307F426A94F8114701E7C8E774E7F9A47E2C2035DB29A206321725, compressed=False)
t.add_input(prev_txid=prev_tx, output_n=1, keys=ki.public_hex, compressed=False)
t.add_output(99900000, '1runeksijzfVxyrpiyCY2LCBvYsSiFsCm')
t.sign(ki.private_byte)
pprint(t.as_dict())
print("Raw:", t.raw_hex())
print("Verified %s " % t.verify())
print(t.raw_hex())

print("\n=== Create and sign transaction with transactions Input and Output objects ===")
print("(Based on http://www.righto.com/2014/02/bitcoins-hard-way-using-raw-bitcoin.html)")
ki = Key('5HusYj2b2x4nroApgfvaSfKYZhRbKFH41bVyPooymbC6KfgSXdD', compressed=False)
txid = "81b4c832d70cb56ff957589752eb4125a4cab78a25a8fc52d6a09e5bd4404d48"
transaction_input = Input(prev_txid=txid, output_n=0, keys=ki.public_byte, compressed=ki.compressed)
pkh = "c8e90996c7c6080ee06284600c684ed904d14c5c"
transaction_output = Output(value=91234, public_hash=pkh)
t = Transaction([transaction_input], [transaction_output])
t.sign(ki.private_byte)
print("Raw:", t.raw_hex())
pprint(t.as_dict())
print("Verified %s " % t.verify())

print("\n=== Create and sign Testnet Transaction with Multiple OUTPUTS using keys from Wallet class "
      "'TestNetWallet' example"
      "\nSee txid f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618 ===")
ki = Key('cRMjy1LLMPsVU4uaAt3br8Ft5vdJLx6prY4Sx7WjPARrpYAnVEkV', network='testnet')  # Private key for import
transaction_input = Input(prev_txid='adee8bdd011f60e52949b65b069ff9f19fc220815fdc1a6034613ed1f6b775f1', output_n=1,
                          keys=ki.public(), network='testnet')
amount_per_address = 27172943
output_addresses = ['mn6xJw1Cp2gLcSSQAYPnX4G2M6GARGyX5j', 'n3pdL33MgTA316odzeydhNrcKXdu6jy8ry',
                    'n1Bq89KaJrcaXEMUEsDSyhKHfTGi8mkfRJ', 'mrqYnxFPcf6u5xkEfmA3dxQzjB7ZcPgtTq',
                    'mwrETLWFdvEfDwRa44JvXngxCZp59MFcC6']
transaction_outputs = []
for output_address in output_addresses:
    transaction_outputs.append(Output(amount_per_address, address=output_address, network='testnet'))
t = Transaction([transaction_input], transaction_outputs, network='testnet')
t.sign(ki.private_byte)
pprint(t.as_dict())
print("Raw Signed Transaction %s" % t.raw_hex())
print("Verified %s" % t.verify())

print("\n=== Create and sign Testnet Transaction with Multiple INPUTS using keys from "
      "Wallet class 'TestNetWallet' example"
      "\nSee txid 82b48b128232256d1d5ce0c6ae7f7897f2b464d44456c25d7cf2be51626530d9 ===")
transaction_outputs = [Output(135000000, address='mkzpsGwaUU7rYzrDZZVXFne7dXEeo6Zpw2', network='testnet')]
t = Transaction(outputs=transaction_outputs, network='testnet')
transaction_inputs = [
    (u'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618', 0,
     'cQowpHh56TrwVk3YSYFuUo8X4ZLXkGJMtbkuo7NyauZZBGs9Tb7U'),
    (u'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618', 1,
     'cSVr1HyJ2V2S2C57HsSF5QwkJjEhfLDpPporv6iFgJG2kFQqE9yh'),
    (u'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618', 2,
     'cPMakfwNRW2dzBBcfcxiJu7ucpD5Xjb1Zev88Tz6mYNrwU4ymZCf'),
    (u'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618', 3,
     'cR1TSoqB8vS3azmBMZa4khssXw1V2agPxM76Xc4ciULie3cdKPDr'),
    (u'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618', 4,
     'cW19vMM1k8x2Luawr1FZogQibggg5745eNE8GLJcZXYQb7eYc3Cf')
]
for ti in transaction_inputs:
    ki = Key(ti[2], network='testnet')
    t.add_input(prev_txid=ti[0], output_n=ti[1], keys=ki.public())
icount = 0
for ti in transaction_inputs:
    ki = Key(ti[2], network='testnet')
    t.sign(ki.private_byte, icount)
    icount += 1
pprint(t.as_dict())
print("Raw Signed Transaction %s" % t.raw_hex())
print("Verified %s" % t.verify())


#
# Create Multisignature Transactions
#

print("\nCreate a multisignature transaction")
pk1 = HDKey()
pk2 = HDKey()
pk3 = HDKey()
t = Transaction()
test_txid = 'f3d9b08dbd873631aaca66a1d18342ba24a22437ea107805405f6bedd3851618'
t.add_input(prev_txid=test_txid, output_n=0, value=100000,
            keys=[pk1.public_byte, pk2.public_byte, pk3.public_byte],
            script_type='p2sh_multisig', sigs_required=2)
t.add_output(100000, '1HsZBGm6nNGG1Moc3TL6S9DSGbnPbsSyW3')
t.sign(pk3.private_byte)
t.sign(pk1.private_byte)
print("Transaction:")
pprint(t.as_dict())
print("Verified %s" % t.verify())


#
# Deserialize transactions
#

print("\nDeserialize Transaction")
rawtx = '0100000001eccf7e3034189b851985d871f91384b8ee357cd47c3024736e5676eb2debb3f2010000006a47304402202a72b6a53' \
        '3582895e102add2e189188b9ab3779b20ae9535f5444196b150489c022042b1db0a2a76a75985264c0eb967af849a22e2af79c3' \
        '8048457dbc6c3d97c3e801210250863ad64a87ae8a2fe83c1af1a8403cb53f53e486d8511dad8a04887e5b2352ffffffff01605' \
        'af405000000001976a914097072524438d003d23a2f23edb65aae1bb3e46988ac00000000'
pprint(Transaction.parse_hex(rawtx).as_dict())

print("\nDeserialize Multisig Transaction")
rawtx = '0100000001181685d3ed6b5f40057810ea3724a224ba4283d1a166caaa313687bd8db0d9f300000000fdfd0000473044022026c' \
        '815ac3604d623876f56dca9c93ef50b4f9e2d43bf5dfcace8f19c0164155a02207d543637bbb7b4ba91759a1eca1b8bb196ab46' \
        'c3d8fd7c113e1b07e365f9f7de01483045022100b3d5dcbac491e1edee328127170c6447cd79e158c6fd3f5e3f959e1ad4b5291' \
        '002205b031a1c3854a3ad494a173c1f23918106ae041c5de1b01fce9573f7e7a05919014c6952210292c3121aa50b9113f9025b' \
        '8a12658c75763feb3d8f3cf7be2236f231cd157e932103c0007ae565abf62a9005801b0dad123e307ab3826b7ad7511f113db9c' \
        '8bae26a2102d132eab76542dfaae8e824ec553f20a8f11c10960203cd581428f66e2b4a98f853aeffffffff01a0860100000000' \
        '001976a91413d215d212cd5188ae02c5635faabdc4d7d4ec9188ac00000000'
pprint(Transaction.parse_hex(rawtx).as_dict())

print("\nDeserialize SegWit Transaction")
rawtx = "01000000000102d6ff09fefa22fabd07306d9185da3cdefbed208d949fdc9985a164dd2ddde097000000006a4730440220385bd" \
        "1b040f520a9560fbe105924540546b7b9d4d21c0f689d7e6d02fd231df00220088c0bec0a976ec522b9cc8f19b42dc18d4e3cc7" \
        "5444734d09b22d5bff73a752012103a739dbb81512ff7e8e080c734159e110d90e96da82d7ea62cc524d4d2259a650ffffffff6" \
        "79487626c91a9426e1b3cdf66dc5319fce5b6507aabdc4fdfa1485eec824b340000000000ffffffff02b81c1200000000001600" \
        "148264e2ece75fb347481df309f130443674be674ae5252f00000000001976a9145384ca03c2e1b3509f335f031ee0c994626de" \
        "36d88ac000247304402201f835e46c76a6701dd80ba925447863d1a31ff3367083459b146564059770aab022072808730fd04d3" \
        "a7613abbe0403c36cd4e7e75ec6f7eed4faa66d1970eb6af3a0121028229ee1a1016847930d5baf8e5d017ad6ebe48167935969" \
        "021865abfa06837f500000000"
t = Transaction.parse_hex(rawtx)
t.inputs[0].value = 2197812
t.inputs[1].value = 2080188
t.verify()
pprint(t.as_dict())
