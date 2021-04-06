# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Scripts class - Parse, Serialize and Evaluate scripts
#    © 2021 - 1200 Web Development <http://1200wd.com/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from bitcoinlib.encoding import *
from bitcoinlib.main import *
from bitcoinlib.config.opcodes import *


_logger = logging.getLogger(__name__)


class ScriptError(Exception):
    """
    Handle Key class Exceptions

    """
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


class Script(object):

    def __init__(self, commands=None):
        self.commands = []
        if commands:
            self.commands = commands
        self.raw = b''
        self.stack = []
        # self.is_locking =
        # self.type =
        # self.keys? signatures?

    @classmethod
    def parse(cls, script):
        cur = 0
        commands = []
        while cur < len(script):
            ch = script[cur]
            cur += 1
            if 1 <= ch <= 75:  # Data
                commands.append(script[cur:cur+ch])
                cur += ch
            elif ch == op.op_pushdata1:
                length = script[cur]
                cur += 1
                commands.append(script[cur:cur+length])
                cur += length
            elif ch == op.op_pushdata2:
                length = varbyteint_to_int(script[cur:cur+2])
                cur += 2
                commands.append(script[cur:cur+length])
                cur += length
            else:  # Other opcode
                commands.append(ch)
        if cur != len(script):
            raise ScriptError("Parsing script failed, invalid length")
        s = cls(commands)
        s.raw = script
        return s

    def serialize(self):
        raw = b''
        for cmd in self.commands:
            if isinstance(cmd, int):
                raw += bytes([cmd])
            else:
                if len(cmd) <= 75:
                    raw += len(cmd).to_bytes(1, 'big')
                elif 75 < len(cmd) <= 255:
                    raw += b'L' + len(cmd).to_bytes(1, 'little')
                else:
                    raw += b'M' + len(cmd).to_bytes(2, 'little')
                raw += cmd
        self.raw = raw
        return raw

    def evaluate(self):
        self.stack = Stack()
        commands = self.commands[:]
        while len(commands):
            command = commands.pop(0)
            if isinstance(command, int):
                print("Stack: %s  ; Running operation %s" % (self.stack, opcodenames[command]))
                if command == op.op_0:  # OP_0
                    self.stack.append(encode_num(0))
                    # self.stack.append(0)
                elif command == op.op_1negate:  # OP_1NEGATE
                    # self.stack.append(b'\x81')
                    self.stack.append(encode_num(-1))
                    # self.stack.append(-1)
                elif 81 <= command <= 96:   # OP_1 to OP_16
                    # self.stack.append(bytes([command-80]))
                    self.stack.append(encode_num(command-80))
                    # self.stack.append(command-80)
                else:
                    method = opcodenames[command].lower()
                    if method not in dir(self.stack):
                        raise ScriptError("Method %s not found" % method)
                    # method_args = op_methods[method]
                    # self.stack.operate(*method_args)
                    try:
                        res = getattr(self.stack, method)()
                        if res is False:
                            return False
                    except Exception as e:
                        print("Error: %s" % e)
                        return False

                    # Encode new items on stack
                    for i in range(len(self.stack)):
                        if isinstance(self.stack[i], int):
                            self.stack[i] = encode_num(self.stack[i])

                    # if not method(self.stack):
                    #     return False
            else:
                print("Add data %s to stack" % command.hex())
                self.stack.append(command)
            # print(self.stack)
        return True

    def __str__(self):
        s_items = []
        for command in self.commands:
            if isinstance(command, int):
                s_items.append(opcodenames[command])
            else:
                s_items.append(command.hex())
        return ' '.join(s_items)


class Stack(list):

    def pop_as_number(self):
        return decode_num(self.pop())

    def op_nop(self):
        pass

    def op_verify(self):
        if self.pop() == b'':
            return False
        return True

    @staticmethod
    def op_return():
        return False

    def op_2drop(self):
        self.pop()
        self.pop()

    def op_2dup(self):
        self.extend(self[-2:])

    def op_3dup(self):
        self.extend(self[-3:])

    def op_2over(self):
        self.extend(self[-4:-2])

    def op_2rot(self):
        self.extend([self.pop(-6), self.pop(-5)])

    # 'op_2swap': (2, '__setitem__',  [slice(-2, -2)], 4, False, True),
    # # 'op_ifdup':

    def op_depth(self):
        self.append(len(self))

    def op_drop(self):
        self.pop()

    def op_dup(self):
        if not len(self):
            return False
        self.append(self[-1:])

    # 'op_nip': (0, '__delitem__', [-2], 2),
    # 'op_over': (0, '__getitem__', [-2], 1, False),

    def op_pick(self):
        self.append(self[-self.pop()])

    # # 'op_roll':
    # 'op_rot': (0, 'pop', [-3], 3, False, True),
    # 'op_swap': (1, 'insert', [-1], 2, False, True),
    # # 'op_tuck': (1, 'insert', [-1, lambda a: a], 2, False, True),
    # # 'op_cat': disabled in bitcoin
    # # 'op_substr': disabled in bitcoin
    # # 'op_left': disabled in bitcoin
    # # 'op_right': disabled in bitcoin
    # 'op_size': (0, '__len__', None, 0, False, True),
    # # 'op_invert': disabled in bitcoin
    # # 'op_and': disabled in bitcoin
    # # 'op_or': disabled in bitcoin
    # # 'op_xor': disabled in bitcoin
    # 'op_equal': (2, '__eq__', None, 1, False),
    def op_equal(self):
        self.append(b'\x01' if self.pop() == self.pop() else b'')

    def op_equalverify(self):
        self.op_equal()

    # # 'op_reserved1': used by op_if
    # # 'op_reserved2': used by op_if
    # 'op_1add': (1, '__add__', [1], 1, True),
    # 'op_1sub': (1, '__sub__', [1], 1, True),
    # # 'op_2mul': disabled in bitcoin
    # # 'op_2div': disabled in bitcoin
    # # 'op_abs':
    # # 'op_not': (1, '__bool__', None, 1, True),
    # # 'op_0notequal':

    def op_add(self):
        self.append(encode_num(self.pop_as_number() + self.pop_as_number()))

    def op_sub(self):
        self.append(encode_num(self.pop_as_number() - self.pop_as_number()))

    # # 'op_mul': disabled in bitcoin
    # # 'op_div':disabled in bitcoin
    # # 'op_mod': disabled in bitcoin
    # # 'op_lshift': disabled in bitcoin
    # # 'op_rshift': disabled in bitcoin
    # 'op_booland': (2, '__and__', None, 2, True),
    # # 'op_boolor':
    # # 'op_numequal':
    # # 'op_numequalverify':
    # # 'op_numnotequal':
    # # 'op_lessthan':
    # # 'op_greaterthan':
    # # 'op_lessthanorequal':
    # # 'op_greaterthanorequal':
    # # 'op_min':
    # # 'op_max':
    # # 'op_within':
    # # 'op_ripemd160':
    # # 'op_sha1':
    # # 'op_sha256':

    def op_hash160(self):
        self.pop()
        return 'hash160'

    # # 'op_hash256':
    # # 'op_codeseparator':

    def op_checksig(self):
        return True

    # # 'op_checksigverify':
    # # 'op_checkmultisig':
    # # 'op_checkmultisigverify':
    # 'op_nop1': (0, '', None, 0, False),
    # # 'op_checklocktimeverify':
    # # 'op_checksequenceverify':
    # 'op_nop4': (0, '', None, 0, False),
    # 'op_nop5': (0, '', None, 0, False),
    # 'op_nop6': (0, '', None, 0, False),
    # 'op_nop7': (0, '', None, 0, False),
    # 'op_nop8': (0, '', None, 0, False),
    # 'op_nop9': (0, '', None, 0, False),
    # 'op_nop10': (0, '', None, 0, False),
    # # 'op_invalidopcode':


def encode_num(num):
    if num == 0:
        return b''
    abs_num = abs(num)
    negative = num < 0
    result = bytearray()
    while abs_num:
        result.append(abs_num & 0xff)
        abs_num >>= 8
    if result[-1] & 0x80:
        if negative:
            result.append(0x80)
        else:
            result.append(0)
    elif negative:
        result[-1] |= 0x80
    return bytes(result)


def decode_num(element):
    if element == b'':
        return 0
    big_endian = element[::-1]
    if big_endian[0] & 0x80:
        negative = True
        result = big_endian[0] & 0x7f
    else:
        negative = False
        result = big_endian[0]
    for c in big_endian[1:]:
        result <<= 8
        result += c
    if negative:
        return -result
    else:
        return result