# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import setuptools
from distutils.core import setup

setup(
    name='kitconc',
    version='1.4.3',
    author='José Lopes Moreira Filho',
    author_email='jlopes@usp.br',
    packages=['kitconc'],
    package_data={'kitconc': ['data/*.*','data/images/*.*','data/scripts/*.*']},
    scripts=['bin/kit.py'],
    url='http://pypi.python.org/pypi/Kitconc/',
    license='LICENSE.txt',
    description='A toolkit for Corpus Linguistics Analysis',
    long_description=open('README.txt').read(),
    long_description_content_type='text/x-rst',
    install_requires=[
        "nltk >= 3.2.5",
        "numpy >= 1.14.0",
        "pandas >= 0.22.0",
        "matplotlib >= 2.1.2",
        "xlsxwriter >= 1.0.2"
    ],
)