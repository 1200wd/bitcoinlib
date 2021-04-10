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
    def test_stack_op_npp(self):
        st = Stack()
        self.assertIsNone(st.op_nop())
        self.assertEqual(st, [])

    def test_stack_op_verify(self):
        self.assertTrue(Stack([b'1']).op_verify())
        self.assertTrue(Stack([b'F']).op_verify())
        self.assertFalse(Stack([b'']).op_verify())
        self.assertRaisesRegex(IndexError, "pop from empty list", Stack([]).op_verify)

    def test_stack_op_return(self):
        self.assertFalse(Stack([]).op_return())

    def test_stack_op_2drop(self):
        st = Stack.from_ints(range(1, 4))
        st.op_2drop()
        self.assertEqual(st, [encode_num(1)])
        self.assertRaisesRegex(IndexError, "pop from empty list", st.op_2drop)

    def test_stack_op_2dup(self):
        l1 = [b'\x01', b'\x02']
        st = Stack(l1)
        st.op_2dup()
        self.assertEqual(st, l1 + l1)
        self.assertRaisesRegex(ValueError, "Stack op_2dup method requires minimum of 2 stack items",
                               Stack([b'\x01']).op_2dup)

    def test_stack_op_3dup(self):
        l1 = [b'\x01', b'\x02', b'\x03']
        st = Stack(l1)
        st.op_3dup()
        self.assertEqual(st, l1 + l1)
        self.assertRaisesRegex(ValueError, "Stack op_3dup method requires minimum of 3 stack items",
                               Stack([b'\x01', b'\x02']).op_3dup)

    def test_stack_op_2over(self):
        self.assertRaisesRegex(ValueError, "Stack op_2over method requires minimum of 4 stack items",
                               Stack([b'\x01', b'\x02']).op_2over)
        st = Stack.from_ints(range(1, 5))
        st.op_2over()
        self.assertEqual(st, [b'\x01', b'\x02', b'\x03', b'\x04', b'\x01', b'\x02'])

    def test_stack_op_2rot(self):
        st = Stack.from_ints(range(1, 7))
        st.op_2rot()
        self.assertEqual(st, [b'\x03', b'\x04', b'\x05', b'\x06', b'\x01', b'\x02'])
        self.assertRaisesRegex(IndexError, "pop index out of range", Stack([b'\x02']).op_2rot)

    def test_stack_op_2swap(self):
        st = Stack.from_ints(range(1, 5))
        st.op_2swap()
        self.assertEqual(st, [b'\x04', b'\x03', b'\x01', b'\x02'])

    def test_stack_op_ifdup(self):
        st = Stack([b''])
        st.op_ifdup()
        self.assertEqual(st, [b''])
        st = Stack([b'1'])
        st.op_ifdup()
        self.assertEqual(st, [b'1', b'1'])
        st = Stack([])
        self.assertRaisesRegex(ValueError, 'Stack op_ifdup method requires minimum of 1 stack item', st.op_ifdup)

    def test_stack_op_depth(self):
        st = Stack.from_ints(range(1, 5))
        st.op_depth()
        self.assertEqual(decode_num(st[-1]), 4)

    def test_stack_op_drop(self):
        st = Stack.from_ints(range(1, 3))
        st.op_drop()
        self.assertEqual(st, [encode_num(1)])
        st.op_drop()
        self.assertRaisesRegex(IndexError, "pop from empty list", st.op_drop)

    def test_stack_op_dup(self):
        st = Stack([b'\x10'])
        st.op_dup()
        self.assertEqual(st, [b'\x10', b'\x10'])
        st = Stack()
        self.assertFalse(st.op_dup())

    def test_stack_op_nip(self):
        self.assertRaisesRegex(IndexError, 'pop index out of range', Stack([b'\x01']).op_nip)
        st = Stack.from_ints([1, 2])
        st.op_nip()
        self.assertEqual(st, [b'\x02'])

    def test_stack_op_over(self):
        self.assertRaisesRegex(ValueError, 'Stack op_over method requires minimum of 2 stack items', Stack([]).op_over)
        st = Stack.from_ints([1, 2])
        st.op_over()
        self.assertEqual(st, [b'\x01', b'\x02', b'\x01'])

    def test_stack_op_pick(self):
        st = Stack.from_ints([1, 2, 3, 3])
        st.op_pick()
        self.assertEqual(st.as_ints(), [1, 2, 3, 1])
        st = Stack.from_ints([1, 2, 3, 4])
        self.assertRaisesRegex(IndexError, 'list index out of range', st.op_pick)

    def test_stack_op_roll(self):
        st = Stack.from_ints([1, 2, 3, 3])
        st.op_roll()
        self.assertEqual(st.as_ints(), [2, 3, 1])
        st = Stack.from_ints([1, 2, 3, 4])
        self.assertRaisesRegex(IndexError, 'pop index out of range', st.op_roll)

    def test_stack_op_rot(self):
        st = Stack.from_ints([1, 2, 3])
        st.op_rot()
        self.assertEqual(st.as_ints(), [2, 3, 1])
        self.assertRaisesRegex(IndexError, 'pop index out of range', Stack([1, 2]).op_rot)

    def test_stack_op_swap(self):
        st = Stack.from_ints([1, 2])
        st.op_swap()
        self.assertEqual(st.as_ints(), [2, 1])
        self.assertRaisesRegex(IndexError, 'pop index out of range', Stack([2]).op_swap)

    def test_stack_op_tuck(self):
        st = Stack.from_ints([1, 2])
        st.op_tuck()
        self.assertEqual(st, [b'\x01', b'\x02', b'\x01'])
        self.assertRaisesRegex(IndexError, 'list index out of range', Stack([2]).op_tuck)

    def test_stack_op_size(self):
        st = Stack([b'\x02\x88\xff'])
        st.op_size()
        self.assertEqual(st[-1], encode_num(3))
        self.assertRaisesRegex(IndexError, 'list index out of range', Stack([]).op_size)

    def test_stack_op_equal(self):
        st = Stack.from_ints([1, 1])
        st.op_equal()
        self.assertEqual(len(st), 1)
        self.assertEqual(st, [b'\x01'])
        st = Stack.from_ints([1, 2])
        st.op_equal()
        self.assertEqual(len(st), 1)
        self.assertEqual(st, [b''])
        self.assertRaisesRegex(IndexError, 'pop from empty list', Stack([b'x99']).op_equal)

    def test_stack_op_equal_verify(self):
        st = Stack.from_ints([1, 1])
        self.assertTrue(st.op_equalverify())
        st = Stack.from_ints([1, 2])
        self.assertFalse(st.op_equalverify())

    # # 'op_reserved1': used by op_if
    # # 'op_reserved2': used by op_if

    def test_stack_op_1add(self):
        st = Stack.from_ints([5])
        st.op_1add()
        self.assertEqual(st.as_ints(), [6])
        self.assertRaisesRegex(IndexError, 'pop from empty list', Stack([]).op_1add)

    def test_stack_op_1sub(self):
        st = Stack.from_ints([5])
        st.op_1sub()
        self.assertEqual(st.as_ints(), [4])
        self.assertRaisesRegex(IndexError, 'pop from empty list', Stack([]).op_1sub)

    def test_stack_operation_op_add(self):
        st = Stack.from_ints(range(1, 7))
        for _ in range(5):
            st.op_add()
        self.assertEqual(decode_num(st[0]), 1+2+3+4+5+6)
        self.assertRaisesRegex(IndexError, "pop from empty list", st.op_add)

    def test_stack_operation_op_sub(self):
        st = Stack.from_ints([2, 5])
        st.op_sub()
        self.assertEqual(decode_num(st[0]), 5 - 2)
        self.assertRaisesRegex(IndexError, "pop from empty list", st.op_sub)
