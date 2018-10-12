SPaG (Scanner, Parser, and Generator)
================================================================================
[![MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/rrozansk/SPaG/blob/master/LICENSE.txt) ![COV](https://img.shields.io/badge/Coverage-99%25-green.svg) ![VER](https://img.shields.io/badge/Version-1.0.0a0-yellow.svg)

  - [Introduction](#introduction)
  - [Installation](#installation)
    - [Source](#source)
    - [Pip](#pip)
  - [Overview](#overview)
    - [Scanner](#scanner)
    - [Parser](#parser)
    - [Generator](#generator)
  - [Generators](#generators)
    - [Status](#status)
    - [Script](#script)
    - [Development](#development)

# Introduction

SPaG is an extensible purely Python framework, with no external dependencies,
capable of compiling input specifications of scanners (regular grammars) and/or
parsers (LL(1) BNF context free grammars) into
[DFA](https://en.wikipedia.org/wiki/Deterministic_finite_automaton)'s
and [LL(1) parse table](https://en.wikipedia.org/wiki/LL_parser)'s. These
results can then be converted into valid scanner/parser programs following the
options configured within the framework during generation. The processes used to
transform the input specifications into DFA's and LL(1) parse tables are very
formal and well defined. Thorough table driven testing is also utilized to
ensure correctness of implementation. The program generator(s) comprise the
extensible portion of the framework allowing new targeted languages to be easily
[pluged-in](#generators). Included in the framework is a script which lightly
wraps the core library functionality to accepts user input file(s) to help drive
the compilation/generation process from the command line. The
[overview](#overview) below describes in detail what each component sets out to
do, how it accomplished those intended goals, and the accepted input.

# Installation

Installation is supported through multiple methods, all of which are listed
below. Any required dependencies along with the steps needed for a proper install
are listed. Installation installs the module containing scanner
(RegularGrammar), parser (ContextFreeGrammar), and generator (Generator) objects
as well as a command line script for easily generating scanners and/or parsers
from input specification(s) and optional configuration file. It also installs
any supported core language [generators](#status) which may grow over time.

## Source

Install from source for the latest up to date code. This may include unreleased
bug fixes, feature extensions, or newly supported language child generators.
Since the code is going to built from source it is generally a good idea to also
test it before installation or package distribution. For this prupose a Makefile
is included to automate testing, linting, virtual environment
installation/cleanup, etc. While the framework is pure, dependent free, Python
the testing is not and some prerequisites are required. All required python
packages are listed in the
[requirments](https://github.com/rrozansk/SPaG/blob/master/requirements.txt).
However, since these packages are installed in a virtual environment with the
help of Make the only requirements the user needs to worry are those which must
be installed on the machine itself and include:
  * git (>= v2.1.3)
  * make (>= v4.1)
  * Python (>= v2.7)
  * Pip (>= v9.0.3)
  * setuptools (>= v40.4.3)
  * virtualenv (>= v16.0.0)

```sh
# Obtain the source code.
$ git clone https://github.com/rrozansk/SPaG.git

# Run sanity.
# 1. Constructs a virtual environment with SPaG installed for testing.
# 2. Enter the newly built virtual environment.
# 3. Lint the code to ensure standards are followed.
# 4. Test the code and generate a report to ensure a working package.
# 5. Leave the virtual environment.
# 6. Clean up.
$ make sanity

# Open the generated report in a web-browser and inspect the results.
$ chrome test_report.html

# If the results look good then install SPaG from the source.
$ make install
```
## Pip

Install a specific prebuilt pacakge distribution from the PyPI repository.
Since the distributions are thoroughly tested and linted before publishing
there is no need for that step in this method of installation, unlike the source
method. The only requirements needed on the host machine for this method to work
include:
  * Python (>= v2.7)
  * Pip (>= v9.0.3)

```sh
# Only step required!
$ pip install SPaG
```

# Overview

The below sections provides a quick overview of each individual core component.
It briefly describes what the component consists of and how it accomplished it's
tasks and goals.

## Scanner

An object exposing only initialazation and read only properties. The scanner
attempts to transform a collection of named patterns (regular expression as
token/type pairs) into a unique minimal DFA accepting any input specified while
also containing an errors sink state for all invalid input (if required). The
transformation begins by first checking the expression for validity while
internalizing it. Next, the use of an augmented version of Dijkstra's [shunting
yard](https://en.wikipedia.org/wiki/Shunting-yard_algorithm) algorithm
transforms the expression into
[prefix notation](https://en.wikipedia.org/wiki/Polish_notation). From here
[Thompson's construction](https://en.wikipedia.org/wiki/Thompson%27s_construction)
is utilized to produce an
[NFA](https://en.wikipedia.org/wiki/Nondeterministic_finite_automaton) with
epsilon productions. The NFA is then directly converted into a
[minimal DFA](https://en.wikipedia.org/wiki/DFA_minimization) with respect to
reachable states using e-closure conversions which are cached. Finally, the
minimal DFA is made
[total](https://en.wikipedia.org/wiki/Partial_function#Total_function), if not
already, so it can be further minimized with respect to nondistinguishable
states using
[Hopcroft's algorithm](https://en.wikipedia.org/wiki/DFA_minimization#Nondistinguishable_states).
This results in the smallest possible total DFA which recognizes the given
input. The input itself (regular expressions) must be specified following these
guidelines:

  * only printable ascii characters (uppercase, lowercase, digits, punctuation,
    whitespace) are supported.
  * supported core operators (and extensions) include:
      * '|'    (union -> choice -> either or)
      * '.'    (concatenation -> combine)
      * '?'    (question -> choice -> 1 or none)
      * '*'    (kleene star -> repitition >= 0)
      * '+'    (kleene plus -> repitition >= 1)
      * ()     (grouping -> disambiguation -> any expression)
      * [ab]   (character class -> choice -> any specified character)
      * [a-c]  (character range -> choice -> any char between the two)
      * [^ab]  (character negation -> choice -> all but the specified)
  * other things to keep in mind (potential gotcha's):
      * character classes and ranges can be combined in the same set of brackets,
        possibly multiple times (e.g. [abc-pqrs-z]).
      * character ranges can be specified as forward or backwards
        (e.g. [a-c] or [c-a]).
      * '^' is required to come first after the bracket for negation to properly
        work. In fact, '^' directly following a bracket is always interpreted as
        negation.
      * '^' may be used with character classes or ranges.
      * if '^' is alone in the brackets (e.g. [^]) it is translated as any
        possible input character (i.e. a 'wildcard').
      * if a literal '-' if required in a character class or range it must be
        specified last so as to not be interpreted as a range.
      * for literal right brackets inside character ranges or classes it must be
        escaped.
      * concatenation can be either implicit or explicit in the given input
        expression(s).
      * operator literals (i.e. '|.?*+()[]') can be specified through escape
        sequences using a backslash (i.e. '\').

## Parser

The parser attempts to transform a collection of
[BNF](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form) production rules
into a parse table. The first step in constructing the resulting table is
determining the terminal and nonterminal sets, which is very trivial. From here,
the sets are used to construct the first and follow sets which identify what
characters can be expected when parsing corresponding production rules.
Subsequently, the first and follow sets are used to construct the predict sets
which are in turn used in the table construction. Finally, the table is
verified by checking for conflicts. While any BNF is accepted only
[LL(1) grammars](https://en.wikipedia.org/wiki/LL_grammar) will produce a valid
parse table containing no conflicts. Furthermore, only left factored LL(1)
grammars will produce a parse table with a single member per entry. To
properly specify a LL(1) grammar the following requirements must be met:

  * No left recursion (direct or indirect)
  * Must be left factored
  * No ambiguity

If any of the above requirements are violated, or the grammar specified is not
LL(1), there will be a conflict in the table. This means with the given set of
input productions and with the aid of a single look ahead token it cannot be
known what rule to choose in order to successfully produce a parse without
backtracking.

## Generator

The base generator is the object which all generators must inherit from. It is
responsible for allowing easy getting and setting of the same set of options
across all generators as well as providing basic protections against bad
option combinations, program input, and generator output. It also allows easy
reuse of language generators to compile many specifications into the same output
language while allowing easy configuration option changes between generation.

# Generators

The generators are wrappers on top of the scanner/parser objects and are
responsible for translating/compiling the intermediate representations from the
output of the scanner/parser into whatever context desired with the given
options configured at the time of generation. Most of the time this will be a
useable program in some choosen programming language, which should obey the
scanner's function type as an input character stream to a token stream while the
parser should take that same token stream to an abstract syntax tree (AST).
However, this is not always the case since it is possible to write other
generators, say for example [cowsay](https://en.wikipedia.org/wiki/Cowsay). This
illustrates the fact that the generators comprise the extensible portion of the
package. This plug-in segment of SPaG will grow over time to subsume more
generators into the core implementation. These implementation will be for
programming languages only. While the newly subsumed generators will be
immediately available if building from source, they will only be only available
in the pip repository as a newer release of the SPaG package. Below is the
status of all the generators currently tracked in the repository, linked to
there implementation, and any applicable notes which may apply.

## Status

|                                     Generator                                    |   Status   |                      Notes                            |
|:--------------------------------------------------------------------------------:|:----------:|:-----------------------------------------------------:|
| [C](https://github.com/rrozansk/SPaG/blob/master/spag/generators/c.py)           | DEVELOPING | Direct scanner generator complete; Parser in progress |
| [Go](https://github.com/rrozansk/SPaG/blob/master/spag/generators/go.py)         |   PLANNED  |                                                       |
| [Python](https://github.com/rrozansk/SPaG/blob/master/spag/generators/python.py) |   PLANNED  |                                                       |

## Script

A script is included in the package installation to allow easy generation of
scanners and/or parsers (and possibly some combination of the two) into any
number of output programming languages from the command line. It is a very light
weight wrapper on the core functionality in the SPaG package. It also allows
easy configuration of genration options and input specifications from command
line or configuration file. Simply stated the CLI program drives the generation
of the cross product of langauges x scanners x parser. Below shows various
examples for the generator to produce scanner's and/or parser's for different
token sets and LL(1) languages which may be found under the
[examples](https://github.com/rrozansk/SPaG/tree/master/examples) directory.
Shown below are some basic invocation's for help, scanner, parser, and
configuration file generation.

```sh
# Generate your scanner and/or parser! ...but first ask for help to see all
# available command line options.
$ spag_cli --help

# Generate any number of scanners (or parsers) for any set of languages at once!
$ spag_cli -s examples/INI/scanner.txt examples/JSON/scanner.txt -g c go
$ spag_cli -p examples/INI/parser.txt examples/JSON/parser.txt -g c go

# Generate a scanner/parser combo (possibly for a languages front-end reader).
$ spag_cli -s examples/INI/scanner.txt -p examples/INI/parser.txt -g c

# Generate a default configuration file for easier runtime configuration.
$ spag_cli --generate-rcfile .spagrc

# Control the generation [in/out]put with the specified configuration values.
$ spag_cli -c .spagrc

# NOTE: It is possible to override configuration file values with command line
# flag values if they are specified AFTER the configuration flag.
$ spag_cli -c .spagrc # Provide flag(s) for overwriting values here.
```

## Development

Creating a new generator is extremely simple, as it only requires the addition
of a single file. This file must contain a class definition following the proper
naming conventions set forth for the new output language to be picked up by the
pacakge script. Furthermore, all python package prerequisites are listed in the
[requirments](https://github.com/rrozansk/SPaG/blob/master/requirements.txt)
file. The below code block serves as a template for createing new generators
which should be placed under spag/generators. The filename (denoted between
curly brackets in the template below) should be named after the language being
compiled to. Notice should also be taken between the capital and lowercase 'F'.

```python
"""
A scanner/parser generator targeting {filename}.
"""
from spag import Generator


class {Filename}(Generator):
    """
    A simple object for compiling scanner's and/or parser's to {filename} programs.
    """

    def _translate(self):
        """
        Override this method in subclasses which should translate the (IR)
        intermediate representation of the given scanner and/or parser to the
        targeted language. It should return the files and there content in a
        dictionary allowing multiple files to be returned for a given language.
        This is the only required function a child generators must implement.

        Return:
          dict[str, str]: Generated file names/paths and associated content.
        """
        raise NotImplementedError('{filename} generator in development')
```

Once you have completed implementing the new generator it needs to be added to
the list of
[supported generators](https://github.com/rrozansk/SPaG/blob/master/spag/generators/__init__.py).
The tests should also be expanded to ensure the new generator can be properly
imported as well. Additionally, the code must be linted, ensuring it follows
the proper conventions set forth and therefore produces a similiar look and feel
as the rest of the code in the repository. Linting, testing and installing can
be automated through the use of the Makefile as shown below.

```sh
# Add the new generator to the __all__ list using your favorite editor.
$ vim spag/generators/__init__.py

# Ask the Makefile what it can do to help in linting, testing and installing.
$ make help

# Run sanity, to ensure no breakage occurs, which lints and tests the code
# against an installed version of the source in a virtual environment.
$ make sanity
```
