from distutils.core import setup

setup(
    name='kitconc',
    version='1.0.0',
    author='Jose Lopes Moreira Filho',
    author_email='jlopes@usp.br',
    packages=['kitconc'],
    package_data={'kitconc': ['data/*.*']},
    scripts=['bin/kit.py'],
    url='http://pypi.python.org/pypi/Kitconc/',
    license='LICENSE.txt',
    description='A toolkit for Corpus Linguistics Analysis',
    long_description=open('README.txt').read(),
    install_requires=[
        "nltk >= 3.2.5",
        "numpy >= 1.14.0",
        "pandas >= 0.22.0",
        "matplotlib >= 2.1.2",
        "xlsxwriter >= 1.0.2"
    ],
)