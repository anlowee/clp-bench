#!/usr/bin/env bash

collection_name=mongodb_clp_bench

sleep 20
mongosh logs --eval "'db.${collection_name}.storageSize().toString()'"
