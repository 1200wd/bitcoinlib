FROM linuxmintd/mint22-amd64
MAINTAINER Cryp Toon <info@1200wd.com>

WORKDIR /code

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y \
    software-properties-common git \
    build-essential python3-dev libgmp3-dev python3-pip python3.12-venv

ENV TZ=Europe/Brussels
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get install -y postgresql postgresql-contrib mariadb-server libpq-dev pkg-config default-libmysqlclient-dev
RUN apt-get clean

RUN git clone https://github.com/1200wd/bitcoinlib.git

WORKDIR /code/bitcoinlib
RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/python3 -m pip install .[dev]

CMD /opt/venv/bin/python3 -m unittest
