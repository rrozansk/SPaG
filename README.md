# Scanner-Parser-Generator

[![LICENSE](https://img.shields.io/badge/LICENSE-MIT-green.svg)](https://github.com/rrozansk/Scanner-Parser-Generator/blob/master/LICENSE.txt) [![RELEASES](https://img.shields.io/badge/Releases-current-yellow.svg)](https://github.com/rrozansk/Scanner-Parser-Generator/releases)

An extensible Python framework capable of producing scanners and/or parsers from regular expressions (regular grammars) and LL(1) BNF languages (a subset of context free grammars) and outputting the results as valid programs in different languages. Included is a Python CLI program which accepts user input to help drive the compilation/generation process.

## Components

The framework is modular in design and made up of only three components: scanner, parser, and program generators. The program generator is the extensible portion, allowing new targeted languages to be easily added. Below describes in detail what each component sets out to do, how it accomplished those intended goals, and the accepted input.

### Scanner

The scanner attempts to transform a collection of named patterns (regular expression/token type pairs) into a unique minimal DFA accepting any input specified while also containing an errors sink state for all invalid input. The transformation begins by first checking the expression for validity while internalizing it. Next, the use of an augmented version of Dijkstra's shunting yard algorithm tranforms the expression into prefix notation. From here Thompsons algorithm is utilized to produce an NFA with epsilon productions. The NFA is then directly converted into a minimal DFA with respect to reachable states using e-closure conversions which are cahced. Finally, the minimal DFA is made total, if not already, so it can be further minimized with respect to indistinguishable states using Hopcroft's algorithm.

[Accepted input coming soon...]

### Parser

The parser attempts to transform a collection of BNF production rules into a parse table. While any BNF is accepted only LL(1) grammars will produce a valid parse table containing no conflicts. Furthermore, the grammar must have no left recursion or ambiguity while also being left factored. The first step in constructing the resulting table is determining the terminal and nonterminal sets, which is very trivial. From here, the sets are used to construct the first and follow sets which identify what characters can be expected when parsing corresponding production rules. Subsequently, the first and follow sets are used to construct the predict sets which are in turn used in the table construction. Finally, the table is verified by checking for conflicts.

[Accepted input coming soon...]

### Generators

[Coming soon...]

## Quick Start Guide

### Prerequisites
  - python 2.7

### Getting Started
```sh
$ git clone https://github.com/rrozansk/Scanner-Parser-Generator.git
$ cd Scanner-Parser-Generator/
$ vim scanner.txt   # edit scanner name and type/pattern token pairs
$ vim parser.txt    # edit grammar name, start production, and LL(1) BNF grammar
$ python generate.py --help
```
