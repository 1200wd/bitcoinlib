# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Script and Stack Class
#
#    © 2021 September - 1200 Web Development <http://1200wd.com/>
#

from pprint import pprint
from bitcoinlib.scripts import *

#
# Stack Class Examples
#
# The Script object uses script language to perform operation on the Stack object.
#

st = Stack.from_ints([2, 3])
print("Stack st %s" % st)
st.op_add()
print("Stack after running op_add %s" % st)

st = Stack([b'\x99'])
print("Stack st %s" % st)
st.op_dup()
print("Stack after running op_dup %s" % st)

st = Stack([b'The quick brown fox jumps over the lazy dog'])
print("Stack st %s" % st)
st.op_ripemd160()
print("Stack in hex after running op_ripemd160 %s" % st)
print(st[0].hex())

st = Stack.from_ints([8, 2, 7])
print("Stack st %s" % st)
st.op_within()
print("Stack in hex after running op_within. Check if last item is between previous 2 numbers, returns 1 if True: %s" %
      st)

# For more Stack examples see unittests in test_script.
# For more information about op-methods: https://en.bitcoin.it/wiki/Script

