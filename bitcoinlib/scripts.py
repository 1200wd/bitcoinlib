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
            elif ch == 76:  # OP_PUSHDATA1
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
                if command == 0:  # OP_0
                    self.stack.append(b'')
                elif command == 79:  # OP_1NEGATE
                    self.stack.append(b'\x81')
                elif 81 <= command <= 96:   # OP_1 to OP_16
                    self.stack.append((command-80).to_bytes(1, 'little'))
                else:
                    method = eval(opcodenames[command].lower())
                    if not method(self.stack):
                        return False
            else:
                print("Add data %s to stack" % command.hex())
                self.stack.append(command)
        return self.stack

    def __str__(self):
        s_items = []
        for command in self.commands:
            if isinstance(command, int):
                s_items.append(opcodenames[command])
            else:
                s_items.append(command.hex())
        return ' '.join(s_items)


def op_add(stack):
    if len(stack) < 2:
        return False
    a = int.from_bytes(stack.pop(), 'little')
    b = int.from_bytes(stack.pop(), 'little')
    res = a + b
    stack.append(res)
    print(stack)
    return True


# def encode_num(num):
#     if num == 0:
#         return b''
#     abs_num = abs(num)
#     negative = num < 0
#     result = bytearray()
#     while abs_num:
#         result.append(abs_num & 0xff)
#         abs_num >>= 8
#     if result[-1] & 0x80:
#         if negative:
#             result.append(0x80)
#         else:
#             result.append(0)
#     elif negative:
#         result[-1] |= 0x80
#     return bytes(result)
#
#
# def decode_num(element):
#     if element == b'':
#         return 0
#     big_endian = element[::-1]
#     if big_endian[0] & 0x80:
#         negative = True
#         result = big_endian[0] & 0x7f
#     else:
#         negative = False
#         result = big_endian[0]
#     for c in big_endian[1:]:
#         result <<= 8
#         result += c
#     if negative:
#         return -result
#     else:
#         return result