FROM kalilinux/kali-last-release
MAINTAINER Cryp Toon <info@1200wd.com>

WORKDIR /code

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y \
    software-properties-common git \
    build-essential python3-dev libgmp3-dev python3-pip

#ENV TZ=Europe/Brussels
#RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get install -y postgresql postgresql-contrib default-libmysqlclient-dev default-mysql-server pkg-config libpq-dev
RUN apt-get clean

RUN git clone https://github.com/1200wd/bitcoinlib.git

WORKDIR /code/bitcoinlib
RUN python3 -m pip install .[dev]

CMD python3 -m unittest
