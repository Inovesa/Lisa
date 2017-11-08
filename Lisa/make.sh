#!/bin/bash
cd core
echo "Making file_cython"
./make.sh file
echo "Making data_cython"
./make.sh data
cd plots
echo "Making plots_cython"
./make.sh plots
