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
from bitcoinlib.keys import Signature


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

    @classmethod
    def from_ints(cls, list_ints):
        return Stack([encode_num(n) for n in list_ints])

    def as_ints(self):
        # TODO: What to do with data/hashes?
        return Stack([decode_num(x) for x in self])

    def pop_as_number(self):
        return decode_num(self.pop())

    def is_arithmetic(self, items=1):
        """
        Check if top stack item is or last stock are arithmetic and has no more then 4 bytes

        :return bool:
        """
        if len(self) < items:
            raise IndexError("Not enough items in list to run operation. Items %d, expected %d" % (len(self), items))
        for i in self[-items:]:
            if len(i) > 4:
                return False
        return True

    def op_nop(self):
        return True

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
        return True

    def op_2dup(self):
        if len(self) < 2:
            raise ValueError("Stack op_2dup method requires minimum of 2 stack items")
        self.extend(self[-2:])
        return True

    def op_3dup(self):
        if len(self) < 3:
            raise ValueError("Stack op_3dup method requires minimum of 3 stack items")
        self.extend(self[-3:])
        return True

    def op_2over(self):
        if len(self) < 4:
            raise ValueError("Stack op_2over method requires minimum of 4 stack items")
        self.extend(self[-4:-2])
        return True

    def op_2rot(self):
        self.extend([self.pop(-6), self.pop(-5)])
        return True

    def op_2swap(self):
        self[-2:-2] = [self.pop(), self.pop()]
        return True

    def op_ifdup(self):
        if not len(self):
            raise ValueError("Stack op_ifdup method requires minimum of 1 stack item")
        if self[-1] != b'':
            self.append(self[-1])
        return True

    def op_depth(self):
        self.append(encode_num(len(self)))
        return True

    def op_drop(self):
        self.pop()
        return True

    def op_dup(self):
        if not len(self):
            return False
        self.append(self[-1])
        return True

    def op_nip(self):
        self.pop(-2)
        return True

    def op_over(self):
        if len(self) < 2:
            raise ValueError("Stack op_over method requires minimum of 2 stack items")
        self.append(self[-2])
        return True

    def op_pick(self):
        self.append(self[-self.pop_as_number()])
        return True

    def op_roll(self):
        self.append(self.pop(-self.pop_as_number()))
        return True

    def op_rot(self):
        self.append(self.pop(-3))
        return True

    def op_swap(self):
        self.append(self.pop(-2))
        return True

    def op_tuck(self):
        self.append(self[-2])
        return True

    def op_size(self):
        self.append(encode_num(len(self[-1])))
        return True

    def op_equal(self):
        self.append(b'\x01' if self.pop() == self.pop() else b'')
        return True

    def op_equalverify(self):
        self.op_equal()
        return self.op_verify()

    # # 'op_reserved1': used by op_if
    # # 'op_reserved2': used by op_if

    def op_1add(self):
        if not self.is_arithmetic():
            return False
        self.append(encode_num(self.pop_as_number() + 1))
        return True

    def op_1sub(self):
        if not self.is_arithmetic():
            return False
        self.append(encode_num(self.pop_as_number() - 1))
        return True

    def op_negate(self):
        if not self.is_arithmetic():
            return False
        self.append(encode_num(-self.pop_as_number()))
        return True

    def op_abs(self):
        if not self.is_arithmetic():
            return False
        self.append(encode_num(abs(self.pop_as_number())))
        return True

    def op_not(self):
        if not self.is_arithmetic():
            return False
        self.append(b'\1' if self.pop() == b'' else b'')
        return True

    def op_0notequal(self):
        if not self.is_arithmetic():
            return False
        self.append(b'' if self.pop() == b'' else b'\1')
        return True

    def op_add(self):
        if not self.is_arithmetic(2):
            return False
        self.append(encode_num(self.pop_as_number() + self.pop_as_number()))
        return True

    def op_sub(self):
        if not self.is_arithmetic(2):
            return False
        self.append(encode_num(self.pop_as_number() - self.pop_as_number()))
        return True

    def op_booland(self):
        if not self.is_arithmetic(2):
            return False
        a = self.pop()
        b = self.pop()
        if a != b'' and b != b'':
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_boolor(self):
        if not self.is_arithmetic(2):
            return False
        a = self.pop()
        b = self.pop()
        if a != b'' or b != b'':
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_numequal(self):
        if not self.is_arithmetic(2):
            return False
        if self.pop() == self.pop():
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_numequalverify(self):
        self.op_numequal()
        return self.op_verify()

    def op_numnotequal(self):
        if not self.is_arithmetic(2):
            return False
        if self.pop() != self.pop():
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_numlessthan(self):
        if not self.is_arithmetic(2):
            return False
        if self.pop_as_number() < self.pop_as_number():
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_numgreaterthan(self):
        if not self.is_arithmetic(2):
            return False
        if self.pop_as_number() > self.pop_as_number():
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_numlessthanorequal(self):
        if not self.is_arithmetic(2):
            return False
        if self.pop_as_number() <= self.pop_as_number():
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_numgreaterthanorequal(self):
        if not self.is_arithmetic(2):
            return False
        if self.pop_as_number() >= self.pop_as_number():
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_min(self):
        if not self.is_arithmetic(2):
            return False
        a = self.pop_as_number()
        b = self.pop_as_number()
        self.append(encode_num(a) if a < b else encode_num(b))
        return True

    def op_max(self):
        if not self.is_arithmetic(2):
            return False
        a = self.pop_as_number()
        b = self.pop_as_number()
        self.append(encode_num(a) if a > b else encode_num(b))
        return True

    def op_within(self):
        if not self.is_arithmetic(3):
            return False
        x = self.pop_as_number()
        vmin = self.pop_as_number()
        vmax = self.pop_as_number()
        if vmin <= x < vmax:
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_ripemd160(self):
        self.append(hashlib.new('ripemd160', self.pop()).digest())
        return True

    def op_sha1(self):
        self.append(hashlib.sha1(self.pop()).digest())
        return True

    def op_sha256(self):
        self.append(hashlib.sha256(self.pop()).digest())
        return True

    def op_hash160(self):
        self.append(hash160(self.pop()))
        return True

    def op_hash256(self):
        self.op_sha256()
        self.op_sha256()
        return True

    # # 'op_codeseparator':

    def op_checksig(self, txid):
        signature = self.pop()
        public_key = self.pop()
        signature = Signature.from_str(signature, public_key=public_key)
        if signature.verify(txid, public_key):
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_checksigverify(self, txid):
        self.op_checksig(txid)
        return self.op_verify()

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