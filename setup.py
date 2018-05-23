# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    PyPi Setup Tool
#    © 2018 April - 1200 Web Development <http://1200wd.com/>
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

from setuptools import setup
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    readmetxt = f.read()

kwargs = {}

install_requires = [
      'requests==2.18.4',
      'ecdsa==0.13',
      'pbkdf2==1.3',
      'pyaes==1.6.1',
      'scrypt==0.8.6',
      'SQLAlchemy==1.2.5'
]
if sys.version_info < (3, 4):
    install_requires.append('enum34')
kwargs['install_requires'] = install_requires

setup(
      name='bitcoinlib',
      version='0.3.36',
      description='Bitcoin and Other cryptocurrency Library',
      long_description=readmetxt,
      classifiers=[
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
            'Intended Audience :: Developers',
            'Intended Audience :: Financial and Insurance Industry',
            'Intended Audience :: Information Technology',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Security :: Cryptography',
            'Topic :: Office/Business :: Financial :: Accounting',
      ],
      url='http://github.com/1200wd/bitcoinlib',
      author='1200wd',
      author_email='info@1200wd.com',
      license='GNU3',
      packages=['bitcoinlib'],
      entry_points={
          'console_scripts': ['cli-wallet=bitcoinlib.tools.cli_wallet:main']
      },
      test_suite='tests',
      include_package_data=True,
      keywords='bitcoin library cryptocurrency tools wallet crypto keys',
      zip_safe=False,
      **kwargs
)
