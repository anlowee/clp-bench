#!/usr/bin/env bash

datasets_path=/home/datasets
grep -r "$1" "${datasets_path}" | wc -l
