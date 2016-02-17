# -*- coding: utf-8 -*-
#
#    bitcoinlib - unit_tests.py
#    Copyright (C) 2016 February 
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

from bitcoinlib import *

def test_main():
    # - Test 1 - Method: change_base(input, base_from, base_to, min_lenght=0)
    test_set = {
        ('F1', 16, '11110001', 2, 0),
        ('a3', 16, '10100011', 2, 0),
        ('11110001', 2, 'f1', 16, 0),
        ('f001', 16, '61441', 10, 0),
        (61441, 10, 'f001', 16, 0),
        ('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, '5283658277747592673868818217239156372404875337009783985623', 10, 0),
        ('1LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, '\xd7{\xf7b\x8c\x19\xe6\x99\x01\r)xz)\xaf\xcf\x8e\x92\xadZ\x05=U\xd7', 256, 0),
        ('5283658277747592673868818217239156372404875337009783985623', 10, 'LeNnaRtV52nNtZXvtw6PaGKpk46hU1Xmx', 58, 0),
        (3, 10, '0011', 2, 4),
    }
    # for var in test_set:
    #     result = change_base(var[0], var[1], var[3], var[4])
    #     print "%s base %s = %s base %s  ==>  Result: %s" % (repr(var[0]), var[1], repr(var[2]), var[3], "Ok" if result==var[2] else "ERROR!!! " + repr(result))

    # - Test 2 - PrivateKey class
    # privatekey_hex = '0C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D'
    # k = PrivateKey(privatekey_hex)
    # print "PrivateKey DEC test result: %r (%s)" % (k.get_dec()=='5500171714335001507730457227127633683517613019341760098818554179534751705629', k.get_dec())
    # print "PrivateKey HEX test result: %r (%s)" % (k.get_hex()=='0c28fca386c7a227600b2fe50b7cae11ec86d3bf1fbe471be89827e19d72aa1d', k.get_hex())
    # print "PrivateKey BIN test result: %r (%s)" % (k.get_bit()=='0000110000101000111111001010001110000110110001111010001000100111011000000000101100101111111001010000101101111100101011100001000111101100100001101101001110111111000111111011111001000111000110111110100010011000001001111110000110011101011100101010101000011101', k.get_bit())
    # print "PrivateKey WIF test result: %r (%s)" % (k.get_wif(False)=='5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ', k.get_wif(False))
    # print "PrivateKey WIF compressed test result: %r (%s)" % (k.get_wif()=='KwdMAjGmerYanjeui5SHS7JkmpZvVipYvB2LJGU1ZxJwYvP98617', k.get_wif())
    # k.import_hex('56c05ebf6e8e9c4719d87c12e915cf41125fce719fc164539c2d9beebc3d220f')
    # print "PritateKey import HEX test, passed: %r" % (k.get_wif()=='Kz8LvfZqTvviTrFF27u9wBwHFhZHifnAp6WTzfqtSaFPq51iogZS')
    # k.import_wif('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyTX')
    # print "PrivateKey import WIF test, passed: %r" % (k.get_hex()=='88ccb90221d9b44df8dd317307de2d6019c9c7448dccaa1e45bae77e5a022b7b')
    # try:
    #     k.import_wif('L1odb1uUozbfK2NrsMyhJfvRsxGM2AxixgPL8vG9BUBnE6W1VyT2') # test with invalid checksum
    #     print "ERROR: Should not accept WIF key with invalid checksum"
    # except ValueError as err:
    #     if err.args[0] == "Invalid checksum, not a valid WIF compressed key":
    #         print "PrivateKey validation Passed"
    #     else:
    #         print "ERROR: Should not accept WIF key with invalid checksum"

    # - Test 3 - PublicKey class
    publickey_hex = '0450863AD64A87AE8A2FE83C1AF1A8403CB53F53E486D8511DAD8A04887E5B23522CD470243453A299FA9E77237716103ABC11A1DF38855ED6F2EE187E9C582BA6'
    K = PublicKey(publickey_hex)
    print K.get_point()
    print K.get_address()


if __name__ == '__main__':
    test_main()
