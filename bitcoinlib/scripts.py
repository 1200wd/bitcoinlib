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
            elif ch == op.op_pushdata1:  # OP_PUSHDATA1
                length = script[cur]
                cur += 1
                commands.append(script[cur:cur+length])
                cur += length
            elif ch == 77:   # OP_PUSHDATA2
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
        self.stack = []
        commands = self.commands[:]
        while len(commands):
            command = commands.pop(0)
            if isinstance(command, int):
                print("Running operation %s" % opcodenames[command])
                if command == op.op_0:  # OP_0
                    self.stack.append(encode_num(0))
                elif command == op.op_1negate:  # OP_1NEGATE
                    # self.stack.append(b'\x81')
                    self.stack.append(encode_num(-1))
                elif 81 <= command <= 96:   # OP_1 to OP_16
                    # self.stack.append(bytes([command-80]))
                    self.stack.append(encode_num(command-80))
                else:
                    method = eval(opcodenames[command].lower())
                    if not method(self.stack):
                        return False
            else:
                print("Add data %s to stack" % command.hex())
                self.stack.append(command)
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

    def operate(self, operations, pop=0):
        elements = []
        for _ in range(pop):
            elements.append(self.pop())
        for op in operations:
            self.append(getattr(elements[0], op)(elements[1]))


def op_nop(stack):
    return True

# def op_ver(stack):
# def op_if(stack):
#  "OP_NOTIF", "OP_VERIF", "OP_VERNOTIF", "OP_ELSE", "OP_ENDIF"


def op_verify(stack):
    if len(stack) < 1:
        return False
    return False if stack.pop() == b'' else True


def op_return(stack):
    return False

# "OP_TOALTSTACK", "OP_FROMALTSTACK", "OP_2DROP", "OP_2DUP", "OP_3DUP", "OP_2OVER",
# "OP_2ROT", "OP_2SWAP", "OP_IFDUP", "OP_DEPTH", "OP_DROP",


def op_dup(stack):
    if not stack:
        return False
    item = stack[0]
    stack.append(item)
    return True

#  "OP_NIP", "OP_OVER", "OP_PICK", "OP_ROLL",
# "OP_ROT", "OP_SWAP", "OP_TUCK", "OP_CAT", "OP_SUBSTR", "OP_LEFT", "OP_RIGHT", "OP_SIZE", "OP_INVERT", "OP_AND",
# "OP_OR", "OP_XOR", "OP_EQUAL", "OP_EQUALVERIFY", "OP_RESERVED1", "OP_RESERVED2", "OP_1ADD", "OP_1SUB", "OP_2MUL",
# "OP_2DIV", "OP_NEGATE", "OP_ABS", "OP_NOT", "OP_0NOTEQUAL",


def op_add(stack):
    if len(stack) < 2:
        return False
    a = decode_num(stack.pop())
    b = decode_num(stack.pop())
    stack.append(encode_num(a + b))
    return True


def op_sub(stack):
    if len(stack) < 2:
        return False
    a = decode_num(stack.pop())
    b = decode_num(stack.pop())
    stack.append(encode_num(a - b))
    return True


def op_mul(stack):
    if len(stack) < 2:
        return False
    a = decode_num(stack.pop())
    b = decode_num(stack.pop())
    stack.append(encode_num(a * b))
    return True

# "OP_DIV", "OP_MOD",
# "OP_LSHIFT", "OP_RSHIFT", "OP_BOOLAND", "OP_BOOLOR", "OP_NUMEQUAL", "OP_NUMEQUALVERIFY", "OP_NUMNOTEQUAL",
# "OP_LESSTHAN", "OP_GREATERTHAN", "OP_LESSTHANOREQUAL", "OP_GREATERTHANOREQUAL", "OP_MIN", "OP_MAX", "OP_WITHIN",
# "OP_RIPEMD160", "OP_SHA1", "OP_SHA256", "OP_HASH160", "OP_HASH256", "OP_CODESEPARATOR", "OP_CHECKSIG",
# "OP_CHECKSIGVERIFY", "OP_CHECKMULTISIG", "OP_CHECKMULTISIGVERIFY", "OP_NOP1", "OP_CHECKLOCKTIMEVERIFY",
# "OP_CHECKSEQUENCEVERIFY", "OP_NOP4", "OP_NOP5", "OP_NOP6", "OP_NOP7", "OP_NOP8", "OP_NOP9", "OP_NOP10",


def op_equal(stack):
    if len(stack) < 2:
        return False
    a = decode_num(stack.pop())
    b = decode_num(stack.pop())
    stack.append(b'\x01' if a == b else b'')
    return True


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