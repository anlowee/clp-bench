#!/usr/bin/env bash

set -e

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
container_name="elasticsearch-clp-bench"

docker build \
    --tag "$container_name" \
    "$script_dir" \
    --file "${script_dir}/Dockerfile"
