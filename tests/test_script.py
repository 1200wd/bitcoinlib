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

    def test_op_stack_op_checkmultisig(self):
        sig1 = b'0E\x02!\x00\xa7]\n\xf9\xf7f\xaa\xc1\xdc\xd2&e[\x089\x81\x02e\xff\x1b\xb34\xb00\xa3_\xa0Q\xd2s`\x92\x02 B\xb6\xbb\xb3\x15d\x8b\x9c\xd5\x07\x87\xdd&u\xf5~\xee\xe7\xf6\x97\xa5\xfc\xb3\x81\xb4\x9d\x90\x82L\xbf7,\x01'
        sig2 = b'0F\x02!\x00\xbb\xb0!\x81\xf1\x10\xa1\x93\x8b\xa6N\xec\xafZV0\xd4\xa6\x91cb\x04c\xad\xc9\xb0#\xdb\xbe\x7f!z\x02!\x00\x80\xd7\xef"\xec\xd4\x08\x9a@nb\'\xb4\x88\xfd\'\xf4\x02jg\x9b:\x1b\xf8ck\xbe\xaf<\x1a\x07n\x01'
        key1 = b'\x04\xdf_j\x9b\x95\xa9\xdb>n\xea!\xfa\xf0\\\xe1\x13p\xd3\x8dW\x14\xf6\x04\xf4\xff\xeb\x9dA\x8a\x1a~O \xea\x16\xe2\xe8J\xf1\xd7\xde\xac]\xa3\xcc\xf8\xf1\x8c\x1d\x18Sbd\xa6\xe9\xccMv\x04\xa4z\xe7\xcb\xc5'
        key2 = b'\x042J\xef\x0f65R"n\xf7@\xff|\x82\xacI\x80\x9am\xee\x16y\xde<\x9c~|\x14\x0b\x04\x16\x05;\xe3\x8d\x19\xc9?\xbeM\xd7\x1b\xfds\xaa?\rK\x87\xe1\x92\x06_\xb3X3\xc4B\xb8qn\x96\x8d?'
        key3 = b"\x04\x13\x07\x04Za\xc6\x9c\x84\x03\xb1\x07n\x0f4\xa8=\r\xcc\x1f\xacc\x07\xbe\xbf\n\x11R\xf0\x1dX\xdaw\xe3\n\x19\xcd\xeds<ie-\xc8y\xfb,4S\xbb8wj\xef\xe6\x12\x1e<\xf8\xde<Y\xa8'\xcc"
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


class TestScript(unittest.TestCase):

    def test_script_verify_transaction_input_p2pkh(self):
        # Verify txid 6efe4f943b7898c4308c67b47bac57551ff41977edc254eafb0436467632450f, input 0
        lock_script = bytes.fromhex('76a914f9cc73824051cc82d64a716c836c54467a21e22c88ac')
        unlock_script = bytes.fromhex(
            '483045022100ba2ec7c40257b3d22864c9558738eea4d8771ab97888368124e176fdd6d7cd8602200f47c8d0c437df1ea8f98'
            '19d344e05b9c93e38e88df1fc46abb6194506c50ce1012103e481f20561573cfd800e64efda61405917cb29e4bd20bed168c5'
            '2b674937f535')
        script = unlock_script + lock_script
        s = Script.parse(script)
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
        redeemscript = bytes.fromhex(
            '522103614101c3dfc98f6a7b562cd9264cc6e0d8d9597f59feea666d4c7605493b928b2102386823b976815e4f6d7279b7b4a2'
            '113c7d9e0796fa7b1ac43caa7d464a1a06db2102e7ae0137cab0a11b49caeae853d06c9499e79029670a2d649cc2e9e58b99dc'
            '5753ae')

        script = unlock_script + lock_script
        s = Script.parse(script)
        self.assertEqual(s.blueprint, [0, 'signature', 'signature', 82, 'key', 'key', 'key', 83, 174, 169,
                                       'data-20', 135])
        self.assertEqual(s.script_types, ['p2sh_multisig', 'p2sh'])
        self.assertEqual(str(s), "OP_0 signature signature OP_2 key key key OP_3 OP_CHECKMULTISIG OP_HASH160 "
                                 "data-20 OP_EQUAL")
        transaction_hash = bytes.fromhex('5a805853bf82bcdd865deb09c73ccdd61d2331ac19d8c2911f17c7d954aec059')
        data = {'redeemscript': redeemscript}
        self.assertTrue(s.evaluate(message=transaction_hash, tx_data=data))

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
        s = Script.parse(script)
        self.assertEqual(s.blueprint, [0, 'signature', 'signature', 'signature', 'signature', 'signature',
                                       'signature', 'signature', 'signature', 88, 'key', 'key', 'key', 'key',
                                       'key', 'key', 'key', 'key', 'key', 'key', 'key', 'key', 'key', 'key', 'key',
                                       95, 174, 169, 'data-20', 135])
        self.assertEqual(s.script_types, ['p2sh_multisig', 'p2sh'])
        self.assertEqual(str(s), "OP_0 signature signature signature signature signature signature signature "
                                 "signature OP_8 key key key key key key key key key key key key key key key OP_15 "
                                 "OP_CHECKMULTISIG OP_HASH160 data-20 OP_EQUAL")
        transaction_hash = bytes.fromhex('8d190df3d02369999cad3eb222ac18b3315ff2bdc449b8fb30eb14db45730fe3')
        data = {'redeemscript': redeemscript}
        self.assertTrue(s.evaluate(message=transaction_hash, tx_data=data))

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
        s = Script.parse(script)
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
            '304402200ff7be6d618235673218107f7f5ffcefeaed5b045dc01a88b7253ec8cc053ec5022039b2eaa510d3a5cf634377e8df'
            'a95061d9ad81e83a334c8cb03084cee110faf301')) + \
                    varstr(bytes.fromhex(
                        '3044022026312b6c39a71168113aaf7073bc904b1c77b4253e741e60de78ff16239cfe6202205cc9c4d6905a9b'
                        '3cebd970d91261896cb7ade4d198d16112651ac6833083b49e01')) + \
                    bytes.fromhex(
                        '52210375e00eb72e29da82b89367947f29ef34afb75e8654f6ea368e0acdfd92976b7c2103a1b26313f430c4b'
                        '15bb1fdce663207659d8cac749a0e53d70eff01874496feff2103c96d495bfdd5ba4145e3e046fee45e84a8a4'
                        '8ad05bd8dbb395c011a32cf9f88053ae')

        script = witnesses + lock_script
        s = Script.parse(script)
        self.assertEqual(s.blueprint, ['signature', 'signature', 82, 'key', 'key', 'key', 83, 174, 168, 'data-32', 135])
        self.assertEqual(s.script_types, ['signature', 'multisig', 'unknown'])
        self.assertEqual(str(s), "signature signature OP_2 key key key OP_3 OP_CHECKMULTISIG OP_SHA256 data-32 OP_EQUAL")
        transaction_hash = bytes.fromhex('43f0f6dfb58acc8ed05f5afc224c2f6c50523230bfcba5e5fd91d345e8a159ab')
        data = {'redeemscript': redeemscript}
        self.assertTrue(s.evaluate(message=transaction_hash, tx_data=data))

    def test_script_verify_transaction_input_p2pk(self):
        pass
        # TODO

    def test_script_verify_transaction_output_return(self):
        script = bytes.fromhex('6a26062c74e4b802d60ffdd1daa37b848e39a2b0ecb2de72c6ca24d71b87813b5e056cb7f1e8c8b0')
        s = Script.parse(script)
        self.assertEqual(s.blueprint, [106, 'data-38'])
        self.assertEqual(s.script_types, ['nulldata'])
        self.assertEqual(str(s), "OP_RETURN data-38")
        self.assertFalse(s.evaluate())

    def test_script_add(self):
        # Verify txid 6efe4f943b7898c4308c67b47bac57551ff41977edc254eafb0436467632450f, input 0
        lock_script = Script.parse(bytes.fromhex('76a914f9cc73824051cc82d64a716c836c54467a21e22c88ac'))
        unlock_script = Script.parse(bytes.fromhex(
            '483045022100ba2ec7c40257b3d22864c9558738eea4d8771ab97888368124e176fdd6d7cd8602200f47c8d0c437df1ea8f98'
            '19d344e05b9c93e38e88df1fc46abb6194506c50ce1012103e481f20561573cfd800e64efda61405917cb29e4bd20bed168c5'
            '2b674937f535'))
        script = unlock_script + lock_script
        self.assertEqual(script.blueprint, ['signature', 'key', 118, 169, 'data-20', 136, 172])
        self.assertEqual(script.script_types, ['sig_pubkey', 'p2pkh'])
        self.assertEqual(str(script), "signature key OP_DUP OP_HASH160 data-20 OP_EQUALVERIFY OP_CHECKSIG")
        transaction_hash = bytes.fromhex('12824db63e7856d00ee5e109fd1c26ac8a6a015858c26f4b336274f6b52da1c3')
        self.assertTrue(script.evaluate(message=transaction_hash))