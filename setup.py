"""
Create the PyPI package distribution(s) for use with python pip or install
directly.
"""
from setuptools import setup


with open('README.md', 'r') as fd:
    README = fd.read()

setup(
    name='SPaG',
    version='1.0.0a0',
    license='MIT',
    author='Ryan Rozanski',
    author_email='',
    maintainer='Ryan Rozanski',
    maintainer_email='',
    description=(
        'A module containing scanner (regular expression) and parser (BNF) '
        'compilers as well as a base generator which all target language '
        'generators must inherit from, allowing any specific language of '
        'interest to be targeted. A script is also included which reads the '
        'respective specification(s) from file and outputs the resulting code '
        'to disk.'
    ),
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/rrozansk/SPaG',
    download_url='https://github.com/rrozansk/SPaG',
    python_requires='>= 2.7.0',
    keywords=' '.join([
        'bnf',
        'BNF',
        'cli',
        'CLI',
        'code-generation',
        'context-free-grammar',
        'lexer',
        'lexer-generator',
        'lexical-analysis',
        'll1',
        'LL1',
        'LL(1)',
        'parser',
        'parser-generator',
        'regular-expression(s)',
        'regular-grammar',
        'scanner',
        'scanner-generator',
        'tokenizer',
        'tokens'
    ]),
    packages=[
        'spag',
        'spag.generators'
    ],
    package_data={
        'spag': [
            '../LICENSE.txt'
        ]
    },
    scripts=[
        'scripts/spag-cli.py'
    ],
    include_package_data=True,
    zip_safe=True,
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Linguistic'
    )
)
