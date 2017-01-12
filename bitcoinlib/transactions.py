# -*- coding: utf-8 -*-
#
#    bitcoinlib Transactions
#    © 2016 December - 1200 Web Development <http://1200wd.com/>
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

from bitcoinlib.encoding import change_base
from bitcoinlib.db import *
from bitcoinlib.keys import HDKey
from bitcoinlib.config import networks
from bitcoinlib.services.services import Service

_logger = logging.getLogger(__name__)


class TransactionError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def varbyteint_to_int(byteint):
    if not byteint:
        print(byteint)
    ni = byteint[0]
    if ni < 253:
        return ni, 1
    if ni == 253:  # integer of 2 bytes
        size = 2
    elif ni == 254:  # integer of 4 bytes
        size = 4
    else:  # integer of 8 bytes
        size = 8
    return change_base(byteint[1:1+size], 256, 10), size


class Transaction:

    @staticmethod
    def import_raw(rawtx):
        if isinstance(rawtx, str):
            rawtx = change_base(rawtx, 16, 256)
        elif not isinstance(rawtx, bytes):
            raise TransactionError("Raw Transaction must be of type bytes or str")

        version = rawtx[0:4][::-1]
        n_inputs, size = varbyteint_to_int(rawtx[4:13])
        cursor = 4 + size
        inputs = []
        for i in range(0, n_inputs):
            inp_hash = rawtx[cursor:cursor+32][::-1]
            if not len(inp_hash):
                raise TransactionError("Input transaction hash not found. Probably malformed raw transaction")
            inp_index = rawtx[cursor+32:cursor+36][::-1]
            cursor += 36

            scriptsig_size, size = varbyteint_to_int(rawtx[cursor:cursor+9])
            cursor += size
            scriptsig = rawtx[cursor:cursor+scriptsig_size]
            cursor += scriptsig_size
            sequence_number = change_base(rawtx[cursor:cursor + 4], 256, 16)
            cursor += 4
            inputs.append({
                'prev_hash': change_base(inp_hash, 256, 16),
                'output_index': change_base(inp_index, 256, 10),
                'script_sig': change_base(scriptsig, 256, 16),
                'sequence_number': sequence_number,
            })
        if len(inputs) != n_inputs:
            raise TransactionError("Error parsing inputs. Number of tx specified %d but %d found" % (n_inputs, len(inputs)))

        outputs = []
        n_outputs, size = varbyteint_to_int(rawtx[cursor:cursor+9])
        cursor += size
        for o in range(0, n_outputs):
            amount = change_base(rawtx[cursor:cursor+8][::-1], 256, 10)
            cursor += 8
            script_size, size = varbyteint_to_int(rawtx[cursor:cursor+9])
            cursor += size
            script = rawtx[cursor:cursor+script_size]
            cursor += script_size
            outputs.append({
                'amount': amount,
                'script': change_base(script, 256, 16),
            })

        locktime = change_base(rawtx[cursor:cursor+4][::-1], 256, 10)

        return Transaction(inputs, outputs, locktime, version)

    def __init__(self, inputs, outputs, locktime=0, version=b'00000001'):
        self.inputs = inputs
        self.outputs = outputs
        self.version = version
        self.locktime = locktime

    def get(self):
        return {
            'inputs': self.inputs,
            'outputs': self.outputs,
            'locktime': self.locktime,
        }


if __name__ == '__main__':

    from pprint import pprint

    # From http://www.righto.com/2014/02/bitcoins-hard-way-using-raw-bitcoin.html
    r2 = '0100000001552980326afb3552e838ed75cd1db23bcbfa868a34609578ca1ccaa4d3fbc7d3010000008c493046022100e51c0d8c3a1e80763e58ca31a000044e78b404776aadcbc0cdbcf63e7855334c022100929e94c588886a20f97fc876a8edf29f0b5b046b7fc037ca8fe9f3599e7ee9d5014104ee58ff546d92040652920e512dbab45911de4a03da232c3a228964d2ef9ef7ca6670005218e406985bda769b2f8a4f38dd7f45524776ef4fd8344a120d8a0518ffffffff01806d0d00000000001976a9143c1e136fbc9cfabe35d6d5d41474295721d44f9c88ac00000000'

    # Random transaction from block #447706
    r3 ='0100000004be8a976420ef000956142320e79d90dd2ce103dda9cf51efb280468ca7ac121d000000006b483045022100e80841d3a21a12c505e60d2896631edac06e0e0e7359207583cb31dd490a652502204fde02010706097f11acd0547c9dff0399354c065d7e1d1d17eeda031185804c0121029418397b2ad61b6d603fc865eb4ada9c5425952c4dbe948a0e0c75c36d4e740affffffffc4475d1a9a50aae5c608d20c28a1ca78bda39056d22aa3d869aefbdab83aa4b4000000006b483045022100cd986b35450080a2ee9397349d7513cecff5cf56c435cae43d33ca83c69cddb30220259f9460b372025dff475a534c472c3b2b7f558f393aedeb4c2a30fb6156f81c01210316dec74bb3f916cab37a979c076e03b54f347fa5a90bf2fc9f14e435c1a4ecbdffffffffaea58d46919cf6b7641a30a0a027f3318aee9173fc3f8f1f03c39670f7ce5c3a000000006a47304402206b3297db37c68ae172dc0de46cdb165ec79ce491edec7d59ed98c80d82edeffb0220244665fec2da49eae564d4cc78939ae2c04504294bbca76367d2e9ce5802f56d0121035b5ff8a770e99152d210f1d875d0e1c570dc9fbe332eaecfc405254f6df59edcffffffff85778efe6c0347762b404a6b5b00c45e7143861ccb2b4bd7b0927d0db9fee509010000006a473044022045330b90adba441e797350baa8a631c3b0d375598c88d6eaaae74526698a7fdc022066ffb7a61fcd394d8eed953eac5a792eccddb20f7b14f4e8dcbdc4e9207f1d1c0121032ebd92c614095f612a9e0dbcdb0d03e75481f9335c756f17bfc206d0dcddc644ffffffff02ce8fb400000000001976a914377ad7e288e893dc4473aeb28b18b1675067abaf88aca4823e00000000001976a914bfb2eb5487e238c7d34ea12b965ae169fba563ba88ac00000000'

    # From bitcoinlib
    r = '0100000001a3919372c9807d92507289d71bdd38f10682a49c47e50dc0136996b43d8aa54e010000006a47304402201f6e18f4532e14f328bc820cb78c53c57c91b1da9949fecb8cf42318b791fb38022045e78c9e55df1cf3db74bfd52ff2add2b59ba63e068680f0023e6a80ac9f51f401210239a18d586c34e51238a7c9a27a342abfb35e3e4aa5ac6559889db1dab2816e9dfeffffff023ef59804000000001976a914af8e14a2cecd715c363b3a72b55b59a31e2acac988ac90940d00000000001976a914f0d34949650af161e7cb3f0325a1a8833075165088acb7740f00'

    t = Transaction.import_raw(r2)
    pprint(t.get())
