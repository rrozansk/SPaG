"""
Create the PyPi package distribution(s) for use with python pip or install directly.
"""
from setuptools import setup, find_packages


with open("README.md", "r") as fd:
    README = fd.read()

setup(
    name="scanner_parser_generator",
    version="0.0.8",
    author="Ryan Rozanski",
    author_email="",
    maintainer="Ryan Rozanski",
    maintainer_email="",
    description=(
        "A CLI program to generate scanners and/or parsers from regular "
        "expressions and LL(1) BNF grammar specifications respectively."
    ),
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/rrozansk/Scanner-Parser-Generator",
    download_url="https://github.com/rrozansk/Scanner-Parser-Generator",
    python_requires=">= 2.7.0, != 3.1, != 3.2, != 3.3, != 3.4, != 3.6",
    packages=find_packages(),
    keywords=" ".join([
        "bnf",
        "BNF",
        "code-generation",
        "context-free-grammar",
        "lexer",
        "lexer-generator",
        "lexical-analysis",
        "ll1",
        "LL(1)",
        "parser",
        "parser-generator",
        "regular-expression(s)",
        "regular-grammar",
        "scanner-generator",
        "scanner",
        "tokenizer",
        "tokens"
    ]),
    license="MIT",
    include_package_data=False,
    zip_safe=True,
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
        "Topic :: Text Processing :: Linguistic"
    )
)
