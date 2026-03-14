FROM alpine:latest
LABEL org.opencontainers.image.authors="info@1200wd.com"

WORKDIR /code

RUN apk add --no-cache git python3-dev gmp-dev python3 py3-pip gcc musl-dev libpq-dev
RUN apk add --no-cache postgresql postgresql-contrib mariadb-dev mysql-client

RUN git clone https://github.com/1200wd/bitcoinlib.git

WORKDIR /code/bitcoinlib
RUN python3 -m pip install .[dev] --break-system-packages

CMD ["python3", "-m", "unittest"]
