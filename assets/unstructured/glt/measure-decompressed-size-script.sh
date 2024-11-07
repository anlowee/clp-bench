#!/usr/bin/env bash

du "$1" -bc | awk 'END {print $1}'
