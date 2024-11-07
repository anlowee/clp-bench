#!/usr/bin/env bash

clp_s_binary=/home/assets/clp-s
data_path=/home/archives

"${clp_s_binary}" c --timestamp-key 't.$date' --target-encoded-size 268435456 "${data_path}" "$1"
