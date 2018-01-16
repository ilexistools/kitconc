from distutils.core import setup

setup(
    name='kitconc',
    version='5.0.0',
    author='Jose Lopes Moreira Filho',
    author_email='jlopes@usp.br',
    packages=['kitconc', 'kitconc.test'],
    package_data={'kitconc': ['data/*.*']},
    scripts=['bin/kit.py'],
    url='http://pypi.python.org/pypi/Kitconc/',
    license='LICENSE.txt',
    description='A toolkit for Corpus Linguistics Analysis',
    long_description=open('README.txt').read(),
    install_requires=[
        "numpy >= 1.1.1"
    ],
)