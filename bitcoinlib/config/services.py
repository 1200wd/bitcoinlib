# -*- coding: utf-8 -*-
#
#    bitcoinlib - Compact Python Bitcoin Library
#    Service Provider definitions
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

serviceproviders = {
    'bitcoin': {
        'blockexplorer': ('BlockExplorerClient', 'https://blockexplorer.com/api/'),
        'blockr': ('BlockrClient', 'http://btc.blockr.io/api/v1/'),
    },
    'testnet': {
        'blockexplorer': ('BlockExplorerClient', 'https://testnet3.blockexplorer.com/api/'),
        'blockr': ('BlockrClient', 'http://tbtc.blockr.io/api/v1/'),
    },
    'litecoin': {
        'blockr': ('BlockrClient', 'http://ltc.blockr.io/api/v1/'),
    }
}
