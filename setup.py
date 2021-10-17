# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os, sys
import platform
import setuptools
from distutils.core import setup
from glob import glob
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
    exit(1)

try:
    import numpy
except ImportError:
    print('Cannot import numpy')

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

if platform.python_implementation() == 'CPython':

    install_req = [
        "nltk >= 3.2.5",
        "numpy >= 1.14.0",
        "pandas >= 0.22.0",
        "xlsxwriter >= 1.0.2",
        "matplotlib >= 2.1.2",
        "pillow >= 2.2.1",
        "requests >= 2.2.1"
    ]
else:
    install_req = [
        "nltk >= 3.2.5",
        "numpy >= 1.14.0",
        "pandas >= 0.22.0",
        "xlsxwriter >= 1.0.2",
        "pillow >= 2.2.1",
        "requests >= 2.2.1"
    ]


setup(
    name='kitconc',
    version='2.1.4',
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
    install_requires=[install_req],
)