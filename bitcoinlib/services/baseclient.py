# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Base Client
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

import requests
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
import json
from bitcoinlib.config.services import serviceproviders


class ClientError(Exception):
    pass


class BaseClient(object):

    def __init__(self, network, provider):
        try:
            self.network = network
            self.provider = provider
            self.url = serviceproviders[network][provider][1]
            self.resp = None
        except:
            raise Warning("This Network is not supported by %s Client" % provider)

    def request(self, url, variables):
        if variables:
            self.url += '?' + urlencode(variables)
        print(url)
        self.resp = requests.get(url)
        if self.resp.status_code != 200:
            raise ClientError("Error connecting to %s on url %s, response [%d] %s" %
                              (self.provider, url, self.resp.status_code, self.resp.text))
        return json.loads(self.resp.text)
