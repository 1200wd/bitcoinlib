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
from typing import Any, Union

from bitcoinlib.encoding import *
from bitcoinlib.main import *
from bitcoinlib.config.opcodes import *
from bitcoinlib.keys import Signature


_logger = logging.getLogger(__name__)


# SCRIPT_TYPES_LOCKING = {
#     # Locking scripts / scriptPubKey (Output)
#     'p2pkh': ['OP_DUP', 'OP_HASH160', 'hash-20', 'OP_EQUALVERIFY', 'OP_CHECKSIG'],
#     'p2sh': ['OP_HASH160', 'hash-20', 'OP_EQUAL'],
#     'p2wpkh': ['OP_0', 'hash-20'],
#     'p2wsh': ['OP_0', 'hash-32'],
#     'multisig': ['op_m', 'multisig', 'op_n', 'OP_CHECKMULTISIG'],
#     'p2pk': ['public_key', 'OP_CHECKSIG'],
#     'nulldata': ['OP_RETURN', 'return_data'],
# }
#
# SCRIPT_TYPES_UNLOCKING = {
#     # Unlocking scripts / scriptSig (Input)
#     'sig_pubkey': ['signature', 'SIGHASH_ALL', 'public_key'],
#     'p2sh_multisig': ['OP_0', 'multisig', 'redeemscript'],
#     'p2sh_p2wpkh': ['OP_0', 'OP_HASH160', 'redeemscript', 'OP_EQUAL'],
#     'p2sh_p2wsh': ['OP_0', 'push_size', 'redeemscript'],
#     'locktime_cltv': ['locktime_cltv', 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP'],
#     'locktime_csv': ['locktime_csv', 'OP_CHECKSEQUENCEVERIFY', 'OP_DROP'],
#     'signature': ['signature']
# }
SCRIPT_TYPES = {
    # <name>: (<type>, <script_commands>, <data-lengths>)
    'p2pkh': ('locking', [op.op_dup, op.op_hash160, 'data', op.op_equalverify, op.op_checksig], [20]),
    'p2pkh_drop': ('locking', ['data', op.op_drop, op.op_dup, op.op_hash160, 'data', op.op_equalverify, op.op_checksig], [32, 20]),
    'p2sh': ('locking', [op.op_hash160, 'data', op.op_equal], [20]),
    'p2wpkh': ('locking', [op.op_0, 'data'], [20]),
    'p2wsh': ('locking', [op.op_0, 'data'], [32]),
    'multisig': ('locking', ['op_n', 'key', 'op_n', op.op_checkmultisig], []),
    'p2pk': ('locking', ['key', op.op_checksig], []),
    'nulldata': ('locking', [op.op_return, 'data'], [0]),
    'nulldata_2': ('locking', [op.op_return, op.op_0], []),
    'sig_pubkey': ('unlocking', ['signature', 'key'], []),
    'p2sh_multisig': ('unlocking', [op.op_0, 'signature', 'op_n', 'key', 'op_n', op.op_checkmultisig], []),  # Check with variant is standard
    'p2sh_multisig_2?': ('unlocking', [op.op_0, 'signature', op.op_verify, 'op_n', 'key', 'op_n', op.op_checkmultisig], []),  # Check with variant is standard
    'p2sh_multisig_3?': ('unlocking', [op.op_0, 'signature', op.op_1add, 'op_n', 'key', 'op_n', op.op_checkmultisig], []),  # Check with variant is standard
    'p2sh_p2wpkh': ('unlocking', [op.op_0, op.op_hash160, 'redeemscript', op.op_equal], []),
    'p2sh_p2wsh': ('unlocking', [op.op_0, 'redeemscript'], []),
    'signature': ('unlocking', ['signature'], []),
    'signature_multisig?': ('unlocking', [op.op_0, 'signature'], []),
    'locktime_cltv': ('unlocking', ['locktime_cltv', op.op_checklocktimeverify, op.op_drop], []),
    'locktime_csv': ('unlocking', ['locktime_csv', op.op_checksequenceverify, op.op_drop], []),
}


class ScriptError(Exception):
    """
    Handle Key class Exceptions

    """
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def _get_script_type(blueprint):
    # Convert blueprint to more generic format
    bp = []
    for item in blueprint:
        if isinstance(item, str) and item[:4] == 'data':
            bp.append('data')
        elif isinstance(item, int) and op.op_1 <= item <= op.op_16:
            bp.append('op_n')
        elif item == 'key' and len(bp) and bp[-1] == 'key':
            bp[-1] = 'key'
        elif item == 'signature' and len(bp) and bp[-1] == 'signature':
            bp[-1] = 'signature'
        else:
            bp.append(item)
    bp_len = [int(c.split('-')[1]) for c in blueprint if isinstance(c, str) and c[:4] == 'data']

    script_types = []
    while len(bp):
        # Find all possible matches with blueprint
        matches = [(key, len(values[1]), values[2]) for key, values in SCRIPT_TYPES.items() if
                   values[1] == bp[:len(values[1])]]
        if not matches:
            script_types.append('unknown')
            break

        # Select match with correct data length if more then 1 match is found
        match_id = 0
        for match in matches:
            data_lens = match[2]
            for i, data_len in enumerate(data_lens):
                bl = bp_len[i]
                if data_len == bl or data_len == 0:
                    match_id = matches.index(match)
                    break

        # Add script type to list
        script_types.append(matches[match_id][0])
        bp = bp[matches[match_id][1]:]

    return script_types


def data_pack(data):
    if len(data) <= 75:
        return len(data).to_bytes(1, 'big') + data
    elif 75 < len(data) <= 255:
        return b'L' + len(data).to_bytes(1, 'little') + data
    else:
        return b'M' + len(data).to_bytes(2, 'little') + data


class Script(object):

    def __init__(self, commands=None, message=None, script_type='', is_locking=True, keys=None, signatures=None,
                 blueprint=None, tx_data=None):
        self.commands = commands if commands else []
        self.raw = b''
        self.stack = []
        self.message = message
        self.script_type = script_type
        self.is_locking = is_locking
        self.keys = keys if keys else []
        self.signatures = signatures if signatures else []
        self._blueprint = blueprint if blueprint else []
        self.tx_data = tx_data

    @classmethod
    def parse(cls, script, message=None, tx_data=None, _level=0):
        cur = 0
        commands = []
        signatures = []
        keys = []
        blueprint = []
        while cur < len(script):
            ch = script[cur]
            cur += 1
            data = None
            if 1 <= ch <= 75:  # Data
                data = script[cur:cur+ch]
                cur += ch
            elif ch == op.op_pushdata1:
                length = script[cur]
                cur += 1
                data = script[cur:cur+length]
                cur += length
            elif ch == op.op_pushdata2:
                length = int.from_bytes(script[cur:cur+2], 'little')
                cur += 2
                data = script[cur:cur+length]
                cur += length
            if data:
                # commands.append(data)
                if data.startswith(b'\x30') and 69 <= len(data) <= 74:
                    commands.append(data)
                    signatures.append(data)
                    blueprint.append('signature')
                elif ((data.startswith(b'\x02') or data.startswith(b'\x03')) and len(data) == 33) or \
                        (data.startswith(b'\x04') and len(data) == 65):
                    commands.append(data)
                    keys.append(data)
                    blueprint.append('key')
                elif len(data) == 20 or len(data) == 32 or (commands and commands[-1] == op.op_return) or \
                        1 < len(data) <= 4:
                    commands.append(data)
                    blueprint.append('data-%d' % len(data))
                else:
                    # FIXME: Only parse sub-scripts if script is expected
                    try:
                        if _level >= 1:
                            commands.append(data)
                            blueprint.append('data-%d' % len(data))
                        else:
                            s2 = Script.parse(data, _level=_level+1)
                            commands.extend(s2.commands)
                            blueprint.extend(s2.blueprint)
                    except (ScriptError, IndexError):
                        commands.append(data)
                        blueprint.append('data-%d' % len(data))
            else:  # Other opcode
                commands.append(ch)
                blueprint.append(ch)
        if cur != len(script):
            msg = "Parsing script failed, invalid length"
            if _level == 1:
                raise ScriptError(msg)
            else:
                _logger.warning(msg)
        s = cls(commands, message, keys=keys, signatures=signatures, blueprint=blueprint, tx_data=tx_data)
        s.raw = script
        s.script_type = _get_script_type(blueprint)
        # s.is_locking = True if locking_type == 'locking' else False
        return s

    def __str__(self):
        s_items = []
        for command in self.blueprint:
            if isinstance(command, int):
                s_items.append(opcodenames.get(command, 'unknown-op-%s' % command))
            else:
                s_items.append(command)
        return ' '.join(s_items)

    @property
    def blueprint(self):
        # TODO: create blueprint from commands if empty
        return self._blueprint

    def serialize(self):
        raw = b''
        for cmd in self.commands:
            if isinstance(cmd, int):
                raw += bytes([cmd])
            else:
                raw += data_pack(cmd)
        self.raw = raw
        return raw

    def evaluate(self, message=None, tx_data=None):
        self.message = self.message if message is None else message
        self.tx_data = self.tx_data if tx_data is None else tx_data
        self.stack = Stack()
        commands = self.commands[:]
        while len(commands):
            command = commands.pop(0)
            if isinstance(command, int):
                # print("Stack: %s  ; Running operation %s" % (self.stack, opcodenames[command]))
                if command == op.op_0:  # OP_0
                    self.stack.append(encode_num(0))
                    # self.stack.append(0)
                elif command == op.op_1negate:  # OP_1NEGATE
                    # self.stack.append(b'\x81')
                    self.stack.append(encode_num(-1))
                    # self.stack.append(-1)
                elif op.op_1 <= command <= op.op_16:   # OP_1 to OP_16
                    # self.stack.append(bytes([command-80]))
                    self.stack.append(encode_num(command-80))
                    # self.stack.append(command-80)
                elif command == op.op_if or command == op.op_notif:
                    method = opcodenames[command].lower()
                    method = getattr(self.stack, method)
                    if not method(commands):
                        return False
                else:
                    method = opcodenames[command].lower()
                    if method not in dir(self.stack):
                        raise ScriptError("Method %s not found" % method)
                    # method_args = op_methods[method]
                    # self.stack.operate(*method_args)
                    try:
                        method = getattr(self.stack, method)
                        if method.__code__.co_argcount > 1:
                            res = method(self.message, self.tx_data)
                        else:
                            res = method()
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
                # print("Add data %s to stack" % command.hex())
                self.stack.append(command)
            # print(self.stack)
        if len(self.stack) == 0:
            return False
        if self.stack.pop() == b'':
            return False
        return True


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

    # def op_ver()  # nodig?

    def op_if(self, commands):
        true_items = []
        false_items = []
        current_array = true_items
        found = False
        num_endifs_needed = 1
        while len(commands) > 0:
            item = commands.pop(0)
            if item in (99, 100):
                # nested if, we have to go another endif
                num_endifs_needed += 1
                current_array.append(item)
            elif num_endifs_needed == 1 and item == 103:
                current_array = false_items
            elif item == 104:
                if num_endifs_needed == 1:
                    found = True
                    break
                else:
                    num_endifs_needed -= 1
                    current_array.append(item)
            else:
                current_array.append(item)
        if not found:
            return False
        element = self.pop()
        if decode_num(element) == 0:
            commands[:0] = false_items
        else:
            commands[:0] = true_items
        return True    #  "OP_NOTIF", "OP_VERIF", "OP_VERNOTIF", "OP_ELSE", "OP_ENDIF"

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

    def op_checksig(self, message, _=None):
        public_key = self.pop()
        signature = self.pop()
        signature = Signature.from_str(signature, public_key=public_key)
        if signature.verify(message, public_key):
            self.append(b'\1')
        else:
            self.append(b'')
        return True

    def op_checksigverify(self, message, _=None):
        self.op_checksig(message, None)
        return self.op_verify()

    def op_checkmultisig(self, message, data=None):
        n = decode_num(self.pop())
        pubkeys = []
        for _ in range(n):
            pubkeys.append(self.pop())
        m = decode_num(self.pop())
        signatures = []
        for _ in range(m):
            signatures.append(self.pop())
        # OP_CHECKMULTISIG bug
        self.pop()
        sigcount = 0
        for pubkey in pubkeys:
            s = Signature.from_str(signatures[sigcount])
            if s.verify(message, pubkey):
                sigcount += 1
                if sigcount >= len(signatures):
                    break

        if sigcount == len(signatures):
            if data and 'redeemscript' in data:
                self.append(data['redeemscript'])
            else:
                self.append(b'\1')
        else:
            self.append(b'')
        return True

    # # 'op_checkmultisig':
    # # 'op_checkmultisigverify':
    # 'op_nop1': (0, '', None, 0, False),
    def op_checklocktimeverify(self, _, data):
        if 'sequence' not in data:
            _logger.warning("Missing 'sequence' value in Script data parameter for operation check lock time verify.")
        if data['sequence'] == 0xffffffff:
            return False

        locktime = int.from_bytes(self[-1], 'little')
        if locktime < 0:
            return False

        if locktime > 50000000:
            if int(datetime.now().timestamp()) < locktime:
                return False
        else:
            if 'blockcount' not in data:
                _logger.warning(
                    "Missing 'blockcount' value in Script data parameter for operation check lock time verify.")
                return False
            if data['blockcount'] < locktime:
                return False
        return True

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