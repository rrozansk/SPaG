"""
Create the PyPi package distribution(s) for use with python pip or install directly.
"""
from setuptools import setup


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
    keywords=" ".join([
        "lexer-generator",
        "parser-generator",
        "scanner-generator",
        "ll1",
        "LL(1)",
        "scanner",
        "parser",
        "lexer",
        "tokenizer",
        "tokens",
        "regular-expression(s)",
        "context-free-grammar",
        "regular-grammar",
        "bnf",
        "BNF",
        "lexical-analysis",
        "code-generation"
    ]),
    license="MIT",
    include_package_data=False,
    zip_safe=True,
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    )
)
