#!/usr/bin/env bash

set -e

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
container_name="clickhouse-clp-bench"

docker build \
    --tag "$container_name" \
    "$script_dir"
