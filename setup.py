from setuptools import setup, find_packages
import os
import shutil
import subprocess

VERSION=open("Lisa/VERSION", 'r').readline().strip()

requires = [
        'cython',
        'matplotlib',
        'numpy',
        'h5py',
        'moviepy',
        'unittest2'
    ]


def do_cythonize(list_of_modules):
    from Cython.Build import cythonize
    list_of_cythons = []
    for file in list_of_modules:
        shutil.copy(file, file[:-3]+"_cython.py")
        hash = subprocess.check_output(["md5sum", file]).split()[0].strip().decode('utf-8')
        with open(file[:-3]+"_cython.py", 'a') as f:
            f.write("\ncython_compile_hash = '"+hash+"'\n")
        list_of_cythons.append(file[:-3]+"_cython.py")
    cytho = cythonize(list_of_cythons)
    for file in list_of_cythons:
        os.remove(file)
    return cytho


setup(
    name="Lisa",
    version=VERSION,
    author="Patrick Schreiber",
    author_email="patrick.schreiber2@student.kit.edu",
    packages=find_packages(),
    ext_modules=do_cythonize(["Lisa/file.py", "Lisa/data.py", "Lisa/plots/plots.py"]),
    install_requires=requires,
    extras_require={"test": requires},
    include_package_data=True
)
