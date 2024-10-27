#!/bin/bash

collection_name=mongodb_clp_bench

mongoexport --quiet --db logs --collection "${collection_name}" --query "'$1'"