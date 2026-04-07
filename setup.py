# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br

from setuptools import setup, find_packages

install_req = [
    "numpy>=1.26.4,<2.0.0",
    "pandas>=2.2.0,<3.0.0",
    "matplotlib>=3.7.0,<4.0.0",
    "xlsxwriter>=3.2.3,<4.0.0",
    "ttkbootstrap>=1.12.0,<2.0.0",
    "pillow>=11.2.0,<12.0.0",
    "requests>=2.31.0,<3.0.0",
    "nltk>=3.9.1,<4.0.0",
    "chardet>=5.2.0,<6.0.0",
    "pypdf>=4.0.0,<7.0.0",
    "cryptography>=3.1,<47.0.0",
    "mcp>=1.0.0,<2.0.0",
    "setuptools>=70.0.0",
]



extras_require = {
    "dev": [
        "pytest>=7.0",
        "pytest-cov>=4.0",
    ]
}

setup(
    name='kitconc',
    version='3.4.3',
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
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "kitconc-app=kitconc.cli_app:main",
            "kitconc-mcp=kitconc.agent.mcp_server:main",
        ]
    },
)
