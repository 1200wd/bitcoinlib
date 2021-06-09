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
        self.assertEqual(s.script_type, ['sig_pubkey', 'p2pkh'])
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
        self.assertEqual(s.script_type, ['p2sh_multisig', 'p2sh'])
        self.assertEqual(str(s), "OP_0 signature signature OP_2 key key key OP_3 OP_CHECKMULTISIG OP_HASH160 "
                                 "data-20 OP_EQUAL")
        transaction_hash = bytes.fromhex('5a805853bf82bcdd865deb09c73ccdd61d2331ac19d8c2911f17c7d954aec059')
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
        self.assertEqual(s.script_type, ['sig_pubkey', 'p2pkh'])
        self.assertEqual(str(s), "signature key OP_DUP OP_HASH160 data-20 OP_EQUALVERIFY OP_CHECKSIG")
        transaction_hash = bytes.fromhex('d63e8748dd7fd62d7530c6e611f8103b906318e01ef80a107832c9166159a58a')
        self.assertTrue(s.evaluate(message=transaction_hash))
