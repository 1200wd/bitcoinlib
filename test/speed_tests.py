# -*- coding: utf-8 -*-
#
#    bitcoinlib speed_tests
#    Copyright (C) 2016 September 
#    1200 Web Development
#    http://1200wd.com/
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

keypairs = {}


def test_speed_generate(nkeys):
    for n in range(0, nkeys):
        keypairs.update({PrivateKey(): None})

def test_speed_priv2pub():
    for k in keypairs.keys():
        keypairs[k] = k.get_public()

def test_speed_pub2addr():
    for pub in keypairs.values():
        pub.get_address()

def test_speed_pubkey_func(func='get_hex'):
    for pub in keypairs.values():
        try:
            eval("pub.%s()" % func)
        except Exception, e:
            print "EXCEPTION %s" % e

def test_speed_privkey_func(func='get_hex'):
    for priv in keypairs.keys():
        try:
            eval("priv.%s()" % func)
        except Exception, e:
            print "EXCEPTION %s" % e


if __name__ == '__main__':
    iterations = 10
    print "==== Speedtests bitcoinlib ===="
    print "\nGenerate %d private keys" % iterations
    duration = timeit.timeit(
        'test_speed_generate(%d)' % iterations, number=1,
        setup='from __main__ import test_speed_generate')
    print "- in %f ms" % (duration * 1000)

    print "\nConvert %d private keys to public keys" % iterations
    duration = timeit.timeit(
        'test_speed_priv2pub()', number=1,
        setup='from __main__ import test_speed_priv2pub')
    print "- in %f ms" % (duration * 1000)

    for k in keypairs.keys():
        pub = PublicKey(keypairs[k])
        keypairs[k] = pub

    print "\nConvert %d public keys to bitcoin address" % iterations
    duration = timeit.timeit(
        'test_speed_pub2addr()', number=1,
        setup='from __main__ import test_speed_pub2addr')
    print "- in %f ms" % (duration * 1000)

    print "\n\n== Test all Private key functions =="
    functions = PrivateKey.__dict__
    for func in functions:
        if func[0] == '_'  or func == 'get_public':
            continue
        print "\nTest PrivateKey function: %s()" % func
        duration = timeit.timeit(
            'test_speed_privkey_func("%s")' % func, number=1,
            setup='from __main__ import test_speed_privkey_func')
        print "- in %f ms" % (duration * 1000)

    print "\n\n== Test all Public key functions =="
    functions = PublicKey.__dict__
    for func in functions:
        if func[0] == '_':
            continue
        print "\nTest PublicKey function: %s()" % func
        duration = timeit.timeit(
            'test_speed_pubkey_func("%s")' % func, number=1,
            setup='from __main__ import test_speed_pubkey_func')
        print "- in %f ms" % (duration * 1000)
