# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#
#    EXAMPLES - Service - Measure execution time per service provider for simple blockcount query
#
#    © 2021 - 2024 December - 1200 Web Development <http://1200wd.com/>
#

from bitcoinlib.services.services import Service


for provider in Service().providers:
    try:
        srv = Service(provider_name=provider, cache_uri='')
    except:
        pass
    else:
        print(provider, srv.blockcount(), srv.execution_time)