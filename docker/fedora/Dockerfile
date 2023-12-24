FROM fedora:latest
MAINTAINER Cryp Toon <info@1200wd.com>

WORKDIR /code

RUN yum update -y; yum clean all

RUN yum install -y python3-devel gmp-devel python3-pip git gcc

RUN yum install -y postgresql postgresql-server mariadb-server libpq-devel mariadb-devel

RUN git clone https://github.com/1200wd/bitcoinlib.git

WORKDIR /code/bitcoinlib
RUN python3 -m pip install .[dev]

CMD python3 -m unittest
