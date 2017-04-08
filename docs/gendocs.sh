rm ~/code/bitcoinlib/docs/source/*
sphinx-apidoc -o source/ ../bitcoinlib --separate
make html

