FROM clickhouse/clickhouse-server:latest

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    libcurl4 \
    libcurl4-openssl-dev \
    tmux \
    vim
