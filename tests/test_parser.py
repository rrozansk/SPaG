"""
Testing for ContextFreeGrammar objects located in src/parser/parser.py
"""
import pytest
from scanner_parser_generator.parser import ContextFreeGrammar


class TestParser(object):
    """
    A test suite for testing the ContextFreeGrammar object.
    """

    @staticmethod
    def _compare_first_sets(expected, actual):
        """
        Compare the expected and actual first sets.
        """
        assert len(expected) == len(actual), 'Invalid first set size produced'

        for elem, items in actual.items():
            assert expected.get(elem, None) == items, \
            'Invalid first set produced'

    @staticmethod
    def _compare_follow_sets(expected, actual):
        """
        Compare the expected and actual follow sets.
        """
        assert len(expected) == len(actual), 'Invalid follow set size produced'

        for elem, items in actual.items():
            assert expected.get(elem, None) == items, \
            'Invalid follow set produced'

    @staticmethod
    def _compare_rules(expected, actual):
        """
        Compare the expected and actual production rules and return a mapping
        between the two for use with table comparison.
        """
        assert len(expected) == len(actual), 'Invalid number of rules produced'

        mapping = {}

        for (idx, (nonterminal, rule)) in enumerate(actual):
            found = False
            for (_idx, (_nonterminal, _rule)) in enumerate(expected):
                if nonterminal == _nonterminal and \
                   len(rule) == len(_rule) and \
                   all([rule[i] == e for i, e in enumerate(_rule)]):
                    mapping[idx] = _idx
                    found = True
                    break

            assert found, 'Invalid production rule produced'

        return mapping

    @staticmethod
    def _compare_tables(expected, actual, _map):
        """
        Compare the expected and actual tables with the help of the mapping
        between rules.
        """
        _cols = {t:i for i, t in enumerate(expected.pop(0)[1:])}
        _rows = {n:i for i, n in enumerate([r.pop(0) for r in expected])}

        table, rows, cols = actual
        assert len(rows) == len(_rows) and \
               not set(rows.keys()) ^ set(_rows.keys()), \
               'Invalid number of table row headers produced'

        assert len(cols) == len(_cols) and \
               not set(cols.keys()) ^ set(_cols.keys()), \
               'Invalid number of table column headers produced'

        assert len(table) == len(expected), \
               'Invalid number of table rows produced'

        assert all([len(table[i]) == len(r) for i, r in enumerate(expected)]), \
               'Invalid number of table columns produced'

        for row in rows:
            for col in cols:
                _actual = {_map[elem] for elem in table[rows[row]][cols[col]]}
                _expected = expected[_rows[row]][_cols[col]]

                assert _expected == _actual, 'Invalid table value produced'

                assert len(_expected) < 2, 'conflict present in parse table'

    @staticmethod
    def _run(**kwargs):
        """
        The 'main' for testing which creates the required object and compares
        the results are what was expected, failing appropriately if they are
        not.
        """
        context_free_grammar = ContextFreeGrammar(kwargs['name'],
                                                  kwargs['productions'],
                                                  kwargs['start'])

        assert context_free_grammar.name() == kwargs['name'], \
               'Invalid name produced'

        assert context_free_grammar.start() == kwargs['start'], \
               'Invalid start production produced'

        assert context_free_grammar.terminals() == kwargs['terminals'], \
               'Invalid terminal set produced'

        assert context_free_grammar.nonterminals() == kwargs['nonterminals'], \
              'Invalid nonterminal set produced'

        TestParser._compare_first_sets(kwargs['first'],
                                       context_free_grammar.first())

        TestParser._compare_follow_sets(kwargs['follow'],
                                        context_free_grammar.follow())

        mapping = TestParser._compare_rules(kwargs['rules'],
                                            context_free_grammar.rules())

        TestParser._compare_tables(kwargs['table'],
                                   context_free_grammar.table(),
                                   mapping)

    @staticmethod
    @pytest.mark.xfail(
        reason='Name is not of type string.',
        raises=TypeError,
    )
    def test_name_invalid():
        """
        Ensure a TypeError is raised when constructing a ContextFreeGrammar
        object if the name is not of type string.
        """
        TestParser._run(**{
            'name': False,
            'productions': {'<S>': ''},
            'start': '<S>',
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Name must be non empty.',
        raises=ValueError,
    )
    def test_name_empty():
        """
        Ensure a ValueError is raised when constructing a ContextFreeGrammar
        object if the name is an empty string.
        """
        TestParser._run(**{
            'name': '',
            'productions': {'<S>': ''},
            'start': '<S>',
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Start is not of type string.',
        raises=TypeError,
    )
    def test_start_invalid():
        """
        Ensure a TypeError is raised when constructing a ContextFreeGrammar
        object if the start production is not of type string.
        """
        TestParser._run(**{
            'name': 'Invalid Start Type',
            'productions': {'<S>': ''},
            'start': False,
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Start must be non empty.',
        raises=ValueError,
    )
    def test_start_empty():
        """
        Ensure a ValueError is raised when constructing a ContextFreeGrammar
        object if the start production is an empty string.
        """
        TestParser._run(**{
            'name': 'Empty Start',
            'productions': {'<S>': ''},
            'start': '',
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Start must be present in given productions.',
        raises=ValueError,
    )
    def test_start_missing():
        """
        Ensure a ValueError is raised when constructing a ContextFreeGrammar
        object if the start production is missing from the production rules.
        """
        TestParser._run(**{
            'name': 'Empty Start',
            'productions': {'<A>': ''},
            'start': '<S>',
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Productions is not of type dict.',
        raises=TypeError,
    )
    def test_production_invalid():
        """
        Ensure a TypeError is raised when constructing a ContextFreeGrammar
        object if the productions are not of type dict.
        """
        TestParser._run(**{
            'name': 'Invalid Production Rules',
            'productions': None,
            'start': '<invalid>',
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Productions must be non empty.',
        raises=ValueError,
    )
    def test_production_empty():
        """
        Ensure a ValueError is raised when constructing a ContextFreeGrammar
        object if the productions are an empty dict.
        """
        TestParser._run(**{
            'name': 'Invalid Production Rules',
            'productions': {},
            'start': '<invalid>',
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Productions nonterminals are not of type string.',
        raises=TypeError,
    )
    def test_production_nonterm_invalid():
        """
        Ensure a TypeError is raised when constructing a ContextFreeGrammar
        object if the productions nonterminals are not of type string.
        """
        TestParser._run(**{
            'name': 'Invalid Production Rules',
            'productions': {
                '<A>': '<A> | <A> a',
                None: '<B> | <B> b'
            },
            'start': '<A>',
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Production nonterminals must be non empty.',
        raises=ValueError,
    )
    def test_production_nonterm_empty():
        """
        Ensure a ValueError is raised when constructing a ContextFreeGrammar
        object if the production nonterminals are empty strings.
        """
        TestParser._run(**{
            'name': 'Invalid Production Rules',
            'productions': {
                '': 'b',
                '<E>': '<E> | <E> a'
            },
            'start': '<E>',
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Productions rules are not of type string.',
        raises=TypeError,
    )
    def test_production_rule_invalid():
        """
        Ensure a TypeError is raised when constructing a ContextFreeGrammar
        object if the production rules are not of type string.
        """
        TestParser._run(**{
            'name': 'Invalid Nonterminal',
            'productions': {
                '<S>': None
            },
            'start': '<S>',
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='First/first conflict.',
        raises=AssertionError,
    )
    def test_conflict_first_first():
        """
        Valid input example which produces a first/first conflict.
        """
        TestParser._run(**{
            'name': 'First/First Conflict',
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
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='First/follow conflict.',
        raises=AssertionError,
    )
    def test_conflict_first_follow():
        """
        Valid input example but produces a first/follow conflict.
        """
        TestParser._run(**{
            'name': 'First/Follow Conflict',
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
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Left recursive.',
        raises=AssertionError,
    )
    def test_conflict_left_recursion():
        """
        Valid input example but produces some conflicts due to the use of left
        recursion.
        """
        TestParser._run(**{
            'name': 'Left Recursion',
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
        })

    @staticmethod
    def test_epsilon_absent():
        """
        Ensure the creation of a simple grammar goes as expected.
        """
        TestParser._run(**{
            'name': 'No Epsilon',
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
        })

    @staticmethod
    def test_epsilon_present():
        """
        Ensure the creation of a simple grammar containing an epsilon goes as
        expected.
        """
        TestParser._run(**{
            'name': 'Epsilon',
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
        })

    @staticmethod
    def test_simple_language():
        """
        Ensure the creation of a simple langugage grammar goes as expected.
        """
        TestParser._run(**{
            'name': 'Simple language',
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
        })

    @staticmethod
    def test_json():
        """
        Ensure the creation of the JSON grammar goes as expected.
        """
        TestParser._run(**{
            'name': 'JSON',
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
        })

    @staticmethod
    def test_ini():
        """
        Ensure the creation of the INI grammar goes as expected.
        """
        TestParser._run(**{
            'name': 'INI',
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
        })

    @staticmethod
    def test_lisp():
        """
        Ensure the creation of the Lisp grammar goes as expected.
        """
        TestParser._run(**{
            'name': 'Lisp',
            'productions': {
                '<expression>': '<atom> | <pair>',
                '<pair>': '( <expression> . <expression> )',
                '<atom>': 'symbol | character | string | boolean | int | float | nil',
            },
            'start': '<expression>',
            'terminals': set(['(', '.', ')', 'symbol', 'character', 'string',
                              'boolean', 'int', 'float', 'nil']),
            'nonterminals': set(['<atom>', '<pair>', '<expression>']),
            'first': {
                '(': set(['(']),
                '.': set(['.']),
                ')': set([')']),
                'symbol': set(['symbol']),
                'character': set(['character']),
                'string': set(['string']),
                'boolean': set(['boolean']),
                'int': set(['int']),
                'float': set(['float']),
                'nil': set(['nil']),
                '<atom>': set(['boolean', 'character', 'float', 'int', 'nil',
                               'string', 'symbol']),
                '<pair>': set(['(']),
                '<expression>': set(['(', 'boolean', 'character', 'float',
                                     'int', 'nil', 'string', 'symbol'])
            },
            'follow': {
                '<atom>': set([0, ')', '.']),
                '<pair>': set([0, ')', '.']),
                '<expression>': set([0, ')', '.'])
            },
            'rules': [
                ('<expression>', ['<atom>']),
                ('<expression>', ['<pair>']),
                ('<pair>', ['(', '<expression>', '.', '<expression>', ')']),
                ('<atom>', ['symbol']),
                ('<atom>', ['character']),
                ('<atom>', ['string']),
                ('<atom>', ['boolean']),
                ('<atom>', ['int']),
                ('<atom>', ['float']),
                ('<atom>', ['nil'])
            ],
            'table': [
                [' ', 0, 'symbol', 'character', 'string', 'boolean', 'int',
                 'float', 'nil', '(', '.', ')'],
                ['<expression>', set([]), set([0]), set([0]), set([0]),
                 set([0]), set([0]), set([0]), set([0]), set([1]), set([]),
                 set([])],
                ['<atom>', set([]), set([3]), set([4]), set([5]), set([6]),
                 set([7]), set([8]), set([9]), set([]), set([]), set([])],
                ['<pair>', set([]), set([]), set([]), set([]), set([]),
                 set([]), set([]), set([]), set([2]), set([]), set([])],
            ]
        })
