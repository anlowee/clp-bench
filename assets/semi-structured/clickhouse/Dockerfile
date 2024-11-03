FROM ubuntu:latest

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    gpg

## Import ClickHouse key
RUN curl -fsSL 'https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key' | gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg] https://packages.clickhouse.com/deb stable main" | tee \
    /etc/apt/sources.list.d/clickhouse.list

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-venv \
    tmux \
    vim \
    libcurl4 \
    libcurl4-openssl-dev \
    clickhouse-server=23.3.1.2823 clickhouse-client=23.3.1.2823 clickhouse-common-static=23.3.1.2823 \
    python3-pip

RUN pip install elasticsearch requests numpy matplotlib
