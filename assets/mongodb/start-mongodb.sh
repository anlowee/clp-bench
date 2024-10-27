#!/bin/bash

collection_name=mongodb_clp_bench

# Check if MongoDB is installed
if ! command -v mongod &> /dev/null; then
    exit 1
fi

# Create the data directory if it doesn't exist
mkdir -p /data/db

# Start MongoDB with specified options
mongod --fork --syslog --wiredTigerCollectionBlockCompressor zstd --zstdDefaultCompressionLevel 3 > /dev/null 2>&1

# Wait for 2 seconds to ensure MongoDB starts
sleep 2

if [ "$1" == "--drop-if-existed" ]; then
    mongosh logs --eval "db.${collection_name}.drop()" > /dev/null 2>&1
fi