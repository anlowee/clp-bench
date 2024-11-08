#!/usr/bin/env bash

collection_name=mongodb_clp_bench

mongoimport \
    --numInsertionWorkers=1 \
    --db logs \
    --collection "${collection_name}" \
    --file "$1" \
    >/dev/null 2>&1
