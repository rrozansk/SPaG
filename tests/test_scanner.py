# disable pylint spacing error to enable 'pretty/readable' transition tables.
# pylint: disable=too-many-lines, bad-whitespace, line-too-long, anomalous-backslash-in-string, too-many-locals, too-many-branches, too-many-statements
"""
    **Testing for RegularGrammar objects located in scanner.py**

Testing is implemented in a table driven fashion using the black box method.
The tests may be run at the command line with the following invocation:

  $ python scanner.py

If all tests passed no output will be produced. In the event of a failure a
ValueError is thrown with the appropriate error/failure message. Both positive
and negative tests cases are extensively tested.
"""
import os
import sys

TEST_DIR = os.path.dirname(__file__)
SRC_DIR = '../src'
sys.path.insert(0, os.path.abspath(os.path.join(TEST_DIR, SRC_DIR)))

from scanner.scanner import RegularGrammar


TESTS = [
    {
        'name': 'Single Alpha',
        'valid': True,
        'expressions': [
            ('alpha', 'a')
        ],
        'DFA': {
            'Q': set(['S', 'A', 'Err']),
            'V': set('a'),
            'T': [
                [' ', 'S', 'A',   'Err'],
                ['a', 'A', 'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['A']),
            'G': {
                'alpha': set(['A']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Explicit Concatenation',
        'valid': True,
        'expressions': [
            ('concat', 'a.b')
        ],
        'DFA': {
            'Q': set(['S', 'A', 'B', 'Err']),
            'V': set('ab'),
            'T': [
                [' ', 'S',   'A',   'B',   'Err'],
                ['a', 'A',   'Err', 'Err', 'Err'],
                ['b', 'Err', 'B',   'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['B']),
            'G': {
                'concat': set(['B']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Alternation',
        'valid': True,
        'expressions': [
            ('alt', 'a|b')
        ],
        'DFA': {
            'Q': set(['S', 'AB', 'Err']),
            'V': set('ab'),
            'T': [
                [' ', 'S',  'AB',  'Err'],
                ['a', 'AB', 'Err', 'Err'],
                ['b', 'AB', 'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['AB']),
            'G': {
                'alt': set(['AB']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Kleene Star',
        'valid': True,
        'expressions': [
            ('star', 'a*')
        ],
        'DFA': {
            'Q': set(['A']),
            'V': set('a'),
            'T': [
                [' ', 'A'],
                ['a', 'A']
            ],
            'S': 'A',
            'F': set(['A']),
            'G': {
                'star': set(['A'])
            }
        }
    },
    {
        'name': 'Kleene Plus',
        'valid': True,
        'expressions': [
            ('plus', 'a+')
        ],
        'DFA': {
            'Q': set(['S', 'A']),
            'V': set('a'),
            'T': [
                [' ', 'S', 'A'],
                ['a', 'A', 'A']
            ],
            'S': 'S',
            'F': set(['A']),
            'G': {
                'plus': set(['A'])
            }
        }
    },
    {
        'name': 'Choice',
        'valid': True,
        'expressions': [
            ('maybe', 'a?')
        ],
        'DFA': {
            'Q': set(['S', 'A', 'Err']),
            'V': set('a'),
            'T': [
                [' ', 'S', 'A',   'Err'],
                ['a', 'A', 'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['S', 'A']),
            'G': {
                'maybe': set(['S', 'A']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Grouping',
        'valid': True,
        'expressions': [
            ('group', '(a|b)*')
        ],
        'DFA': {
            'Q': set(['AB*']),
            'V': set('ab'),
            'T': [
                [' ', 'AB*'],
                ['a', 'AB*'],
                ['b', 'AB*']
            ],
            'S': 'AB*',
            'F': set(['AB*']),
            'G': {
                'group': set(['AB*'])
            }
        }
    },
    {
        'name': 'Association',
        'valid': True,
        'expressions': [
            ('assoc', 'a|b*')
        ],
        'DFA': {
            'Q': set(['S', 'A', 'B', 'Err']),
            'V': set('ab'),
            'T': [
                [' ', 'S', 'A',   'B',   'Err'],
                ['a', 'A', 'Err', 'Err', 'Err'],
                ['b', 'B', 'Err', 'B',   'Err']
            ],
            'S': 'S',
            'F': set(['S', 'A', 'B']),
            'G': {
                'assoc': set(['S', 'A', 'B']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Operator Alpha Literals',
        'valid': True,
        'expressions': [
            ('concat', '\.'),
            ('alt', '\|'),
            ('star', '\*'),
            ('question', '\?'),
            ('plus', '\+'),
            ('slash', '\\\\'),
            ('lparen', '\('),
            ('rparen', '\)'),
            ('lbracket', '\['),
            ('rbracket', '\]')
        ],
        'DFA': {
            'Q': set(['S', 'F', 'Err']),
            'V': set('.|*?+\\()[]'),
            'T': [
                [' ',  'S', 'F',   'Err'],
                ['.',  'F', 'Err', 'Err'],
                ['|',  'F', 'Err', 'Err'],
                ['*',  'F', 'Err', 'Err'],
                ['?',  'F', 'Err', 'Err'],
                ['+',  'F', 'Err', 'Err'],
                ['\\', 'F', 'Err', 'Err'],
                ['(',  'F', 'Err', 'Err'],
                [')',  'F', 'Err', 'Err'],
                ['[',  'F', 'Err', 'Err'],
                [']',  'F', 'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['F']),
            'G': {
                'concat': set(['F']),
                'alt': set(['F']),
                'star': set(['F']),
                'question': set(['F']),
                'plus': set(['F']),
                'slash': set(['F']),
                'lparen': set(['F']),
                'rparen': set(['F']),
                'lbracket': set(['F']),
                'rbracket': set(['F']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Implicit Concatenation Characters',
        'valid': True,
        'expressions': [
            ('permutation1', 'ab'),
            ('permutation2', 'a(b)'),
            ('permutation3', '(a)b'),
            ('permutation4', '(a)(b)')
        ],
        'DFA': {
            'Q': set(['S', 'A', 'B', 'Err']),
            'V': set('ab'),
            'T': [
                [' ', 'S',   'A',   'B',   'Err'],
                ['a', 'A',   'Err', 'Err', 'Err'],
                ['b', 'Err', 'B',   'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['B']),
            'G': {
                'permutation1': set(['B']),
                'permutation2': set(['B']),
                'permutation3': set(['B']),
                'permutation4': set(['B']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Implicit Concatenation Star Operator',
        'valid': True,
        'expressions': [
            ('permutation1', 'a*b'),
            ('permutation2', 'a*(b)'),
            ('permutation3', '(a)*b'),
            ('permutation4', '(a)*(b)')
        ],
        'DFA': {
            'Q': set(['A', 'B', 'Err']),
            'V': set('ab'),
            'T': [
                [' ', 'A', 'B',   'Err'],
                ['a', 'A', 'Err', 'Err'],
                ['b', 'B', 'Err', 'Err']
            ],
            'S': 'A',
            'F': set(['B']),
            'G': {
                'permutation1': set(['B']),
                'permutation2': set(['B']),
                'permutation3': set(['B']),
                'permutation4': set(['B']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Implicit Concatenation Plus Operator',
        'valid': True,
        'expressions': [
            ('permutation1', 'a+b'),
            ('permutation2', 'a+(b)'),
            ('permutation3', '(a)+b'),
            ('permutation4', '(a)+(b)')
        ],
        'DFA': {
            'Q': set(['S', 'A', 'B', 'Err']),
            'V': set('ab'),
            'T': [
                [' ', 'S',   'A', 'B',   'Err'],
                ['a', 'A',   'A', 'Err', 'Err'],
                ['b', 'Err', 'B', 'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['B']),
            'G': {
                'permutation1': set(['B']),
                'permutation2': set(['B']),
                'permutation3': set(['B']),
                'permutation4': set(['B']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Implicit Concatenation Question Operator',
        'valid': True,
        'expressions': [
            ('permutation1', 'a?b'),
            ('permutation2', 'a?(b)'),
            ('permutation3', '(a)?b'),
            ('permutation4', '(a)?(b)')
        ],
        'DFA': {
            'Q': set(['S', 'A', 'B', 'Err']),
            'V': set('ab'),
            'T': [
                [' ', 'S', 'A',   'B',   'Err'],
                ['a', 'A', 'Err', 'Err', 'Err'],
                ['b', 'B', 'B',   'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['B']),
            'G': {
                'permutation1': set(['B']),
                'permutation2': set(['B']),
                'permutation3': set(['B']),
                'permutation4': set(['B']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Implicit Concatenation 10 - Mixed',
        'valid': True,
        'expressions': [
            ('concat', 'a.bc.de')
        ],
        'DFA': {
            'Q': set(['S', 'A', 'B', 'C', 'D', 'E', 'Err']),
            'V': set('abcde'),
            'T': [
                [' ', 'S',   'A',   'B',   'C',   'D',   'E',   'Err'],
                ['a', 'A',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                ['b', 'Err', 'B',   'Err', 'Err', 'Err', 'Err', 'Err'],
                ['c', 'Err', 'Err', 'C',   'Err', 'Err', 'Err', 'Err'],
                ['d', 'Err', 'Err', 'Err', 'D',   'Err', 'Err', 'Err'],
                ['e', 'Err', 'Err', 'Err', 'Err', 'E',   'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['E']),
            'G': {
                'concat': set(['E']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Randomness 1',
        'valid': True,
        'expressions': [
            ('random', 'a*(b|cd)*')
        ],
        'DFA': {
            'Q': set(['AC', 'B', 'DE', 'Err']),
            'V': set('abcd'),
            'T': [
                [' ', 'AC',  'B',   'DE',  'Err'],
                ['a', 'AC',  'Err', 'Err', 'Err'],
                ['b', 'DE',  'Err', 'DE',  'Err'],
                ['c', 'B',   'Err', 'B',   'Err'],
                ['d', 'Err', 'DE',  'Err', 'Err']
            ],
            'S': 'AC',
            'F': set(['AC', 'DE']),
            'G': {
                'random': set(['AC', 'DE']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Randomness 2',
        'valid': True,
        'expressions': [
            ('random', 'a?b*')
        ],
        'DFA': {
            'Q': set(['A', 'B', 'Err']),
            'V': set('ab'),
            'T': [
                [' ', 'A',  'B',   'Err'],
                ['a', 'B',  'Err', 'Err'],
                ['b', 'B',  'B',   'Err']
            ],
            'S': 'A',
            'F': set(['A', 'B']),
            'G': {
                'random': set(['A', 'B']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Randomness 3',
        'valid': True,
        'expressions': [
            ('random', '(a*b)|(a.bcd.e)')
        ],
        'DFA': {
            'Q': set(['S', 'A', 'A*', 'B', 'C', 'D', 'F', 'Err']),
            'V': set('abcde'),
            'T': [
                [' ', 'S',   'A',   'A*',  'B',   'C',   'D',   'F',   'Err'],
                ['a', 'A',   'A*',  'A*',  'Err', 'Err', 'Err', 'Err', 'Err'],
                ['b', 'F',   'B',   'F',   'Err', 'Err', 'Err', 'Err', 'Err'],
                ['c', 'Err', 'Err', 'Err', 'C',   'Err', 'Err', 'Err', 'Err'],
                ['d', 'Err', 'Err', 'Err', 'Err', 'D',   'Err', 'Err', 'Err'],
                ['e', 'Err', 'Err', 'Err', 'Err', 'Err', 'F',   'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['F', 'B']),
            'G': {
                'random': set(['F', 'B']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Randomness 4',
        'valid': True,
        'expressions': [
            ('random', '(foo)?(bar)+')
        ],
        'DFA': {
            'Q': set(['S', 'F', 'FO', 'FOO', 'B', 'BA', 'BAR', 'Err']),
            'V': set('fobar'),
            'T': [
                [' ', 'S',   'F',   'FO',  'FOO', 'B',   'BA',  'BAR', 'Err'],
                ['f', 'F',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                ['o', 'Err', 'FO',  'FOO', 'Err', 'Err', 'Err', 'Err', 'Err'],
                ['b', 'B',   'Err', 'Err', 'B',   'Err', 'Err', 'B',   'Err'],
                ['a', 'Err', 'Err', 'Err', 'Err', 'BA',  'Err', 'Err', 'Err'],
                ['r', 'Err', 'Err', 'Err', 'Err', 'Err', 'BAR', 'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['BAR']),
            'G': {
                'random': set(['BAR']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Forward Character Range',
        'valid': True,
        'expressions': [
            ('range', '[a-c]')
        ],
        'DFA': {
            'Q': set(['S', 'F', 'Err']),
            'V': set('abc'),
            'T': [
                [' ', 'S',   'F',   'Err'],
                ['a', 'F',   'Err', 'Err'],
                ['b', 'F',   'Err', 'Err'],
                ['c', 'F',   'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['F']),
            'G': {
                'range': set(['F']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Backward Character Range',
        'valid': True,
        'expressions': [
            ('range', '[c-a]')
        ],
        'DFA': {
            'Q': set(['S', 'F', 'Err']),
            'V': set('abc'),
            'T': [
                [' ', 'S',   'F',   'Err'],
                ['a', 'F',   'Err', 'Err'],
                ['b', 'F',   'Err', 'Err'],
                ['c', 'F',   'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['F']),
            'G': {
                'range': set(['F']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Literal Negation Character Range',
        'valid': True,
        'expressions': [
            ('range', '[a-^]')
        ],
        'DFA': {
            'Q': set(['S', 'F', 'Err']),
            'V': set('^_`a'),
            'T': [
                [' ', 'S',   'F',   'Err'],
                ['^', 'F',   'Err', 'Err'],
                ['_', 'F',   'Err', 'Err'],
                ['`', 'F',   'Err', 'Err'],
                ['a', 'F',   'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['F']),
            'G': {
                'range': set(['F']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Negated Character Range',
        'valid': True,
        'expressions': [
            ('range', '[^!-~]*')
        ],
        'DFA': {
            'Q': set(['S']),
            'V': set(' \t\n\r\f\v'),
            'T': [
                [' ',  'S'],
                [' ',  'S'],
                ['\t', 'S'],
                ['\n', 'S'],
                ['\r', 'S'],
                ['\f', 'S'],
                ['\v', 'S']
            ],
            'S': 'S',
            'F': set(['S']),
            'G': {
                'range': set(['S'])
            }
        }
    },
    {
        'name': 'Character Class',
        'valid': True,
        'expressions': [
            ('class', '[abc]')
        ],
        'DFA': {
            'Q': set(['S', 'F', 'Err']),
            'V': set('abc'),
            'T': [
                [' ', 'S',   'F',   'Err'],
                ['a', 'F',   'Err', 'Err'],
                ['b', 'F',   'Err', 'Err'],
                ['c', 'F',   'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['F']),
            'G': {
                'class': set(['F']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Character Class with Copies',
        'valid': True,
        'expressions': [
            ('class', '[aaa]')
        ],
        'DFA': {
            'Q': set(['S', 'F', 'Err']),
            'V': set('a'),
            'T': [
                [' ', 'S',   'F',   'Err'],
                ['a', 'F',   'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['F']),
            'G': {
                'class': set(['F']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Character Class with Literal Right Bracket',
        'valid': True,
        'expressions': [
            ('class', '[\]]*')
        ],
        'DFA': {
            'Q': set(['S']),
            'V': set(']'),
            'T': [
                [' ', 'S'],
                [']', 'S']
            ],
            'S': 'S',
            'F': set(['S']),
            'G': {
                'class': set(['S'])
            }
        }
    },
    {
        'name': 'Negated Character Class',
        'valid': True,
        'expressions': [
            ('class', '[^^!"#$%&\'()*+,./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\\]_`abcdefghijklmnopqrstuvwxyz{|}~-]*')
        ],
        'DFA': {
            'Q': set(['S']),
            'V': set(' \t\n\r\f\v'),
            'T': [
                [' ',  'S'],
                [' ',  'S'],
                ['\t', 'S'],
                ['\n', 'S'],
                ['\r', 'S'],
                ['\f', 'S'],
                ['\v', 'S']
            ],
            'S': 'S',
            'F': set(['S']),
            'G': {
                'class': set(['S'])
            }
        }
    },
    {
        'name': 'Character Class Range Combo',
        'valid': True,
        'expressions': [
            ('class', '[abc-e]*')
        ],
        'DFA': {
            'Q': set(['S']),
            'V': set('abcde'),
            'T': [
                [' ', 'S'],
                ['a', 'S'],
                ['b', 'S'],
                ['c', 'S'],
                ['d', 'S'],
                ['e', 'S']
            ],
            'S': 'S',
            'F': set(['S']),
            'G': {
                'class': set(['S'])
            }
        }
    },
    {
        'name': 'Character Range Class Combo',
        'valid': True,
        'expressions': [
            ('class', '[a-cde]*')
        ],
        'DFA': {
            'Q': set(['S']),
            'V': set('abcde'),
            'T': [
                [' ', 'S'],
                ['a', 'S'],
                ['b', 'S'],
                ['c', 'S'],
                ['d', 'S'],
                ['e', 'S']
            ],
            'S': 'S',
            'F': set(['S']),
            'G': {
                'class': set(['S'])
            }
        }
    },
    {
        'name': 'Integer',
        'valid': True,
        'expressions': [
            ('int', "0|([-+]?[1-9][0-9]*)")
        ],
        'DFA': {
            'Q': set(['S', 'Zero', 'Sign', 'Int', 'Err']),
            'V': set('+-0123456789'),
            'T': [
                [' ', 'S',    'Zero', 'Sign', 'Int', 'Err'],
                ['+', 'Sign', 'Err',  'Err',  'Err', 'Err'],
                ['-', 'Sign', 'Err',  'Err',  'Err', 'Err'],
                ['0', 'Zero', 'Err',  'Err',  'Int', 'Err'],
                ['1', 'Int',  'Err',  'Int',  'Int', 'Err'],
                ['2', 'Int',  'Err',  'Int',  'Int', 'Err'],
                ['3', 'Int',  'Err',  'Int',  'Int', 'Err'],
                ['4', 'Int',  'Err',  'Int',  'Int', 'Err'],
                ['5', 'Int',  'Err',  'Int',  'Int', 'Err'],
                ['6', 'Int',  'Err',  'Int',  'Int', 'Err'],
                ['7', 'Int',  'Err',  'Int',  'Int', 'Err'],
                ['8', 'Int',  'Err',  'Int',  'Int', 'Err'],
                ['9', 'Int',  'Err',  'Int',  'Int', 'Err']
            ],
            'S': 'S',
            'F': set(['Zero', 'Int']),
            'G': {
                'int': set(['Zero', 'Int']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Float',
        'valid': True,
        'expressions': [
            ('float', '[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?')
        ],
        'DFA': {
            'Q': set(['S', 'WholePart', 'ExpPart', 'FractionPart', 'eSignum', 'Sigfrac', 'Sigexp', 'Signum', 'Err']),
            'V': set('+-.0123456789eE'),
            'T': [
                [' ', 'S',         'WholePart', 'ExpPart', 'FractionPart', 'eSignum', 'Sigfrac',      'Sigexp',  'Signum',    'Err'],
                ['+', 'Signum',    'Err',       'Err',     'Err',          'Err',     'Err',          'eSignum', 'Err',       'Err'],
                ['-', 'Signum',    'Err',       'Err',     'Err',          'Err',     'Err',          'eSignum', 'Err',       'Err'],
                ['.', 'Sigfrac',   'Sigfrac',   'Err',     'Err',          'Err',     'Err',          'Err',     'Sigfrac',   'Err'],
                ['0', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                ['1', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                ['2', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                ['3', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                ['4', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                ['5', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                ['6', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                ['7', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                ['8', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                ['9', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                ['E', 'Err',       'Sigexp',    'Err',     'Sigexp',       'Err',     'Err',          'Err',     'Err',       'Err'],
                ['e', 'Err',       'Sigexp',    'Err',     'Sigexp',       'Err',     'Err',          'Err',     'Err',       'Err']
            ],
            'S': 'S',
            'F': set(['WholePart', 'ExpPart', 'FractionPart']),
            'G': {
                'float': set(['WholePart', 'ExpPart', 'FractionPart']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'White Space',
        'valid': True,
        'expressions': [
            ('white', '( |\t|\n|\r|\f|\v)*')
        ],
        'DFA': {
            'Q': set(['S']),
            'V': set(' \t\n\r\f\v'),
            'T': [
                [' ',  'S'],
                [' ',  'S'],
                ['\t', 'S'],
                ['\n', 'S'],
                ['\r', 'S'],
                ['\f', 'S'],
                ['\v', 'S']
            ],
            'S': 'S',
            'F': set(['S']),
            'G': {
                'white': set(['S'])
            }
        }
    },
    {
        'name': 'Boolean',
        'valid': True,
        'expressions': [
            ('bool', '(true)|(false)')
        ],
        'DFA': {
            'Q': set(['S', 'T', 'R', 'F', 'A', 'L', 'US', 'E', 'Err']),
            'V': set('truefals'),
            'T': [
                [' ', 'S',   'T',   'R',   'F',   'A',   'L',   'US',  'E',   'Err'],
                ['t', 'T',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                ['r', 'Err', 'R',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                ['u', 'Err', 'Err', 'US',  'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                ['e', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'E',   'Err', 'Err'],
                ['f', 'F',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                ['a', 'Err', 'Err', 'Err', 'A',   'Err', 'Err', 'Err', 'Err', 'Err'],
                ['l', 'Err', 'Err', 'Err', 'Err', 'L',   'Err', 'Err', 'Err', 'Err'],
                ['s', 'Err', 'Err', 'Err', 'Err', 'Err', 'US',  'Err', 'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['E']),
            'G': {
                'bool': set(['E']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Line Comment',
        'valid': True,
        'expressions': [
            ('comment', '(#|;)[^\n]*\n')
        ],
        'DFA': {
            'Q': set(['S', '_', 'F', 'Err']),
            'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
            'T': [
                [' ',  'S',   '_', 'F',   'Err'],
                ['#',  '_',   '_', 'Err', 'Err'],
                [';',  '_',   '_', 'Err', 'Err'],
                ['\n', 'Err', 'F', 'Err', 'Err'],
                ['0',  'Err', '_', 'Err', 'Err'],
                ['1',  'Err', '_', 'Err', 'Err'],
                ['2',  'Err', '_', 'Err', 'Err'],
                ['3',  'Err', '_', 'Err', 'Err'],
                ['4',  'Err', '_', 'Err', 'Err'],
                ['5',  'Err', '_', 'Err', 'Err'],
                ['6',  'Err', '_', 'Err', 'Err'],
                ['7',  'Err', '_', 'Err', 'Err'],
                ['8',  'Err', '_', 'Err', 'Err'],
                ['9',  'Err', '_', 'Err', 'Err'],
                [' ',  'Err', '_', 'Err', 'Err'],
                ['\t', 'Err', '_', 'Err', 'Err'],
                ['\v', 'Err', '_', 'Err', 'Err'],
                ['\f', 'Err', '_', 'Err', 'Err'],
                ['\r', 'Err', '_', 'Err', 'Err'],
                ['a',  'Err', '_', 'Err', 'Err'],
                ['b',  'Err', '_', 'Err', 'Err'],
                ['c',  'Err', '_', 'Err', 'Err'],
                ['d',  'Err', '_', 'Err', 'Err'],
                ['e',  'Err', '_', 'Err', 'Err'],
                ['f',  'Err', '_', 'Err', 'Err'],
                ['g',  'Err', '_', 'Err', 'Err'],
                ['h',  'Err', '_', 'Err', 'Err'],
                ['i',  'Err', '_', 'Err', 'Err'],
                ['j',  'Err', '_', 'Err', 'Err'],
                ['k',  'Err', '_', 'Err', 'Err'],
                ['l',  'Err', '_', 'Err', 'Err'],
                ['m',  'Err', '_', 'Err', 'Err'],
                ['n',  'Err', '_', 'Err', 'Err'],
                ['o',  'Err', '_', 'Err', 'Err'],
                ['p',  'Err', '_', 'Err', 'Err'],
                ['q',  'Err', '_', 'Err', 'Err'],
                ['r',  'Err', '_', 'Err', 'Err'],
                ['s',  'Err', '_', 'Err', 'Err'],
                ['t',  'Err', '_', 'Err', 'Err'],
                ['u',  'Err', '_', 'Err', 'Err'],
                ['v',  'Err', '_', 'Err', 'Err'],
                ['w',  'Err', '_', 'Err', 'Err'],
                ['x',  'Err', '_', 'Err', 'Err'],
                ['y',  'Err', '_', 'Err', 'Err'],
                ['z',  'Err', '_', 'Err', 'Err'],
                ['A',  'Err', '_', 'Err', 'Err'],
                ['B',  'Err', '_', 'Err', 'Err'],
                ['C',  'Err', '_', 'Err', 'Err'],
                ['D',  'Err', '_', 'Err', 'Err'],
                ['E',  'Err', '_', 'Err', 'Err'],
                ['F',  'Err', '_', 'Err', 'Err'],
                ['G',  'Err', '_', 'Err', 'Err'],
                ['H',  'Err', '_', 'Err', 'Err'],
                ['I',  'Err', '_', 'Err', 'Err'],
                ['J',  'Err', '_', 'Err', 'Err'],
                ['K',  'Err', '_', 'Err', 'Err'],
                ['L',  'Err', '_', 'Err', 'Err'],
                ['M',  'Err', '_', 'Err', 'Err'],
                ['N',  'Err', '_', 'Err', 'Err'],
                ['O',  'Err', '_', 'Err', 'Err'],
                ['P',  'Err', '_', 'Err', 'Err'],
                ['Q',  'Err', '_', 'Err', 'Err'],
                ['R',  'Err', '_', 'Err', 'Err'],
                ['S',  'Err', '_', 'Err', 'Err'],
                ['T',  'Err', '_', 'Err', 'Err'],
                ['U',  'Err', '_', 'Err', 'Err'],
                ['V',  'Err', '_', 'Err', 'Err'],
                ['W',  'Err', '_', 'Err', 'Err'],
                ['X',  'Err', '_', 'Err', 'Err'],
                ['Y',  'Err', '_', 'Err', 'Err'],
                ['Z',  'Err', '_', 'Err', 'Err'],
                ['!',  'Err', '_', 'Err', 'Err'],
                ['"',  'Err', '_', 'Err', 'Err'],
                ['$',  'Err', '_', 'Err', 'Err'],
                ['%',  'Err', '_', 'Err', 'Err'],
                ['&',  'Err', '_', 'Err', 'Err'],
                ['\'', 'Err', '_', 'Err', 'Err'],
                ['(',  'Err', '_', 'Err', 'Err'],
                [')',  'Err', '_', 'Err', 'Err'],
                ['*',  'Err', '_', 'Err', 'Err'],
                ['+',  'Err', '_', 'Err', 'Err'],
                [',',  'Err', '_', 'Err', 'Err'],
                ['-',  'Err', '_', 'Err', 'Err'],
                ['.',  'Err', '_', 'Err', 'Err'],
                ['/',  'Err', '_', 'Err', 'Err'],
                [':',  'Err', '_', 'Err', 'Err'],
                ['<',  'Err', '_', 'Err', 'Err'],
                ['=',  'Err', '_', 'Err', 'Err'],
                ['>',  'Err', '_', 'Err', 'Err'],
                ['?',  'Err', '_', 'Err', 'Err'],
                ['@',  'Err', '_', 'Err', 'Err'],
                ['[',  'Err', '_', 'Err', 'Err'],
                ['\\', 'Err', '_', 'Err', 'Err'],
                [']',  'Err', '_', 'Err', 'Err'],
                ['^',  'Err', '_', 'Err', 'Err'],
                ['_',  'Err', '_', 'Err', 'Err'],
                ['`',  'Err', '_', 'Err', 'Err'],
                ['{',  'Err', '_', 'Err', 'Err'],
                ['|',  'Err', '_', 'Err', 'Err'],
                ['}',  'Err', '_', 'Err', 'Err'],
                ['~',  'Err', '_', 'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['F']),
            'G': {
                'comment': set(['F']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Block Comment',
        'valid': True,
        'expressions': [
            ('comment', '/[*][^]*[*]/')
        ],
        'DFA': {
            'Q': set(['BEGIN', 'SINK', 'FSLASH', 'SIGEND', 'END', 'ERR']),
            'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
            'T': [
                [' ',  'BEGIN',  'SINK',   'FSLASH', 'SIGEND', 'END',    'ERR'],
                ['/',  'FSLASH', 'SINK',   'ERR',    'END',    'SINK',   'ERR'],
                ['*',  'ERR',    'SIGEND', 'SINK',   'SIGEND', 'SIGEND', 'ERR'],
                ['#',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                [';',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['\n', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['0',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['1',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['2',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['3',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['4',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['5',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['6',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['7',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['8',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['9',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                [' ',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['\t', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['\v', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['\f', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['\r', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['a',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['b',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['c',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['d',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['e',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['f',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['g',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['h',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['i',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['j',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['k',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['l',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['m',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['n',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['o',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['p',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['q',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['r',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['s',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['t',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['u',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['v',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['w',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['x',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['y',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['z',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['A',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['B',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['C',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['D',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['E',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['F',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['G',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['H',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['I',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['J',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['K',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['L',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['M',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['N',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['O',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['P',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['Q',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['R',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['S',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['T',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['U',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['V',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['W',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['X',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['Y',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['Z',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['!',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['"',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['$',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['%',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['&',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['\'', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['(',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                [')',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['+',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                [',',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['-',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['.',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                [':',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['<',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['=',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['>',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['?',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['@',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['[',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['\\', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                [']',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['^',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['_',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['`',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['{',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['|',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['}',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                ['~',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR']
            ],
            'S': 'BEGIN',
            'F': set(['END']),
            'G': {
                'comment': set(['END']),
                '_sink': set(['ERR'])
            }
        }
    },
    {
        'name': 'Character',
        'valid': True,
        'expressions': [
            ('char', "'[^]'")
        ],
        'DFA': {
            'Q': set(['S', '_1', '_2', 'F', 'Err']),
            'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
            'T': [
                [' ',  'S',   '_1', '_2',  'F',   'Err'],
                ['#',  'Err', '_2', 'Err', 'Err', 'Err'],
                [';',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['\n', 'Err', '_2', 'Err', 'Err', 'Err'],
                ['0',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['1',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['2',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['3',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['4',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['5',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['6',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['7',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['8',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['9',  'Err', '_2', 'Err', 'Err', 'Err'],
                [' ',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['\t', 'Err', '_2', 'Err', 'Err', 'Err'],
                ['\v', 'Err', '_2', 'Err', 'Err', 'Err'],
                ['\f', 'Err', '_2', 'Err', 'Err', 'Err'],
                ['\r', 'Err', '_2', 'Err', 'Err', 'Err'],
                ['a',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['b',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['c',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['d',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['e',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['f',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['g',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['h',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['i',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['j',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['k',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['l',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['m',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['n',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['o',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['p',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['q',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['r',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['s',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['t',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['u',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['v',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['w',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['x',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['y',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['z',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['A',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['B',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['C',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['D',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['E',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['F',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['G',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['H',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['I',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['J',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['K',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['L',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['M',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['N',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['O',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['P',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['Q',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['R',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['S',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['T',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['U',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['V',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['W',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['X',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['Y',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['Z',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['!',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['"',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['$',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['%',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['&',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['\'', '_1',  '_2', 'F',   'Err', 'Err'],
                ['(',  'Err', '_2', 'Err', 'Err', 'Err'],
                [')',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['*',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['+',  'Err', '_2', 'Err', 'Err', 'Err'],
                [',',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['-',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['.',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['/',  'Err', '_2', 'Err', 'Err', 'Err'],
                [':',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['<',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['=',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['>',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['?',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['@',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['[',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['\\', 'Err', '_2', 'Err', 'Err', 'Err'],
                [']',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['^',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['_',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['`',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['{',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['|',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['}',  'Err', '_2', 'Err', 'Err', 'Err'],
                ['~',  'Err', '_2', 'Err', 'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['F']),
            'G': {
                'char': set(['F']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'String',
        'valid': True,
        'expressions': [
            ('str', '"[^"]*"')
        ],
        'DFA': {
            'Q': set(['S', '_', 'F', 'Err']),
            'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
            'T': [
                [' ',  'S',   '_', 'F',   'Err'],
                ['#',  'Err', '_', 'Err', 'Err'],
                [';',  'Err', '_', 'Err', 'Err'],
                ['\n', 'Err', '_', 'Err', 'Err'],
                ['0',  'Err', '_', 'Err', 'Err'],
                ['1',  'Err', '_', 'Err', 'Err'],
                ['2',  'Err', '_', 'Err', 'Err'],
                ['3',  'Err', '_', 'Err', 'Err'],
                ['4',  'Err', '_', 'Err', 'Err'],
                ['5',  'Err', '_', 'Err', 'Err'],
                ['6',  'Err', '_', 'Err', 'Err'],
                ['7',  'Err', '_', 'Err', 'Err'],
                ['8',  'Err', '_', 'Err', 'Err'],
                ['9',  'Err', '_', 'Err', 'Err'],
                [' ',  'Err', '_', 'Err', 'Err'],
                ['\t', 'Err', '_', 'Err', 'Err'],
                ['\v', 'Err', '_', 'Err', 'Err'],
                ['\f', 'Err', '_', 'Err', 'Err'],
                ['\r', 'Err', '_', 'Err', 'Err'],
                ['a',  'Err', '_', 'Err', 'Err'],
                ['b',  'Err', '_', 'Err', 'Err'],
                ['c',  'Err', '_', 'Err', 'Err'],
                ['d',  'Err', '_', 'Err', 'Err'],
                ['e',  'Err', '_', 'Err', 'Err'],
                ['f',  'Err', '_', 'Err', 'Err'],
                ['g',  'Err', '_', 'Err', 'Err'],
                ['h',  'Err', '_', 'Err', 'Err'],
                ['i',  'Err', '_', 'Err', 'Err'],
                ['j',  'Err', '_', 'Err', 'Err'],
                ['k',  'Err', '_', 'Err', 'Err'],
                ['l',  'Err', '_', 'Err', 'Err'],
                ['m',  'Err', '_', 'Err', 'Err'],
                ['n',  'Err', '_', 'Err', 'Err'],
                ['o',  'Err', '_', 'Err', 'Err'],
                ['p',  'Err', '_', 'Err', 'Err'],
                ['q',  'Err', '_', 'Err', 'Err'],
                ['r',  'Err', '_', 'Err', 'Err'],
                ['s',  'Err', '_', 'Err', 'Err'],
                ['t',  'Err', '_', 'Err', 'Err'],
                ['u',  'Err', '_', 'Err', 'Err'],
                ['v',  'Err', '_', 'Err', 'Err'],
                ['w',  'Err', '_', 'Err', 'Err'],
                ['x',  'Err', '_', 'Err', 'Err'],
                ['y',  'Err', '_', 'Err', 'Err'],
                ['z',  'Err', '_', 'Err', 'Err'],
                ['A',  'Err', '_', 'Err', 'Err'],
                ['B',  'Err', '_', 'Err', 'Err'],
                ['C',  'Err', '_', 'Err', 'Err'],
                ['D',  'Err', '_', 'Err', 'Err'],
                ['E',  'Err', '_', 'Err', 'Err'],
                ['F',  'Err', '_', 'Err', 'Err'],
                ['G',  'Err', '_', 'Err', 'Err'],
                ['H',  'Err', '_', 'Err', 'Err'],
                ['I',  'Err', '_', 'Err', 'Err'],
                ['J',  'Err', '_', 'Err', 'Err'],
                ['K',  'Err', '_', 'Err', 'Err'],
                ['L',  'Err', '_', 'Err', 'Err'],
                ['M',  'Err', '_', 'Err', 'Err'],
                ['N',  'Err', '_', 'Err', 'Err'],
                ['O',  'Err', '_', 'Err', 'Err'],
                ['P',  'Err', '_', 'Err', 'Err'],
                ['Q',  'Err', '_', 'Err', 'Err'],
                ['R',  'Err', '_', 'Err', 'Err'],
                ['S',  'Err', '_', 'Err', 'Err'],
                ['T',  'Err', '_', 'Err', 'Err'],
                ['U',  'Err', '_', 'Err', 'Err'],
                ['V',  'Err', '_', 'Err', 'Err'],
                ['W',  'Err', '_', 'Err', 'Err'],
                ['X',  'Err', '_', 'Err', 'Err'],
                ['Y',  'Err', '_', 'Err', 'Err'],
                ['Z',  'Err', '_', 'Err', 'Err'],
                ['!',  'Err', '_', 'Err', 'Err'],
                ['"',  '_',   'F', 'Err', 'Err'],
                ['$',  'Err', '_', 'Err', 'Err'],
                ['%',  'Err', '_', 'Err', 'Err'],
                ['&',  'Err', '_', 'Err', 'Err'],
                ['\'', 'Err', '_', 'Err', 'Err'],
                ['(',  'Err', '_', 'Err', 'Err'],
                [')',  'Err', '_', 'Err', 'Err'],
                ['*',  'Err', '_', 'Err', 'Err'],
                ['+',  'Err', '_', 'Err', 'Err'],
                [',',  'Err', '_', 'Err', 'Err'],
                ['-',  'Err', '_', 'Err', 'Err'],
                ['.',  'Err', '_', 'Err', 'Err'],
                ['/',  'Err', '_', 'Err', 'Err'],
                [':',  'Err', '_', 'Err', 'Err'],
                ['<',  'Err', '_', 'Err', 'Err'],
                ['=',  'Err', '_', 'Err', 'Err'],
                ['>',  'Err', '_', 'Err', 'Err'],
                ['?',  'Err', '_', 'Err', 'Err'],
                ['@',  'Err', '_', 'Err', 'Err'],
                ['[',  'Err', '_', 'Err', 'Err'],
                ['\\', 'Err', '_', 'Err', 'Err'],
                [']',  'Err', '_', 'Err', 'Err'],
                ['^',  'Err', '_', 'Err', 'Err'],
                ['_',  'Err', '_', 'Err', 'Err'],
                ['`',  'Err', '_', 'Err', 'Err'],
                ['{',  'Err', '_', 'Err', 'Err'],
                ['|',  'Err', '_', 'Err', 'Err'],
                ['}',  'Err', '_', 'Err', 'Err'],
                ['~',  'Err', '_', 'Err', 'Err']
            ],
            'S': 'S',
            'F': set(['F']),
            'G': {
                'str': set(['F']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Identifiers',
        'valid': True,
        'expressions': [
            ('id', '[_a-zA-Z][_a-zA-Z0-9]*')
        ],
        'DFA': {
            'Q': set(['Char', 'DigitOrChar', 'Err']),
            'V': set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'),
            'T': [
                [' ',  'Char',        'DigitOrChar', 'Err'],
                ['a',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['b',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['c',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['d',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['e',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['f',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['g',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['h',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['i',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['j',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['k',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['l',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['m',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['n',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['o',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['p',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['q',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['r',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['s',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['t',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['u',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['v',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['w',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['x',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['y',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['z',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['A',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['B',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['C',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['D',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['E',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['F',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['G',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['H',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['I',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['J',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['K',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['L',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['M',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['N',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['O',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['P',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['Q',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['R',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['S',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['T',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['U',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['V',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['W',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['X',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['Y',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['Z',  'DigitOrChar', 'DigitOrChar', 'Err'],
                ['0',  'Err',         'DigitOrChar', 'Err'],
                ['1',  'Err',         'DigitOrChar', 'Err'],
                ['2',  'Err',         'DigitOrChar', 'Err'],
                ['3',  'Err',         'DigitOrChar', 'Err'],
                ['4',  'Err',         'DigitOrChar', 'Err'],
                ['5',  'Err',         'DigitOrChar', 'Err'],
                ['6',  'Err',         'DigitOrChar', 'Err'],
                ['7',  'Err',         'DigitOrChar', 'Err'],
                ['8',  'Err',         'DigitOrChar', 'Err'],
                ['9',  'Err',         'DigitOrChar', 'Err'],
                ['_',  'DigitOrChar', 'DigitOrChar', 'Err']
            ],
            'S': 'Char',
            'F': set(['DigitOrChar']),
            'G': {
                'id': set(['DigitOrChar']),
                '_sink': set(['Err'])
            }
        }
    },
    {
        'name': 'Unbalanced Left Paren',
        'valid': False,
        'expressions': [
            ('invalid', '(foo|bar')
        ],
        'DFA': {}
    },
    {
        'name': 'Unbalanced Right Paren',
        'valid': False,
        'expressions': [
            ('invalid', 'foo|bar)')
        ],
        'DFA': {}
    },
    {
        'name': 'Invalid Escape Sequence',
        'valid': False,
        'expressions': [
            ('invalid', '\j')
        ],
        'DFA': {}
    },
    {
        'name': 'Empty Escape Sequence',
        'valid': False,
        'expressions': [
            ('invalid', '\\')
        ],
        'DFA': {}
    },
    {
        'name': 'Empty Expression',
        'valid': False,
        'expressions': [
            ('invalid', '')
        ],
        'DFA': {}
    },
    {
        'name': 'Empty Character Range/Class',
        'valid': False,
        'expressions': [
            ('class/range', '[]')
        ],
        'DFA': {}
    },
    {
        'name': 'Invalid Character',
        'valid': False,
        'expressions': [
            ('invalid', '\x99')
        ],
        'DFA': {}
    },
    {
        'name': ['Invalid Scanner Name'],
        'valid': False,
        'expressions': [
            ('invalid', 'foo')
        ],
        'DFA': {}
    },
    {
        'name': 'Invalid Scanner Tokens',
        'valid': False,
        'expressions': ["invalid"],
        'DFA': {}
    },
    {
        'name': 'Invalid Scanner Token Key',
        'valid': False,
        'expressions': [
            (True, 'invalid')
        ],
        'DFA': {}
    },
    {
        'name': 'Invalid Scanner Token Value',
        'valid': False,
        'expressions': [
            ('invalid', True)
        ],
        'DFA': {}
    },
    {
        'name': 'Invalid Expression * Arity',
        'valid': False,
        'expressions': [
            ('invalid', '*')
        ],
        'DFA': {}
    },
    {
        'name': 'Invalid Expression + Arity',
        'valid': False,
        'expressions': [
            ('invalid', '+')
        ],
        'DFA': {}
    },
    {
        'name': 'Invalid Expression ? Arity',
        'valid': False,
        'expressions': [
            ('invalid', '?')
        ],
        'DFA': {}
    },
    {
        'name': 'Invalid Expression | Arity',
        'valid': False,
        'expressions': [
            ('invalid', 'a|')
        ],
        'DFA': {}
    },
    {
        'name': 'Invalid Expression . Arity',
        'valid': False,
        'expressions': [
            ('invalid', 'a.')
        ],
        'DFA': {}
    },
]

# re-enable pylint errors.
# pylint: enable=bad-whitespace, line-too-long, anomalous-backslash-in-string
def run_tests():
    """
    The test driver which iterates over table defined tests and executes them
    accordingly, throwing a ValueError upon failure.
    """
    from itertools import permutations
    print 'FUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUCK'

    for test in TESTS:
        try:
            regular_grammar = RegularGrammar(test['name'], test['expressions'])
        except ValueError as regular_grammar_exception:
            if test['valid']:                   # test type (input output)
                raise regular_grammar_exception # Unexpected Failure (+-)
            continue                            # Expected Failure   (--)

        if not test['valid']:                   # Unexpected Pass    (-+)
            raise ValueError('Panic: Negative test passed without error')

        # Failure checking for:  Expected Pass      (++)

        if regular_grammar.name() != test['name']:
            raise ValueError('Error: Incorrect DFA name returned')

        expressions = regular_grammar.expressions()

        if len(expressions) != len(test['expressions']):
            raise ValueError('Error: Incorrect expression count in grammar')

        idx = 0
        expressions = sorted(expressions, key=lambda x: x[0])
        test['expressions'] = sorted(test['expressions'], key=lambda x: x[0])
        for name, pattern in test['expressions']:
            _name, _pattern = expressions[idx]
            idx += 1
            if _name != name or _pattern != pattern:
                raise ValueError('Error: Incorrect token name/pattern created')

        V = regular_grammar.alphabet()
        if V != test['DFA']['V']:
            raise ValueError('Error: Incorrect alphabet produced')

        Q = regular_grammar.states()
        if len(Q) != len(test['DFA']['Q']):
            raise ValueError('Error: Incorrect number of states produced')

        F = regular_grammar.accepting()
        if len(F) != len(test['DFA']['F']):
            raise ValueError('Error: Incorrect number of finish states')

        G = regular_grammar.types()
        if len(G) != len(test['DFA']['G']):
            raise ValueError('Error: Incorrect number of types')

        state, symbol, T = regular_grammar.transitions()
        if len(T) != len(test['DFA']['T'])-1 or \
           (T and len(T[0]) != len(test['DFA']['T'][0])-1):
            raise ValueError('Error: Incorrect number of transitions produced')

        # Check if DFA's are isomorphic by attempting to find a bijection
        # between them since they both already look very 'similar'.
        Qp = test['DFA']['Q']
        S = regular_grammar.start()

        _state, _symbol, Tp = dict(), dict(), list()
        if T:
            _state = {s:idx for idx, s in enumerate(test['DFA']['T'].pop(0)[1:])}
            _symbol = {s:idx for idx, s in enumerate([row.pop(0) for row in test['DFA']['T']])}
            Tp = test['DFA']['T']

        found = False
        for _map in (dict(zip(Q, perm)) for perm in permutations(Qp, len(Qp))):
            if _map[S] != test['DFA']['S']:
                continue
            if not all([_map[f] in test['DFA']['F'] for f in F]):
                continue
            if not all([{_map[s] for s in types} == \
               test['DFA']['G'].get(name, set()) for name, types in G.items()]):
                continue
            if not all([all([_map[T[symbol[v]][state[q]]] == \
               Tp[_symbol[v]][_state[_map[q]]] for q in Q]) for v in V]):
                continue
            found = True
            break

        if not found:
            raise ValueError('Error: Non-isomorphic DFA produced')


if __name__ == '__main__':
    run_tests()
