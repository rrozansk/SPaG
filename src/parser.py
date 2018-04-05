"""
 parser.py includes the implementation and testing of ContextFreeGrammar
 objects.

 The ContextFreeGrammar object represents a BNF style grammar which can be
 programatically transformed into a parse table for the given language. While
 it is possible for any grammar to be specified, only LL1 grammars are
 supported with the following requirements to successfully produce a parse
 table:

   1. No left recursion (both direct and indirect)
   2. Must be left factored
   3. No ambiguity

 If any of the above requirements are violated, or the grammer specified is not
 LL1, there will be a conflict set produced to show the issues in the grammar.

 Testing is implemented in a table driven fashion using the black box method.
 The tests may be run at the command line with the following invocation:

   $ python parser.py

 If all tests passed no output will be produced. In the event of a failure a
 ValueError is thrown with the appropriate error/failure message. Both positive
 and negative tests cases are extensively tested.
"""
from copy import deepcopy


class ContextFreeGrammar(object):
    """
    ContextFreeGrammar represents a Backus Normal Form (BNF) grammar which can
    be programatically transformed into a parse table.
    """

    EOI = 0  # end of input marker
    EPS = 1  # Epsilon marker

    _name = None
    _start = None
    _terms = None
    _nterms = None
    _first = None
    _follow = None
    _prods = None
    _rules = None
    _tbl = None

    def __init__(self, name, productions, start):
        """
        Attempt to initialize a Context Free Gramamr object with the specified
        name, production rules and start rule. Productions rules are a list
        where each individual item (production rule) is represented as tuple.
        The first element is the nonterminal symbol and the second element is a
        string containing the productions, seperated by a vertical bar (|). An
        empty production specifies an epsilon.

        If creation is unsuccessful a ValueWrror will be thrown, otherwise the
        results can be queried through the API provided below.

        Type: string x list[tuples] -> None | raise ValueError
        """
        if type(name) is not str:
            raise ValueError('Invalid Input: name must be a string')

        self._name = name

        if type(start) is not str:
            raise ValueError('Invalid Input: starting must be a string')

        self._start = start

        if type(productions) is not dict:
            raise ValueError('Invalid Input: productions must be a dict')

        self._prods = {}
        for nonterminal, rhs in productions.items():
            if type(nonterminal) is not str:
                raise ValueError('Invalid Input: nonterminal must be a string')

            if type(rhs) is not str:
                raise ValueError('Invalid Input: rules must be a string')

            rules = [rule.split() for rule in rhs.split('|')]
            self._prods[nonterminal] = rules

        nonterms = self._nonterminals()
        terms = self._terminals(nonterms)
        first = self._first(terms, nonterms)
        follow = self._follow(nonterms, first)
        table, rules = self._table(terms, nonterms, first, follow)
        conflicts = self._conflicts(table)

        self._nterms = nonterms
        self._terms = terms
        self._first = first
        self._follow = follow
        self._tbl = table
        self._rules = rules
        self._conflicts = conflicts

    def name(self):
        """
        Get the name of the Context Free Grammar.

        Type: None -> string
        """
        return deepcopy(self._name)

    def start(self):
        """
        Get the start state of the grammar.

        Type: None -> string
        """
        return deepcopy(self._start)

    def terminals(self):
        """
        Get the terminals of the grammar.

        Type: None -> set
        """
        return deepcopy(self._terms)

    def nonterminals(self):
        """
        Get the nonterminals of the grammar.

        Type: None -> set
        """
        return deepcopy(self._nterms)

    def first(self):
        """
        Get the first set of the grammar.

        Type: None -> set
        """
        return deepcopy(self._first)

    def follow(self):
        """
        Get the follow set of the grammar.

        Type: None -> set
        """
        return deepcopy(self._follow)

    def rules(self):
        """
        Get the production rules of the grammar.

        Type: None -> set
        """
        return deepcopy(self._rules)

    def table(self):
        """
        Get the parse table of the grammar.

        Type: None -> set
        """
        return deepcopy(self._tbl)

    def conflicts(self):
        """
        Get the conflicts in the grammar.

        Type: None -> set
        """
        return deepcopy(self._conflicts)

    def _nonterminals(self):
        """
        Report all non terminals which are just the production rules.

        Runtime: O(n) - linear to the number of productions.
        Type: None -> set
        """
        return set(self._prods.keys())

    def _terminals(self, nonterminals):
        """
        Report all literal symbols which appear in the grammar.

        Runtime: O(n) - linear to the number symbols in the grammar.
        Type: None -> set
        """
        terminals = set()
        for productions in self._prods.values():
            terminals.update(*productions)
        return terminals - nonterminals

    def _first_production(self, production, first):
        """
        Compute the first set of a single nonterminal's rhs/production.

        Runtime: O(n) - linear to the number of production rules.
        Type: None -> set
        """
        _first = set([self.EPS])
        for symbol in production:
            _first.update(first[symbol])
            if self.EPS not in first[symbol]:
                _first.discard(self.EPS)
                break
        return _first

    def _first(self, terminals, nonterminals):
        """
        Calculate the first set following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Runtime: O(?) - ?
        Type: None -> set
        """
        first = {}

        # foreach elem A of TERMS do _first[A] = {A}
        for terminal in terminals:
            first[terminal] = set([terminal])

        # foreach elem A of NONTERMS do _first[A] = {}
        for nonterminal in nonterminals:
            first[nonterminal] = set()

        # loop until nothing new happens updating the _first sets
        while True:
            changed = False

            for nonterminal, productions in self._prods.items():
                for production in productions:
                    new = self._first_production(production, first)
                    new.update(first[nonterminal])
                    if new != first[nonterminal]:
                        first[nonterminal] = new
                        changed = True

            if not changed:
                return first

    def _follow(self, nonterminals, first):
        """
        Calculate the follow set following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Runtime: O(?) - ?
        Type: None -> set
        """
        # foreach elem A of NONTERMS do Follow[A] = {}
        follow = {nonterminal: set() for nonterminal in nonterminals}

        # put $ (end of input marker) in Follow(<Start>)
        follow[self._start] = set([self.EOI])

        # loop until nothing new happens updating the Follow sets
        while True:
            changed = False

            for nonterminal, productions in self._prods.items():
                for production in productions:
                    for idx in range(0, len(production)):
                        if production[idx] in nonterminals:
                            new = self._first_production(production[idx+1:], first)
                            new.update(follow[production[idx]])
                            if self.EPS in new:
                                new.discard(self.EPS)
                                new.update(follow[nonterminal])

                            if new != follow[production[idx]]:
                                follow[production[idx]] = new
                                changed = True

            if not changed:
                return follow

    def _predict(self, nonterminal, production, first, follow):
        """
        Calculate the predict set following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Runtime: O(?) - ?
        Type: None -> set
        """
        predict = self._first_production(production, first)
        if self.EPS in predict:
            predict.discard(self.EPS)
            predict.update(follow[nonterminal])
        return predict

    def _table(self, terminals, nonterminals, first, follow):
        """
        Construct the LL(1) parsing table by finding predict sets.

        Runtime: O(?) - ?
        Type: None -> set
        """
        # build the table with row and column headers
        terminals = list(terminals)+[self.EOI]
        nonterminals = list(nonterminals)
        table = [[n]+[set() for _ in terminals] for n in nonterminals]
        table.insert(0, [' ']+terminals)

        # acct for row/column headers
        tlookup = {t:c for c,t in enumerate(terminals, 1)}
        nlookup = {n:c for c,n in enumerate(nonterminals, 1)}

        productions = []
        rule = 0
        for nonterminal, _productions in self._prods.items():
            idx_n = nlookup[nonterminal]
            for production in _productions:
                predict = self._predict(nonterminal, production, first, follow)
                for terminal in predict:
                    table[idx_n][tlookup[terminal]].add(rule)
                productions.append((rule, nonterminal, production))
                rule += 1

        return (table, productions)

    def _conflicts(self, table):
        """
        Grammar is ll(1) if parse table has (@maximum) a single entry per
        table slot conflicting for the predicitions.

        Runtime: O(?) - ?
        Type: None -> set
        """
        conflicts = []
        for row in range(1, len(table)):  # ignore column headers
            for col in range(1, len(table[row])):  # ignore row header
                if len(table[row][col]) > 1:
                    conflict = (table[row][0], table[0][col], table[row][col])
                    conflicts.append(conflict)
        return conflicts


if __name__ == "__main__":

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
                (0, '<S>', ['<E>']),
                (1, '<S>', ['<E>', 'a']),
                (2, '<E>', ['b']),
                (3, '<E>', [])
            ],
            'table': [
                [' ', 'a', 0, 'b'],
                ['<S>', set([1]), set([0]), set([0, 1])],
                ['<E>', set([3]), set([3]), set([2])]
            ],
            'conflicts': [('<S>', 'b', set([0, 1]))]
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
                (0, '<S>', ['<A>', 'a', 'b']),
                (1, '<A>', ['a']),
                (2, '<A>', [])
            ],
            'table': [
                [' ', 'a', 0, 'b'],
                ['<S>', set([0]), set([]), set([])],
                ['<A>', set([1, 2]), set([]), set([])]
            ],
            'conflicts': [('<A>', 'a', set([1, 2]))]
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
                (0, '<E>', ['<E>', '<A>', '<T>']),
                (1, '<E>', ['<T>']),
                (2, '<A>', ['+']),
                (3, '<A>', ['-']),
                (4, '<T>', ['<T>', '<M>', '<F>']),
                (5, '<T>', ['<F>']),
                (6, '<M>', ['*']),
                (7, '<F>', ['(', '<E>', ')']),
                (8, '<F>', ['id'])
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
            ],
            'conflicts': [
                ('<E>', 'id', set([0, 1])),
                ('<E>', '(', set([0, 1])),
                ('<T>', 'id', set([4, 5])),
                ('<T>', '(', set([4, 5]))
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
            'table': None,
            'conflicts': None
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
            'table': None,
            'conflicts': None
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
            'table': None,
            'conflicts': None
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
            'table': None,
            'conflicts': None
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
                (0, '<E>', ['<T>', '<E\'>']),
                (1, '<E\'>', ['<A>', '<T>', '<E\'>']),
                (2, '<E\'>', []),
                (3, '<A>', ['+']),
                (4, '<A>', ['-']),
                (5, '<T>', ['<F>', '<T\'>']),
                (6, '<T\'>', ['<M>', '<F>', '<T\'>']),
                (7, '<T\'>', []),
                (8, '<M>', ['*']),
                (9, '<F>', ['(', '<E>', ')']),
                (10, '<F>', ['id'])
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
            ],
            'conflicts': []
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
                (0, '<S>', ['<A>', 'a', '<A>', 'b']),
                (1, '<S>', ['<B>', 'b', '<B>', 'a']),
                (2, '<A>', []),
                (3, '<B>', [])
            ],
            'table': [
                [' ', 0, 'a', 'b'],
                ['<S>', set([]), set([0]), set([1])],
                ['<A>', set([]), set([2]), set([2])],
                ['<B>', set([]), set([3]), set([3])]
            ],
            'conflicts': [],
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
                (0, '<STMT>', ['if', '<EXPR>', 'then', '<STMT>']),
                (1, '<STMT>', ['while', '<EXPR>', 'do', '<STMT>']),
                (2, '<STMT>', ['<EXPR>']),
                (3, '<EXPR>', ['<TERM>', '->', 'id']),
                (4, '<EXPR>', ['zero?', '<TERM>']),
                (5, '<EXPR>', ['not', '<EXPR>']),
                (6, '<EXPR>', ['++', 'id']),
                (7, '<EXPR>', ['--', 'id']),
                (8, '<TERM>', ['id']),
                (9, '<TERM>', ['constant']),
                (10, '<BLOCK>', ['<STMT>']),
                (11, '<BLOCK>', ['{', '<STMTS>', '}']),
                (12, '<STMTS>', ['<STMT>', '<STMTS>']),
                (13, '<STMTS>', [])
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
            ],
            'conflicts': []
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
              (0, '<VALUE>', ['string']),
              (1, '<VALUE>', ['number']),
              (2, '<VALUE>', ['bool']),
              (3, '<VALUE>', ['null']),
              (4, '<VALUE>', ['<OBJECT>']),
              (5, '<VALUE>', ['<ARRAY>']),
              (6, '<OBJECT>', ['{', '<OBJECT\'>']),
              (7, '<OBJECT\'>', ['}']),
              (8, '<OBJECT\'>', ['<MEMBERS>', '}']),
              (9, '<MEMBERS>', ['<PAIR>', '<MEMBERS\'>']),
              (10, '<PAIR>', ['string', ':', '<VALUE>']),
              (11, '<MEMBERS\'>', [',', '<MEMBERS>']),
              (12, '<MEMBERS\'>', []),
              (13, '<ARRAY>', ['[', '<ARRAY\'>']),
              (14, '<ARRAY\'>', [']']),
              (15, '<ARRAY\'>', ['<ELEMENTS>', ']']),
              (16, '<ELEMENTS>', ['<VALUE>', '<ELEMENTS\'>']),
              (17, '<ELEMENTS\'>', [',', '<ELEMENTS>']),
              (18, '<ELEMENTS\'>', [])
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
                     ],
            'conflicts': []
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
              (0, '<INI>', ['<SECTION>', '<INI>']),
              (1, '<INI>', []),
              (2, '<SECTION>', ['<HEADER>', '<SETTINGS>']),
              (3, '<HEADER>', ['[', 'string', ']']),
              (4, '<SETTINGS>', ['<KEY>', '<SEP>', '<VALUE>', '<SETTINGS>']),
              (5, '<SETTINGS>', []),
              (6, '<KEY>', ['string']),
              (7, '<SEP>', [':']),
              (8, '<SEP>', ['=']),
              (9, '<VALUE>', ['string']),
              (10, '<VALUE>', ['number']),
              (11, '<VALUE>', ['bool'])
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
                     ],
            'conflicts': []
        }
    ]

    def make_rule_key(rule):
        return rule[1] + ''.join(rule[2])

    def row_header(row):
        return row[0]

    def conflict_key(conflict):
        return conflict[0]+conflict[1]

    for test in TESTS:
        try:
            name = test['name']
            productions = test['productions']
            start = test['start']
            grammar = ContextFreeGrammar(name, productions, start)
        except ValueError as e:
            if test['valid']:  # test type (input output)
                raise e        # Unexpected Failure (+-)
            continue           # Expected Failure   (--)

        if not test['valid']:  # Unexpected Pass    (-+)
            raise ValueError('Panic: Negative test passed without error')

        # Failure checking for:  Expected Pass      (++)

        if grammar.name() != test['name']:
            raise ValueError('Invalid name produced')

        if grammar.start() != test['start']:
            raise ValueError('Invalid start production produced')

        if grammar.terminals() != test['terminals']:
            raise ValueError('Invalid terminal set produced')

        if grammar.nonterminals() != test['nonterminals']:
            raise ValueError('Invalid nonterminal set produced')

        first = grammar.first()
        if len(first) != len(test['first']):
            raise ValueError('Invalid first set size produced')

        for elem in test['first']:
            if first.get(elem, None) != test['first'][elem]:
                raise ValueError('Invalid first set produced')

        follow = grammar.follow()
        if len(follow) != len(test['follow']):
            raise ValueError('Invalid follow set size produced')

        for elem in test['follow']:
            if follow.get(elem, None) != test['follow'][elem]:
                raise ValueError('Invalid follow set produced')

        rules = grammar.rules()
        if len(rules) != len(test['rules']):
            raise ValueError('Invalid number of table rules produced')

        rules.sort(key=make_rule_key)
        test['rules'].sort(key=make_rule_key)

        _map = {}
        for idx in range(0, len(rules)):
            i, iname, iproduction = rules[idx]
            j, jname, jproduction = test['rules'][idx]

            if iname != jname:
                raise ValueError('Invalid production rule name produced')

            if len(iproduction) != len(jproduction):
                raise ValueError('Invalid production rule produced')

            if not all(map(lambda i,j: i == j, iproduction, jproduction)):
                raise ValueError('Invalid production rule produced')

            _map[i] = j

        table = grammar.table()
        if len(table) != len(test['table']):
            raise ValueError('Invalid number of table rows produced')

        if not all(map(lambda r,_r: len(r) == len(_r), table, test['table'])):
            raise ValueError('Invalid number of table columns produced')

        # sort by nonterminal header
        table.sort(key=row_header)
        test['table'].sort(key=row_header)

        # transpose
        table = [list(row) for row in zip(*table)]
        test['table'] = [list(row) for row in zip(*test['table'])]

        # sort by terminal header
        table.sort(key=row_header)
        test['table'].sort(key=row_header)

        for r in range(0, len(table)):
            for c in range(0, len(table[0])):
                iterm = table[r][c]
                jterm = test['table'][r][c]
                if type(iterm) != type(jterm):
                    raise ValueError('Invalid table value type produced')

                if type(iterm) is str and iterm != jterm:
                    raise ValueError('Invalid table header value produced')
                if type(iterm) is int and iterm != jterm:
                    raise ValueError('Invalid table header value produced')
                if type(iterm) is set:
                    if {_map[term] for term in iterm} != jterm:
                        raise ValueError('Invalid table value produced')

        conflicts = grammar.conflicts()
        if len(conflicts) != len(test['conflicts']):
            raise ValueError('Invalid number of conflicts produced')

        conflicts.sort(key=conflict_key)
        test['conflicts'].sort(key=conflict_key)

        for idx in range(0, len(conflicts)):
            iterm, ichar, iconflict = conflicts[idx]
            jterm, jchar, jconflict = test['conflicts'][idx]

            if iterm != jterm:
                raise ValueError('Invalid conflicts nonterminal produced')

            if ichar != jchar:
                raise ValueError('Invalid conflicts transition produced')

            if {_map[item] for item in iconflict} != jconflict:
                raise ValueError('Invalid conflicts produced')
