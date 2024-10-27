#!/bin/bash

collection_name=mongodb_clp_bench

# Check if the first argument is '--size-only'
if [ "$1" == "--size-only" ]; then
    # Execute only the second command
    mongosh logs --eval "'db.${collection_name}.storageSize()'"
else
    # Execute only the first command
    mongoimport --numInsertionWorkers=1 --db logs --collection "${collection_name}" --file "$1" > /dev/null 2>&1
fi