# Grammar-Generator

[![LICENSE](https://img.shields.io/badge/LICENSE-MIT-green.svg)](https://github.com/rrozansk/Grammar-Generator/blob/master/LICENSE.txt) [![RELEASES](https://img.shields.io/badge/Releases-current-yellow.svg)](https://github.com/rrozansk/Grammar-Generator/releases)

A scanner/parser generator written in python with easy extensibility to target any language.

The scanner (a.k.a. tokenizer or lexer) is a set of regular expressions combined with a type.
It is importatnt to note that generated output for scanners obey maximal munch of input.
They are also encoded using the directly coded approach which ensures an extremely fast runtime.
In fact, the resulting scanners run in time linear to the input O(n) for ALL input!

The parser is a set of BNF production rules for an LL1 language.

Currently only generation to c code is targeted, but go and python are planned as well.
If your language of interest is not currently supported it is possible to write your own generator following the the c generator in src/generators/c.py as a template.

Finally, it is possible to generate a scanner and parser individually or together.
If a scanner is generated a token type and interface will also generated in addition to the scanner.
If a parser is generated only it will be generated and will use the same scanner/token interface which would have been generated, but is now expected to be provided by the user.

## Prerequisites
  - python 2.7

## Getting Started
```sh
$ git clone https://github.com/rrozansk/Grammar-Generator.git
$ cd Grammar_Generator
$ vim generate.py    # edit tokens, grammar and import the wanted language generator
$ python generate.py
```
