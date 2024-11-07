#!/usr/bin/env bash

glt_binary=/home/assets/glt
data_path=/home/archives

"${glt_binary}" s "${data_path}" "$1" | wc -l
