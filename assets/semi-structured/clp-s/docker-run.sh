#!/usr/bin/env bash

set -e
set -u

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
container_name="clp-clp-bench"

docker run \
    --privileged \
    -it \
    --rm \
    --workdir /home \
    --network host \
    --name "$container_name" \
    --mount "type=bind,src=$script_dir,dst=/home/assets" \
    --mount "type=bind,src=$1,dst=/home/datasets" \
    "$container_name" \
    /bin/bash -l
