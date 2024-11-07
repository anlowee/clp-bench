#!/usr/bin/env bash

bash -c "du $1 -bc" | awk 'END {print $1}'
