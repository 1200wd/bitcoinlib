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
    def test_stack_op_nop(self):
        st = Stack()
        self.assertTrue(st.op_nop())
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
        self.assertTrue(st.op_2drop())
        self.assertEqual(st, [encode_num(1)])
        self.assertRaisesRegex(IndexError, "pop from empty list", st.op_2drop)

    def test_stack_op_2dup(self):
        l1 = [b'\x01', b'\x02']
        st = Stack(l1)
        self.assertTrue(st.op_2dup())
        self.assertEqual(st, l1 + l1)
        self.assertRaisesRegex(ValueError, "Stack op_2dup method requires minimum of 2 stack items",
                               Stack([b'\x01']).op_2dup)

    def test_stack_op_3dup(self):
        l1 = [b'\x01', b'\x02', b'\x03']
        st = Stack(l1)
        self.assertTrue(st.op_3dup())
        self.assertEqual(st, l1 + l1)
        self.assertRaisesRegex(ValueError, "Stack op_3dup method requires minimum of 3 stack items",
                               Stack([b'\x01', b'\x02']).op_3dup)

    def test_stack_op_2over(self):
        self.assertRaisesRegex(ValueError, "Stack op_2over method requires minimum of 4 stack items",
                               Stack([b'\x01', b'\x02']).op_2over)
        st = Stack.from_ints(range(1, 5))
        self.assertTrue(st.op_2over())
        self.assertEqual(st, [b'\x01', b'\x02', b'\x03', b'\x04', b'\x01', b'\x02'])

    def test_stack_op_2rot(self):
        st = Stack.from_ints(range(1, 7))
        self.assertTrue(st.op_2rot())
        self.assertEqual(st, [b'\x03', b'\x04', b'\x05', b'\x06', b'\x01', b'\x02'])
        self.assertRaisesRegex(IndexError, "pop index out of range", Stack([b'\x02']).op_2rot)

    def test_stack_op_2swap(self):
        st = Stack.from_ints(range(1, 5))
        self.assertTrue(st.op_2swap())
        self.assertEqual(st, [b'\x04', b'\x03', b'\x01', b'\x02'])

    def test_stack_op_ifdup(self):
        st = Stack([b''])
        self.assertTrue(st.op_ifdup())
        self.assertEqual(st, [b''])
        st = Stack([b'1'])
        self.assertTrue(st.op_ifdup())
        self.assertEqual(st, [b'1', b'1'])
        st = Stack([])
        self.assertRaisesRegex(ValueError, 'Stack op_ifdup method requires minimum of 1 stack item', st.op_ifdup)

    def test_stack_op_depth(self):
        st = Stack.from_ints(range(1, 5))
        self.assertTrue(st.op_depth())
        self.assertEqual(decode_num(st[-1]), 4)

    def test_stack_op_drop(self):
        st = Stack.from_ints(range(1, 3))
        self.assertTrue(st.op_drop())
        self.assertEqual(st, [encode_num(1)])
        self.assertTrue(st.op_drop())
        self.assertRaisesRegex(IndexError, "pop from empty list", st.op_drop)

    def test_stack_op_dup(self):
        st = Stack([b'\x10'])
        self.assertTrue(st.op_dup())
        self.assertEqual(st, [b'\x10', b'\x10'])
        st = Stack()
        self.assertFalse(st.op_dup())

    def test_stack_op_nip(self):
        self.assertRaisesRegex(IndexError, 'pop index out of range', Stack([b'\x01']).op_nip)
        st = Stack.from_ints([1, 2])
        self.assertTrue(st.op_nip())
        self.assertEqual(st, [b'\x02'])

    def test_stack_op_over(self):
        self.assertRaisesRegex(ValueError, 'Stack op_over method requires minimum of 2 stack items', Stack([]).op_over)
        st = Stack.from_ints([1, 2])
        self.assertTrue(st.op_over())
        self.assertEqual(st, [b'\x01', b'\x02', b'\x01'])

    def test_stack_op_pick(self):
        st = Stack.from_ints([1, 2, 3, 3])
        self.assertTrue(st.op_pick())
        self.assertEqual(st.as_ints(), [1, 2, 3, 1])
        st = Stack.from_ints([1, 2, 3, 4])
        self.assertRaisesRegex(IndexError, 'list index out of range', st.op_pick)

    def test_stack_op_roll(self):
        st = Stack.from_ints([1, 2, 3, 3])
        self.assertTrue(st.op_roll())
        self.assertEqual(st.as_ints(), [2, 3, 1])
        st = Stack.from_ints([1, 2, 3, 4])
        self.assertRaisesRegex(IndexError, 'pop index out of range', st.op_roll)

    def test_stack_op_rot(self):
        st = Stack.from_ints([1, 2, 3])
        self.assertTrue(st.op_rot())
        self.assertEqual(st.as_ints(), [2, 3, 1])
        self.assertRaisesRegex(IndexError, 'pop index out of range', Stack([1, 2]).op_rot)

    def test_stack_op_swap(self):
        st = Stack.from_ints([1, 2])
        self.assertTrue(st.op_swap())
        self.assertEqual(st.as_ints(), [2, 1])
        self.assertRaisesRegex(IndexError, 'pop index out of range', Stack([2]).op_swap)

    def test_stack_op_tuck(self):
        st = Stack.from_ints([1, 2])
        self.assertTrue(st.op_tuck())
        self.assertEqual(st, [b'\x01', b'\x02', b'\x01'])
        self.assertRaisesRegex(IndexError, 'list index out of range', Stack([2]).op_tuck)

    def test_stack_op_size(self):
        st = Stack([b'\x02\x88\xff'])
        self.assertTrue(st.op_size())
        self.assertEqual(st[-1], encode_num(3))
        self.assertRaisesRegex(IndexError, 'list index out of range', Stack([]).op_size)

    def test_stack_op_equal(self):
        st = Stack.from_ints([1, 1])
        self.assertTrue(st.op_equal())
        self.assertEqual(len(st), 1)
        self.assertEqual(st, [b'\x01'])
        st = Stack.from_ints([1, 2])
        self.assertTrue(st.op_equal())
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
        self.assertTrue(st.op_1add())
        self.assertEqual(st.as_ints(), [6])
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 0, expected 1',
                               Stack([]).op_1add)

    def test_stack_op_1sub(self):
        st = Stack.from_ints([5])
        self.assertTrue(st.op_1sub())
        self.assertEqual(st.as_ints(), [4])
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 0, expected 1',
                               Stack([]).op_1sub)

    def test_stack_op_negate(self):
        st = Stack.from_ints([3])
        self.assertTrue(st.op_negate())
        self.assertEqual(decode_num(st[0]), -3)
        st = Stack.from_ints([-1003])
        self.assertTrue(st.op_negate())
        self.assertEqual(decode_num(st[0]), 1003)
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 0, expected 1',
                               Stack([]).op_negate)

    def test_stack_op_abs(self):
        st = Stack.from_ints([3])
        self.assertTrue(st.op_abs())
        self.assertEqual(decode_num(st[0]), 3)
        st = Stack.from_ints([-1003])
        self.assertTrue(st.op_abs())
        self.assertEqual(decode_num(st[0]), 1003)
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 0, expected 1',
                               Stack([]).op_abs)

    def test_stack_op_not(self):
        st = Stack([b''])
        self.assertTrue(st.op_not())
        self.assertEqual(st[-1], b'\1')
        st = Stack([b'\1'])
        self.assertTrue(st.op_not())
        self.assertEqual(st[-1], b'')
        st = Stack([b'\x99\xff'])
        self.assertTrue(st.op_not())
        self.assertEqual(st[-1], b'')
        self.assertFalse(Stack([b'\x99\xff\xff\xff\xff']).op_not())
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 0, expected 1',
                               Stack([]).op_not)

    def test_stack_op_0notequal(self):
        st = Stack([b'\1'])
        self.assertTrue(st.op_0notequal())
        self.assertEqual(st[-1], b'\1')
        st = Stack([b''])
        self.assertTrue(st.op_0notequal())
        self.assertEqual(st[-1], b'')
        st = Stack([b'\x99\xff'])
        self.assertTrue(st.op_0notequal())
        self.assertEqual(st[-1], b'\1')
        self.assertFalse(Stack([b'\x99\xff\xff\xff\xff']).op_0notequal())
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 0, expected 1',
                               Stack([]).op_0notequal)

    def test_stack_op_add(self):
        st = Stack.from_ints(range(1, 7))
        for _ in range(5):
            self.assertTrue(st.op_add())
        self.assertEqual(decode_num(st[0]), 1 + 2 + 3 + 4 + 5 + 6)
        self.assertRaisesRegex(IndexError, "Not enough items in list to run operation. Items 1, expected 2",
                               st.op_add)

    def test_stack_op_sub(self):
        st = Stack.from_ints([2, 5])
        self.assertTrue(st.op_sub())
        self.assertEqual(decode_num(st[0]), 5 - 2)
        self.assertRaisesRegex(IndexError, "Not enough items in list to run operation. Items 1, expected 2",
                               st.op_sub)

    def test_stack_op_booland(self):
        st = Stack([b'', b''])
        self.assertTrue(st.op_booland())
        self.assertEqual(st[-1], b'')
        st = Stack([b'', b'\1'])
        self.assertTrue(st.op_booland())
        self.assertEqual(st[-1], b'')
        st = Stack([b'\1', b'\1'])
        self.assertTrue(st.op_booland())
        self.assertEqual(st[-1], b'\1')
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 0, expected 2',
                               Stack([]).op_booland)

    def test_stack_op_boolor(self):
        st = Stack([b'', b''])
        self.assertTrue(st.op_boolor())
        self.assertEqual(st[-1], b'')
        st = Stack([b'', b'\1'])
        self.assertTrue(st.op_boolor())
        self.assertEqual(st[-1], b'\1')
        st = Stack([b'\1', b'\1'])
        self.assertTrue(st.op_boolor())
        self.assertEqual(st[-1], b'\1')
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 0, expected 2',
                               Stack([]).op_boolor)

    def test_stack_op_numequal(self):
        st = Stack([b'\x08', b'\x08'])
        self.assertTrue(st.op_numequal())
        self.assertEqual(st[-1], b'\1')
        st = Stack([b'\x08', b'\x07'])
        self.assertTrue(st.op_numequal())
        self.assertEqual(st[-1], b'')
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 0, expected 2',
                               Stack([]).op_numequal)

    def test_stack_op_numequalverify(self):
        st = Stack([b'\x08', b'\x08'])
        self.assertTrue(st.op_numequalverify())
        st = Stack([b'\x08', b'\x07'])
        self.assertFalse(st.op_numequalverify())

    def test_stack_op_numnotequal(self):
        st = Stack([b'\x89', b'\x89'])
        self.assertTrue(st.op_numnotequal())
        self.assertEqual(st[-1], b'')
        st = Stack([b'\x82', b'\x02'])
        self.assertTrue(st.op_numnotequal())
        self.assertEqual(st[-1], b'\1')
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 0, expected 2',
                               Stack([]).op_numnotequal)

    def test_stack_op_numlessthan(self):
        st = Stack([b'\2', b'\1'])
        self.assertTrue(st.op_numlessthan())
        self.assertEqual(st[-1], b'\1')
        st = Stack([b'\x82', b'\x02'])
        self.assertTrue(st.op_numlessthan())
        self.assertEqual(st[-1], b'')
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 1, expected 2',
                               Stack([b'\1']).op_numlessthan)

    def test_stack_op_numgreaterthan(self):
        st = Stack([b'\2', b'\3'])
        self.assertTrue(st.op_numgreaterthan())
        self.assertEqual(st[-1], b'\1')
        st = Stack([b'\x04', b'\x81'])
        self.assertTrue(st.op_numgreaterthan())
        self.assertEqual(st[-1], b'')
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 1, expected 2',
                               Stack([b'\1']).op_numgreaterthan)

    def test_stack_op_numlessthanorequal(self):
        st = Stack([b'\2', b'\2'])
        self.assertTrue(st.op_numlessthanorequal())
        self.assertEqual(st[-1], b'\1')
        st = Stack([b'\x82', b'\x02'])
        self.assertTrue(st.op_numlessthanorequal())
        self.assertEqual(st[-1], b'')
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 1, expected 2',
                               Stack([b'\1']).op_numlessthanorequal)

    def test_stack_op_numgreaterthanorequal(self):
        st = Stack([b'\3', b'\3'])
        self.assertTrue(st.op_numgreaterthanorequal())
        self.assertEqual(st[-1], b'\1')
        st = Stack([b'\x04', b'\x81'])
        self.assertTrue(st.op_numgreaterthanorequal())
        self.assertEqual(st[-1], b'')
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 1, expected 2',
                               Stack([b'\1']).op_numgreaterthanorequal)

    def test_stack_op_min(self):
        st = Stack([b'\1', b'\2'])
        self.assertTrue(st.op_min())
        self.assertEqual(st[-1], b'\1')
        st = Stack([b'\3', b'\2'])
        self.assertTrue(st.op_min())
        self.assertEqual(st[-1], b'\2')
        st = Stack([b'\3', b'\x82'])
        self.assertTrue(st.op_min())
        self.assertEqual(st[-1], b'\x82')
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 1, expected 2',
                               Stack([b'\1']).op_min)

    def test_stack_op_max(self):
        st = Stack([b'\1', b'\2'])
        self.assertTrue(st.op_max())
        self.assertEqual(st[-1], b'\2')
        st = Stack([b'\3', b'\2'])
        self.assertTrue(st.op_max())
        self.assertEqual(st[-1], b'\3')
        st = Stack([b'\3', b'\x82'])
        self.assertTrue(st.op_max())
        self.assertEqual(st[-1], b'\3')
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 1, expected 2',
                               Stack([b'\1']).op_max)

    def test_stack_op_within(self):
        st = Stack([b'\x09', b'\x07', b'\x08'])
        self.assertTrue(st.op_within())
        self.assertEqual(st, [b'\1'])
        st = Stack([b'\x09', b'\x07', b'\x09'])
        self.assertTrue(st.op_within())
        self.assertEqual(st, [b''])
        self.assertRaisesRegex(IndexError, 'Not enough items in list to run operation. Items 1, expected 3',
                               Stack([b'\1']).op_within)

    def test_op_ripemd160(self):
        st = Stack([b'The quick brown fox jumps over the lazy dog'])
        self.assertTrue(st.op_ripemd160())
        self.assertEqual(st[0].hex(), '37f332f68db77bd9d7edd4969571ad671cf9dd3b')
        self.assertRaisesRegex(IndexError, 'pop from empty list', Stack([]).op_ripemd160)

    def test_stack_op_sha1(self):
        st = Stack([b'The quick brown fox jumps over the lazy dog'])
        self.assertTrue(st.op_sha1())
        self.assertEqual(st[0].hex(), '2fd4e1c67a2d28fced849ee1bb76e7391b93eb12')
        self.assertRaisesRegex(IndexError, 'pop from empty list', Stack([]).op_sha1)

    def test_stack_op_sha256(self):
        st = Stack([b'The quick brown fox jumps over the lazy dog'])
        self.assertTrue(st.op_sha256())
        self.assertEqual(st[0].hex(), 'd7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592')
        self.assertRaisesRegex(IndexError, 'pop from empty list', Stack([]).op_sha256)

    def test_stack_op_hash160(self):
        st = Stack([bytes.fromhex('0298ddb14f0a9871c4755985f0ece53f99580d243474e5e300078f3dad809b3d45')])
        self.assertTrue(st.op_hash160())
        self.assertEqual(st[0].hex(), 'c8d26159052b4eddb5a945f0795f220366868189')
        self.assertRaisesRegex(IndexError, 'pop from empty list', Stack([]).op_hash160)

    def test_stack_op_hash256(self):
        st = Stack([b'The quick brown fox jumps over the lazy dog'])
        self.assertTrue(st.op_hash256())
        self.assertEqual(st[0].hex(), '6d37795021e544d82b41850edf7aabab9a0ebe274e54a519840c4666f35b3937')
        self.assertRaisesRegex(IndexError, 'pop from empty list', Stack([]).op_hash256)

    def test_stack_op_checksig(self):
        txid = b'G\x9bp)\xc8\x811\x97\xdeS\x90\xae\x86\xc2\xc7\xfb\x9d\xd3\x17\x01F\x13N,\x19v\xdb\x0f\x1a\xab\xd8X'
        key = '03508cb60bb7fecfcf0b4e44eedf6e588cd54bdb28dd38b662f52fdbe35e61ab68'
        sig = '3044022065affcfb58c7e4a8dd2ad787fb069e623dc1f8160b664a17695fcc2ed5c16be002206803240c5f9ba90d3ad2eab' \
              '327fa4e6940cf74d639bfcde0f9d2aeb91182df5b01'
        st = Stack([bytes.fromhex(sig), bytes.fromhex(key)])
        self.assertTrue(st.op_checksig(txid))
        self.assertEqual(st[0], b'\1')

        sig = '3044022065affcfb58c7e4a8dd2ad787fb069e623dc1f8160b664a17695fcc2dd5c16be002206803240c5f9ba90d3ad2eab' \
              '327fa4e6940cf74d639bfcde0f9d2aeb91182df5b01'
        st = Stack([bytes.fromhex(sig), bytes.fromhex(key)])
        self.assertTrue(st.op_checksig(txid))
        self.assertEqual(st[0], b'')

        self.assertRaisesRegex(IndexError, 'pop from empty list', Stack([bytes.fromhex(key)]).op_checksig, txid)

    def test_op_stack_op_checksigverify(self):
        txid = '0d12fdc4aac9eaaab9730999e0ce84c3bd5bb38dfd1f4c90c613ee177987429c'
        key = 'b2da575054fb5daba0efde613b0b8e37159b8110e4be50f73cbe6479f6038f5b'
        sig = '70b55404702ffa86ecfa4e88e0f354004a0965a5eea5fbbd297436001ae920df5da0917d7bd645c2a09671894375e3d353' \
              '3138e8de09bc89cb251cbfae4cc523'
        st = Stack([bytes.fromhex(sig), bytes.fromhex(key)])
        self.assertTrue(st.op_checksigverify(txid))
