# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Bitcoinlib Script class
#    © 2018 May - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.scripts import *
import unittest
from tests.test_custom import CustomAssertions


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

        st = Stack.from_ints(range(-2, 3))
        for _ in range(len(st) - 1):
            self.assertTrue(st.op_add())
        self.assertEqual(decode_num(st[0]), 0)

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

    def test_op_stack_op_checkmultisig(self):
        sig1 = b'0E\x02!\x00\xa7]\n\xf9\xf7f\xaa\xc1\xdc\xd2&e[\x089\x81\x02e\xff\x1b\xb34\xb00\xa3_\xa0Q\xd2s`\x92' \
               b'\x02 B\xb6\xbb\xb3\x15d\x8b\x9c\xd5\x07\x87\xdd&u\xf5~\xee\xe7\xf6\x97\xa5\xfc\xb3\x81\xb4\x9d\x90' \
               b'\x82L\xbf7,\x01'
        sig2 = b'0F\x02!\x00\xbb\xb0!\x81\xf1\x10\xa1\x93\x8b\xa6N\xec\xafZV0\xd4\xa6\x91cb\x04c\xad\xc9\xb0#\xdb\xbe' \
               b'\x7f!z\x02!\x00\x80\xd7\xef"\xec\xd4\x08\x9a@nb\'\xb4\x88\xfd\'\xf4\x02jg\x9b:\x1b\xf8ck\xbe\xaf<' \
               b'\x1a\x07n\x01'
        key1 = b'\x04\xdf_j\x9b\x95\xa9\xdb>n\xea!\xfa\xf0\\\xe1\x13p\xd3\x8dW\x14\xf6\x04\xf4\xff\xeb\x9dA\x8a\x1a~' \
               b'O \xea\x16\xe2\xe8J\xf1\xd7\xde\xac]\xa3\xcc\xf8\xf1\x8c\x1d\x18Sbd\xa6\xe9\xccMv\x04\xa4z\xe7\xcb\xc5'
        key2 = b'\x042J\xef\x0f65R"n\xf7@\xff|\x82\xacI\x80\x9am\xee\x16y\xde<\x9c~|\x14\x0b\x04\x16\x05;\xe3\x8d\x19' \
               b'\xc9?\xbeM\xd7\x1b\xfds\xaa?\rK\x87\xe1\x92\x06_\xb3X3\xc4B\xb8qn\x96\x8d?'
        key3 = b"\x04\x13\x07\x04Za\xc6\x9c\x84\x03\xb1\x07n\x0f4\xa8=\r\xcc\x1f\xacc\x07\xbe\xbf\n\x11R\xf0\x1dX\xda" \
               b"w\xe3\n\x19\xcd\xeds<ie-\xc8y\xfb,4S\xbb8wj\xef\xe6\x12\x1e<\xf8\xde<Y\xa8'\xcc"
        transaction_hash = bytes.fromhex('feb5df818d0120d3d08853a375e802267ea2cdfb80bfde37027606fac5219e2f')
        st = Stack([sig1, sig2, b'\2', key1, key2, key3, b'\3'])
        self.assertTrue(st.op_checkmultisig(message=transaction_hash))
        self.assertEqual(st, [b'\1'])

    def test_op_stack_op_checkmultisigverify(self):
        sig1 = b'0E\x02!\x00\xa7]\n\xf9\xf7f\xaa\xc1\xdc\xd2&e[\x089\x81\x02e\xff\x1b\xb34\xb00\xa3_\xa0Q\xd2s`\x92\x02 B\xb6\xbb\xb3\x15d\x8b\x9c\xd5\x07\x87\xdd&u\xf5~\xee\xe7\xf6\x97\xa5\xfc\xb3\x81\xb4\x9d\x90\x82L\xbf7,\x01'
        sig2 = b'0F\x02!\x00\xbb\xb0!\x81\xf1\x10\xa1\x93\x8b\xa6N\xec\xafZV0\xd4\xa6\x91cb\x04c\xad\xc9\xb0#\xdb\xbe\x7f!z\x02!\x00\x80\xd7\xef"\xec\xd4\x08\x9a@nb\'\xb4\x88\xfd\'\xf4\x02jg\x9b:\x1b\xf8ck\xbe\xaf<\x1a\x07n\x01'
        key1 = b'\x04\xdf_j\x9b\x95\xa9\xdb>n\xea!\xfa\xf0\\\xe1\x13p\xd3\x8dW\x14\xf6\x04\xf4\xff\xeb\x9dA\x8a\x1a~O \xea\x16\xe2\xe8J\xf1\xd7\xde\xac]\xa3\xcc\xf8\xf1\x8c\x1d\x18Sbd\xa6\xe9\xccMv\x04\xa4z\xe7\xcb\xc5'
        key2 = b'\x042J\xef\x0f65R"n\xf7@\xff|\x82\xacI\x80\x9am\xee\x16y\xde<\x9c~|\x14\x0b\x04\x16\x05;\xe3\x8d\x19\xc9?\xbeM\xd7\x1b\xfds\xaa?\rK\x87\xe1\x92\x06_\xb3X3\xc4B\xb8qn\x96\x8d?'
        key3 = b"\x04\x13\x07\x04Za\xc6\x9c\x84\x03\xb1\x07n\x0f4\xa8=\r\xcc\x1f\xacc\x07\xbe\xbf\n\x11R\xf0\x1dX\xdaw\xe3\n\x19\xcd\xeds<ie-\xc8y\xfb,4S\xbb8wj\xef\xe6\x12\x1e<\xf8\xde<Y\xa8'\xcc"
        transaction_hash = bytes.fromhex('feb5df818d0120d3d08853a375e802267ea2cdfb80bfde37027606fac5219e2f')
        st = Stack([sig1, sig2, b'\2', key1, key2, key3, b'\3'])
        self.assertTrue(st.op_checkmultisigverify(message=transaction_hash))
        self.assertEqual(st, [])

    def test_op_nops(self):
        for n in [None, 1] + list(range(4, 11)):
            self.assertTrue(getattr(Stack(), 'op_nop%s' % (str(n) if n else ''))())

    def test_op_checklocktimeverify(self):
        cur_timestamp = int(datetime.now().timestamp())
        st = Stack([encode_num(500)])
        self.assertTrue(st.op_checklocktimeverify(tx_locktime=1000, sequence=1))
        self.assertFalse(st.op_checklocktimeverify(tx_locktime=1000, sequence=0xffffffff))
        self.assertFalse(st.op_checklocktimeverify(tx_locktime=499, sequence=1))
        self.assertTrue(st.op_checklocktimeverify(tx_locktime=500, sequence=1))
        self.assertFalse(st.op_checklocktimeverify(tx_locktime=cur_timestamp, sequence=1))

        st = Stack([encode_num(cur_timestamp-100)])
        self.assertTrue(st.op_checklocktimeverify(sequence=0xfffffffe, tx_locktime=cur_timestamp))
        self.assertFalse(st.op_checklocktimeverify(sequence=0xfffffffe, tx_locktime=660600))

        cur_timestamp = int(datetime.now().timestamp())
        st = Stack([encode_num(cur_timestamp+100)])
        self.assertFalse(st.op_checklocktimeverify(sequence=0xfffffffe, tx_locktime=cur_timestamp))

    # TODO: Add
    # def test_op_checksequenceverify(self):

    def test_op_if(self):
        s = Script([op.op_5, op.op_1, op.op_if, op.op_2, op.op_else, op.op_5, op.op_endif, op.op_add, op.op_1])
        self.assertTrue(s.evaluate())
        self.assertEqual(decode_num(s.stack[0]), 7)

        s = Script([op.op_5, op.op_0, op.op_if, op.op_2, op.op_else, op.op_5, op.op_endif, op.op_add, op.op_1])
        self.assertTrue(s.evaluate())
        self.assertEqual(decode_num(s.stack[0]), 10)

        s = Script([op.op_5, op.op_1, op.op_notif, op.op_2, op.op_else, op.op_5, op.op_endif, op.op_add, op.op_1])
        self.assertTrue(s.evaluate())
        self.assertEqual(decode_num(s.stack[0]), 10)

        s = Script([op.op_5, op.op_0, op.op_notif, op.op_2, op.op_else, op.op_5, op.op_endif, op.op_add, op.op_1])
        self.assertTrue(s.evaluate())
        self.assertEqual(decode_num(s.stack[0]), 7)


class TestScriptTypes(unittest.TestCase):

    def test_script_type_p2pkh(self):
        s = Script.parse_hex('76a914af8e14a2cecd715c363b3a72b55b59a31e2acac988ac')
        self.assertEqual(['p2pkh'], s.script_types)

    def test_script_type_p2pkh_2(self):
        s = Script.parse_hex('76a914a13fdfc301c89094f5dc1089e61888794130e38188ac')
        self.assertEqual(['p2pkh'], s.script_types)

    def test_script_type_p2sh(self):
        s = Script.parse_bytes(bytes.fromhex('a914e3bdbeab033c7e03fd4cbf3a03ff14533260f3f487'))
        self.assertEqual(['p2sh'], s.script_types)

    def test_script_type_nulldata(self):
        s = Script.parse_bytes(bytes.fromhex('6a20985f23805edd2938e5bd9f744d36ccb8be643de00b369b901ae0b3fea911a1dd'))
        self.assertEqual(['nulldata'], s.script_types)
        self.assertEqual('985f23805edd2938e5bd9f744d36ccb8be643de00b369b901ae0b3fea911a1dd',
                         s.commands[1].hex())

    def test_script_type_nulldata_2(self):
        s = Script.parse_bytes(bytes.fromhex('6a'))
        self.assertEqual(['nulldata_2'], s.script_types)
        self.assertEqual([106], s.commands)

    def test_script_type_multisig(self):
        scr = '514104fcf07bb1222f7925f2b7cc15183a40443c578e62ea17100aa3b44ba66905c95d4980aec4cd2f6eb426d1b1ec45d7672' \
              '4f26901099416b9265b76ba67c8b0b73d210202be80a0ca69c0e000b97d507f45b98c49f58fec6650b64ff70e6ffccc3e6d00' \
              '52ae'
        s = Script.parse_hex(scr)
        self.assertEqual(['multisig'], s.script_types)
        self.assertEqual(1, s.sigs_required)
        self.assertEqual(2, len(s.keys))

    def test_script_type_multisig_2(self):
        scr = '5121032487c2a32f7c8d57d2a93906a6457afd00697925b0e6e145d89af6d3bca330162102308673d169' \
              '87eaa010e540901cc6fe3695e758c19f46ce604e174dac315e685a52ae'
        s = Script.parse_hex(scr)
        self.assertEqual(['multisig'], s.script_types)
        self.assertEqual(2, len(s.keys))

    def test_script_multisig_errors(self):
        scr = bytes.fromhex('51'
                            '4104fcf07bb1222f7925f2b7cc15183a40443c578e62ea17100aa3b44ba66905c95d4980aec4cd2f6eb426'
                            'd1b1ec45d76724f26901099416b9265b76ba67c8b0b73d'
                            '210202be80a0ca69c0e000b97d507f45b98c49f58fec6650b64ff70e6ffccc3e6d00'
                            '210202be80a0ca69c0e000b97d507f45b98c49f58fec6650b64ff70e6ffccc3e6d0052ae')
        self.assertRaisesRegex(ScriptError, '3 keys found but 2 keys expected',
                                Script.parse, scr)
        self.assertRaisesRegex(ScriptError, 'Number of signatures required \(3\) is higher then number of keys \(2\)',
                                Script.parse,
                                '532102d9d64770e0510c650cfaa0c05ba34f6faa35a18defcf9f2d493c4c225d93fbf221020c39c418c2'
                                '38ba876d09c4529bdafb2a1295c57ece923997ab693bf0a84189b852ae')

    def test_script_type_empty_unknown(self):
        s = Script.parse(b'')
        self.assertEqual(s.commands, [])
        self.assertEqual(s.as_bytes(), b'')

    def test_script_deserialize_sig_pk(self):
        scr = '493046022100cf4d7571dd47a4d47f5cb767d54d6702530a3555726b27b6ac56117f5e7808fe0221008cbb42233bb04d7f28a' \
              '715cf7c938e238afde90207e9d103dd9018e12cb7180e0141042daa93315eebbe2cb9b5c3505df4c6fb6caca8b75678609856' \
              '7550d4820c09db988fe9997d049d687292f815ccd6e7fb5c1b1a91137999818d17c73d0f80aef9'
        s = Script.parse_hex(scr)
        self.assertEqual(['sig_pubkey'], s.script_types)
        self.assertEqual(s.signatures[0].as_der_encoded(),
                         bytearray(b"0F\x02!\x00\xcfMuq\xddG\xa4\xd4\x7f\\\xb7g\xd5Mg\x02S\n5Urk\'\xb6\xacV"
                                   b"\x11\x7f^x\x08\xfe\x02!\x00\x8c\xbbB#;\xb0M\x7f(\xa7\x15\xcf|\x93\x8e#"
                                   b"\x8a\xfd\xe9\x02\x07\xe9\xd1\x03\xdd\x90\x18\xe1,\xb7\x18\x0e\x01"))
        self.assertEqual(s.keys[0].public_byte,
                         bytearray(b'\x04-\xaa\x931^\xeb\xbe,\xb9\xb5\xc3P]\xf4\xc6\xfbl\xac\xa8\xb7Vx`\x98'
                                   b'VuP\xd4\x82\x0c\t\xdb\x98\x8f\xe9\x99}\x04\x9dhr\x92\xf8\x15\xcc\xd6'
                                   b'\xe7\xfb\\\x1b\x1a\x91\x13y\x99\x81\x8d\x17\xc7=\x0f\x80\xae\xf9'))

    def test_script_deserialize_sig_hashtype(self):
        scr = '493046022100cf4d7571dd47a4d47f5cb767d54d6702530a3555726b27b6ac56117f5e7808fe0221008cbb42233bb04d7f28a' \
              '715cf7c938e238afde90207e9d103dd9018e12cb7180e03'
        s = Script.parse_hex(scr)
        self.assertEqual(3, s.signatures[0].hash_type)
        self.assertEqual(3, s.hash_type)
        self.assertEqual(s.keys, [])
        self.assertEqual(s.signatures[0].as_der_encoded(),
                         b"0F\x02!\x00\xcfMuq\xddG\xa4\xd4\x7f\\\xb7g\xd5Mg\x02S\n5Urk'\xb6\xacV\x11\x7f^x\x08\xfe"
                         b"\x02!\x00\x8c\xbbB#;\xb0M\x7f(\xa7\x15\xcf|\x93\x8e#"
                         b'\x8a\xfd\xe9\x02\x07\xe9\xd1\x03\xdd\x90\x18\xe1,\xb7\x18\x0e\x03')

    def test_script_p2tr(self):
        scr = '512013334589ddbcb9d81d3d774f9eb88e14666b54ef33008444d0f1ad78879fe033'
        s = Script.parse_hex(scr)
        self.assertEqual('p2tr', s.script_types[0])
        self.assertEqual([81, 'data-32'], s.blueprint)


class TestScript(unittest.TestCase, CustomAssertions):

    def test_script_verify_transaction_input_p2pkh(self):
        # Verify txid 6efe4f943b7898c4308c67b47bac57551ff41977edc254eafb0436467632450f, input 0
        lock_script = bytes.fromhex('76a914f9cc73824051cc82d64a716c836c54467a21e22c88ac')
        unlock_script = bytes.fromhex(
            '483045022100ba2ec7c40257b3d22864c9558738eea4d8771ab97888368124e176fdd6d7cd8602200f47c8d0c437df1ea8f98'
            '19d344e05b9c93e38e88df1fc46abb6194506c50ce1012103e481f20561573cfd800e64efda61405917cb29e4bd20bed168c5'
            '2b674937f535')
        script = unlock_script + lock_script
        s = Script.parse_bytes(script)
        self.assertEqual(s.blueprint, ['signature', 'key', 118, 169, 'data-20', 136, 172])
        self.assertEqual(s.script_types, ['sig_pubkey', 'p2pkh'])
        self.assertEqual(str(s), "signature key OP_DUP OP_HASH160 data-20 OP_EQUALVERIFY OP_CHECKSIG")
        transaction_hash = bytes.fromhex('12824db63e7856d00ee5e109fd1c26ac8a6a015858c26f4b336274f6b52da1c3')
        self.assertTrue(s.evaluate(message=transaction_hash))

    def test_script_verify_transaction_input_p2sh_multisig(self):
        # Verify txid 29c3d56d2d49b4b85884e03c6ea89bcd295c05c1a269869f3821e5d47aea8c71, input 0
        lock_script = bytes.fromhex('a9147dae466253944bb084f8ac01343504941ae15c3287')
        unlock_script = bytes.fromhex(
            '0047304402200b0ee6c93789b7b8bbff647752d7110d2fc0e0bf913f3dec8192d5a6a1da2dc20220502920194c49986b44eebd'
            '192b561bda1d428b5821117b0fd60f0d4504026dba01483045022100d412fe60888e8069ca85f87722d6dc0384f9574cc79f4e'
            '7f0129564cb51c0a38022027ba0c114bcf867ea569a55d9eb0929c148b7fdf20f176fd10944b4e0fe7a8d9014c695221036141'
            '01c3dfc98f6a7b562cd9264cc6e0d8d9597f59feea666d4c7605493b928b2102386823b976815e4f6d7279b7b4a2113c7d9e07'
            '96fa7b1ac43caa7d464a1a06db2102e7ae0137cab0a11b49caeae853d06c9499e79029670a2d649cc2e9e58b99dc5753ae')

        script = unlock_script + lock_script
        s = Script.parse_bytes(script)
        self.assertEqual(s.blueprint, [0, 'signature', 'signature', [82, 'key', 'key', 'key', 83, 174], 169,
                                       'data-20', 135])
        self.assertEqual(s.script_types, ['p2sh_multisig', 'p2sh'])
        self.assertEqual(str(s), "OP_0 signature signature redeemscript OP_HASH160 "
                                 "data-20 OP_EQUAL")
        transaction_hash = bytes.fromhex('5a805853bf82bcdd865deb09c73ccdd61d2331ac19d8c2911f17c7d954aec059')
        self.assertTrue(s.evaluate(message=transaction_hash))

    def test_script_verify_transaction_input_p2sh_multisig_huge(self):
        # Verify txid d0244d87cb38b01a7b4591c2d8001569011ce949b12a0779807e283764c559a3, input 0
        lock_script = bytes.fromhex('a91442c0ef1bc8426c22fc1b352b3914d947afad220f87')
        unlock_script = bytes.fromhex(
            '0047304402203668ee9156149aefd7538669f6f66c92e4f6aa802f6c18c736c388941b282fae022044b040b4527f6a6ef66c3c46'
            'cbc02e7a0ae5e08cb17a6abf9004de45a0d44f2e014830450221009af3500b12ec21aaeb0b9c5edc8fa0c078c9173e244a1162cd'
            '4686f4da8d6ee502203680ef8b9bc3a4a81c7b01d0fac34c3c1be7b744be7909b90e2f4f22d04308430147304402200611698a6c'
            '21953350cce43f7b21dd307bf23582f9759fbc499f8e4d5dcd1791022018feec8fbadb366e276d254ce1a109b8428212e11092d5'
            '73c9241f4edee42cfa01473044022075e937491475fa17152a455bdba429dce5c62b7f11f816fdaa5d100d9f2cc4b4022062c8c6'
            '627950f86efe1634a6e624951e8669552882d53b7460ad273337d048800147304402204cd6e7fce0e7b5e92cfed5d167966ef066'
            '4b299b564e57f00e8789b6c457b5b002201ebec3bada198b42411d5b3e26144a6f98b60b03c67c222343f7491edd8c7410014730'
            '4402203af77501770fe323688e184fdf92b370013d683dded4314c248cf1a8edf959db02205ea1d43f4773f047f670394d23dffd'
            '8ab41c6d3a7cce0edae8ecfefd8540ff0a0148304502210094adc3574386905392c18a680c18097cac7e1c17fb6776945f814bb8'
            'ca2c50200220446a0576514cccca0905d251ca978ad8393649e5ac8d80b6b37581a50da21dc6014730440220579369a2eee6f828'
            '1d57a34af15c3572d6b64e9ae6cee60bfc33b2e831520a420220630b2fd75159cdb7eef6495ef3754a35ff6e30800600f0c89be4'
            'aa0df6524842014d01025821032673b3bbd1cf671d483221ba3314a0e78def088ca28a35f881791eae10b537da21029ab6d3131d'
            '26d98576c51c1cb1357255ce31dc09f8331c22f9c1a4324246dbe32103f77c139a101535b23ae058726c0683b2b3b4cc488a14c9'
            '735308b1f8d57f7b902102cd0d5e4051e00c31b47d2cddf8a2650a602196ee1d0dcc871e3c82e91395c3de21037cc775b5b3be47'
            'b14aa1f58ec19a6e23d9a0a546e76a18a8386377ad993365522102fbf91889e817b14551be30d2c7b2a1c3d6bbaa045b24f66775'
            '561a0bcd0c7561210384b9f424fb646da1bf59b4d226190b3eae808a9ac4db7eb3be8f8cb0b29e20282103f65e07f56ef1ab3df0'
            '88003710a68ce47cfce91e377061394eff4c7cb6931f5c210254f9e470c2ca756059966fd95a161021ab221424bd5feb27a0144e'
            'fb6484bdca21025bcbfc18bfb1fc956b0b4936806926acd7e940477a364b2377bab7c8a0056d102103d53fb58f0628544c60a796'
            '2cd8064810865aae782d9d0c9777e1a36952db1c0e210378c616601b5a91eaec5c157988393fc45cf947033a10ebca6c40481406'
            '4e750721022f8e765f9dcd25102f0dc53b1155720e9e63c52d6c89fdf2be13a465b74c75892102c3ac37a4a4a47a193907a08fee'
            '9ffb09a6c51f402db71b7524caf7c067c5495e2102ce51833ecc7751a4a48062f182b08c6bd641a0866a7ce4d2fdbdc7b30e76ba'
            '8e5fae')
        redeemscript = bytes.fromhex(
            '5821032673b3bbd1cf671d483221ba3314a0e78def088ca28a35f881791eae10b537da21029ab6d3131d26d98576c51c1cb13572'
            '55ce31dc09f8331c22f9c1a4324246dbe32103f77c139a101535b23ae058726c0683b2b3b4cc488a14c9735308b1f8d57f7b9021'
            '02cd0d5e4051e00c31b47d2cddf8a2650a602196ee1d0dcc871e3c82e91395c3de21037cc775b5b3be47b14aa1f58ec19a6e23d9'
            'a0a546e76a18a8386377ad993365522102fbf91889e817b14551be30d2c7b2a1c3d6bbaa045b24f66775561a0bcd0c7561210384'
            'b9f424fb646da1bf59b4d226190b3eae808a9ac4db7eb3be8f8cb0b29e20282103f65e07f56ef1ab3df088003710a68ce47cfce9'
            '1e377061394eff4c7cb6931f5c210254f9e470c2ca756059966fd95a161021ab221424bd5feb27a0144efb6484bdca21025bcbfc'
            '18bfb1fc956b0b4936806926acd7e940477a364b2377bab7c8a0056d102103d53fb58f0628544c60a7962cd8064810865aae782d'
            '9d0c9777e1a36952db1c0e210378c616601b5a91eaec5c157988393fc45cf947033a10ebca6c404814064e750721022f8e765f9d'
            'cd25102f0dc53b1155720e9e63c52d6c89fdf2be13a465b74c75892102c3ac37a4a4a47a193907a08fee9ffb09a6c51f402db71b'
            '7524caf7c067c5495e2102ce51833ecc7751a4a48062f182b08c6bd641a0866a7ce4d2fdbdc7b30e76ba8e5fae')

        script = unlock_script + lock_script
        s = Script.parse_bytes(script)
        self.assertEqual(s.blueprint, [0, 'signature', 'signature', 'signature', 'signature', 'signature',
                                       'signature', 'signature', 'signature', [88, 'key', 'key', 'key', 'key',
                                       'key', 'key', 'key', 'key', 'key', 'key', 'key', 'key', 'key', 'key', 'key',
                                       95, 174], 169, 'data-20', 135])
        self.assertEqual(s.script_types, ['p2sh_multisig', 'p2sh'])
        self.assertEqual(str(s), "OP_0 signature signature signature signature signature signature signature "
                                 "signature redeemscript OP_HASH160 data-20 OP_EQUAL")
        transaction_hash = bytes.fromhex('8d190df3d02369999cad3eb222ac18b3315ff2bdc449b8fb30eb14db45730fe3')
        self.assertEqual(s.redeemscript, redeemscript)
        self.assertTrue(s.evaluate(message=transaction_hash))

    def test_script_verify_transaction_input_p2wpkh(self):
        # Verify txid 75a918220a54d31cf43ce93e6d62bc0c642932cfabab0cb73c8b99b0a2b015c2, input 0
        lock_script = op.op_dup.to_bytes(1, 'little') + op.op_hash160.to_bytes(1, 'little') + \
                      bytes.fromhex('147022028ab0454769a1ff6a5c94ce1a719d8f1b4b') + \
                      op.op_equalverify.to_bytes(1, 'little') + op.op_checksig.to_bytes(1, 'little')
        witnesses = varstr(bytes.fromhex(
            '3044022037fa29824b6ced7631d34154fba9922c477615c215df0ff4ef446dda9e64a8560220283c1e6f7fb8cd2cf68a148e'
            '7cce8f1b43dd4d162224b80b0cab38989ebf485401')) + varstr(
            bytes.fromhex('02f9009565c28990216c5d09ea8842b9b0e668346695f9aa275a8ae8d5e73fdca3'))
        script = witnesses + lock_script
        s = Script.parse_bytes(script)
        self.assertEqual(s.blueprint, ['signature', 'key', 118, 169, 'data-20', 136, 172])
        self.assertEqual(s.script_types, ['sig_pubkey', 'p2pkh'])
        self.assertEqual(str(s), "signature key OP_DUP OP_HASH160 data-20 OP_EQUALVERIFY OP_CHECKSIG")
        transaction_hash = bytes.fromhex('d63e8748dd7fd62d7530c6e611f8103b906318e01ef80a107832c9166159a58a')
        self.assertTrue(s.evaluate(message=transaction_hash))

    def test_script_verify_transaction_input_p2wsh(self):
        lock_script = op.op_sha256.to_bytes(1, 'little') + \
                      bytes.fromhex('20701a8d401c84fb13e6baf169d59684e17abd9fa216c8cc5b9fc63d622ff8c58d') + \
                      op.op_equal.to_bytes(1, 'little')
        redeemscript = bytes.fromhex(
            '52210375e00eb72e29da82b89367947f29ef34afb75e8654f6ea368e0acdfd92976b7c2103a1b26313f430c4b15bb1fdce6632'
            '07659d8cac749a0e53d70eff01874496feff2103c96d495bfdd5ba4145e3e046fee45e84a8a48ad05bd8dbb395c011a32cf9f8'
            '8053ae')
        witnesses = varstr(bytes.fromhex(
                        '304402200ff7be6d618235673218107f7f5ffcefeaed5b045dc01a88b7253ec8cc053ec50'
                        '22039b2eaa510d3a5cf634377e8dfa95061d9ad81e83a334c8cb03084cee110faf301')) + \
                    varstr(bytes.fromhex(
                        '3044022026312b6c39a71168113aaf7073bc904b1c77b4253e741e60de78ff16239cfe6202205cc9c4d6905a9b'
                        '3cebd970d91261896cb7ade4d198d16112651ac6833083b49e01')) + redeemscript

        script = witnesses + lock_script
        s = Script.parse_bytes(script)
        self.assertEqual(s.blueprint, ['signature', 'signature', 82, 'key', 'key', 'key', 83, 174, 168, 'data-32', 135])
        self.assertEqual(s.script_types, ['unknown'])
        self.assertEqual(str(s), "signature signature OP_2 key key key OP_3 OP_CHECKMULTISIG OP_SHA256 data-32 OP_EQUAL")
        transaction_hash = bytes.fromhex('43f0f6dfb58acc8ed05f5afc224c2f6c50523230bfcba5e5fd91d345e8a159ab')
        data = {'redeemscript': redeemscript}
        self.assertTrue(s.evaluate(message=transaction_hash, env_data=data))

    def test_script_verify_transaction_input_p2pk(self):
        p2pk_lockscript = '210312ed54eee6c84b440dd90623a714360196bebd842bfa64c7c7767b71b92a238dac'  # key + checksig
        p2pk_unlockscript = \
            ('463043021f52f02788988b941e3b810357762ccea5148e405edf124ea6b3b7eb9eba15430220609a9261612aaaa7544b7dae34'
             '7b5dc3e53b0fc304957d6c4a46e1ae90a5d30001')  # signature
        script = p2pk_unlockscript + p2pk_lockscript
        s = Script.parse_hex(script)
        transaction_hash = bytes.fromhex("67b94bf5a5c17a5f6b2bedbefc51a17db669ce7ff3bbbc4943cfd876d68df986")
        self.assertTrue(s.evaluate(message=transaction_hash))

    def test_script_verify_transaction_output_return(self):
        script = bytes.fromhex('6a26062c74e4b802d60ffdd1daa37b848e39a2b0ecb2de72c6ca24d71b87813b5e056cb7f1e8c8b0')
        s = Script.parse_bytes(script)
        self.assertEqual(s.blueprint, [106, 'data-38'])
        self.assertEqual(s.script_types, ['nulldata'])
        self.assertEqual(str(s), "OP_RETURN data-38")
        self.assertFalse(s.evaluate())

    def test_script_add(self):
        # Verify txid 6efe4f943b7898c4308c67b47bac57551ff41977edc254eafb0436467632450f, input 0
        lock_script = Script.parse_bytes(bytes.fromhex('76a914f9cc73824051cc82d64a716c836c54467a21e22c88ac'))
        unlock_script = Script.parse_bytes(bytes.fromhex(
            '483045022100ba2ec7c40257b3d22864c9558738eea4d8771ab97888368124e176fdd6d7cd8602200f47c8d0c437df1ea8f98'
            '19d344e05b9c93e38e88df1fc46abb6194506c50ce1012103e481f20561573cfd800e64efda61405917cb29e4bd20bed168c5'
            '2b674937f535'))
        script = unlock_script + lock_script
        self.assertEqual(script.blueprint, ['signature', 'key', 118, 169, 'data-20', 136, 172])
        self.assertEqual(script.script_types, ['sig_pubkey', 'p2pkh'])
        self.assertEqual(str(script), "signature key OP_DUP OP_HASH160 data-20 OP_EQUALVERIFY OP_CHECKSIG")
        transaction_hash = bytes.fromhex('12824db63e7856d00ee5e109fd1c26ac8a6a015858c26f4b336274f6b52da1c3')
        self.assertTrue(script.evaluate(message=transaction_hash))

    def test_script_create_simple(self):
        script = Script([op.op_2, op.op_5, op.op_sub, op.op_1])
        self.assertEqual(str(script), 'OP_2 OP_5 OP_SUB OP_1')
        self.assertEqual(repr(script), '<Script([op_2, op_5, op_sub, op_1])>')
        self.assertEqual(script.serialize().hex(), '52559451')
        self.assertEqual(script.serialize_list(), [b'R', b'U', b'\x94', b'Q'])
        self.assertTrue(script.evaluate())
        self.assertEqual(script.stack, [b'\3'])

    def test_script_calc_evaluate(self):
        s = Script.parse('0101016293016387')
        self.assertListEqual(s.blueprint, ['data-1', 'data-1', 147, 'data-1', 135])
        self.assertTrue(s.view(), '01 62 OP_ADD 63 OP_EQUAL')
        self.assertTrue(s.evaluate())

    def test_script_serialize(self):
        # Serialize p2sh_p2wsh tx 77ad5a0f9447dbfb9adcdb9b2437e91780519ec8ee24a8eda91b25a0666205cb from sigs and keys
        sig1 = b'0E\x02!\x00\xde\x8fDH\xe2\xd2\xe7F\x18>B\xe4\xfd\x87\xb8\x0b\x87\xfb\xb1\xd7ZYL\xa4\x08\x12\xe5\x07v' \
               b'\xd5\xd6\x14\x02 ]kH\xfe\x1c\xc5\x90\r\xf6fF\x085\xfa\x10C\xb8^\x92":\x15\x87\x98\x95\xf1(\t\xdb?}' \
               b'\xe3\x01'
        sig2 = b"0D\x02 hp\xd6\xdc\r\xe3\xef\xd5\xd6\xe1u\xd3i\xc8\x81KN\x86X\x96S!\x8c\xe9R\xe6\xbc\xc1\xa4>\xd5\xa3" \
               b"\x02 U\xafu\xda\xad`\x92$\xd1\xf6Jc5\xeb\xb9\xe1M\xeb!L&\xec'{\xb2\xaeW2n\xa7\xb3\x02\x01"
        key1 = bytes.fromhex('02cd9107f8f1505ffd779bb7d8596ee686afc116e340f01b435871a038922255eb')
        key2 = bytes.fromhex('0297faa15d33e14e80ca8a8616030b677941245fea12c4ef2ca28b14bd35ed42e1')
        key3 = bytes.fromhex('0221b302fb92b25f171f1cd57bd22e60a1d2956f5831df17d94b3e9c3490aad598')
        redeemscript = Script([op.op_2, key1, key2, key3, op.op_3, op.op_checkmultisig])
        script_hash = bytes.fromhex('b0fcc0caed77aeba9786f39920151162dfaf90e679aafab7a71e9b978e7d3f39')
        self.assertEqual(redeemscript.as_hex(),
                         '522102cd9107f8f1505ffd779bb7d8596ee686afc116e340f01b435871a038922255eb210297faa15d33e14e80c'
                         'a8a8616030b677941245fea12c4ef2ca28b14bd35ed42e1210221b302fb92b25f171f1cd57bd22e60a1d2956f58'
                         '31df17d94b3e9c3490aad59853ae')

        transaction_hash = b'\xc9u\x9d*]\xc8*\xf2\xb9-\xb5z\x02\x96\xc7\xce\x88e\xdd$\x8dO{M\x8e\x92ge\xc1g\x8f\x84'
        script = Script([op.op_0, sig1, sig2]) + Script(redeemscript.commands) + \
                 Script([op.op_sha256, script_hash, op.op_equal])
        self.assertEqual(str(script), 'OP_0 signature signature OP_2 key key key OP_3 OP_CHECKMULTISIG OP_SHA256 '
                                      'data-32 OP_EQUAL')
        self.assertTrue(script.evaluate(message=transaction_hash, env_data={'redeemscript': redeemscript.serialize()}))
        self.assertEqual(script.stack, [])

    def test_script_deserialize_sig_pk2(self):
        spk = '473044022034519a85fb5299e180865dda936c5d53edabaaf6d15cd1740aac9878b76238e002207345fcb5a62deeb8d9d80e5' \
              'b412bd24d09151c2008b7fef10eb5f13e484d1e0d01210207c9ece04a9b5ef3ff441f3aad6bb63e323c05047a820ab45ebbe6' \
              '1385aa7446'
        s = Script.parse(spk)
        self.assertEqual(s.script_types, ['sig_pubkey'])
        self.assertEqual(
            s.signatures[0].as_der_encoded().hex(),
            '3044022034519a85fb5299e180865dda936c5d53edabaaf6d15cd1740aac9878b76238e00220'
            '7345fcb5a62deeb8d9d80e5b412bd24d09151c2008b7fef10eb5f13e484d1e0d01')
        self.assertEqual(
            s.keys[0].hex(), '0207c9ece04a9b5ef3ff441f3aad6bb63e323c05047a820ab45ebbe61385aa7446')

    def test_deserialize_script_with_sizebyte(self):
        script_size_byte = b'\x16\x00\x14y\t\x19r\x18lD\x9e\xb1\xde\xd2+x\xe4\r\x00\x9b\xdf\x00\x89'
        script = b'\x00\x14y\t\x19r\x18lD\x9e\xb1\xde\xd2+x\xe4\r\x00\x9b\xdf\x00\x89'
        s1 = Script.parse(script_size_byte)
        s2 = Script.parse(script)
        s1._raw = s2.as_bytes()
        self.assertDictEqualExt(s1.__dict__, s2.__dict__)

    def test_script_parse_redeemscript(self):
        redeemscript = '524104a882d414e478039cd5b52a92ffb13dd5e6bd4515497439dffd691a0f12af9575fa349b5694ed3155b136f09' \
                       'e63975a1700c9f4d4df849323dac06cf3bd6458cd41046ce31db9bdd543e72fe3039a1f1c047dab87037c36a669ff' \
                       '90e28da1848f640de68c2fe913d363a51154a0c62d7adea1b822d05035077418267b1a1379790187410411ffd36c7' \
                       '0776538d079fbae117dc38effafb33304af83ce4894589747aee1ef992f63280567f52f5ba870678b4ab4ff6c8ea6' \
                       '00bd217870a8b4f1f09f3a8e8353ae'
        s = Script.parse_hex(redeemscript)
        self.assertEqual(s.serialize().hex(), redeemscript)

    def test_script_create_redeemscript(self):
        key1 = '5JruagvxNLXTnkksyLMfgFgf3CagJ3Ekxu5oGxpTm5mPfTAPez3'
        key2 = '5JX3qAwDEEaapvLXRfbXRMSiyRgRSW9WjgxeyJQWwBugbudCwsk'
        key3 = '5JjHVMwJdjPEPQhq34WMUhzLcEd4SD7HgZktEh8WHstWcCLRceV'
        keylist = [Key(k) for k in [key1, key2, key3]]
        redeemscript = Script(keys=keylist, sigs_required=2, script_types=['multisig'])
        expected_redeemscript = \
                       '524104a882d414e478039cd5b52a92ffb13dd5e6bd4515497439dffd691a0f12af9575fa349b5694ed3155b136f09' \
                       'e63975a1700c9f4d4df849323dac06cf3bd6458cd41046ce31db9bdd543e72fe3039a1f1c047dab87037c36a669ff' \
                       '90e28da1848f640de68c2fe913d363a51154a0c62d7adea1b822d05035077418267b1a1379790187410411ffd36c7' \
                       '0776538d079fbae117dc38effafb33304af83ce4894589747aee1ef992f63280567f52f5ba870678b4ab4ff6c8ea6' \
                       '00bd217870a8b4f1f09f3a8e8353ae'
        self.assertEqual(expected_redeemscript, redeemscript.serialize().hex())

        redeemscript3 = b'\x52' + b''.join([varstr(k.public_byte) for k in keylist]) + b'\x53\xae'
        self.assertEqual(redeemscript3, redeemscript.serialize())

    def test_script_create_redeemscript_2(self):
        key1 = Key('02600ca766925ef97fbd4b38b8dc35714edc27e1a0d454268d592c369835f49584')
        redeemscript = Script(keys=[key1], sigs_required=1, script_types=['multisig'])
        expected_redeemscript = '512102600ca766925ef97fbd4b38b8dc35714edc27e1a0d454268d592c369835f4958451ae'
        self.assertEqual(expected_redeemscript, redeemscript.serialize().hex())

    def test_script_different_hashtype(self):
        scr = '493046022100cf4d7571dd47a4d47f5cb767d54d6702530a3555726b27b6ac56117f5e7808fe0221008cbb42233bb04d7f28a' \
              '715cf7c938e238afde90207e9d103dd9018e12cb7180e03'
        s = Script.parse(scr)
        self.assertEqual(s.signatures[0].hash_type, 3)

    def test_script_large_redeemscript_packing(self):
        redeemscript_str = 'OP_15 key key key key key key key key key key key key key key key OP_15 OP_CHECKMULTISIG'
        redeemscript = '5f2103938f49f584ecdb52041cab7e8ac2b241feec7ff00c2823ee6e249425a2df18d52103938f49f584ecdb5204' \
                       '1cab7e8ac2b241feec7ff00c2823ee6e249425a2df18d52103938f49f584ecdb52041cab7e8ac2b241feec7ff00c' \
                       '2823ee6e249425a2df18d52103938f49f584ecdb52041cab7e8ac2b241feec7ff00c2823ee6e249425a2df18d521' \
                       '03938f49f584ecdb52041cab7e8ac2b241feec7ff00c2823ee6e249425a2df18d52103938f49f584ecdb52041cab' \
                       '7e8ac2b241feec7ff00c2823ee6e249425a2df18d52103938f49f584ecdb52041cab7e8ac2b241feec7ff00c2823' \
                       'ee6e249425a2df18d52103938f49f584ecdb52041cab7e8ac2b241feec7ff00c2823ee6e249425a2df18d5210393' \
                       '8f49f584ecdb52041cab7e8ac2b241feec7ff00c2823ee6e249425a2df18d52103938f49f584ecdb52041cab7e8a' \
                       'c2b241feec7ff00c2823ee6e249425a2df18d52103938f49f584ecdb52041cab7e8ac2b241feec7ff00c2823ee6e' \
                       '249425a2df18d52103938f49f584ecdb52041cab7e8ac2b241feec7ff00c2823ee6e249425a2df18d52103938f49' \
                       'f584ecdb52041cab7e8ac2b241feec7ff00c2823ee6e249425a2df18d52103938f49f584ecdb52041cab7e8ac2b2' \
                       '41feec7ff00c2823ee6e249425a2df18d52103938f49f584ecdb52041cab7e8ac2b241feec7ff00c2823ee6e2494' \
                       '25a2df18d55fae'

        s = Script.parse_hex(redeemscript)
        self.assertEqual((str(s)), redeemscript_str)

        redeemscript2 = data_pack(bytes.fromhex(redeemscript))
        s = Script.parse_bytes(redeemscript2)
        self.assertEqual((str(s)), redeemscript_str)

        redeemscript_size = '4d0102' + redeemscript
        s = Script.parse_hex(redeemscript_size)
        self.assertEqual((str(s)), redeemscript_str)

        redeemscript_size = '4dff01' + redeemscript
        s = Script.parse_hex(redeemscript_size)
        self.assertEqual((str(s)), "redeemscript OP_15 OP_CHECKMULTISIG")

        redeemscript_error = '4d0101' + redeemscript
        self.assertRaisesRegex(ScriptError, "Malformed script, not enough data found", Script.parse_hex,
                               redeemscript_error)

        redeemscript_error = '4d0202' + redeemscript
        self.assertRaisesRegex(ScriptError, "Malformed script, not enough data found", Script.parse_hex,
                               redeemscript_error)

    def test_script_view(self):
        script = bytes.fromhex(
            '483045022100ba2ec7c40257b3d22864c9558738eea4d8771ab97888368124e176fdd6d7cd8602200f47c8d0c437df1ea8f98'
            '19d344e05b9c93e38e88df1fc46abb6194506c50ce1012103e481f20561573cfd800e64efda61405917cb29e4bd20bed168c5'
            '2b674937f53576a914f9cc73824051cc82d64a716c836c54467a21e22c88ac')
        s = Script.parse(script)
        expected_str = ('3045022100ba2ec7c40257b3d22864c9558738eea4d8771ab97888368124e176fdd6d7cd8602200f47c8d0c437'
                        'df1ea8f9819d344e05b9c93e38e88df1fc46abb6194506c50ce101 03e481f20561573cfd800e64efda6140591'
                        '7cb29e4bd20bed168c52b674937f535 OP_DUP OP_HASH160 f9cc73824051cc82d64a716c836c54467a21e22c'
                        ' OP_EQUALVERIFY OP_CHECKSIG')
        self.assertEqual(s.view(), expected_str)
        self.assertEqual(s.blueprint, s.view(blueprint=True, as_list=True, op_code_numbers=True))
        self.assertEqual(str(s), s.view(blueprint=True))

    def test_script_str(self):
        script_str = "1 98 OP_ADD 99 OP_EQUAL"
        s = Script.parse_str(script_str)
        self.assertEqual(s.view(), script_str)
        self.assertTrue(s.evaluate())
        self.assertEqual(s.as_hex(), '0101016293016387')

        script_str_2 = "OP_DUP OP_HASH160 af8e14a2cecd715c363b3a72b55b59a31e2acac9 OP_EQUALVERIFY OP_CHECKSIG"
        s = Script.parse_str(script_str_2)
        clist = [118, 169, b'\xaf\x8e\x14\xa2\xce\xcdq\\6;:r\xb5[Y\xa3\x1e*\xca\xc9', 136, 172]
        self.assertListEqual(s.commands, clist)
        self.assertEqual(s.view(), script_str_2)

    def test_script_locking_type(self):
        script_str = (b'"\x00 \x04\x7f\x8d]S\x04\xb8\xa1x\xbf\xfb\xd7\xc1\xc0\xc7\xc2To\xc9O\xc3\xb2\x91\n\xdb\x9db'
                      b'\x19\x85{]\x9f')
        self.assertEqual(Script.parse(script_str, is_locking=True).script_types, ['p2wsh'])
        self.assertEqual(Script.parse(script_str, is_locking=False).script_types, ['p2sh_p2wsh'])

class TestScriptMPInumbers(unittest.TestCase):

    def test_encode_decode_numbers(self):
        for i in range(-100000, 100000):
            bn = encode_num(i)
            n = decode_num(bn)
            self.assertEqual(n, i, "Verschil bij %d" % i)
