#!/usr/bin/env bash
COMPILE_TIME_HASH=($(md5sum $1.py))  # array assignment such that compile_time_hash only has the first entry which is the hash
echo -e "cython_compile_hash = '$COMPILE_TIME_HASH'\n" >> $1_cython.py
