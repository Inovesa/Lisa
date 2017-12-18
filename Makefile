CYTHON = cython3
CYTHON_FLAGS = -3
CC=gcc
CC_PARAMS = -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing -I/usr/include/python3.5

.ONESHELL:

default: all

all: plots data file config

plots: Lisa/plots/plots.py
	@echo "Compiling plots.py"
	@cd Lisa/plots
	@cp plots.py plots_cython.py  # do this to avoid some problem with init of module or so?
	@../../add_hash.sh plots
	@$(CYTHON) $(CYTHON_FLAGS) plots_cython.py
	@$(CC) $(CC_PARAMS) -o plots_cython.so plots_cython.c
	@rm plots_cython.py
	@rm -rf __pycache__
	@rm -rf plots_cython.c

data: Lisa/data/data.py
	@echo "Compiling data.py"
	@cd Lisa/data
	@cp data.py data_cython.py  # do this to avoid some problem with init of module or so?
	@../../add_hash.sh data
	@$(CYTHON) $(CYTHON_FLAGS) data_cython.py
	@$(CC) $(CC_PARAMS) -o data_cython.so data_cython.c
	@rm data_cython.py
	@rm -rf __pycache__
	@rm -rf data_cython.c

file: Lisa/data/file.py
	@echo "Compiling file.py"
	@cd Lisa/data
	@cp file.py file_cython.py  # do this to avoid some problem with init of module or so?
	@../../add_hash.sh file
	@$(CYTHON) $(CYTHON_FLAGS) file_cython.py
	@$(CC) $(CC_PARAMS) -o file_cython.so file_cython.c
	@rm file_cython.py
	@rm -rf __pycache__
	@rm -rf file_cython.c

config: Lisa/plots/config.py
	@echo "Compiling config.py"
	@cd Lisa/plots
	@cp config.py config_cython.py  # do this to avoid some problem with init of module or so?
	@../../add_hash.sh config
	@$(CYTHON) $(CYTHON_FLAGS) config_cython.py
	@$(CC) $(CC_PARAMS) -o config_cython.so config_cython.c
	@rm config_cython.py
	@rm -rf __pycache__
	@rm -rf config_cython.c

