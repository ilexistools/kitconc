# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os 
import setuptools
from distutils.core import setup
import numpy 

from glob import glob
try:
    from Cython.Distutils.extension import Extension
    from Cython.Distutils import build_ext
except ImportError:
    from setuptools import Extension
    USING_CYTHON = False
else:
    USING_CYTHON = True

ext = 'pyx' if USING_CYTHON else 'c'
sources = glob('kitconc/*.%s' % (ext,))
extensions = [Extension(source.split('.')[0].replace(os.path.sep, '.'),sources=[source],) for source in sources]
cmdclass = {'build_ext': build_ext} if USING_CYTHON else {}


setup(
    name='kitconc',
    version='2.0.5',
    author='José Lopes Moreira Filho',
    author_email='jlopes@usp.br',
    packages=['kitconc'],
    cmdclass=cmdclass,
    ext_modules=extensions,
    include_dirs=[numpy.get_include()],
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