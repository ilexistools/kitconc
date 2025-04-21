# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br

import sys
import platform
from setuptools import setup, find_packages
import textwrap
import pkg_resources

def is_installed(requirement):
    try:
        pkg_resources.require(requirement)
    except pkg_resources.ResolutionError:
        return False
    else:
        return True

if not is_installed('numpy>=1.14.0'):
    print(textwrap.dedent("""
        Error: numpy needs to be installed first. You can install it via:

        $ pip install numpy
    """), file=sys.stderr)
    sys.exit(1)

install_req = [
    "numpy>=1.24.0,<2.0.0",
    "pandas>=2.2.0,<3.0.0",
    "matplotlib>=3.7.0,<4.0.0",
    "xlsxwriter>=3.2.3,<4.0.0",
    "ttkbootstrap>=1.12.0,<2.0.0",
    "pillow>=11.2.0,<12.0.0",
    "requests>=2.31.0,<3.0.0",
    "nltk>=3.9.1,<4.0.0",
    "chardet>=5.2.0,<6.0.0",
    "ipython>=9.1.0,<10.0.0",
    "spacy>=3.6.1,<4.0.0",
    "setuptools>=65.5.0,<70.0.0"
]



setup(
    name='kitconc',
    version='3.0.0',
    author='José Lopes Moreira Filho',
    author_email='jlopes@alumni.usp.br',
    packages=find_packages(),
    package_data={
        'kitconc': ['data/*.*', 'data/images/*.*', 'data/scripts/*.*']
    },
    url='http://pypi.python.org/pypi/Kitconc/',
    license='MIT',
    license_files=['LICENSE.txt'],
    description='A toolkit for Corpus Linguistics Analysis',
    long_description=open('README.txt', encoding='utf-8').read(),
    long_description_content_type='text/x-rst',
    install_requires=install_req,
)
