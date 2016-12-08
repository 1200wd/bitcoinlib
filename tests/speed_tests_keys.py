# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Various Speed Tests
#    © 2016 November - 1200 Web Development <http://1200wd.com/>
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

from bitcoinlib.keys import *
import timeit

ITERATIONS = 10
keypairs = {}
test_results = []


def test_speed_generate(nkeys):
    for n in range(0, nkeys):
        keypairs.update({Key(): None})


def test_speed_priv2pub():
    for k in keypairs.keys():
        keypairs[k] = k.public()


def test_speed_pub2addr():
    for pub in keypairs.values():
        pub.address()


def test_speed_pubkey_func(func='hex'):
    for pub in keypairs.values():
        try:
            eval("pub.%s()" % func)
        except Exception as e:
            print("EXCEPTION %s" % e)


def test_speed_privkey_func(func='hex'):
    for priv in keypairs.keys():
        try:
            eval("priv.%s()" % func)
        except Exception as e:
            print("EXCEPTION %s" % e)


def add_test_result(test, func='', time=0):
    print(test)
    test_results.append({
        'test': test,
        'function': func,
        'time': time,
        'timems': time * 1000,
        'iterations': ITERATIONS,
    })


if __name__ == '__main__':
    print("==== Speedtests bitcoinlib ====")
    testname = "Generate %d private keys" % ITERATIONS
    duration = timeit.timeit(
        'test_speed_generate(%d)' % ITERATIONS, number=1,
        setup='from __main__ import test_speed_generate')
    add_test_result(testname, time=duration)

    testname = "Convert %d private keys to public keys" % ITERATIONS
    duration = timeit.timeit(
        'test_speed_priv2pub()', number=1,
        setup='from __main__ import test_speed_priv2pub')
    add_test_result(testname, time=duration)

    for k in keypairs.keys():
        pub = Key(keypairs[k])
        keypairs[k] = pub

    testname = "Convert %d public keys to bitcoin address" % ITERATIONS
    duration = timeit.timeit(
        'test_speed_pub2addr()', number=1,
        setup='from __main__ import test_speed_pub2addr')
    add_test_result(testname, time=duration)

    print("== Test all Private key functions ==")
    functions = Key.__dict__
    for func in functions:
        if func[0] == '_' or func == 'public':
            continue
        testname = "Test PrivateKey function: %s()" % func
        duration = timeit.timeit(
            'test_speed_privkey_func("%s")' % func, number=1,
            setup='from __main__ import test_speed_privkey_func')
        add_test_result(testname, time=duration, func=func)

    print("== Test all Public key functions ==")
    functions = Key.__dict__
    for func in functions:
        if func[0] == '_':
            continue
        testname = "Test PublicKey function: %s()" % func
        duration = timeit.timeit(
            'test_speed_pubkey_func("%s")' % func, number=1,
            setup='from __main__ import test_speed_pubkey_func')
        add_test_result(testname, time=duration, func=func)

    print("\n\n{:<50} {:<16}".format('Test', 'Milliseconds'))
    for t in test_results:
        print("{:<50} {:10.3f} ms".format(t['test'], t['timems']))
