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
        stack = []
        commands = self.commands[:]
        while len(commands):
            command = commands.pop(0)
            if isinstance(command, int):
                if command == 0 or command == 79 or 81 <= command <= 96:   # OP_0 to OP_16 and OP_1NEGATE (-1)
                    stack.append(command)
                print("Running operation %s" % opcodenames[command])
            else:
                print("Add data %s to stack" % command.hex())
                stack.append(command)

    def __str__(self):
        s_items = []
        for command in self.commands:
            if isinstance(command, int):
                s_items.append(opcodenames[command])
            else:
                s_items.append(command.hex())
        return ' '.join(s_items)




