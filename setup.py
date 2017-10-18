from setuptools import setup, find_packages
from Cython.Build import cythonize
import os

VERSION=open("Lisa/VERSION", 'r').read().strip()

requires = [
        'matplotlib',
        'numpy',
        'h5py',
        'moviepy'
    ]

import shutil


def do_cythonize(list_of_modules):
    list_of_cythons = []
    for file in list_of_modules:
        shutil.copy(file, file[:-3]+"_cython.py")
        list_of_cythons.append(file[:-3]+"_cython.py")
    return cythonize(list_of_cythons)


setup(
    name="Lisa",
    version=VERSION,
    author="Patrick Schreiber",
    author_email="patrick.schreiber2@student.kit.edu",
    packages=find_packages(),
    ext_modules=do_cythonize(["Lisa/core/file.py", "Lisa/core/data.py", "Lisa/core/plots/plots.py"]),
    install_requires=requires,
    extras_require={"test": requires},
    include_package_data=True
)
