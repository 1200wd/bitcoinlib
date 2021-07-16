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

from io import BytesIO
from bitcoinlib.encoding import *
from bitcoinlib.main import *
from bitcoinlib.config.opcodes import *
from bitcoinlib.keys import Signature, Key


_logger = logging.getLogger(__name__)


SCRIPT_TYPES = {
    # <name>: (<type>, <script_commands>, <data-lengths>)
    'p2pkh': ('locking', [op.op_dup, op.op_hash160, 'data', op.op_equalverify, op.op_checksig], [20]),
    'p2pkh_drop': ('locking', ['data', op.op_drop, op.op_dup, op.op_hash160, 'data', op.op_equalverify, op.op_checksig],
                   [32, 20]),
    'p2sh': ('locking', [op.op_hash160, 'data', op.op_equal], [20]),
    'p2wpkh': ('locking', [op.op_0, 'data'], [20]),
    'p2wsh': ('locking', [op.op_0, 'data'], [32]),
    'multisig': ('locking', ['op_n', 'key', 'op_n', op.op_checkmultisig], []),
    'p2pk': ('locking', ['key', op.op_checksig], []),
    'nulldata': ('locking', [op.op_return, 'data'], [0]),
    'nulldata_1': ('locking', [op.op_return, op.op_0], []),
    'nulldata_2': ('locking', [op.op_return], []),
    'sig_pubkey': ('unlocking', ['signature', 'key'], []),
    # 'p2sh_multisig': ('unlocking', [op.op_0, 'signature', 'op_n', 'key', 'op_n', op.op_checkmultisig], []),
    'p2sh_multisig': ('unlocking', [op.op_0, 'signature', 'redeemscript'], []),
    'p2sh_multisig_2?': ('unlocking', [op.op_0, 'signature', op.op_verify, 'redeemscript'], []),
    'p2sh_multisig_3?': ('unlocking', [op.op_0, 'signature', op.op_1add, 'redeemscript'], []),
    'p2sh_p2wpkh': ('unlocking', [op.op_0, op.op_hash160, 'redeemscript', op.op_equal], []),
    'p2sh_p2wsh': ('unlocking', [op.op_0, 'redeemscript'], []),
    'signature': ('unlocking', ['signature'], []),
    'signature_multisig': ('unlocking', [op.op_0, 'signature'], []),
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


def _get_script_types(blueprint):
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
        script_type = matches[match_id][0]
        if script_type == 'multisig' and script_types[-1:] == ['signature_multisig']:
            script_types.pop()
            script_type = 'p2sh_multisig'
        script_types.append(script_type)
        bp = bp[matches[match_id][1]:]

    return script_types


def data_pack(data):
    """
    Add data length prefix to data string to include data in a script

    :param data: Data to be packed
    :type data: bytes

    :return bytes:
    """
    if len(data) <= 75:
        return len(data).to_bytes(1, 'big') + data
    elif 75 < len(data) <= 255:
        return b'L' + len(data).to_bytes(1, 'little') + data
    else:
        return b'M' + len(data).to_bytes(2, 'little') + data


def get_data_type(data):
    """
    Get type of data in script. Recognises signatures, keys, hashes or sequence data. Return 'other' if data is not
    recognised.

    :param data: Data part of script
    :type data: bytes

    :return str:
    """
    if isinstance(data, Key):
        return 'key_object'
    elif isinstance(data, Signature):
        return 'signature_object'
    elif data.startswith(b'\x30') and 69 <= len(data) <= 74:
        return 'signature'
    elif ((data.startswith(b'\x02') or data.startswith(b'\x03')) and len(data) == 33) or \
            (data.startswith(b'\x04') and len(data) == 65):
        return 'key'
    elif len(data) == 20 or len(data) == 32 or 1 < len(data) <= 4:
        return 'data-%d' % len(data)
    else:
        return 'other'


class Script(object):

    def __init__(self, commands=None, message=None, script_types='', is_locking=True, keys=None, signatures=None,
                 blueprint=None, tx_data=None, public_hash=b'', sigs_required=None, redeemscript=b'',
                 hash_type=SIGHASH_ALL):
        """
        Create a Script object with specified parameters. Use parse() method to create a Script from raw hex

        :param commands:
        :type commands: list
        :param message:
        :param script_types:
        :param is_locking:
        :param keys:
        :type keys: list of Key
        :param signatures:
        :type signatures: list of Signature
        :param blueprint:
        :param tx_data:
        """
        self.commands = commands if commands else []
        self.raw = b''
        self.stack = []
        self.message = message
        self.script_types = script_types if script_types else []
        self.is_locking = is_locking
        self.keys = keys if keys else []
        self.signatures = signatures if signatures else []
        self._blueprint = blueprint if blueprint else []
        self.tx_data = tx_data
        self.sigs_required = sigs_required if sigs_required else len(self.keys) if len(self.keys) else 1
        self.redeemscript = redeemscript
        self.public_hash = public_hash
        self.hash_type = hash_type

        if not self.commands and self.script_types and (self.keys or self.signatures or self.public_hash):
            for st in self.script_types:
                st_values = SCRIPT_TYPES[st]
                script_template = st_values[1]
                self.is_locking = True if st_values[0] == 'locking' else False
                sig_n_and_m = [len(self.keys), self.sigs_required]
                for tc in script_template:
                    command = [tc]
                    if tc == 'data':
                        command = [self.public_hash] if self.public_hash else []
                    elif tc == 'signature':
                        command = self.signatures
                    elif tc == 'key':
                        command = self.keys
                    elif tc == 'op_n':
                        command = [sig_n_and_m.pop() + 80]
                    elif tc == 'redeemscript':
                        command = [self.redeemscript]
                    if not command or command == [b'']:
                        raise ScriptError("Cannot create script, please supply %s" % (tc if tc != 'data' else
                                          'public key hash'))
                    self.commands += command
        if not (self.keys and self.signatures and self.blueprint):
            self._blueprint = []
            for c in self.commands:
                if isinstance(c, int):
                    self._blueprint.append(c)
                else:
                    data_type = get_data_type(c)
                    if data_type in ['key', 'signature', 'key_object', 'signature_object']:
                        if data_type == 'key_object':
                            data_type = 'key'
                        elif data_type == 'signature_object':
                            data_type = 'signature'
                        self._blueprint.append(data_type)
                    else:
                        self._blueprint.append('data-%d' % len(c))

    @classmethod
    def parse(cls, script, message=None, tx_data=None, strict=True, _level=0):
        """
        Parse raw script and return Script object. Extracts script commands, keys, signatures and other data.

        Wrapper for the :func:`parse_bytesio` method. Convert hexadecimal string or bytes script to BytesIO.

        :param script: Raw script to parse in bytes, BytesIO or hexadecimal string format
        :type script: BytesIO, bytes, str
        :param message: Signed mesage to verify, normally a transaction hash
        :type message: bytes
        :param tx_data: Dictionary with extra information needed to verify script. Such as 'redeemscript' for
        multisignature scripts and 'blockcount' for time locked scripts
        :type tx_data: dict
        :param strict: Raise exception when script is malformed, incomplete or not understood. Default is True
        :type strict: bool
        :param _level: Internal argument used to avoid recursive depth
        :type _level: int

        :return Script:
        """
        if isinstance(script, bytes):
            script = BytesIO(script)
        elif isinstance(script, str):
            script = BytesIO(bytes.fromhex(script))
        return cls.parse_bytesio(script, message, tx_data, strict, _level)

    @classmethod
    def parse_bytesio(cls, script, message=None, tx_data=None, strict=True, _level=0):
        """
        Parse raw script and return Script object. Extracts script commands, keys, signatures and other data.

        :param script: Raw script to parse in bytes, BytesIO or hexadecimal string format
        :type script: BytesIO
        :param message: Signed mesage to verify, normally a transaction hash
        :type message: bytes
        :param tx_data: Dictionary with extra information needed to verify script. Such as 'redeemscript' for
        multisignature scripts and 'blockcount' for time locked scripts
        :type tx_data: dict
        :param strict: Raise exception when script is malformed, incomplete or not understood. Default is True
        :type strict: bool
        :param _level: Internal argument used to avoid recursive depth
        :type _level: int

        :return Script:
        """
        commands = []
        signatures = []
        keys = []
        blueprint = []
        redeemscript = b''
        sigs_required = None
        # hash_type = SIGHASH_ALL  # todo: check
        hash_type = None

        while script:
            chb = script.read(1)
            if not chb:
                break
            ch = int.from_bytes(chb, 'big')
            data = None
            data_length = 0
            if 1 <= ch <= 75:  # Data`
                data_length = ch
            elif ch == op.op_pushdata1:
                data_length = int.from_bytes(script.read(1), 'big')
            elif ch == op.op_pushdata2:
                data_length = int.from_bytes(script.read(2), 'little')
            if data_length:
                data = script.read(data_length)
                if len(data) != data_length:
                    msg = "Malformed script, not enough data found"
                    if strict:
                        raise ScriptError(msg)
                    else:
                        _logger.warning(msg)

            if data:
                data_type = get_data_type(data)
                commands.append(data)
                if data_type == 'signature':
                    sig = Signature.from_str(data)
                    signatures.append(sig)
                    hash_type = sig.hash_type
                    blueprint.append('signature')
                elif data_type == 'signature_object':
                    signatures.append(data)
                    hash_type = data.hash_type
                    blueprint.append('signature')
                elif data_type == 'key':
                    keys.append(Key(data))
                    blueprint.append('key')
                elif data_type == 'key_object':
                    keys.append(data)
                    blueprint.append('key')
                elif data_type[:4] == 'data':
                    # FIXME: This is arbitrary
                    blueprint.append('data-%d' % len(data))
                elif len(commands) >= 2 and commands[-2] == op.op_return:
                    blueprint.append('data-%d' % len(data))
                else:
                    # FIXME: Only parse sub-scripts if script is expected
                    try:
                        if _level >= 1:
                            blueprint.append('data-%d' % len(data))
                        else:
                            s2 = Script.parse_bytes(data, _level=_level+1)
                            commands.pop()
                            commands += s2.commands
                            blueprint += s2.blueprint
                            keys += s2.keys
                            signatures += s2.signatures
                            redeemscript = s2.redeemscript
                            sigs_required = s2.sigs_required
                    except (ScriptError, IndexError):
                        blueprint.append('data-%d' % len(data))
            else:  # Other opcode
                commands.append(ch)
                blueprint.append(ch)

        s = cls(commands, message, keys=keys, signatures=signatures, blueprint=blueprint, tx_data=tx_data,
                hash_type=hash_type)
        script.seek(0)
        s.raw = script.read()

        s.script_types = _get_script_types(blueprint)

        # Extract extra information from script data
        for st in s.script_types[:1]:
            if st == 'multisig':
                s.redeemscript = s.raw
                s.sigs_required = s.commands[0] - 80
                if s.sigs_required > len(keys):
                    raise ScriptError("Number of signatures required (%d) is higher then number of keys (%d)" %
                                      (s.sigs_required, len(keys)))
                if len(s.keys) != s.commands[-2] - 80:
                    raise ScriptError("%d keys found but %d keys expected" %
                                      (len(s.keys), s.commands[-2] - 80))
            elif st in ['p2wpkh', 'p2wsh', 'p2sh'] and len(s.commands) > 1:
                s.public_hash = s.commands[1]
            elif st == 'p2pkh' and len(s.commands) > 2:
                s.public_hash = s.commands[2]
        s.redeemscript = redeemscript if redeemscript else s.redeemscript
        s.sigs_required = sigs_required if sigs_required else s.sigs_required

        return s

    @classmethod
    def parse_hex(cls, script, message=None, tx_data=None, strict=True, _level=0):
        """
        Parse raw script and return Script object. Extracts script commands, keys, signatures and other data.

        Wrapper for the :func:`parse_bytesio` method. Convert hexadecimal string script to BytesIO.

        :param script: Raw script to parse in hexadecimal string format
        :type script: str
        :param message: Signed mesage to verify, normally a transaction hash
        :type message: bytes
        :param tx_data: Dictionary with extra information needed to verify script. Such as 'redeemscript' for
        multisignature scripts and 'blockcount' for time locked scripts
        :type tx_data: dict
        :param strict: Raise exception when script is malformed, incomplete or not understood. Default is True
        :type strict: bool
        :param _level: Internal argument used to avoid recursive depth
        :type _level: int

        :return Script:
        """
        return cls.parse_bytesio(BytesIO(bytes.fromhex(script)), message, tx_data, strict, _level)

    @classmethod
    def parse_bytes(cls, script, message=None, tx_data=None, strict=True, _level=0):
        """
        Parse raw script and return Script object. Extracts script commands, keys, signatures and other data.

        Wrapper for the :func:`parse_bytesio` method. Convert bytes script to BytesIO.

        :param script: Raw script to parse in bytes format
        :type script: bytes
        :param message: Signed mesage to verify, normally a transaction hash
        :type message: bytes
        :param tx_data: Dictionary with extra information needed to verify script. Such as 'redeemscript' for
        multisignature scripts and 'blockcount' for time locked scripts
        :type tx_data: dict
        :param strict: Raise exception when script is malformed or incomplete
        :type strict: bool
        :param _level: Internal argument used to avoid recursive depth
        :type _level: int

        :return Script:
        """
        return cls.parse_bytesio(BytesIO(script), message, tx_data, strict, _level)

    def __str__(self):
        s_items = []
        for command in self.blueprint:
            if isinstance(command, int):
                s_items.append(opcodenames.get(command, 'unknown-op-%s' % command))
            else:
                s_items.append(command)
        return ' '.join(s_items)

    def __add__(self, other):
        self.commands += other.commands
        self.raw += other.raw
        if other.message and not self.message:
            self.message = other.message
        self.is_locking = None
        self.keys += other.keys
        self.signatures += other.signatures
        self._blueprint += other._blueprint
        self.script_types = _get_script_types(self._blueprint)
        if other.tx_data and not self.tx_data:
            self.tx_data = other.tx_data
        return self

    def __bool__(self):
        return bool(self.commands)

    @property
    def blueprint(self):
        # TODO: create blueprint from commands if empty
        return self._blueprint

    def serialize(self):
        """
        Serialize script. Return all commands and data as bytes

        :return bytes:
        """
        raw = b''
        for cmd in self.commands:
            if isinstance(cmd, int):
                raw += bytes([cmd])
            else:
                raw += data_pack(cmd)
        self.raw = raw
        return raw

    def serialize_list(self):
        """
        Serialize script and return commands and data as list

        :return list of bytes:
        """
        clist = []
        for cmd in self.commands:
            if isinstance(cmd, int):
                clist.append(bytes([cmd]))
            else:
                clist.append(cmd)
        return clist

    def evaluate(self, message=None, tx_data=None):
        self.message = self.message if message is None else message
        self.tx_data = self.tx_data if tx_data is None else tx_data
        self.stack = Stack()

        commands = self.commands[:]
        while len(commands):
            command = commands.pop(0)
            if isinstance(command, int):
                if command == op.op_0:  # OP_0
                    self.stack.append(encode_num(0))
                elif command == op.op_1negate:  # OP_1NEGATE
                    self.stack.append(encode_num(-1))
                elif op.op_1 <= command <= op.op_16:   # OP_1 to OP_16
                    self.stack.append(encode_num(command-80))
                elif command == op.op_if or command == op.op_notif:
                    method = opcodenames[command].lower()
                    method = getattr(self.stack, method)
                    if not method(commands):
                        return False
                else:
                    method = opcodenames[command].lower()
                    if method not in dir(self.stack):
                        raise ScriptError("Method %s not found" % method)
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
            else:
                self.stack.append(command)

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

    # def op_ver()  # unused

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
        return True

    def op_notif(self, commands):
        element = self.pop()
        if decode_num(element) == 0:
            self.append(b'\1')
        else:
            self.append(b'\0')
        return self.op_if(commands)

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

    # # 'op_reserved1': unused
    # # 'op_reserved2': unused

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

    # 'op_codeseparator':  not implemented, mostly unused

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
        return self.op_checksig(message, None) and self.op_verify()

    def op_checkmultisig(self, message, data=None):
        n = decode_num(self.pop())
        pubkeys = []
        for _ in range(n):
            pubkeys.append(self.pop())
        m = decode_num(self.pop())
        signatures = []
        for _ in range(m):
            signatures.append(self.pop())
        if len(self):
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

    def op_checkmultisigverify(self, message, data=None):
        return self.op_checkmultisig(message, data) and  self.op_verify()

    def op_nop1(self):
        return True

    def op_checklocktimeverify(self, _, data):
        if not data or 'sequence' not in data:
            _logger.warning("Missing 'sequence' value in Script data parameter for operation check lock time verify.")
        if data and data['sequence'] == 0xffffffff:
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

    def op_nop4(self):
        return True

    def op_nop5(self):
        return True

    def op_nop6(self):
        return True

    def op_nop7(self):
        return True

    def op_nop8(self):
        return True

    def op_nop9(self):
        return True

    def op_nop10(self):
        return True

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