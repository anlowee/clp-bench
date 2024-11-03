FROM ghcr.io/y-scope/clp/clp-core-dependencies-x86-ubuntu-jammy:main

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    vim \
    python3-venv \
    sqlite3 \
    tmux \
    htop \
    rsync \
    jq
