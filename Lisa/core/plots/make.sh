cp "$1.py" "$1_cython.py"  # do this to avoid some problem with init of module or so?
cython3 -3 $1_cython.py
gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing -I/usr/include/python3.5 -o $1_cython.so $1_cython.c
rm $1_cython.py
rm -rf __pycache__
rm $1_cython.c
