FROM ubuntu:jammy

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    wget \
    curl \
    gnupg

# Import MongoDB public GPG key and create MongoDB apt source list
RUN curl -fsSL 'https://www.mongodb.org/static/pgp/server-6.0.asc' \
    | gpg --dearmor -o /usr/share/keyrings/mongodb-server-6.0.gpg \
    && echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ]" \
    "https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" \
    | tee /etc/apt/sources.list.d/mongodb-org-6.0.list

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    mongodb-org=6.0.19 \
    mongodb-org-database=6.0.19 \
    mongodb-org-server=6.0.19 \
    mongodb-org-mongos=6.0.19 \
    mongodb-org-tools=6.0.19 \
    python3-venv \
    tmux \
    vim \
    libcurl4 \
    libcurl4-openssl-dev \
    python3-pip

RUN pip install pymongo requests numpy matplotlib