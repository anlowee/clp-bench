#!/bin/bash

set -e
set -u

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
container_name="mongodb-clp-bench"

docker run \
	--privileged \
	--rm \
    -it \
	--workdir /home \
	--network host \
	--name "$container_name" \
	--mount "type=bind,src=$script_dir,dst=/home/assets" \
	--mount "type=bind,src=$1,dst=/home/datasets" \
    --mount "type=bind,src=$2,dst=/data/db" \
	"$container_name" \
	/bin/bash -l