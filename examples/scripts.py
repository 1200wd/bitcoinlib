# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Script and Stack Class
#
#    © 2021 September - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.scripts import *
from bitcoinlib.transactions import Transaction

#
# Stack Class Examples
#
# The Script object uses script language to perform operation on the Stack object.
#

st = Stack.from_ints([2, 3])
print("\nStack st %s" % st)
st.op_add()
print("Stack after running op_add %s" % st)

st = Stack([b'\x99'])
print("\nStack st %s" % st)
st.op_dup()
print("Stack after running op_dup %s" % st)

st = Stack([b'The quick brown fox jumps over the lazy dog'])
print("\nStack st %s" % st)
st.op_ripemd160()
print("Stack in hex after running op_ripemd160 %s" % st)
print(st[0].hex())

st = Stack.from_ints([8, 2, 7])
print("\nStack st %s" % st)
st.op_within()
print("Stack in hex after running op_within. Checks if last item is between previous 2 numbers, returns 1 if True: %s" %
      st)

txid = '0d12fdc4aac9eaaab9730999e0ce84c3bd5bb38dfd1f4c90c613ee177987429c'
key = 'b2da575054fb5daba0efde613b0b8e37159b8110e4be50f73cbe6479f6038f5b'
sig = '70b55404702ffa86ecfa4e88e0f354004a0965a5eea5fbbd297436001ae920df5da0917d7bd645c2a09671894375e3d3533138e8de09bc89cb251cbfae4cc523'
st = Stack([bytes.fromhex(sig), bytes.fromhex(key)])
print("\nSignature verified: %s" % st.op_checksigverify(bytes.fromhex(txid)))


# For more Stack examples see unittests in test_script.
# For more information about op-methods: https://en.bitcoin.it/wiki/Script


#
# Script Class Examples
#
# The Script object uses script language to perform operation on the Stack object.
#

sc = [op.op_8, op.op_16, op.op_dup, op.op_1]
s = Script(sc)
print("\nScript %s" % s)
print("Evaluate: %s" % s.evaluate())
print("Stack after evaluation: %s" % s.stack)

sc = [op.op_8, encode_num(512), op.op_16, op.op_2dup]
s = Script(sc)
print("\nScript %s" % s)
print("Evaluate: %s" % s.evaluate())
print("Stack after evaluation: %s" % s.stack)

script = '493046022100cf4d7571dd47a4d47f5cb767d54d6702530a3555726b27b6ac56117f5e7808fe0221008cbb42233bb04d7f28a' \
         '715cf7c938e238afde90207e9d103dd9018e12cb7180e03'
s = Script.parse(script)
print("\nScript hex %s" % script)
print("Parsed script: %s" % s)

print("\nVerify input 0 of transaction c8ea60ae943d84a8620a4ce3d3e12813293cdc48f6811dbc1c30578dfd1b2717")
traw = '010000000182406edfc43449e2f94097867316cbc631dfdf9dc57dcc125297b0b59d3a2eda240000008b483045022100e05371e4d640d351d62699573811d93858b057eb01852d6c0b45d21d0ee90bb102201dc0b5ae1fee4dc1e7787e5cbbba2021387f52a9368856386931d4f8d9bdd938014104c4b7a7f7bb2c899f4aeab75b41567c040ae79506d43ee72f650c95b6319e47402f0ba88d1c5a294d075885442679dc24882ea37c31e0dbc82cfd51ed185d7e94ffffffff02ab4b0000000000001976a914ee493bd17ae7fa7fdabe4adb2b861ad7a8b954ad88acc5a5e70b000000001976a9147ddb236e7877d5040e2a59e4be544c65934e573a88ac00000000'
t = Transaction.parse_hex(traw)
i = t.inputs[0]
transaction_hash_input_0 = transaction_hash = t.signature_hash(i.index_n)
s = Script.parse(i.unlocking_script + i.script_code)
print("Validation script input 0: %s" % s)
print("Evaluate: %s" % s.evaluate(transaction_hash_input_0))

print("\nCreate redeemscript:")
key1 = '5JruagvxNLXTnkksyLMfgFgf3CagJ3Ekxu5oGxpTm5mPfTAPez3'
key2 = '5JX3qAwDEEaapvLXRfbXRMSiyRgRSW9WjgxeyJQWwBugbudCwsk'
key3 = '5JjHVMwJdjPEPQhq34WMUhzLcEd4SD7HgZktEh8WHstWcCLRceV'
keylist = [Key(k) for k in [key1, key2, key3]]
print("Keys: %s" % keylist)
redeemscript = Script(keys=keylist, sigs_required=2, script_types=['multisig'])
print("Redeemscript hex: %s" % redeemscript.serialize().hex())
print("Redeemscript: %s" % redeemscript)


#
# Deserialize input and output transaction scripts
#

print("\n=== Determine Script Types ===")
script = '76a914f0d34949650af161e7cb3f0325a1a8833075165088ac'
s = Script.parse_hex(script)
print("\np2pkh: %s" % s.script_types[0])
print(s)

script = '473044022034519a85fb5299e180865dda936c5d53edabaaf6d15cd1740aac9878b76238e002207345fcb5a62deeb8d9d80e5b41' \
         '2bd24d09151c2008b7fef10eb5f13e484d1e0d01210207c9ece04a9b5ef3ff441f3aad6bb63e323c05047a820ab45ebbe61385aa' \
         '7446'
s = Script.parse_hex(script)
print("\nsig_pubkey: %s" % s.script_types[0])
print(s)

script = '6a20985f23805edd2938e5bd9f744d36ccb8be643de00b369b901ae0b3fea911a1dd'
s = Script.parse_hex(script)
print("\nnulldata: %s" % s.script_types[0])
print(s)

script = '5121032487c2a32f7c8d57d2a93906a6457afd00697925b0e6e145d89af6d3bca330162102308673d16987eaa010e540901cc6' \
         'fe3695e758c19f46ce604e174dac315e685a52ae'
s = Script.parse_hex(script)
print("\nmultisig: %s" % s.script_types[0])
print(s)

script = b"\x00\x14\xdc'M\xf8\x110Ke\xbd\x95\x1fq\xa3\x81\x0e\xc1\x91\x0b\xd7\x96"
s = Script.parse(script)
print("\np2wpkh: %s" % s.script_types[0])
print(s)

script = b'\x00 X|\x82_z\xb2\xdcV!\x0f\x92q\x15\x85\xed\x0cj\x84\x930]~\xa7\xb2\xd4\xb3a\x1e\\\xda\x85*'
s = Script.parse(script)
print("\np2wsh: %s" % s.script_types[0])
print(s)
