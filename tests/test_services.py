# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Service Class
#    © 2017 December - 1200 Web Development <http://1200wd.com/>
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

import unittest
import datetime
from bitcoinlib.services.services import *
from tests.test_custom import CustomAssertions

MAXIMUM_ESTIMATED_FEE_DIFFERENCE = 2.00  # Maximum difference from average estimated fee before test_estimatefee fails.
# Use value above >0, and 1 for 100%


class TestService(unittest.TestCase, CustomAssertions):

    def test_transaction_bitcoin_testnet_get_raw(self):
        tx_id = 'd3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955'
        raw_tx = '0100000001a3919372c9807d92507289d71bdd38f10682a49c47e50dc0136996b43d8aa54e010000006a47304402201f6e' \
                 '18f4532e14f328bc820cb78c53c57c91b1da9949fecb8cf42318b791fb38022045e78c9e55df1cf3db74bfd52ff2add2b5' \
                 '9ba63e068680f0023e6a80ac9f51f401210239a18d586c34e51238a7c9a27a342abfb35e3e4aa5ac6559889db1dab2816e' \
                 '9dfeffffff023ef59804000000001976a914af8e14a2cecd715c363b3a72b55b59a31e2acac988ac90940d000000000019' \
                 '76a914f0d34949650af161e7cb3f0325a1a8833075165088acb7740f00'
        self.assertEqual(raw_tx, Service(network='testnet').getrawtransaction(tx_id))

    def test_transaction_bitcoin_get_raw(self):
        tx_id = 'b7feea5e7c79d4f6f343b5ca28fa2a1fcacfe9a2b7f44f3d2fd8d6c2d82c4078'
        raw_tx = '01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff5d0342fe06244d69' \
                 '6e656420627920416e74506f6f6c20626a31312f4542312f4144362f432058d192b6fabe6d6defcf958e3cf9814240e00f' \
                 'a5e36e8cc319cd8141e20890607ccb1954e64843d804000000000000003914000057190200ffffffff013b33b158000000' \
                 '001976a914338c84849423992471bffb1a54a8d9b1d69dc28a88ac00000000'
        self.assertEqual(raw_tx, Service().getrawtransaction(tx_id))

    def test_sendrawtransaction(self):
        raw_tx = \
         '010000000108004b4c0394a211d4ec0d344b70bf1e3b1ce1731d11d1d30279ab0c0f6d9fd7000000006c493046022100ab18a72f7' \
         '87e4c8ea5d2f983b99df28d27e13482b91fd6d48701c055af92f525022100d1c26b8a779896a53a026248388896501e724e46407f' \
         '14a4a1b6478d3293da24012103e428723c145e61c35c070da86faadaf0fab21939223a5e6ce3e1cfd76bad133dffffffff0240420' \
         'f00000000001976a914bbaeed8a02f64c9d40462d323d379b8f27ad9f1a88ac905d1818000000001976a914046858970a72d33817' \
         '474c0e24e530d78716fc9c88ac00000000'
        srv = Service(network='testnet')
        try:
            srv.sendrawtransaction(raw_tx)
        except ServiceError:
            pass
        for provider in srv.errors:
            if provider == 'blockcypher.testnet':
                self.assertIn('has already been spent', srv.errors['blockcypher.testnet'])
            elif provider == 'blockexplorer.testnet' or provider == 'bitcoind.testnet':
                self.assertIn('Missing inputs', srv.errors['blockexplorer.testnet'])
            elif provider == 'chain.so':
                self.assertIn('are still available to spend', srv.errors['chain.so'])

    def test_get_balance(self):
        srv = Service(min_providers=5)
        srv.getbalance('15gHNr4TCKmhHDEG31L2XFNvpnEcnPSQvd')
        prev = None
        if len(srv.results) < 2:
            self.fail("Only 1 or less service providers found, nothing to compare")
        for provider in srv.results:
            balance = srv.results[provider]
            if prev is not None and balance != prev:
                self.fail("Different address balance from service providers: %d != %d" % (balance, prev))
            else:
                prev = balance

    def test_get_utxos(self):
        srv = Service()
        utxos = srv.getutxos('1Mxww5Q2AK3GxG4R2KyCEao6NJXyoYgyAx')
        tx_hash = '9cd7b51b7b9421d70549c765c254fe8682a123cae7b979d6f18d386cfa55cef8'
        self.assertEqual(tx_hash, utxos[0]['tx_hash'])

    def test_estimatefee(self):
        srv = Service(min_providers=5)
        srv.estimatefee()
        if len(srv.results) < 2:
            self.fail("Only 1 or less service providers found, no fee estimates to compare")
        feelist = list(srv.results.values())
        average_fee = sum(feelist) / float(len(feelist))
        for provider in srv.results:
            value = srv.results[provider]
            if not value:
                self.fail("Provider '%s' returns fee estimate of zero" % provider)
            fee_difference_from_average = (abs(value - average_fee) / average_fee)
            if fee_difference_from_average > MAXIMUM_ESTIMATED_FEE_DIFFERENCE:
                self.fail("Estimated fee of provider '%s' is %.1f%% different from average fee" %
                          (provider, fee_difference_from_average * 100))

    def test_gettransactions(self):
        tx_hash = '6961d06e4a921834bbf729a94d7ab423b18ddd92e5ce9661b7b871d852f1db74'
        address = '1Lj1M4zGHgiMJRCZcSR1tj11Q5Bkis197w'
        block_height = 300000
        input_total = 4534802265
        output_total = 4534776015
        fee = 26250
        status = 'confirmed'
        size = 523
        input0 = {
            'address': '1Lj1M4zGHgiMJRCZcSR1tj11Q5Bkis197w',
            'index_n': 0,
            'output_n': 1,
            'prev_hash': '4cb83c6611df40118c39a471419887a2a0aad42fc9e41d8c8790a18d6bd7daef',
            'value': 3200955
        }
        input2 = {
            'address': '1E1MxdfLkv1TZWQRkCtszxEVnrxwRBByZP',
            'index_n': 2,
            'output_n': 1,
            'prev_hash': 'fa422d9fbac6a344af5656325acde172cd5714ebddd2f35068d3f265095add52',
            'value': 4527385460
        }

        srv = Service(min_providers=5)
        srv.gettransactions(address)
        for provider in srv.results:
            res = srv.results[provider]
            t = [r for r in res if r.hash == tx_hash][0]

            # Compare transaction
            if t.block_height:
                self.assertEqual(t.block_height, block_height,
                                 msg="Unexpected block height for %s provider" % provider)
            self.assertEqual(t.input_total, input_total, msg="Unexpected input_total %d for %s provider" % (
                t.input_total, provider))
            self.assertEqual(t.fee, fee, msg="Unexpected fee for %s provider" % provider)
            self.assertEqual(t.output_total, output_total, msg="Unexpected output_total %d for %s provider" % (
                t.output_total, provider))

            self.assertEqual(t.status, status, msg="Unexpected status for %s provider" % provider)
            if t.size:
                self.assertEqual(t.size, size, msg="Unexpected transaction size for %s provider" % provider)

            # Remove extra field from input dict and compare inputs and outputs
            r_inputs = [
                {key: inp[key] for key in ['address', 'index_n', 'output_n', 'prev_hash', 'value']}
                for inp in [i.dict() for i in t.inputs]
            ]
            if provider in ['blockchaininfo']:  # Some providers do not provide previous hashes
                r_inputs[0]['prev_hash'] = '4cb83c6611df40118c39a471419887a2a0aad42fc9e41d8c8790a18d6bd7daef'
                r_inputs[2]['prev_hash'] = 'fa422d9fbac6a344af5656325acde172cd5714ebddd2f35068d3f265095add52'
            self.assertEqual(r_inputs[0], input0, msg="Unexpected transaction input values for %s provider" % provider)
            self.assertEqual(r_inputs[2], input2, msg="Unexpected transaction input values for %s provider" % provider)

    def test_gettransaction(self):
        expected_dict = {
            'block_hash': '000000000000000000f3ae4004e9bcc39b3d4dc0f342b76a1830ee8607b7f00a',
            'inputs': [
                {
                    'value': 299889,
                    'output_n': 51,
                    'prev_hash': 'fa7b29d0e1cf62c79749c977dd9b3fedcfa348e696600f2240206eedaccbb309',
                    'double_spend': False,
                    'index_n': 0,
                    'script_type': 'p2pkh',
                    'address': '1CCBgvQdqPHGrRJxpKEnjJkgFp5UsDYvWD'
                },
                {
                    'value': 1000022,
                    'output_n': 0,
                    'prev_hash': '512f4363ccb28d04d47edd684840cc074f2a3b625838909a6074d277883b9f83',
                    'double_spend': False,
                    'index_n': 1,
                    'script_type': 'p2pkh',
                    'address': '1Hw3ZTxMqVK3jgmJSod4LF5XFbDVYc3EZP'
                },
                {
                    'value': 219439,
                    'output_n': 55,
                    'prev_hash': '0ccd49e93261c9dd2bee124d90849677e93f789d2dc83013bfb0643beb962733',
                    'double_spend': False,
                    'index_n': 2,
                    'script_type': 'p2pkh',
                    'address': '1CCBgvQdqPHGrRJxpKEnjJkgFp5UsDYvWD'
                },
                {
                    'value': 219436,
                    'output_n': 56,
                    'prev_hash': '1b110073aed6637f9a492ceaac45d2b978b75f0139df0401032ad68c0944d38c',
                    'double_spend': False,
                    'index_n': 3,
                    'script_type': 'p2pkh',
                    'address': '1CCBgvQdqPHGrRJxpKEnjJkgFp5UsDYvWD'
                },
                {
                    'value': 110996,
                    'output_n': 50,
                    'prev_hash': 'a2d613e5a649102672462aa6a09e3e833769f5a85a65a8844acc723c07a8991d',
                    'double_spend': False,
                    'index_n': 4,
                    'script_type': 'p2pkh',
                    'address': '1CCBgvQdqPHGrRJxpKEnjJkgFp5UsDYvWD'
                },
                {
                    'value': 602,
                    'output_n': 2434,
                    'prev_hash': 'd8505b78a4cddbd058372443bbce9ea74a313c27c586b7bbe8bc3825b7c7cbd7',
                    'double_spend': False,
                    'index_n': 5,
                    'script_type': 'p2pkh',
                    'address': '1CCBgvQdqPHGrRJxpKEnjJkgFp5UsDYvWD'
                }
            ],
            'locktime': 478952,
            'input_total': 1850384,
            'network': 'bitcoin',
            'status': 'confirmed',
            'version': b'\x00\x00\x00\x02',
            'outputs':
                [
                    {
                        'spent': True,
                        'value': 1000032,
                        'script_type': 'p2pkh',
                        'address': '15witRoAeoSKgBLVA27oj1F2KQ1Sg1bjNz',
                        'output_n': 0
                    },
                    {
                        'spent': True,
                        'value': 845308,
                        'script_type': 'p2pkh',
                        'address': '1PTJHj3jzbfcRg6LauAAV6Qirs5VUe8M6C',
                        'output_n': 1,
                    }
                ],
            'fee': 5044,
            'block_height': 478953,
            'output_total': 1845340,
            'size': 964,
            'hash': '2ae77540ec3ef7b5001de90194ed0ade7522239fe0fc57c12c772d67274e2700',
            'date': datetime.datetime(2017, 8, 4)
        }

        srv = Service(network='bitcoin', min_providers=10)

        # Get transactions by hash
        srv.gettransaction('2ae77540ec3ef7b5001de90194ed0ade7522239fe0fc57c12c772d67274e2700').dict()

        for provider in srv.results:
            print("Comparing provider %s" % provider)
            self.assertDictEqualExt(srv.results[provider].dict(), expected_dict,
                                    ['block_hash', 'block_height', 'spent', 'value'])

    def test_gettransaction_coinbase(self):
        expected_dict = {
            'block_hash': '0000000000000000002d966c99d68245b20468dc9c2a7a776a836add03362199',
            'block_height': 500834,
            'coinbase': True,
            'date': datetime.datetime(2017, 12, 24, 14, 16, 30),
            'flag': b'\1',
            'hash': '68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13',
            'input_total': 1717718311,
            'inputs': [
                {'address': '',
                 'index_n': 0,
                 'output_n': 4294967295,
                 'prev_hash': '0000000000000000000000000000000000000000000000000000000000000000',
                 'public_key': [],
                 'script': '0362a4071c2f5669614254432f4d696e656420627920676c6f62616c686173682f2cfabe6d6d2c31604d43cac'
                           '8b0f5c819c1d2b6f9051349d7633df07fc664be73533e64ccf9010000000000000010c147e903973b4143d99d'
                           'e6b376ca0200',
                 'script_type': 'coinbase',
                 'sequence': 4294967295,
                 }
            ],
            'locktime': 0,
            'network': 'bitcoin',
            'output_total': 1717718311,
            'outputs': [
                {'address': '18cBEMRxXHqzWWCxZNtU91F5sbUNKhL5PX',
                 'output_n': 0,
                 'public_key_hash': '536ffa992491508dca0354e52f32a3a7a679a53a',
                 'script': '76a914536ffa992491508dca0354e52f32a3a7a679a53a88ac',
                 'script_type': 'p2pkh',
                 'value': 1717718311
                 },
                {'address': '',
                 'output_n': 1,
                 'public_key_hash': '',
                 'script': '6a24aa21a9ed8e77dfd1d42865e64f1d5ef40f74eeb2ad21c8c40c71f6e615a7c1fcb7701629',
                 'script_type': 'nulldata',
                 'spent': False,
                 'value': 0
                 },
            ],
            'status': 'confirmed',
            'version': b'\x00\x00\x00\x01'
        }
        srv = Service(network='bitcoin', min_providers=10)

        # Get transactions by hash
        srv.gettransaction('68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13').dict()

        for provider in srv.results:
            print("Comparing provider %s" % provider)
            self.assertDictEqualExt(srv.results[provider].dict(), expected_dict,
                                    ['block_hash', 'block_height', 'spent', 'value', 'flag'])
