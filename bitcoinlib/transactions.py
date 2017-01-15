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

import binascii
from bitcoinlib.encoding import change_base, varbyteint_to_int
from bitcoinlib.main import *
from bitcoinlib.services.bitcoind import BitcoindClient

_logger = logging.getLogger(__name__)


class TransactionError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.error(msg)

    def __str__(self):
        return self.msg


def deserialize_transaction(rawtx):
    """
    Deserialize a raw transaction

    :param rawtx: Raw transaction in bytes
    :return: json list with inputs, outputs, locktime and version
    """
    version = rawtx[0:4][::-1]
    n_inputs, size = varbyteint_to_int(rawtx[4:13])
    cursor = 4 + size
    inputs = []
    for i in range(0, n_inputs):
        inp_hash = rawtx[cursor:cursor + 32][::-1]
        if not len(inp_hash):
            raise TransactionError("Input transaction hash not found. Probably malformed raw transaction")
        inp_index = rawtx[cursor + 32:cursor + 36][::-1]
        cursor += 36

        scriptsig_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        scriptsig = rawtx[cursor:cursor + scriptsig_size]
        cursor += scriptsig_size
        sequence_number = binascii.hexlify(rawtx[cursor:cursor + 4])
        cursor += 4
        inputs.append({'prev_hash': binascii.hexlify(inp_hash), 'output_index': change_base(inp_index, 256, 10),
                       'script_sig': binascii.hexlify(scriptsig), 'sequence_number': sequence_number, })
    if len(inputs) != n_inputs:
        raise TransactionError("Error parsing inputs. Number of tx specified %d but %d found" % (n_inputs, len(inputs)))

    outputs = []
    n_outputs, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
    cursor += size
    for o in range(0, n_outputs):
        amount = change_base(rawtx[cursor:cursor + 8][::-1], 256, 10)
        cursor += 8
        script_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        script = rawtx[cursor:cursor + script_size]
        cursor += script_size
        outputs.append({'amount': amount, 'script': binascii.hexlify(script), })
    if not outputs:
        raise TransactionError("Error no outputs found in this transaction")
    locktime = change_base(rawtx[cursor:cursor + 4][::-1], 256, 10)

    return inputs, outputs, locktime, version


class Transaction:

    @staticmethod
    def import_raw(rawtx):
        if isinstance(rawtx, str):
            rawtx = binascii.unhexlify(rawtx)
        elif not isinstance(rawtx, bytes):
            raise TransactionError("Raw Transaction must be of type bytes or str")

        inputs, outputs, locktime, version = deserialize_transaction(rawtx)

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
    import json
    workdir = os.path.dirname(__file__)
    with open('/home/lennart/code/bitcoinlib/tests/transactions_raw.json', 'r') as f:
        d = json.load(f)

    pprint(d)
    # Simple raw transaction with 1 input and 2 outputs (destination and change address).
    # See http://www.siliconian.com/blog/16-bitcoin-blockchain/22-deconstructing-bitcoin-transactions
    # for a colorfull deserialisation example.
    rt = '01000000' \
         '01' \
         'a3919372c9807d92507289d71bdd38f10682a49c47e50dc0136996b43d8aa54e' \
         '01000000' \
         '6a' \
         '47304402201f6e18f4532e14f328bc820cb78c53c57c91b1da9949fecb8cf42318b791fb38022045e78c9e55df1cf3db74bf' \
         'd52ff2add2b59ba63e068680f0023e6a80ac9f51f401210239a18d586c34e51238a7c9a27a342abfb35e3e4aa5ac6559889db' \
         '1dab2816e9d' \
         'feffffff' \
         '02' \
         '3ef59804' \
         '00000000' \
         '1976a9' \
         '14af8e14a2cecd715c363b3a72b55b59a31e2acac988ac90940d' \
         '0000000000' \
         '1976a9' \
         '14f0d34949650af161e7cb3f0325a1a8833075165088acb7740f' \
         '00'

    t = Transaction.import_raw(rt)
    pprint(t.get())

    if False:  # Set to True to enable example
        # Deserialize transactions in latest block with bitcoind client
        bdc = BitcoindClient.from_config()

        print("\n=== DESERIALIZE LAST BLOCKS TRANSACTIONS ===")
        blockhash = bdc.proxy.getbestblockhash()
        bestblock = bdc.proxy.getblock(blockhash)
        print('... %d transactions found' % len(bestblock['tx']))
        ci = 0
        ct = len(bestblock['tx'])
        for txid in bestblock['tx']:
            ci += 1
            print("[%d/%d] Deserialize txid %s" % (ci, ct, txid))
            try:
                rt = bdc.getrawtransaction(txid)
            except:
                pass
            print("- raw %s" % rt)
            t = Transaction.import_raw(rt)
            pprint(t.get())
        print("===   %d raw transactions deserialised   ===" % ct)
        print("===   D O N E   ===")

        # Deserialize transactions in the bitcoind mempool client
        print("\n=== DESERIALIZE MEMPOOL TRANSACTIONS ===")
        newtxs = bdc.proxy.getrawmempool()
        ci = 0
        ct = len(newtxs)
        print("Found %d transactions in mempool" % len(newtxs))
        for txid in newtxs:
            ci += 1
            print("[%d/%d] Deserialize txid %s" % (ci, ct, txid))
            try:
                rt = bdc.getrawtransaction(txid)
                print("- raw %s" % rt)
                t = Transaction.import_raw(rt)
                pprint(t.get())
            except:
                print(txid)
        print("===   %d mempool transactions deserialised   ===" % ct)
        print("===   D O N E   ===")
