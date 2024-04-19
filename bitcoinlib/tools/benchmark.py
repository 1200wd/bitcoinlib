# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    Benchmark - Test library speed
#    © 2020 - 2024 Februari - 1200 Web Development <http://1200wd.com/>
#


import time
import random
import json
from bitcoinlib.keys import *
from bitcoinlib.wallets import *
from bitcoinlib.transactions import *
from bitcoinlib.mnemonic import *

try:
    wallet_method = Wallet
except NameError:
    wallet_method = HDWallet

try:
    BITCOINLIB_VERSION
except:
    BITCOINLIB_VERSION = '0.4.10 and below'


class Benchmark:

    def __init__(self):
        wallet_delete_if_exists('wallet_multisig_huge', force=True)
        wallet_delete_if_exists('wallet_large', force=True)

    @staticmethod
    def benchmark_bip38():
        # Encrypt and decrypt BIP38 key
        k = Key()
        if BITCOINLIB_VERSION > '0.6.0':
            bip38_key = k.encrypt(password='satoshi')
        else:
            bip38_key = k.bip38_encrypt('satoshi')
        if BITCOINLIB_VERSION > '0.5.1':
            k2 = Key(bip38_key, password='satoshi')
        else:
            k2 = Key(bip38_key, passphrase='satoshi')
        assert(k.wif() == k2.wif())

    @staticmethod
    def benchmark_create_key():
        for i in range(0, 1000):
            k = Key()

    @staticmethod
    def benchmark_create_hdkey():
        for i in range(0, 1000):
            k = HDKey()

    @staticmethod
    def benchmark_encoding():
        # Convert very large numbers to and from base58 / bech32
        pk = random.randint(0, 10 ** 4000)
        large_b58 = change_base(pk, 10, 58, 6000)
        large_b32 = change_base(pk, 10, 32, 7000)
        assert(change_base(large_b58, 58, 10) == pk)
        assert(change_base(large_b32, 32, 10) == pk)

    @staticmethod
    def benchmark_mnemonic():
        # Generate Mnemonic passphrases
        for i in range(100):
            m = Mnemonic().generate(256)
            Mnemonic().to_entropy(m, includes_checksum=False)

    @staticmethod
    def benchmark_transactions():
        # Deserialize transaction and verify
        raw_hex = "02000000000101b7006080d9d1d2928f70be1140d4af199d6ba4f9a7b0096b6461d7d4d16a96470600000000fdffffff11205c0600000000001976a91416e7a7d921edff13eaf5831eefd6aaca5728d7fb88acad960700000000001600140dd69a4ce74f03342cd46748fc40a877c7ccef0e808b08000000000017a914bd27a59ba92179389515ecea6b87824a42e002ee873efb0b0000000000160014b4a3a8da611b66123c19408c289faa04c71818d178b21100000000001976a914496609abfa498b6edbbf83e93fd45c1934e05b9888ac34d01900000000001976a9144d1ce518b35e19f413963172bd2c84bd90f8f23488ace06e1f00000000001976a914440d99e9e2879c1b0f8e9a1d5a288a4b6cfcc15288acff762c000000000016001401429b4b17e97f8d4419b4594ffe9f54e85037e7241e4500000000001976a9146083df8eb862f759ea0f1c04d3f13a3dfa9aff5888acf09056000000000017a9144fcaf4edac9da6890c09a819d0d7b8f300edbe478740fa97000000000017a9147431dcb6061217b0c80c6fa0c0256c1221d74b4a87208e9c000000000017a914a3e1e764fefa92fc5befa179b2b80afd5a9c20bd87ecf09f000000000017a9142ca7dc95f76530521a1edfc439586866997a14828754900101000000001976a9142e6c1941e2f9c47b535d0cf5dc4be5038e02336588acc0996d01000000001976a91492268fb9d7b8a3c825a4efc486a0679dbf006fae88acd790ae0300000000160014fe350625e2887e9bc984a69a7a4f60439e7ee7152182c81300000000160014f60834ef165253c571b11ce9fa74e46692fc5ec10248304502210081cb31e1b53a36409743e7c785e00d5df7505ca2373a1e652fec91f00c15746b02203167d7cc1fa43e16d411c620b90d9516cddac31d9e44e452651f50c950dc94150121026e5628506ecd33242e5ceb5fdafe4d3066b5c0f159b3c05a621ef65f177ea28600000000"
        for i in range(100):
            if BITCOINLIB_VERSION >= '0.5.3':
                t = Transaction.parse(raw_hex)
            else:
                t = Transaction.import_raw(raw_hex)
            t.inputs[0].value = 485636658
            t.verify()
            assert(t.verified is True)

    @staticmethod
    def benchmark_wallets_multisig():
        # Create large multisig wallet
        network = 'bitcoinlib_test'
        n_keys = 8
        sigs_req = 5
        key_list = [HDKey(network=network) for _ in range(0, n_keys)]
        pk_n = random.randint(0, n_keys - 1)
        key_list_cosigners = [k.public_master(multisig=True) for k in key_list if k is not key_list[pk_n]]
        key_list_wallet = [key_list[pk_n]] + key_list_cosigners
        w = wallet_method.create('wallet_multisig_huge', keys=key_list_wallet, sigs_required=sigs_req, network=network)

        if BITCOINLIB_VERSION >= '0.5.0':
            w.get_keys(number_of_keys=2)
        else:
            w.get_key(number_of_keys=2)
        w.utxos_update()
        to_address = HDKey(network=network).address()
        if BITCOINLIB_VERSION >= '0.7.0':
            t = w.sweep(to_address, broadcast=False)
        else:
            t = w.sweep(to_address, offline=True)
        key_pool = [i for i in range(0, n_keys - 1) if i != pk_n]
        while len(t.inputs[0].signatures) < sigs_req:
            co_id = random.choice(key_pool)
            t.sign(key_list[co_id])
            key_pool.remove(co_id)
        assert(t.verify() is True)

    @staticmethod
    def benchmark_wallets_large():
        # Create large wallet with many keys
        network = 'bitcoinlib_test'
        n_keys = 250
        w = wallet_method.create('wallet_large', network=network)
        if BITCOINLIB_VERSION >= '0.5.0':
            w.get_keys(number_of_keys=n_keys)
        else:
            w.get_key(number_of_keys=n_keys)

    def run(self, only_dict=False):
        start_time = time.time()
        bench_dict = {'version': BITCOINLIB_VERSION}
        only_dict or print("Running BitcoinLib benchmarks speed test for version %s" % BITCOINLIB_VERSION)

        benchmark_methods = [m for m in dir(self) if callable(getattr(self, m)) if m.startswith('benchmark_')]
        for method in benchmark_methods:
            m_start_time = time.time()
            try:
                getattr(self, method)()
            except Exception as e:
                only_dict or print("Error occured running test: %s" % str(e))
                m_duration = 0
            else:
                m_duration = time.time() - m_start_time
            only_dict or print("%s, %.5f seconds" % (method, m_duration))
            bench_dict.update({method: m_duration})

        duration = time.time() - start_time
        only_dict or print("Total running time: %.5f seconds" % duration)
        bench_dict.update({'duration': duration})
        return bench_dict


if __name__ == '__main__':
    res = Benchmark().run(bool(sys.argv[1:]))
    print(json.dumps(res))
