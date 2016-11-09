# -*- coding: utf-8 -*-
#
#    bitcoinlib - bitcoind_config.py
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

def read_config_file(filename):
    """
    Read a simple ``'='``-delimited config file.
    Raises :const:`IOError` if unable to open file, or :const:`ValueError`
    if an parse error occurs.
    """
    f = open(filename)
    try:
        cfg = {}
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    (key, value) = line.split('=', 1)
                    cfg[key] = value
                except ValueError:
                    pass  # Happens when line has no '=', ignore
    finally:
        f.close()
    return cfg


def read_default_config(filename=None):
    """
    Read bitcoin default configuration from the current user's home directory.

    Arguments:

    - `filename`: Path to a configuration file in a non-standard location (optional)
    """
    if filename is None:
        import os
        import platform
        home = os.getenv("HOME")
        if not home:
            raise IOError("Home directory not defined, don't know where to look for config file")

        if platform.system() == "Darwin":
            location = 'Library/Application Support/Bitcoin/bitcoin.conf'
        else:
            location = '.bitcoin/bitcoin.conf'
        filename = os.path.join(home, location)

    elif filename.startswith("~"):
        import os
        filename = os.path.expanduser(filename)

    try:
        return read_config_file(filename)
    except (IOError, ValueError):
        pass  # Cannot read config file, ignore
