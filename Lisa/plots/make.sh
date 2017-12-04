cp "$1.py" "$1_cython.py"  # do this to avoid some problem with init of module or so?
COMPILE_TIME_HASH=($(md5sum $1.py))  # array assignment such that compile_time_hash only has the first entry which is the hash
echo -e "cython_compile_hash = '$COMPILE_TIME_HASH'\n" >> $1"_cython.py"
cython3 -3 $1_cython.py
gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing -I/usr/include/python3.5 -o $1_cython.so $1_cython.c
rm $1_cython.py
rm -rf __pycache__
rm $1_cython.c
