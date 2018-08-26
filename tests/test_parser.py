# disable pylint spacing error to enable 'pretty/readable' transition tables.
# pylint: disable=anomalous-backslash-in-string, too-many-locals, too-many-statements, too-many-branches
"""
    **Testing for ContextFreeGrammar objects located in parser.py**

Testing is implemented in a table driven fashion using the black box method.
The tests may be run at the command line with the following invocation:

  $ python test_parser.py

If all tests passed no output will be produced. In the event of a failure a
ValueError is thrown with the appropriate error/failure message. Both positive
and negative tests cases are extensively tested.
"""
import os
import sys

TEST_DIR = os.path.dirname(__file__)
SRC_DIR = '../src'
sys.path.insert(0, os.path.abspath(os.path.join(TEST_DIR, SRC_DIR)))

from parser.parser import ContextFreeGrammar


TESTS = [
    {
        'name': 'Invalid Grammar: First/First Conflict',
        'valid': True,
        'productions': {
            '<S>': '<E> | <E> a',
            '<E>': 'b |'
        },
        'start': '<S>',
        'terminals': set(['a', 'b']),
        'nonterminals': set(['<S>', '<E>']),
        'first': {
            'a': set(['a']),
            'b': set(['b']),
            '<S>': set(['b', 'a', 1]),
            '<E>': set(['b', 1])
        },
        'follow': {
            '<S>': set([0]),
            '<E>': set([0, 'a'])
        },
        'rules': [
            ('<S>', ['<E>']),
            ('<S>', ['<E>', 'a']),
            ('<E>', ['b']),
            ('<E>', [])
        ],
        'table': [
            [' ', 'a', 0, 'b'],
            ['<S>', set([1]), set([0]), set([0, 1])],
            ['<E>', set([3]), set([3]), set([2])]
        ]
    },
    {
        'name': 'Invalid Grammar: First/Follow Conflict',
        'valid': True,
        'productions': {
            '<S>': '<A> a b',
            '<A>': 'a |'
        },
        'start': '<S>',
        'terminals': set(['a', 'b']),
        'nonterminals': set(['<S>', '<A>']),
        'first': {
            'a': set(['a']),
            'b': set(['b']),
            '<S>': set(['a']),
            '<A>': set(['a', 1])
        },
        'follow': {
            '<S>': set([0]),
            '<A>': set(['a'])
        },
        'rules': [
            ('<S>', ['<A>', 'a', 'b']),
            ('<A>', ['a']),
            ('<A>', [])
        ],
        'table': [
            [' ', 'a', 0, 'b'],
            ['<S>', set([0]), set([]), set([])],
            ['<A>', set([1, 2]), set([]), set([])]
        ]
    },
    {
        'name': 'Invalid Grammar: Left Recursion',
        'valid': True,
        'productions': {
            '<E>': '<E> <A> <T> | <T>',
            '<A>': '+ | -',
            '<T>': '<T> <M> <F> | <F>',
            '<M>': '*',
            '<F>': '( <E> ) | id'
        },
        'start': '<E>',
        'terminals': set(['(', ')', '+', '*', '-', 'id']),
        'nonterminals': set(['<E>', '<A>', '<T>', '<M>', '<F>']),
        'first': {
            '(': set(['(']),
            ')': set([')']),
            '+': set(['+']),
            '-': set(['-']),
            '*': set(['*']),
            'id': set(['id']),
            '<E>': set(['(', 'id']),
            '<A>': set(['+', '-']),
            '<T>': set(['(', 'id']),
            '<M>': set(['*']),
            '<F>': set(['(', 'id'])
        },
        'follow': {
            '<E>': set([0, '+', '-', ')']),
            '<A>': set(['(', 'id']),
            '<T>': set([0, '+', '-', '*', ')']),
            '<M>': set(['(', 'id']),
            '<F>': set([0, '+', '-', '*', ')'])
        },
        'rules': [
            ('<E>', ['<E>', '<A>', '<T>']),
            ('<E>', ['<T>']),
            ('<A>', ['+']),
            ('<A>', ['-']),
            ('<T>', ['<T>', '<M>', '<F>']),
            ('<T>', ['<F>']),
            ('<M>', ['*']),
            ('<F>', ['(', '<E>', ')']),
            ('<F>', ['id'])
        ],
        'table': [
            [' ', 0, 'id', ')', '(', '+', '*', '-'],
            ['<E>', set([]), set([0, 1]), set([]), set([0, 1]), set([]),
             set([]), set([])],
            ['<A>', set([]), set([]), set([]), set([]), set([2]), set([]),
             set([3])],
            ['<M>', set([]), set([]), set([]), set([]), set([]), set([6]),
             set([])],
            ['<T>', set([]), set([4, 5]), set([]), set([4, 5]), set([]),
             set([]), set([])],
            ['<F>', set([]), set([8]), set([]), set([7]), set([]), set([]),
             set([])]
        ]
    },
    {
        'name': False,
        'valid': False,
        'productions': {
            'Invalid Name Type': '<E> | <E> a'
        },
        'start': '<S>',
        'terminals': None,
        'nonterminals': None,
        'first': None,
        'follow': None,
        'rules': None,
        'table': None
    },
    {
        'name': 'Invalid Start Type',
        'valid': False,
        'productions': {
            '<S>': '<E> | <E> a'
        },
        'start': False,
        'terminals': None,
        'nonterminals': None,
        'first': None,
        'follow': None,
        'rules': None,
        'table': None
    },
    {
        'name': 'Invalid Production Rules',
        'valid': False,
        'productions': {
            None: '<E> | <E> a'
        },
        'start': False,
        'terminals': None,
        'nonterminals': None,
        'first': None,
        'follow': None,
        'rules': None,
        'table': None
    },
    {
        'name': 'Invalid Nonterminal',
        'valid': False,
        'productions': {
            '<S>': None
        },
        'start': False,
        'terminals': None,
        'nonterminals': None,
        'first': None,
        'follow': None,
        'rules': None,
        'table': None
    },
    {
        'name': 'Valid Grammar: With Epsilon',
        'valid': True,
        'productions': {
            '<E>': '<T> <E\'>',
            '<E\'>': '<A> <T> <E\'> |',
            '<A>': '+ | - ',
            '<T>': '<F> <T\'>',
            '<T\'>': '<M> <F> <T\'> |',
            '<M>': '*',
            '<F>': '( <E> ) | id'
        },
        'start': '<E>',
        'terminals': set(['+', '-', '*', '(', ')', 'id']),
        'nonterminals': set(['<E>', '<E\'>', '<A>', '<T>', '<T\'>', '<M>',
                             '<F>']),
        'first': {
            '+': set(['+']),
            '-': set(['-']),
            '*': set(['*']),
            '(': set(['(']),
            ')': set([')']),
            'id': set(['id']),
            '<E>': set(['(', 'id']),
            '<E\'>': set(['+', '-', 1]),
            '<A>': set(['+', '-']),
            '<T>': set(['(', 'id']),
            '<T\'>': set([1, '*']),
            '<M>': set(['*']),
            '<F>': set(['(', 'id'])
        },
        'follow': {
            '<E>': set([0, ')']),
            '<E\'>': set([0, ')']),
            '<A>': set(['(', 'id']),
            '<T>': set([')', '+', '-', 0]),
            '<T\'>': set([')', '+', '-', 0]),
            '<M>': set(['(', 'id']),
            '<F>': set([')', '+', '-', '*', 0])
        },
        'rules': [
            ('<E>', ['<T>', '<E\'>']),
            ('<E\'>', ['<A>', '<T>', '<E\'>']),
            ('<E\'>', []),
            ('<A>', ['+']),
            ('<A>', ['-']),
            ('<T>', ['<F>', '<T\'>']),
            ('<T\'>', ['<M>', '<F>', '<T\'>']),
            ('<T\'>', []),
            ('<M>', ['*']),
            ('<F>', ['(', '<E>', ')']),
            ('<F>', ['id'])
        ],
        'table': [
            [' ', 0, 'id', ')', '(', '+', '*', '-'],
            ['<E>', set([]), set([0]), set([]), set([0]), set([]), set([]),
             set([])],
            ['<E\'>', set([2]), set([]), set([2]), set([]), set([1]),
             set([]), set([1])],
            ['<A>', set([]), set([]), set([]), set([]), set([3]), set([]),
             set([4])],
            ['<T>', set([]), set([5]), set([]), set([5]), set([]), set([]),
             set([])],
            ['<T\'>', set([7]), set([]), set([7]), set([]), set([7]),
             set([6]), set([7])],
            ['<M>', set([]), set([]), set([]), set([]), set([]), set([8]),
             set([])],
            ['<F>', set([]), set([10]), set([]), set([9]), set([]),
             set([]), set([])]
        ]
    },
    {
        'name': 'Valid Grammar: No Epsilon',
        'valid': True,
        'productions': {
            '<S>': '<A> a <A> b | <B> b <B> a',
            '<A>': '',
            '<B>': ''
        },
        'start': '<S>',
        'terminals': set(['a', 'b']),
        'nonterminals': set(['<S>', '<A>', '<B>']),
        'first': {
            'a': set(['a']),
            'b': set(['b']),
            '<S>': set(['a', 'b']),
            '<A>': set([1]),
            '<B>': set([1])
        },
        'follow': {
            '<S>': set([0]),
            '<A>': set(['b', 'a']),
            '<B>': set(['a', 'b'])
        },
        'rules': [
            ('<S>', ['<A>', 'a', '<A>', 'b']),
            ('<S>', ['<B>', 'b', '<B>', 'a']),
            ('<A>', []),
            ('<B>', [])
        ],
        'table': [
            [' ', 0, 'a', 'b'],
            ['<S>', set([]), set([0]), set([1])],
            ['<A>', set([]), set([2]), set([2])],
            ['<B>', set([]), set([3]), set([3])]
        ]
    },
    {
        'name': 'Valid Grammar: Simple language',
        'valid': True,
        'productions': {
            '<STMT>': 'if <EXPR> then <STMT>\
                        | while <EXPR> do <STMT>\
                        | <EXPR>',
            '<EXPR>': '<TERM> -> id\
                        | zero? <TERM>\
                        | not <EXPR>\
                        | ++ id\
                        | -- id',
            '<TERM>': 'id | constant',
            '<BLOCK>': '<STMT> | { <STMTS> }',
            '<STMTS>': '<STMT> <STMTS> |'
        },
        'start': '<STMTS>',
        'terminals': set(['if', 'then', 'while', 'do', '->', 'zero?',
                          'not', '++', '--', 'id', 'constant', '{', '}']),
        'nonterminals': set(['<STMT>', '<STMTS>', '<BLOCK>', '<TERM>',
                             '<EXPR>']),
        'first': {
            'if': set(['if']),
            'then': set(['then']),
            'while': set(['while']),
            'do': set(['do']),
            '->': set(['->']),
            'zero?': set(['zero?']),
            'not': set(['not']),
            '++': set(['++']),
            '--': set(['--']),
            'id': set(['id']),
            'constant': set(['constant']),
            '{': set(['{']),
            '}': set(['}']),
            '<STMT>': set(['constant', '++', 'zero?', 'while', 'not', '--',
                           'id', 'if']),
            '<STMTS>': set([1, 'constant', '++', 'zero?', 'while', 'not',
                            '--', 'id', 'if']),
            '<BLOCK>': set(['constant', '++', 'zero?', 'while', 'not', '--',
                            '{', 'id', 'if']),
            '<TERM>': set(['constant', 'id']),
            '<EXPR>': set(['++', 'not', 'constant', 'zero?', '--', 'id'])
        },
        'follow': {
            '<STMT>': set([0, 'constant', '++', 'not', 'while', 'zero?',
                           '--', '}', 'id', 'if']),
            '<STMTS>': set([0, '}']),
            '<BLOCK>': set([]),
            '<TERM>': set([0, 'then', 'constant', 'do', 'not', 'id', 'if',
                           '++', '--', 'while', 'zero?', '->', '}']),
            '<EXPR>': set([0, 'then', 'constant', 'do', '++', '--',
                           'while', 'not', 'zero?', '}', 'id', 'if'])
        },
        'rules': [
            ('<STMT>', ['if', '<EXPR>', 'then', '<STMT>']),
            ('<STMT>', ['while', '<EXPR>', 'do', '<STMT>']),
            ('<STMT>', ['<EXPR>']),
            ('<EXPR>', ['<TERM>', '->', 'id']),
            ('<EXPR>', ['zero?', '<TERM>']),
            ('<EXPR>', ['not', '<EXPR>']),
            ('<EXPR>', ['++', 'id']),
            ('<EXPR>', ['--', 'id']),
            ('<TERM>', ['id']),
            ('<TERM>', ['constant']),
            ('<BLOCK>', ['<STMT>']),
            ('<BLOCK>', ['{', '<STMTS>', '}']),
            ('<STMTS>', ['<STMT>', '<STMTS>']),
            ('<STMTS>', [])
        ],
        'table': [
            [' ', 0, 'then', 'constant', 'do', '++', 'zero?', 'while',
             'not', '--', '{', '->', '}', 'id', 'if'],
            ['<STMT>', set([]), set([]), set([2]), set([]), set([2]),
             set([2]), set([1]), set([2]), set([2]), set([]), set([]),
             set([]), set([2]), set([0])],
            ['<EXPR>', set([]), set([]), set([3]), set([]), set([6]),
             set([4]), set([]), set([5]), set([7]), set([]), set([]),
             set([]), set([3]), set([])],
            ['<BLOCK>', set([]), set([]), set([10]), set([]), set([10]),
             set([10]), set([10]), set([10]), set([10]), set([11]),
             set([]), set([]), set([10]), set([10])],
            ['<STMTS>', set([13]), set([]), set([12]), set([]), set([12]),
             set([12]), set([12]), set([12]), set([12]), set([]), set([]),
             set([13]), set([12]), set([12])],
            ['<TERM>', set([]), set([]), set([9]), set([]), set([]),
             set([]), set([]), set([]), set([]), set([]), set([]), set([]),
             set([8]), set([])]
        ]
    },
    {
        'name': 'Valid Grammar: JSON',
        'valid': True,
        'productions': {
            '<VALUE>': 'string | number | bool | null | <OBJECT> | <ARRAY>',
            '<OBJECT>': '{ <OBJECT\'>',
            '<OBJECT\'>': '} | <MEMBERS> }',
            '<MEMBERS>': '<PAIR> <MEMBERS\'>',
            '<PAIR>': 'string : <VALUE>',
            '<MEMBERS\'>': ', <MEMBERS> |',
            '<ARRAY>': '[ <ARRAY\'>',
            '<ARRAY\'>': '] | <ELEMENTS> ]',
            '<ELEMENTS>': '<VALUE> <ELEMENTS\'>',
            '<ELEMENTS\'>': ', <ELEMENTS> |'
        },
        'start': '<VALUE>',
        'terminals': set(['{', '}', ',', '[', ']', ':', 'string', 'number',
                          'bool', 'null']),
        'nonterminals': set(['<VALUE>', '<OBJECT>', '<OBJECT\'>',
                             '<MEMBERS>', '<PAIR>', '<MEMBERS\'>',
                             '<ARRAY>', '<ARRAY\'>', '<ELEMENTS>',
                             '<ELEMENTS\'>']),
        'first': {
            '{': set(['{']),
            '}': set(['}']),
            ',': set([',']),
            '[': set(['[']),
            ']': set([']']),
            ':': set([':']),
            'string': set(['string']),
            'number': set(['number']),
            'bool': set(['bool']),
            'null': set(['null']),
            '<VALUE>': set(['string', 'number', 'bool', 'null', '{', '[']),
            '<OBJECT>': set(['{']),
            '<OBJECT\'>': set(['}', 'string']),
            '<MEMBERS>': set(['string']),
            '<PAIR>': set(['string']),
            '<MEMBERS\'>': set([1, ',']),
            '<ARRAY>': set(['[']),
            '<ARRAY\'>': set([']', 'string', 'number', 'bool', 'null', '{',
                              '[']),
            '<ELEMENTS>': set(['string', 'number', 'bool', 'null', '{',
                               '[']),
            '<ELEMENTS\'>': set([1, ','])
        },
        'follow': {
            '<VALUE>': set([0, ']', '}', ',']),
            '<OBJECT>': set([0, ']', '}', ',']),
            '<OBJECT\'>': set([0, ']', '}', ',']),
            '<MEMBERS>': set(['}']),
            '<PAIR>': set(['}', ',']),
            '<MEMBERS\'>': set(['}']),
            '<ARRAY>': set([0, ']', '}', ',']),
            '<ARRAY\'>': set([0, ']', '}', ',']),
            '<ELEMENTS>': set([']']),
            '<ELEMENTS\'>': set([']'])
        },
        'rules': [
            ('<VALUE>', ['string']),
            ('<VALUE>', ['number']),
            ('<VALUE>', ['bool']),
            ('<VALUE>', ['null']),
            ('<VALUE>', ['<OBJECT>']),
            ('<VALUE>', ['<ARRAY>']),
            ('<OBJECT>', ['{', '<OBJECT\'>']),
            ('<OBJECT\'>', ['}']),
            ('<OBJECT\'>', ['<MEMBERS>', '}']),
            ('<MEMBERS>', ['<PAIR>', '<MEMBERS\'>']),
            ('<PAIR>', ['string', ':', '<VALUE>']),
            ('<MEMBERS\'>', [',', '<MEMBERS>']),
            ('<MEMBERS\'>', []),
            ('<ARRAY>', ['[', '<ARRAY\'>']),
            ('<ARRAY\'>', [']']),
            ('<ARRAY\'>', ['<ELEMENTS>', ']']),
            ('<ELEMENTS>', ['<VALUE>', '<ELEMENTS\'>']),
            ('<ELEMENTS\'>', [',', '<ELEMENTS>']),
            ('<ELEMENTS\'>', [])
        ],
        'table': [[' ', 0, ':', 'string', ']', 'number', ',', 'bool', '{',
                   'null', '}', '['],
                  ['<PAIR>', set([]), set([]), set([10]), set([]),
                   set([]), set([]), set([]), set([]), set([]),
                   set([]), set([])],
                  ['<VALUE>', set([]), set([]), set([0]), set([]),
                   set([1]), set([]), set([2]), set([4]), set([3]),
                   set([]), set([5])],
                  ['<OBJECT>', set([]), set([]), set([]), set([]),
                   set([]), set([]), set([]), set([6]), set([]),
                   set([]), set([])],
                  ['<ELEMENTS>', set([]), set([]), set([16]), set([]),
                   set([16]), set([]), set([16]), set([16]), set([16]),
                   set([]), set([16])],
                  ['<OBJECT\'>', set([]), set([]), set([8]), set([]),
                   set([]), set([]), set([]), set([]), set([]),
                   set([7]), set([])],
                  ['<MEMBERS\'>', set([]), set([]), set([]), set([]),
                   set([]), set([11]), set([]), set([]), set([]),
                   set([12]), set([])],
                  ['<ARRAY>', set([]), set([]), set([]), set([]),
                   set([]), set([]), set([]), set([]), set([]),
                   set([]), set([13])],
                  ['<MEMBERS>', set([]), set([]), set([9]), set([]),
                   set([]), set([]), set([]), set([]), set([]),
                   set([]), set([])],
                  ['<ELEMENTS\'>', set([]), set([]), set([]), set([18]),
                   set([]), set([17]), set([]), set([]), set([]),
                   set([]), set([])],
                  ["<ARRAY'>", set([]), set([]), set([15]), set([14]),
                   set([15]), set([]), set([15]), set([15]), set([15]),
                   set([]), set([15])]
                 ]
    },
    {
        'name': 'Valid Grammar: INI',
        'valid': True,
        'productions': {
            '<INI>': '<SECTION> <INI> |',
            '<SECTION>': '<HEADER> <SETTINGS>',
            '<HEADER>': '[ string ]',
            '<SETTINGS>': '<KEY> <SEP> <VALUE> <SETTINGS> |',
            '<KEY>': 'string',
            '<SEP>': ': | =',
            '<VALUE>': 'string | number | bool'
        },
        'start': '<INI>',
        'terminals': set(['string', 'number', 'bool', ':', '=', '[', ']']),
        'nonterminals': set(['<INI>', '<SECTION>', '<HEADER>',
                             '<SETTINGS>', '<KEY>', '<SEP>', '<VALUE>']),
        'first': {
            'string': set(['string']),
            'number': set(['number']),
            'bool': set(['bool']),
            ':': set([':']),
            '=': set(['=']),
            '[': set(['[']),
            ']': set([']']),
            '<INI>': set([1, '[']),
            '<SECTION>': set(['[']),
            '<HEADER>': set(['[']),
            '<SETTINGS>': set([1, 'string']),
            '<KEY>': set(['string']),
            '<SEP>': set([':', '=']),
            '<VALUE>': set(['string', 'number', 'bool'])
        },
        'follow': {
            '<INI>': set([0]),
            '<SECTION>': set([0, '[']),
            '<HEADER>': set([0, '[', 'string']),
            '<SETTINGS>': set([0, '[']),
            '<KEY>': set([':', '=']),
            '<SEP>': set(['string', 'number', 'bool']),
            '<VALUE>': set([0, '[', 'string'])
        },
        'rules': [
            ('<INI>', ['<SECTION>', '<INI>']),
            ('<INI>', []),
            ('<SECTION>', ['<HEADER>', '<SETTINGS>']),
            ('<HEADER>', ['[', 'string', ']']),
            ('<SETTINGS>', ['<KEY>', '<SEP>', '<VALUE>', '<SETTINGS>']),
            ('<SETTINGS>', []),
            ('<KEY>', ['string']),
            ('<SEP>', [':']),
            ('<SEP>', ['=']),
            ('<VALUE>', ['string']),
            ('<VALUE>', ['number']),
            ('<VALUE>', ['bool'])
        ],
        'table': [[' ', 0, 'bool', 'string', '=', '[', ':', ']', 'number'],
                  ['<VALUE>', set([]), set([11]), set([9]), set([]),
                   set([]), set([]), set([]), set([10])],
                  ['<KEY>', set([]), set([]), set([6]), set([]),
                   set([]), set([]), set([]), set([])],
                  ['<SETTINGS>', set([5]), set([]), set([4]), set([]),
                   set([5]), set([]), set([]), set([])],
                  ['<SECTION>', set([]), set([]), set([]), set([]),
                   set([2]), set([]), set([]), set([])],
                  ['<HEADER>', set([]), set([]), set([]), set([]),
                   set([3]), set([]), set([]), set([])],
                  ['<SEP>', set([]), set([]), set([]), set([8]),
                   set([]), set([7]), set([]), set([])],
                  ['<INI>', set([1]), set([]), set([]), set([]),
                   set([0]), set([]), set([]), set([])],
                 ]
    }
]

# re-enable pylint errors.
# pylint: enable=anomalous-backslash-in-string
def run_tests():
    """
    The test driver which iterates over table defined tests and executes them
    accordingly, throwing a ValueError upon failure.
    """
    for test in TESTS:
        try:
            name = test['name']
            productions = test['productions']
            start = test['start']
            context_free_grammar = ContextFreeGrammar(name, productions, start)
        except ValueError as context_free_grammar_exception:
            if test['valid']:                        # test type (input output)
                raise context_free_grammar_exception # Unexpected Failure (+-)
            continue                                 # Expected Failure   (--)

        if not test['valid']:                        # Unexpected Pass    (-+)
            raise ValueError('Panic: Negative test passed without error')

        # Failure checking for:  Expected Pass      (++)

        if context_free_grammar.name() != test['name']:
            raise ValueError('Invalid name produced')

        if context_free_grammar.start() != test['start']:
            raise ValueError('Invalid start production produced')

        if context_free_grammar.terminals() != test['terminals']:
            raise ValueError('Invalid terminal set produced')

        if context_free_grammar.nonterminals() != test['nonterminals']:
            raise ValueError('Invalid nonterminal set produced')

        first = context_free_grammar.first()
        if len(first) != len(test['first']):
            raise ValueError('Invalid first set size produced')

        for elem in test['first']:
            if first.get(elem, None) != test['first'][elem]:
                raise ValueError('Invalid first set produced')

        follow = context_free_grammar.follow()
        if len(follow) != len(test['follow']):
            raise ValueError('Invalid follow set size produced')

        for elem in test['follow']:
            if follow.get(elem, None) != test['follow'][elem]:
                raise ValueError('Invalid follow set produced')

        rules = context_free_grammar.rules()
        if len(rules) != len(test['rules']):
            raise ValueError('Invalid number of table rules produced')

        _map = {}
        for (idx, (nonterminal, rule)) in enumerate(rules):
            found = False
            for (_idx, (_nonterminal, _rule)) in enumerate(test['rules']):
                if nonterminal == _nonterminal and \
                   len(rule) == len(_rule) and \
                   all([rule[i] == e for i, e in enumerate(_rule)]):
                    _map[idx] = _idx
                    found = True
                    break

            if not found:
                raise ValueError('Invalid production rule produced')

        _cols = {t:i for i, t in enumerate(test['table'].pop(0)[1:])}
        _rows = {n:i for i, n in enumerate([r.pop(0) for r in test['table']])}

        table, rows, cols = context_free_grammar.table()
        if len(rows) != len(_rows) or set(rows.keys()) ^ set(_rows.keys()):
            raise ValueError('Invalid number of table row headers produced')

        if len(cols) != len(_cols) or set(cols.keys()) ^ set(_cols.keys()):
            raise ValueError('Invalid number of table column headers produced')

        if len(table) != len(test['table']):
            raise ValueError('Invalid number of table rows produced')

        if not all([len(table[i]) == len(r) for i, r in enumerate(test['table'])]):
            raise ValueError('Invalid number of table columns produced')

        for row in rows:
            for col in cols:
                produced = {_map[elem] for elem in table[rows[row]][cols[col]]}
                expected = test['table'][_rows[row]][_cols[col]]
                if produced != expected:
                    raise ValueError('Invalid table value produced')


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(os.path.dirname(__file__))

    run_tests()
