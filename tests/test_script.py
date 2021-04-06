# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Bitcoinlib Script class
#    © 2018 May - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.scripts import *
import unittest


class TestStack(unittest.TestCase):

    # https://en.bitcoin.it/wiki/Script
    def test_op_npp(self):
        st = Stack()
        self.assertIsNone(st.op_nop())
        self.assertEqual(st, [])

    def test_op_verify(self):
        self.assertTrue(Stack([b'1']).op_verify())
        self.assertTrue(Stack([b'F']).op_verify())
        self.assertFalse(Stack([b'']).op_verify())
        self.assertRaisesRegex(IndexError, "pop from empty list", Stack([]).op_verify)

    def test_stack_operation_op_add(self):
        st = Stack([encode_num(n) for n in range(1, 7)])
        for _ in range(5):
            st.op_add()
        self.assertEqual(decode_num(st[0]), 1+2+3+4+5+6)
        self.assertRaisesRegex(IndexError, "pop from empty list", st.op_add)

    def test_stack_operation_op_sub(self):
        st = Stack([encode_num(n) for n in [2, 5]])
        st.op_sub()
        self.assertEqual(decode_num(st[0]), 5 - 2)
        self.assertRaisesRegex(IndexError, "pop from empty list", st.op_sub)
