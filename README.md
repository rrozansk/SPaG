# Scanner-Parser-Generator

[![LICENSE](https://img.shields.io/badge/LICENSE-MIT-green.svg)](https://github.com/rrozansk/Scanner-Parser-Generator/blob/master/LICENSE.txt) [![RELEASES](https://img.shields.io/badge/Releases-current-yellow.svg)](https://github.com/rrozansk/Scanner-Parser-Generator/releases)

An extensible purely Python framework (with no external dependencies!) capable
of producing scanners and/or parsers from regular expressions (regular grammars)
and LL(1) BNF languages (a subset of context free grammars), outputting the
results as valid programs in the choosen language. The framework is modular in
design being made up of only three components: scanner, parser, and program
generators. The scanner/parser tranformation processes are very formal,
well defined and understood and thorough table driven testing is also utilized
to ensure correctness. The program generator is the extensible portion,
allowing new targeted languages to be easily added (see below). Included is a
Python CLI program which accepts user file input(s) to help drive the
compilation/generation process. Below describes in detail what each component
sets out to do, how it accomplished those intended goals, and the accepted
input.

### Scanner

The scanner attempts to transform a collection of named patterns (regular
expression/token type pairs) into a unique minimal DFA accepting any input
specified while also containing an errors sink state for all invalid input.
The transformation begins by first checking the expression for validity while
internalizing it. Next, the use of an augmented version of Dijkstra's shunting
yard algorithm transforms the expression into prefix notation. From here
Thompson's algorithm is utilized to produce an NFA with epsilon productions. The
NFA is then directly converted into a minimal DFA with respect to reachable
states using e-closure conversions which are cached. Finally, the minimal DFA is
made total, if not already, so it can be further minimized with respect to
indistinguishable states using Hopcroft's algorithm.

Regular expressions must be specified following these guidelines:
```text
    - only printable ascii characters (33-126) and spaces are supported
    - supported operators:
        |                (union -> choice -> either or)
        ?                (question -> choice -> 1 or none)
        .                (concatenation -> combine)
        *                (kleene star -> repitition >= 0)
        +                (plus -> repitition >= 1)
        ()               (grouping -> disambiguation -> any expression)
        [ab]             (character class -> choice -> any specified char)
        [a-c] or [c-a]   (character range -> choice -> any char between the two)
        [^ab] or [^a-c]  (character negation -> choice -> all but the specified)
        NOTES: '^' is required to come first after the bracket for negation.
               If alone ([^]) it is translated as all alphabet characters.
               It is still legal for character ranges as well ([b-^] and
               negated as [^^-b]). Note that the reverse range was needed. If
               the first character is a '^' it will always mean negation! If a
               single '^' is wanted then there is no need to use a class/range.
               Classes and ranges can be combined between the same set of
               brackets ([abc-z]), even multiple times if wanted/needed. Due to
               this though the '-' char must come as the last character in the
               class if the literal is wanted. For literal right brackets an
               escape is needed if mentioned ([\]]). All other characters are
               treated as literals.
    - concat can be either implicit or explicit
    - supported escape sequences:
        operator literals   -> \?, \*, \., \+, \|
        grouping literals   -> \(, \), \[, \]
        whitespace literals -> \s, \t, \n, \r, \f, \v
        escape literal      -> \\\\
```

### Parser

The parser attempts to transform a collection of BNF production rules into a
parse table. While any BNF is accepted only LL(1) grammars will produce a valid
parse table containing no conflicts. Furthermore, the grammar must have no left
recursion or ambiguity while also being left factored. The first step in
constructing the resulting table is determining the terminal and nonterminal
sets, which is very trivial. From here, the sets are used to construct the first
and follow sets which identify what characters can be expected when parsing
corresponding production rules. Subsequently, the first and follow sets are used
to construct the predict sets which are in turn used in the table construction.
Finally, the table is verified by checking for conflicts.

### Generators

The generators are very light weight wrappers on top of the scanner/parser
objects and are responsible for compiling there output into a useable program in
the choosen language. Adding a new generator is extremely simple as it only requires
the addition of a single file containing a single class definition.

Using the below as a template create a new file with the given contents under
src/generators, naming the file after the language being compiled to:

```python
"""
A scanner/parser generator targeting {filename}.
"""
from . import Generator


class {Filename}(Generator):
    """
    A simple object for compiling scanner's and/or parser's to {filename}.
    """

    def output(self, filename):
        """
        Attempt to generate the required output file for {filename}.
        """
        pass
```

NOTE: the class name is a capitalized version of the filename.
This is important for the framework to automatically pick up and use the file/class.

Below shows the current status of the generators:

  * [![C](https://img.shields.io/badge/C-Developing-yellow.svg)](https://github.com/rrozansk/Scanner-Parser-Generator/blob/master/src/generators/c.py)
  * [![Golang](https://img.shields.io/badge/Golang-Planned-red.svg)](https://github.com/rrozansk/Scanner-Parser-Generator/blob/master/src/generators/go.py)
  * [![Python](https://img.shields.io/badge/Python-Planned-red.svg)](https://github.com/rrozansk/Scanner-Parser-Generator/blob/master/src/generators/python.py)

## Quick Start Guide

### Prerequisites (Code Generation)
  - python 2.7 or 3.5

### Getting Started
```sh
$ git clone https://github.com/rrozansk/Scanner-Parser-Generator.git
$ cd Scanner-Parser-Generator/
$ vim scanner.txt   # edit scanner name and type/pattern token pairs
$ vim parser.txt    # edit grammar name, start production, and LL(1) BNF grammar
$ python generate.py --help
```
