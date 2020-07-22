# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Unit Tests for Service Class
#    © 2018-2019 November - 1200 Web Development <http://1200wd.com/>
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
from datetime import datetime
from bitcoinlib.services.services import *
from tests.test_custom import CustomAssertions

MAXIMUM_ESTIMATED_FEE_DIFFERENCE = 3.00  # Maximum difference from average estimated fee before test_estimatefee fails.
# Use value above >0, and 1 for 100%

DATABASEFILE_CACHE_UNITTESTS = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlibcache.unittest.sqlite')
DATABASEFILE_CACHE_UNITTESTS2 = os.path.join(str(BCL_DATABASE_DIR), 'bitcoinlibcache2.unittest.sqlite')
TIMEOUT_TEST = 2


# Wrapper class for the Service client: Set cache_uri, timeout and ignore provider priority
class ServiceTest(Service):

    def __init__(self, network=DEFAULT_NETWORK, min_providers=1, max_providers=1, providers=None,
                 timeout=TIMEOUT_TEST, cache_uri=DATABASEFILE_CACHE_UNITTESTS, ignore_priority=True,
                 exclude_providers=None):
        super(self.__class__, self).__init__(network, min_providers, max_providers, providers, timeout, cache_uri,
                                             ignore_priority, exclude_providers)


class TestService(unittest.TestCase, CustomAssertions):

    def test_service_transaction_get_raw_testnet(self):
        tx_id = 'd3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955'
        raw_tx = '0100000001a3919372c9807d92507289d71bdd38f10682a49c47e50dc0136996b43d8aa54e010000006a47304402201f6e' \
                 '18f4532e14f328bc820cb78c53c57c91b1da9949fecb8cf42318b791fb38022045e78c9e55df1cf3db74bfd52ff2add2b5' \
                 '9ba63e068680f0023e6a80ac9f51f401210239a18d586c34e51238a7c9a27a342abfb35e3e4aa5ac6559889db1dab2816e' \
                 '9dfeffffff023ef59804000000001976a914af8e14a2cecd715c363b3a72b55b59a31e2acac988ac90940d000000000019' \
                 '76a914f0d34949650af161e7cb3f0325a1a8833075165088acb7740f00'
        self.assertEqual(raw_tx, ServiceTest(network='testnet').getrawtransaction(tx_id))

    def test_service_transaction_get_raw_bitcoin(self):
        tx_id = 'b7feea5e7c79d4f6f343b5ca28fa2a1fcacfe9a2b7f44f3d2fd8d6c2d82c4078'
        raw_tx = '01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff5d0342fe06244d69' \
                 '6e656420627920416e74506f6f6c20626a31312f4542312f4144362f432058d192b6fabe6d6defcf958e3cf9814240e00f' \
                 'a5e36e8cc319cd8141e20890607ccb1954e64843d804000000000000003914000057190200ffffffff013b33b158000000' \
                 '001976a914338c84849423992471bffb1a54a8d9b1d69dc28a88ac00000000'
        self.assertEqual(raw_tx, ServiceTest().getrawtransaction(tx_id))

    def test_service_transaction_get_raw_litecoin(self):
        tx_id = '832518d58e9678bcdb9fe0e417a138daeb880c3a2ee1fb1659f1179efc383c25'
        raw_tx = '01000000018d3a15210548821144e323b9138226926ec66e5f79a3871d4cdefde479a5e076000000006b48304502201952' \
                 '093e6082574209150659b294c8e634a30c469fd3dff97a38c8e9ea641d9a022100a9621d0f9d05cbbe274309689bc9086b' \
                 '795bc67751f1572eddb47c6ae029cda0012102461acd52a39d260be22c18780def2bb77255abd4c3ea4fd65673ad302492' \
                 '1c62ffffffff02b5055501000000001976a914cfb8e7aafe540a0b1b56e686145c8bb48d34391588ac00e1f50500000000' \
                 '1976a914c1b1668730f13dd1772977e8ce96e3f5f78d290388ac00000000'
        self.assertEqual(raw_tx, ServiceTest(network='litecoin').getrawtransaction(tx_id))

    def test_service_transaction_get_raw_dash(self):
        tx_id = '885042c885dc0d44167ce71ce82bb28b09bdd8445b7639ea96a5f5be8ceba4cf'
        raw_tx = '0100000001edfbcd24cd10350844061d62d03be6f3ed9c28b26b0b8082539c5d29454f7cb3010000006b483045022100e' \
                 '87b6a6dff07d1b91d12f530992cf8fa9f26a541af525337bbbc5c954cbf072b022062f1cc0f33d036c1c60a7d561de060' \
                 '67528fffca52292d803b75e53f7dfbf63d0121028bd465d7eb03bbee946c3a277ad1b331f78add78c6723eed00097520e' \
                 'dc21ed2ffffffff0200f90295000000001976a914de4b569d39f05bfc43f56a1b22d7783a7d0661d488aca0fc7c040000' \
                 '00001976a9141495ac5ca428a17197c7cb5065614d8eabfcf8cb88ac00000000'
        self.assertEqual(raw_tx, ServiceTest(network='dash').getrawtransaction(tx_id))

    def test_service_sendrawtransaction(self):
        raw_tx = \
         '010000000108004b4c0394a211d4ec0d344b70bf1e3b1ce1731d11d1d30279ab0c0f6d9fd7000000006c493046022100ab18a72f7' \
         '87e4c8ea5d2f983b99df28d27e13482b91fd6d48701c055af92f525022100d1c26b8a779896a53a026248388896501e724e46407f' \
         '14a4a1b6478d3293da24012103e428723c145e61c35c070da86faadaf0fab21939223a5e6ce3e1cfd76bad133dffffffff0240420' \
         'f00000000001976a914bbaeed8a02f64c9d40462d323d379b8f27ad9f1a88ac905d1818000000001976a914046858970a72d33817' \
         '474c0e24e530d78716fc9c88ac00000000'
        srv = ServiceTest(network='testnet')
        try:
            srv.sendrawtransaction(raw_tx)
        except ServiceError:
            pass
        for provider in srv.errors:
            print("Provider %s" % provider)
            prov_error = str(srv.errors[provider])
            if isinstance(srv.errors[provider], Exception) or 'response [429]' in prov_error \
                    or 'response [503]' in prov_error:
                pass
            elif provider == 'blockcypher.testnet':
                self.assertIn('has already been spent', prov_error)
            elif provider == 'chain.so':
                self.assertIn('are still available to spend', prov_error)

    def test_service_get_balance(self):
        srv = ServiceTest(min_providers=5)
        srv.getbalance('15gHNr4TCKmhHDEG31L2XFNvpnEcnPSQvd')
        prev = None
        if len(srv.results) < 2:
            self.fail("Only 1 or less service providers found, nothing to compare. Errors %s" % srv.errors)
        for provider in srv.results:
            print("Provider %s" % provider)
            balance = srv.results[provider]
            if prev is not None and balance != prev:
                self.fail("Different address balance from service providers: %d != %d" % (balance, prev))
            else:
                prev = balance

    def test_service_get_balance_litecoin(self):
        srv = ServiceTest(min_providers=5, network='litecoin')
        srv.getbalance('Lct7CEpiN7e72rUXmYucuhqnCy5F5Vc6Vg')
        prev = None
        if len(srv.results) < 2:
            self.fail("Only 1 or less service providers found, nothing to compare. Errors %s" % srv.errors)
        for provider in srv.results:
            print("Provider %s" % provider)
            balance = srv.results[provider]
            if prev is not None and balance != prev:
                self.fail("Different address balance from service providers: %d != %d" % (balance, prev))
            else:
                prev = balance

    def test_service_address_conversion(self):
        srv = ServiceTest(min_providers=2, network='litecoin_legacy', providers=['cryptoid', 'litecoreio'])
        srv.getbalance('3N59KFZBzpnq4EoXo2cDn2GKjX1dfkv1nB')
        exp_dict = {'cryptoid.litecoin.legacy': 95510000, 'litecoreio.litecoin.legacy': 95510000}
        for r in srv.results:
            if r not in exp_dict:
                print("WARNING: Provider %s not found in results" % r)
            self.assertEqual(srv.results[r], exp_dict[r])

    def test_service_get_utxos(self):
        expected_dict = {
            'tx_hash': '9cd7b51b7b9421d70549c765c254fe8682a123cae7b979d6f18d386cfa55cef8',
            'output_n': 0,
            'block_height': 478371,
            'address': '1Mxww5Q2AK3GxG4R2KyCEao6NJXyoYgyAx',
            'date': datetime(2017, 7, 31, 6, 0, 52),
            'value': 190000}
        srv = ServiceTest(min_providers=3)
        srv.getutxos('1Mxww5Q2AK3GxG4R2KyCEao6NJXyoYgyAx')
        for provider in srv.results:
            print("Provider %s" % provider)
            self.assertDictEqualExt(srv.results[provider][0], expected_dict, ['date', 'block_height'])

    def test_service_get_utxos_after_txid(self):
        srv = ServiceTest(min_providers=3)
        tx_hash = '9ae79dd82aa05c66ac76aeffc2fe07e579978c57ce5537115864548da0768d58'
        srv.getutxos('1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1',
                     after_txid='9293869acee7d90661ee224135576b45b4b0dbf2b61e4ce30669f1099fecac0c')
        for provider in srv.results:
            print("Testing provider %s" % provider)
            self.assertEqual(srv.results[provider][0]['tx_hash'], tx_hash)

    def test_service_get_utxos_litecoin(self):
        srv = ServiceTest(network='litecoin', min_providers=3)
        srv.getutxos('Lct7CEpiN7e72rUXmYucuhqnCy5F5Vc6Vg')
        tx_hash = '832518d58e9678bcdb9fe0e417a138daeb880c3a2ee1fb1659f1179efc383c25'
        for provider in srv.results:
            print("Provider %s" % provider)
            self.assertEqual(srv.results[provider][0]['tx_hash'], tx_hash)

    def test_service_get_utxos_litecoin_after_txid(self):
        srv = ServiceTest(network='litecoin', min_providers=3)
        tx_hash = '201a27d05a2efa4c72ae5b0b9fe7094350a9d7c503ce022ddc28768196ba1d28'
        srv.getutxos('Lfx4mFjhRvqyRKxXKqn6jyb17D6NDmosEV',
                     after_txid='b328a91dd15b8b82fef5b01738aaf1f486223d34ee54357e1430c22e46ddd04e')
        for provider in srv.results:
            print("Comparing provider %s" % provider)
            self.assertEqual(srv.results[provider][0]['tx_hash'], tx_hash)

    def test_service_estimatefee(self):
        srv = ServiceTest(min_providers=5)
        srv.estimatefee()
        if len(srv.results) < 2:
            self.fail("Only 1 or less service providers found, no fee estimates to compare. Errors %s" % srv.errors)
        feelist = list(srv.results.values())
        average_fee = sum(feelist) / float(len(feelist))

        # Normalize with dust amount, to avoid errors on small differences
        dust = Network().dust_amount
        for provider in srv.results:
            print("Provider %s" % provider)
            if srv.results[provider] < average_fee and average_fee - srv.results[provider] > dust:
                srv.results[provider] += dust
            elif srv.results[provider] > average_fee and srv.results[provider] - average_fee > dust:
                srv.results[provider] -= dust

        for provider in srv.results:
            value = srv.results[provider]
            if not value:
                self.fail("Provider '%s' returns fee estimate of zero" % provider)
            fee_difference_from_average = (abs(value - average_fee) / average_fee)
            if fee_difference_from_average > MAXIMUM_ESTIMATED_FEE_DIFFERENCE:
                self.fail("Estimated fee of provider '%s' is %.1f%% different from average fee" %
                          (provider, fee_difference_from_average * 100))

    # NOT ENOUGH SERVICE PROVIDERS OFFER FEE ESTIMATES FOR LITECOIN AT THE MOMENT
    # def test_estimatefee_litecoin(self):
    #     srv = ServiceTest(min_providers=5, network='litecoin')
    #     srv.estimatefee()
    #     if len(srv.results) < 2:
    #         self.fail("Only 1 or less service providers found, no fee estimates to compare")
    #     feelist = list(srv.results.values())
    #     average_fee = sum(feelist) / float(len(feelist))
    #     for provider in srv.results:
    #         value = srv.results[provider]
    #         if not value:
    #             self.fail("Provider '%s' returns fee estimate of zero" % provider)
    #         fee_difference_from_average = (abs(value - average_fee) / average_fee)
    #         if fee_difference_from_average > MAXIMUM_ESTIMATED_FEE_DIFFERENCE:
    #             self.fail("Estimated fee of provider '%s' is %.1f%% different from average fee" %
    #                       (provider, fee_difference_from_average * 100))

    def test_service_gettransactions(self):
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

        srv = ServiceTest(min_providers=3)
        srv.gettransactions(address)
        for provider in srv.results:
            print("Testing: %s" % provider)
            res = srv.results[provider]
            t = [r for r in res if r.txid == tx_hash][0]

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
                for inp in [i.as_dict() for i in t.inputs]
            ]

            if provider in ['blockchaininfo']:  # Some providers do not provide previous hashes
                r_inputs[0]['prev_hash'] = '4cb83c6611df40118c39a471419887a2a0aad42fc9e41d8c8790a18d6bd7daef'
                r_inputs[2]['prev_hash'] = 'fa422d9fbac6a344af5656325acde172cd5714ebddd2f35068d3f265095add52'
            self.assertEqual(r_inputs[0], input0, msg="Unexpected transaction input values for %s provider" % provider)
            self.assertEqual(r_inputs[2], input2, msg="Unexpected transaction input values for %s provider" % provider)

    def test_service_gettransactions_after_txid(self):
        res = ServiceTest(timeout=TIMEOUT_TEST).\
            gettransactions('3As4asrpMryntmrVgexCD9i3f3qZP92Zct',
                            after_txid='d14f4dfafa3578250ffd596b3f69836ef5e35d57ceced1cc0850d2246964dd3a')
        self.assertEqual(res[0].txid, '8b8a8f1de23f70b2bdaa74488d97dc64728c2d99d2d486945c71e258fdef6ca1')

    def test_service_gettransactions_after_txid_segwit(self):
        res = ServiceTest(timeout=TIMEOUT_TEST).\
            gettransactions('bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c',
                            after_txid='f91d0a8a78462bc59398f2c5d7a84fcff491c26ba54c4833478b202796c8aafd')
        tx_ids = [
            '9e914f4438cdfd2681bf5fb0b3dea8206fffcc48d1ca7e0f05f7b77c76115803',
            'a4bc261faf9ca47722760c9f9f075ab974c7351d8da7b0b5e5a316b3aa7aefa2',
            '04be18177781f8060d63390a705cf89ffed2252a3506fab69be7079bc7ba9410']
        self.assertIn(res[0].txid, tx_ids)
        self.assertIn(res[1].txid, tx_ids)
        self.assertIn(res[2].txid, tx_ids)

    def test_service_gettransactions_after_txid_litecoin(self):
        res = ServiceTest('litecoin').gettransactions(
            'LhVR1yL8cEjPJsiuVnqjEfeGCEtS25jE2J',
            after_txid='c44967c6db6fa3c1307f9a98bbe0308aa29d99330ada866192735b31bcb0d53f')
        self.assertEqual(res[0].txid, 'e0c1e90fa2195869905e90d4fa644082dfd0523540c13baea0c7a4e246ef40e4')

    def test_service_gettransactions_addresslist_error(self):
        self.assertRaisesRegexp(ServiceError, "Address parameter must be of type text",
                               ServiceTest().gettransactions,
                                ['1LGJzocooaciEtsxEVAajLhCymCXNvPoLh', '19KedreX9aR64fN7tnNzVLVFHQAUL6dLzr'])

    def test_service_gettransaction(self):
        expected_dict = {
            'block_hash': '000000000000000000f3ae4004e9bcc39b3d4dc0f342b76a1830ee8607b7f00a',
            'inputs': [
                {
                    'value': 299889,
                    'output_n': 51,
                    'prev_hash': 'fa7b29d0e1cf62c79749c977dd9b3fedcfa348e696600f2240206eedaccbb309',
                    'double_spend': False,
                    'index_n': 0,
                    'script_type': 'sig_pubkey',
                    'address': '1CCBgvQdqPHGrRJxpKEnjJkgFp5UsDYvWD'
                },
                {
                    'value': 1000022,
                    'output_n': 0,
                    'prev_hash': '512f4363ccb28d04d47edd684840cc074f2a3b625838909a6074d277883b9f83',
                    'double_spend': False,
                    'index_n': 1,
                    'script_type': 'sig_pubkey',
                    'address': '1Hw3ZTxMqVK3jgmJSod4LF5XFbDVYc3EZP'
                },
                {
                    'value': 219439,
                    'output_n': 55,
                    'prev_hash': '0ccd49e93261c9dd2bee124d90849677e93f789d2dc83013bfb0643beb962733',
                    'double_spend': False,
                    'index_n': 2,
                    'script_type': 'sig_pubkey',
                    'address': '1CCBgvQdqPHGrRJxpKEnjJkgFp5UsDYvWD'
                },
                {
                    'value': 219436,
                    'output_n': 56,
                    'prev_hash': '1b110073aed6637f9a492ceaac45d2b978b75f0139df0401032ad68c0944d38c',
                    'double_spend': False,
                    'index_n': 3,
                    'script_type': 'sig_pubkey',
                    'address': '1CCBgvQdqPHGrRJxpKEnjJkgFp5UsDYvWD'
                },
                {
                    'value': 110996,
                    'output_n': 50,
                    'prev_hash': 'a2d613e5a649102672462aa6a09e3e833769f5a85a65a8844acc723c07a8991d',
                    'double_spend': False,
                    'index_n': 4,
                    'script_type': 'sig_pubkey',
                    'address': '1CCBgvQdqPHGrRJxpKEnjJkgFp5UsDYvWD'
                },
                {
                    'value': 602,
                    'output_n': 2434,
                    'prev_hash': 'd8505b78a4cddbd058372443bbce9ea74a313c27c586b7bbe8bc3825b7c7cbd7',
                    'double_spend': False,
                    'index_n': 5,
                    'script_type': 'sig_pubkey',
                    'address': '1CCBgvQdqPHGrRJxpKEnjJkgFp5UsDYvWD'
                }
            ],
            'locktime': 478952,
            'input_total': 1850384,
            'network': 'bitcoin',
            'status': 'confirmed',
            'version': 2,
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
            'date': datetime(2017, 8, 4, 5, 17, 27)
        }

        srv = ServiceTest(network='bitcoin', min_providers=3)

        # Get transactions by hash
        srv.gettransaction('2ae77540ec3ef7b5001de90194ed0ade7522239fe0fc57c12c772d67274e2700')

        for provider in srv.results:
            print("Comparing provider %s" % provider)
            self.assertDictEqualExt(srv.results[provider].as_dict(), expected_dict,
                                    ['block_hash', 'block_height', 'spent', 'value'])

    def test_service_gettransaction_dash(self):
        expected_dict = {'block_hash': '000000000000002eddff510f4f6c61243e350102c58bdf8c986430b405ce7a22',
                         'network': 'dash', 'input_total': 2575500000, 'fee_per_kb': None, 'outputs': [
                {'public_key_hash': 'de4b569d39f05bfc43f56a1b22d7783a7d0661d4', 'output_n': 0, 'spent': True,
                 'public_key': '', 'address': 'XvxE6SRkZMbhBW34QfrgxPqcNmgTsRvyeJ', 'script_type': 'p2pkh',
                 'script': '76a914de4b569d39f05bfc43f56a1b22d7783a7d0661d488ac', 'value': 2500000000},
                {'public_key_hash': '1495ac5ca428a17197c7cb5065614d8eabfcf8cb', 'output_n': 1, 'spent': True,
                 'public_key': '', 'address': 'XcZgeaA4cwUqBqtKUPfZHUme8a5G3gA8LC', 'script_type': 'p2pkh',
                 'script': '76a9141495ac5ca428a17197c7cb5065614d8eabfcf8cb88ac', 'value': 75300000}],
                         'output_total': 2575300000, 'block_height': 900147, 'locktime': 0, 'flag': None,
                         'coinbase': False,
                         'status': 'confirmed', 'verified': False, 'version': 1,
                         'hash': '885042c885dc0d44167ce71ce82bb28b09bdd8445b7639ea96a5f5be8ceba4cf', 'size': 226,
                         'fee': 200000, 'inputs': [
                {'redeemscript': '', 'address': 'XczHdW9k4Kg9mu6AdJayJ1PJtfX3Z9wYxm', 'double_spend': False,
                 'sequence': 4294967295,
                 'prev_hash': 'b37c4f45295d9c5382800b6bb2289cedf3e63bd0621d0644083510cd24cdfbed', 'output_n': 1,
                 'signatures': [
                     'e87b6a6dff07d1b91d12f530992cf8fa9f26a541af525337bbbc5c954cbf072b62f1cc0f33d036c1c60a7d561de0'
                     '6067528fffca52292d803b75e53f7dfbf63d',
                     'e87b6a6dff07d1b91d12f530992cf8fa9f26a541af525337bbbc5c954cbf072b62f1cc0f33d036c1c60a7d561de0'
                     '6067528fffca52292d803b75e53f7dfbf63d'],
                 'public_key': '028bd465d7eb03bbee946c3a277ad1b331f78add78c6723eed00097520edc21ed2', 'index_n': 0,
                 'script_type': 'sig_pubkey',
                 'script': '483045022100e87b6a6dff07d1b91d12f530992cf8fa9f26a541af525337bbbc5c954cbf072b022062f1cc'
                           '0f33d036c1c60a7d561de06067528fffca52292d803b75e53f7dfbf63d0121028bd465d7eb03bbee946c3a'
                           '277ad1b331f78add78c6723eed00097520edc21ed2',
                 'value': 2575500000}], 'date': datetime(2018, 7, 8, 21, 35, 58)}

        srv = ServiceTest(network='dash', min_providers=3)

        # Get transactions by hash
        srv.gettransaction('885042c885dc0d44167ce71ce82bb28b09bdd8445b7639ea96a5f5be8ceba4cf')
        for provider in srv.results:
            print("Comparing provider %s" % provider)
            self.assertDictEqualExt(srv.results[provider].as_dict(), expected_dict,
                                    ['block_hash', 'block_height', 'spent', 'value'])

    def test_service_gettransactions_litecoin(self):
        tx_hash = '832518d58e9678bcdb9fe0e417a138daeb880c3a2ee1fb1659f1179efc383c25'
        address = 'Lct7CEpiN7e72rUXmYucuhqnCy5F5Vc6Vg'
        block_height = 400003
        input_total = 122349237
        output_total = 122349237
        fee = 0
        status = 'confirmed'
        size = 226
        input0 = {
            'address': 'Lg9fq8MQLF3MLhUzrVSphzBvWRV8CsX7bW',
            'index_n': 0,
            'output_n': 0,
            'prev_hash': '76e0a579e4fdde4c1d87a3795f6ec66e92268213b923e3441182480521153a8d',
            'value': 122349237
        }

        srv = ServiceTest(min_providers=5, network='litecoin')
        srv.gettransactions(address)
        for provider in srv.results:
            print("Provider %s" % provider)
            res = srv.results[provider]
            txs = [r for r in res if r.txid == tx_hash]
            t = txs[0]

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
                for inp in [i.as_dict() for i in t.inputs]
            ]
            if provider in ['blockchaininfo']:  # Some providers do not provide previous hashes
                r_inputs[0]['prev_hash'] = '4cb83c6611df40118c39a471419887a2a0aad42fc9e41d8c8790a18d6bd7daef'
                r_inputs[2]['prev_hash'] = 'fa422d9fbac6a344af5656325acde172cd5714ebddd2f35068d3f265095add52'
            self.assertEqual(r_inputs[0], input0, msg="Unexpected transaction input values for %s provider" % provider)

    def test_service_gettransaction_coinbase(self):
        expected_dict = {
            'block_hash': '0000000000000000002d966c99d68245b20468dc9c2a7a776a836add03362199',
            'block_height': 500834,
            'coinbase': True,
            'date': datetime(2017, 12, 24, 13, 16, 30),
            'flag': b'\1',
            'hash': '68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13',
            'input_total': 0,
            'inputs': [
                {'address': '',
                 'index_n': 0,
                 'prev_hash': '0000000000000000000000000000000000000000000000000000000000000000',
                 'public_key': [],
                 'script_type': 'coinbase',
                 'sequence': 4294967295,
                 'value': 0
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
                 'value': 1717718311,
                 'spent': True,
                 'spending_txid': '3dce59e01ac169d384b603e9884c871a34c2c02000e4afb3f83ba7c2cc7a25dd',
                 'spending_index_n': 0,
                 },
                {'address': '',
                 'output_n': 1,
                 'public_key_hash': '',
                 'script': '6a24aa21a9ed8e77dfd1d42865e64f1d5ef40f74eeb2ad21c8c40c71f6e615a7c1fcb7701629',
                 'script_type': 'nulldata',
                 'value': 0
                 },
            ],
            'status': 'confirmed',
            'version': 1
        }
        srv = ServiceTest(network='bitcoin', min_providers=3, providers=['blocksmurfer'])

        # Get transactions by hash
        srv.gettransaction('68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13')

        for provider in srv.results:
            print("Comparing provider %s" % provider)
            for o in srv.results[provider].outputs:
                if o.spending_txid == '':
                    o.spending_txid = None
            self.assertDictEqualExt(srv.results[provider].as_dict(), expected_dict,
                                    ['block_hash', 'block_height', 'spent', 'spending_txid', 'spending_index_n',
                                     'flag'])

    def test_service_gettransaction_segwit_p2wpkh(self):
        expected_dict = {
            'block_hash': '00000000000000000006e7007407805af2bfb386439e570f5310bb97cdcf0352',
            'block_height': 547270,
            'coinbase': False,
            'date': datetime(2018, 10, 25, 16, 30, 46),
            'fee': 2662,
            'witness_type': 'segwit',
            'hash': '299dab85f10c37c6296d4fb10eaa323fb456a5e7ada9adf41389c447daa9c0e4',
            'input_total': 506323064,
            'inputs':
                [{
                    'address': 'bc1qpjnaav9yvane7qq3a7efq6nw229g6gh09jzlvc',
                    'index_n': 0,
                    'output_n': 1,
                    'prev_hash': '444c4a42da547711063be57eecb48cd92d1a6d4afbc64a57e75b69d74df59eb9',
                    'public_hash': '0ca7deb0a467679f0011efb2906a6e528a8d22ef',
                    'script_code': '76a9140ca7deb0a467679f0011efb2906a6e528a8d22ef88ac',
                    'sequence': 4294967295,
                    'sigs_required': 1,
                    'unlocking_script_unsigned': '76a9140ca7deb0a467679f0011efb2906a6e528a8d22ef88ac',
                    'value': 506323064}
                ],
            'locktime': 0,
            'network': 'bitcoin',
            'output_total': 506320402,
            'outputs':
                [{
                    'address': 'bc1qly3xxn4qqfeyy8lakmcc0y6kqg2eu96srjzycu',
                    'output_n': 0,
                    'public_hash': 'f922634ea00272421ffdb6f187935602159e1750',
                    'script': '0014f922634ea00272421ffdb6f187935602159e1750',
                    'value': 506320402}
                ],
            'size': 191,
        }
        srv = ServiceTest(network='bitcoin', min_providers=3)
        srv.gettransaction('299dab85f10c37c6296d4fb10eaa323fb456a5e7ada9adf41389c447daa9c0e4')

        for provider in srv.results:
            print("\nComparing provider %s" % provider)
            self.assertDictEqualExt(srv.results[provider].as_dict(), expected_dict,
                                    ['block_hash', 'block_height', 'spent', 'value', 'flag'])

    def test_service_gettransaction_large_p2sh(self):
        srv = ServiceTest(timeout=TIMEOUT_TEST)
        txid = 'c5b0bce9acfcd32961493a7f1ae1dcfc4371f56ebdcbd23d6125875a845eb33d'
        t = srv.gettransaction(txid)
        self.assertEqual(t.txid, txid)
        self.assertTrue(t.verify())

    def test_service_gettransaction_nulldata(self):
        nulldata_str = b'jK0\nfrom bitcoinlib.transactions import Output\nfrom bitcoinlib.wallets import'
        srv = ServiceTest(timeout=TIMEOUT_TEST)
        t = srv.gettransaction('c6960cd3a688db18550c06b08ed744382cfc9abce63cf6f97981e4b61bba81dc')
        self.assertEqual(t.outputs[0].lock_script, nulldata_str)

    def test_service_gettransaction_segwit_coinbase(self):
        txid = 'ed7e0ecceb6c4d6f10ca935d8dc037921f9855fd46a2e51d82f76dd5ec564a3a'
        srv = ServiceTest(network='bitcoin')
        t = srv.gettransaction(txid)
        self.assertTrue(t.verify())
        self.assertTrue(t.inputs[0].valid)

    def test_service_network_litecoin_legacy(self):
        txid = 'bac36bcf8f0f27752d6fa6909e49d710d95b575fa41cf7802b01291c71b30c21'
        address = 'LVqLipGhyQ1nWtPPc8Xp3zn6JxcU1Hi8eG'
        srv = ServiceTest(network='litecoin_legacy')
        tx = srv.gettransaction(txid)
        print(list(srv.results.keys())[0])
        self.assertEqual(tx.inputs[0].address, '3HbvJBjPxJ1wGYHiUJBkfmZziZohzhQhmy')

        balance = srv.getbalance(address)
        self.assertEqual(balance, 1080900000)

        utxos = srv.getutxos(address)
        self.assertIn(txid, [utxo['tx_hash'] for utxo in utxos])

    def test_service_blockcount(self):
        srv = ServiceTest(min_providers=3)
        n_blocks = None
        for provider in srv.results:
            if n_blocks is not None:
                self.assertAlmostEqual(srv.results[provider], n_blocks, delta=5000,
                                       msg="Provider %s value %d != %d" % (provider, srv.results[provider], n_blocks))
            n_blocks = srv.results[provider]

        # Test Litecoin network
        srv = ServiceTest(min_providers=3, network='litecoin')
        n_blocks = None
        for provider in srv.results:
            if n_blocks is not None:
                self.assertAlmostEqual(srv.results[provider], n_blocks, delta=5000,
                                       msg="Provider %s value %d != %d" % (provider, srv.results[provider], n_blocks))
            n_blocks = srv.results[provider]

        # Test Dash network
        srv = ServiceTest(min_providers=3, network='dash')
        n_blocks = None
        for provider in srv.results:
            if n_blocks is not None:
                self.assertAlmostEqual(srv.results[provider], n_blocks, delta=5000,
                                       msg="Provider %s value %d != %d" % (provider, srv.results[provider], n_blocks))
            n_blocks = srv.results[provider]

    def test_service_max_providers(self):
        srv = ServiceTest(max_providers=1, cache_uri='')
        srv._blockcount = None
        srv.blockcount()
        self.assertEqual(srv.resultcount, 1)

    def test_service_errors(self):
        self.assertRaisesRegexp(ServiceError, "Provider 'unknown_provider' not found in provider definitions",
                                Service, providers='unknown_provider')

    def test_service_mempool(self):
        txid = 'ed7e0ecceb6c4d6f10ca935d8dc037921f9855fd46a2e51d82f76dd5ec564a3a'
        srv = ServiceTest(min_providers=3)
        srv.mempool(txid)
        for provider in srv.results:
            # print("Mempool: Comparing btc provider %s" % provider)
            self.assertListEqual(srv.results[provider], [])

        txid = 'b348f416ff86b28652c2e7f961fbcb1a6099fbb398c6e902e37b680208498d77'
        srv = ServiceTest(min_providers=3, network='litecoin')
        srv.mempool(txid)
        for provider in srv.results:
            # print("Mempool: Comparing ltc provider %s" % provider)
            self.assertListEqual(srv.results[provider], [])

        txid = '15641a37e21a0cf7611a1633954be645512f1ab725a0d5077a9ad0aa0ca20bed'
        srv = ServiceTest(min_providers=3, network='dash')
        srv.mempool(txid)
        for provider in srv.results:
            # print("Mempool: Comparing dash provider %s" % provider)
            self.assertListEqual(srv.results[provider], [])

    # FIXME: Disabled, not enough working providers
    # def test_service_dash(self):
    #     srv = ServiceTest(network='dash')
    #     address = 'XoLTipv6ryWECYu94vbkmDjntAXqNgouTW'
    #     tx_hash = 'f770f05d2b1c63b71b2650227252da06ef226661982c4ee9b136b64f77bbbd0c'
    #     self.assertGreaterEqual(srv.getbalance(address), 50000000000)
    #     self.assertEqual(srv.getutxos(address)[0]['tx_hash'], tx_hash)
    #     self.assertEqual(srv.gettransactions(address)[0].txid, tx_hash)

    def test_service_getblock_height(self):
        srv = ServiceTest(timeout=TIMEOUT_TEST, exclude_providers=['chainso'])
        b = srv.getblock(599999, parse_transactions=True, limit=3)
        print("Test getblock using provider %s" % list(srv.results.keys())[0])
        self.assertEqual(b.height, 599999)
        self.assertEqual(to_hexstring(b.block_hash), '00000000000000000003ecd827f336c6971f6f77a0b9fba362398dd867975645')
        self.assertEqual(to_hexstring(b.merkle_root), 'ca13ce7f21619f73fb5a062696ec06a4427c6ad9e523e7bc1cf5287c137ddcea')
        self.assertEqual(b.nonce_int, 687352075)
        if list(srv.results.keys())[0] != 'blockchair':
            self.assertEqual(to_hexstring(b.prev_block), '00000000000000000006c6a3fdbfe651c87e207ca0109749899a6116baa33bf0')
        self.assertEqual(b.time, 1571443335)
        self.assertEqual(b.tx_count, 3394)
        self.assertEqual(b.version_int, 536928256)
        self.assertEqual(b.bits_int, 387294044)

        t1 = b.transactions[1]
        self.assertEqual(t1.txid, '23d7e1fb5c6749c00cb9f0f0c993e0b92c477f095658a8fdaa07ed706209b288')
        self.assertEqual(t1.size, 246)
        # self.assertEqual(t1.fee, 84000)
        self.assertEqual(t1.locktime, 0)
        self.assertEqual(t1.inputs[0].address, '3Fe8L5dUaRn4uLHQLsfUGSJAT6S23Wtk47')
        self.assertEqual(to_hexstring(t1.inputs[0].prev_hash),
                 'a3cc61610b3a662fd3d3d6b4bf15c6a295cb8246f90e8fe132852f8265a4713b')
        self.assertEqual(t1.outputs[1].address, '3ADMeKFFJB4cNJ3mYNGTsaFv85ad5ZcjHu')
        # self.assertEqual(t1.outputs[1].value, 8638768306)

    def test_service_getblock_parse_tx_paging(self):
        srv = ServiceTest(timeout=TIMEOUT_TEST)
        b = srv.getblock(120000, parse_transactions=True, limit=4, page=2)
        print("Test getblock using provider %s" % list(srv.results.keys())[0])
        self.assertEqual(to_hexstring(b.block_hash),
                         '0000000000000e07595fca57b37fea8522e95e0f6891779cfd34d7e537524471')
        self.assertEqual(b.height, 120000)
        self.assertEqual(to_hexstring(b.merkle_root),
                         '6dbba50b72ad0569c2449090a371516e3865840e905483cac0f54d96944eee28')
        self.assertEqual(b.tx_count, 56)
        self.assertEqual(b.transactions[0].txid, '79b8ea58d3a3d18b583ac7b8fed5b7b06706a5198d4ffc38095d9fc55dc62030')
        self.assertEqual(b.transactions[3].txid, '6182f42ea89a59df3a417f958e1c9bb3f0ea8ee7193cda760b477c4ce09c357c')

    def test_service_getblock_parse_tx_paging_last_page(self):
        srv = ServiceTest(timeout=TIMEOUT_TEST)
        b = srv.getblock(336454, limit=5, page=58)
        self.assertEqual(len(b.transactions), 2)

    def test_service_getblock_litecoin(self):
        srv = ServiceTest(timeout=TIMEOUT_TEST, network='litecoin')
        b = srv.getblock(1000000, parse_transactions=True, limit=2)
        print("Test getblock using provider %s" % list(srv.results.keys())[0])
        self.assertEqual(b.height, 1000000)
        self.assertEqual(to_hexstring(b.block_hash), '8ceae698f0a2d338e39b213eb9c253a91a270ca6451a4d9bba7bf2c9e637dfda')
        self.assertEqual(to_hexstring(b.merkle_root),
                         '8473ff4c3ae380d9d1bf0f1f0b5c389676d3a3877923c0a23e9b21388624c5ab')
        # self.assertEqual(b['nonce'], 282613863)
        if list(srv.results.keys())[0] != 'blockchair.litecoin':
            self.assertEqual(to_hexstring(b.prev_block),
                             'a08b044b936d9e6bdf496a562eb1325fc131fce3cc13a270417d96551054bc30')
        self.assertEqual(b.time, 1464536851)
        self.assertEqual(b.tx_count, 18)
        # self.assertEqual(b['version'], 4)

        if b.transactions and len(b.transactions) > 1:
            t1 = b.transactions[1]
            self.assertEqual(t1.txid, '6e7bfce6aee69312629b1f60afe6dcef02f367207642f2dc380a554c21181eb2')
            self.assertEqual(t1.size, 225)
            self.assertEqual(t1.fee, 200000)
            self.assertEqual(t1.locktime, 0)
            self.assertEqual(t1.inputs[0].address, 'LQW7Swb2rqW1HSNoqcxeQqqyzN9ZrLHux8')
            self.assertEqual(to_hexstring(t1.inputs[0].prev_hash), 'd4668ec9fe59feee65e6800b186a89b8c8fe16fda966139'
                                                                   '3037e4ccb5c439abe')
            self.assertEqual(t1.outputs[1].address, 'LMY9Uc2rLjPwf3trcUvsT7QNs7NeyGcbY3')
            self.assertEqual(t1.outputs[1].value, 10000000000)

    def test_service_getrawblock(self):
        srv = ServiceTest()
        rb = '010000003747479c453ab1a5ca7b44db3a283ebedd8cd68b510ddbeba57e3b5b00000000b76ab5df9ccc1bc5725cbf0a014d689' \
             '9fe6dc15089e61068f4945ac25c970518d3767649ffff001d37e9a13d0101000000010000000000000000000000000000000000' \
             '000000000000000000000000000000ffffffff0804ffff001d02a708ffffffff0100f2052a0100000043410468c05213a45afe3' \
             '9ca018044e77e7c30dfdac7b6ed1fcf7bb9176514c1f3d8da7483979441bce524de1ab4b1223b14aaae7bb1e2f5b0efa26cacd4' \
             '92739d2fb7ac00000000'
        prb = srv.getrawblock(1200)
        self.assertEqual(prb, rb)

    def test_service_isspent(self):
        srv = ServiceTest()
        self.assertFalse(srv.isspent('9b0fc92260312ce44e74ef369f5c66bbb85848f2eddd5a7a1cde251e54ccfdd5', 0))
        self.assertTrue(srv.isspent('b51104386fa9422f04fffaa09f76b69fc17f91238c93e10f58eafaaf671db6d4', 0))

    def test_service_isspent_litecoin(self):
        srv = ServiceTest(network='litecoin')
        self.assertFalse(srv.isspent('a74c2b8c5206a39e2f0becf86f296ab9b3a29259c225471c9dabfbb87b6b5d4a', 1))
        self.assertTrue(srv.isspent('1941cd1a901b3692d2b1d6c337460745c6045c1c4a4a18b0895e5bfc137b6c60', 0))

    def test_service_getinfo(self):
        srv = ServiceTest()
        res = srv.getinfo()
        fields = [k for k, _ in res.items()]
        self.assertListEqual(sorted(fields), ['blockcount', 'chain', 'difficulty', 'hashrate', 'mempool_size'])


class TestServiceCache(unittest.TestCase):

    # TODO: Add mysql and postgres support
    @classmethod
    def setUpClass(cls):
        try:
            if os.path.isfile(DATABASEFILE_CACHE_UNITTESTS2):
                os.remove(DATABASEFILE_CACHE_UNITTESTS2)
        except Exception:
            pass

    def test_service_cache_transactions(self):
        srv = ServiceTest(cache_uri=DATABASEFILE_CACHE_UNITTESTS2)
        address = '1JQ7ybfFBoWhPJpjoihezpeAjd2xv9nXaN'
        # Get 2 transactions, nothing in cache
        res = srv.gettransactions(address, limit=2)
        self.assertGreaterEqual(len(res), 2)
        self.assertEqual(srv.results_cache_n, 0)
        self.assertEqual(res[0].txid, '2ac5145f6e7c47c2ec57ede85ad842b3d9f826feaebf2b00f861359fed3ba4a7')

        # Get 10 transactions, 2 in cache rest from service providers
        res = srv.gettransactions(address, limit=10)
        self.assertEqual(len(res), 10)
        self.assertGreaterEqual(srv.results_cache_n, 2)

        # Get 10 transactions, all from cache
        res = srv.gettransactions(address, limit=10)
        self.assertEqual(len(res), 10)
        self.assertEqual(srv.results_cache_n, 10)
        self.assertEqual(list(srv.results.values()), [])

    def test_service_cache_gettransaction(self):
        srv = ServiceTest(network='litecoin_testnet', cache_uri=DATABASEFILE_CACHE_UNITTESTS2)
        txid = 'b6533d361daac291f64fff32a5c157a4785b423ce36e2eac27117879f93973da'

        t = srv.gettransaction(txid)
        self.assertEqual(srv.results_cache_n, 0)
        self.assertEqual(t.fee, 6680)

        t = srv.gettransaction(txid)
        self.assertEqual(srv.results_cache_n, 1)
        self.assertEqual(t.fee, 6680)

        rawtx = srv.getrawtransaction(txid)
        self.assertEqual(srv.results_cache_n, 1)
        self.assertEqual(rawtx, '0100000001ce18990b7a14afaf00eef179852daf07a7eb0eaaf90ae92393220fcd6fd899a101000000'
                                'db00483045022100bdcd0f4713b35872154c94e65fe65946abf60ef9b6b307479981dbec546b22ce02'
                                '20156d537a93b174392e23360c4336785362de1028c9400ef298252c9006cdb01501483045022100b5'
                                'f876fdd2a6200bed1f15b9eba213e24fb3b9707b07ba8f24ef06bf8e774018022002165eeb777463a6'
                                'e1bceb0d2c29c2ad3aa46b639b744520020e1a028c66bc3c0147522102a6126cabab675799a7f8022d'
                                'c756b40fd5226c8ebe3c279e4f5aebc034b6d48d21039b904498e7702692b72b265dfb0221994bb850'
                                '5ee50837aba768083b3a25aba952aeffffffff0240787d010000000017a914d9f17035fdd2180e4e67'
                                'de2c17d63c218948780a875022d64ead01000017a91494d0071ed66b6584650440fdc6dfc2916a119b'
                                '068700000000')

    def test_service_cache_transactions_after_txid(self):
        # Do not store anything in cache if after_txid is used
        srv = ServiceTest(cache_uri=DATABASEFILE_CACHE_UNITTESTS2, exclude_providers=['chainso'])
        address = '12spqcvLTFhL38oNJDDLfW1GpFGxLdaLCL'
        res = srv.gettransactions(address,
                                  after_txid='5f31da8f47a5bd92a6929179082c559e8acc270a040b19838230aab26309cf2d')
        self.assertGreaterEqual(len(res), 1)
        self.assertGreaterEqual(srv.results_cache_n, 0)
        res = srv.gettransactions(address,
                                  after_txid='5f31da8f47a5bd92a6929179082c559e8acc270a040b19838230aab26309cf2d')
        self.assertGreaterEqual(len(res), 1)
        self.assertGreaterEqual(srv.results_cache_n, 0)
        res = srv.gettransactions(address)
        self.assertGreaterEqual(len(res), 1)
        self.assertGreaterEqual(srv.results_cache_n, 0)
        res = srv.gettransactions(address,
                                  after_txid='5f31da8f47a5bd92a6929179082c559e8acc270a040b19838230aab26309cf2d')
        self.assertGreaterEqual(len(res), 1)
        self.assertGreaterEqual(srv.results_cache_n, 1)

        # Test utxos
        utxos = srv.getutxos(address)
        self.assertGreaterEqual(len(utxos), 1)
        self.assertGreaterEqual(srv.results_cache_n, 1)

    # FIXME: Fails with some providers, needs testing
    def test_service_cache_transaction_coinbase(self):
        srv = ServiceTest(cache_uri=DATABASEFILE_CACHE_UNITTESTS2, exclude_providers=['bitaps', 'bitgo'])
        t = srv.gettransaction('68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13')
        if t:
            self.assertGreaterEqual(srv.results_cache_n, 0)
            srv.gettransaction('68104dbd6819375e7bdf96562f89290b41598df7b002089ecdd3c8d999025b13')
            self.assertGreaterEqual(srv.results_cache_n, 1)

    def test_service_cache_with_latest_tx_query(self):
        srv = ServiceTest(cache_uri=DATABASEFILE_CACHE_UNITTESTS2)
        address = 'bc1qxfrgfhs49d7dtcfzlhp7f7cwsp8zpp60hywp0f'
        after_txid = '13401ad121c8ae91e18b4bb0db5d8f350a2b0b5ddd5ca26165137bf07fefad90'
        srv.gettransaction('4156e78f347e47d2ccdd4a19614d958c6e4502d09a68f63ed0c72691f63a5028')
        txs = srv.gettransactions(address, limit=5)
        self.assertGreaterEqual(len(txs), 5)
        txs = srv.gettransactions(address, after_txid=after_txid, limit=5)
        self.assertGreaterEqual(len(txs), 5)

    def test_service_cache_correctly_update_spent_info(self):
        srv = ServiceTest(cache_uri=DATABASEFILE_CACHE_UNITTESTS2, exclude_providers=['chainso'])
        srv.gettransactions('1KoAvaL3wfpcNvGCQYkqFJG9Ccqm52sZHa', limit=1)
        txs = srv.gettransactions('1KoAvaL3wfpcNvGCQYkqFJG9Ccqm52sZHa')
        print(srv.results)
        self.assertTrue(txs[0].outputs[0].spent)

    def test_service_cache_getblock_hash(self):

        def check_block_128594(b):
            self.assertEqual(b.height, 128594)
            self.assertEqual(to_hexstring(b.block_hash),
                             '0000000000001a7dcac3c01bf10c5d5fe53dc8cc4b9c94001662e9d7bd36f6cc')
            self.assertEqual(to_hexstring(b.merkle_root),
                             '36cbe8252102410779271e8e325183f63ed9c18534ebc13ef4220f57ae2a9c17')
            self.assertEqual(b.nonce_int, 423727070)
            self.assertEqual(to_hexstring(b.prev_block),
                             '000000000000166d87b745a1d2af24f51c4b98021f8c027954711ce45f2024b3')
            self.assertEqual(b.time, 1307204137)
            self.assertEqual(b.tx_count, 93)
            self.assertEqual(b.version_int, 1)
            self.assertEqual(b.transactions[0].txid, '85249ed3a9526b980e9b7c37b0be9a8fb6bd4462418d7dd808ad702a00777577')

        srv = ServiceTest(cache_uri=DATABASEFILE_CACHE_UNITTESTS2,
                          exclude_providers=['chainso', 'blockchair', 'blockchaininfo'])  # Those providers return incomplete results
        b = srv.getblock('0000000000001a7dcac3c01bf10c5d5fe53dc8cc4b9c94001662e9d7bd36f6cc', limit=1)
        print("Test getblock with hash using provider %s" % list(srv.results.keys())[0])
        check_block_128594(b)
        self.assertEqual(srv.results_cache_n, 0)

        # Now retrieve from cache
        bc = srv.getblock('0000000000001a7dcac3c01bf10c5d5fe53dc8cc4b9c94001662e9d7bd36f6cc', limit=1)
        self.assertEqual(srv.results_cache_n, 1)
        check_block_128594(bc)

    def test_service_cache_disabled(self):
        srv = ServiceTest(cache_uri='')
        srv.gettransaction('eeb0c4bae63970f2ece284bcc871098942d5aff1d960398e523a9b339d25f73e')
        self.assertEqual(srv.results_cache_n, 0)
        srv.gettransaction('eeb0c4bae63970f2ece284bcc871098942d5aff1d960398e523a9b339d25f73e')
        self.assertEqual(srv.results_cache_n, 0)
