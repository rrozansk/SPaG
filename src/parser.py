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
import copy


class ContextFreeGrammar(object):
    """
    ContextFreeGrammar represents a Backus Normal Form (BNF) grammar which can
    be programatically transformed into a parse table.
    """

    EOI = 0  # end of input marker
    EPS = 1  # Epsilon marker

    _name = None
    _start = None
    _terminals = None
    _nonterminals = None
    _first = None
    _follow = None
    _productions = None
    _rules = None
    _table = None

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

        self._productions = []

        for (lhs, rhs) in productions:
            if type(lhs) is not str:
                raise ValueError('Invalid Input: lhs must be a string')

            if type(rhs) is not str:
                raise ValueError('Invalid Input: rhs must be a string')

            rule = (lhs, [rules.split() for rules in rhs.split('|')])
            self._productions.append(rule)

        nonterms = self._nonterminals()
        terms = self._terminals(nonterms)
        first = self._first(terms, nonterms)
        follow = self._follow(nonterms, first)
        table, rules = self._table(terms, nonterms, first, follow)
        conflicts = self._conflicts(table)

        self._nonterminals = nonterms
        self._terminals = terms
        self._first = first
        self._follow = follow
        self._table = table
        self._rules = rules
        self._conflicts = conflicts

    def name(self):
        """
        Get the name of the Context Free Grammar.

        Runtime: O(1) - constant.
        Type: None -> string
        """
        return self._name

    def start(self):
        """
        Get the start state of the grammar.

        Runtime: O(1) - constant.
        Type: None -> string
        """
        return self._start

    def terminals(self):
        """
        Get the terminals of the grammar.

        Runtime: O(n) - linear to the number of terminals in the grammar.
        Type: None -> set
        """
        return copy.deepcopy(self._terminals)

    def nonterminals(self):
        """
        Get the nonterminals of the grammar.

        Runtime: O(n) - linear to the number of nonterminals in the grammar.
        Type: None -> set
        """
        return copy.deepcopy(self._nonterminals)

    def first(self):
        """
        Get the first set of the grammar.

        Runtime: O(nm) - linear to the number of terminals and nonterminals.
        Type: None -> set
        """
        return copy.deepcopy(self._first)

    def follow(self):
        """
        Get the follow set of the grammar.

        Runtime: O(n) - linear to the number of nonterminals.
        Type: None -> set
        """
        return copy.deepcopy(self._follow)

    def rules(self):
        """
        Get the production rules of the grammar.

        Runtime: O(n) - linear to the number of production rules.
        Type: None -> set
        """
        return copy.deepcopy(self._rules)

    def table(self):
        """
        Get the parse table of the grammar.

        Runtime: O(nm) - linear to the number of nonterminals and terminals.
        Type: None -> set
        """
        return copy.deepcopy(self._table)

    def conflicts(self):
        """
        Get the conflicts in the grammar.

        Runtime: O(n) - linear to the number of conflicts in the grammar.
        Type: None -> set
        """
        return copy.deepcopy(self._conflicts)

    def _nonterminals(self):
        """
        Report all non terminals which are just the production rules.

        Runtime: O(n) - linear to the number of productions.
        Type: None -> set
        """
        return frozenset({production for (production, _) in self._productions})

    def _terminals(self, nonterminals):
        """
        Report all literal symbols which appear in the grammar.

        Runtime: O(?) - ?
        Type: None -> set
        """
        terminals = set()
        for (_, productions) in self._productions:
            for production in productions:
                for symbol in production:
                    if symbol not in nonterminals:
                        terminals.add(symbol)
        return frozenset(terminals)

    def _first_production(self, production, first):
        """
        Compute the first set of a single nonterminal's rhs/production.

        Runtime: O(n) - linear to the number of production rules.
        Type: None -> set
        """
        _first = frozenset([self.EPS])
        for idx in range(0, len(production)):
            _first |= first[production[idx]]
            if self.EPS not in first[production[idx]]:
                return _first - frozenset([self.EPS])
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
            first[terminal] = frozenset([terminal])

        # foreach elem A of NONTERMS do _first[A] = {}
        for nonterminal in nonterminals:
            first[nonterminal] = frozenset()

        # loop until nothing new happens updating the _first sets
        while True:
            changed = False

            for (nonterminal, productions) in self._productions:
                for production in productions:
                    new = self._first_production(production, first) |\
                          first[nonterminal]
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
        follow = {nonterminal: frozenset() for nonterminal in nonterminals}

        # put $ (end of input marker) in Follow(<Start>)
        follow[self._start] = frozenset([self.EOI])

        # loop until nothing new happens updating the Follow sets
        while True:
            changed = False

            for (nonterminal, productions) in self._productions:
                for production in productions:
                    for idx in range(0, len(production)):
                        if production[idx] in nonterminals:
                            new = self._first_production(production[idx+1:], first) |\
                                  follow[production[idx]]
                            if self.EPS in new:
                                new = follow[nonterminal] |\
                                      (new - frozenset([self.EPS]))

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
            predict = (predict - frozenset([self.EPS])) | follow[nonterminal]
        return predict

    def _table(self, terminals, nonterminals, first, follow):
        """
        Construct the LL(1) parsing table by finding predict sets.

        Runtime: O(?) - ?
        Type: None -> set
        """
        # build the table with row and column headers
        terminals = list(terminals | frozenset([self.EOI]))
        nonterminals = list(nonterminals)
        table = [[n]+[frozenset() for _ in terminals] for n in nonterminals]
        table.insert(0, [' ']+terminals)

        # flatten productions, and fill in table
        productions = []
        rule = 0
        for (nonterminal, _productions) in self._productions:
            idx_n = nonterminals.index(nonterminal)+1  # acct for column header
            for production in _productions:
                predict = self._predict(nonterminal, production, first, follow)
                for terminal in predict:
                    idx_t = terminals.index(terminal)+1  # acct for row header
                    table[idx_n][idx_t] |= frozenset([rule])
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
            'productions': [
                ('<S>', '<E> | <E> a'),
                ('<E>', 'b |')
            ],
            'start': '<S>',
            'terminals': frozenset(['a', 'b']),
            'nonterminals': frozenset(['<S>', '<E>']),
            'first': {
                'a': frozenset(['a']),
                'b': frozenset(['b']),
                '<S>': frozenset(['b', 'a', 1]),
                '<E>': frozenset(['b', 1])
            },
            'follow': {
                '<S>': frozenset([0]),
                '<E>': frozenset([0, 'a'])
            },
            'rules': [
                (0, '<S>', ['<E>']),
                (1, '<S>', ['<E>', 'a']),
                (2, '<E>', ['b']),
                (3, '<E>', [])
            ],
            'table': [
                [' ', 'a', 0, 'b'],
                ['<S>', frozenset([1]), frozenset([0]), frozenset([0, 1])],
                ['<E>', frozenset([3]), frozenset([3]), frozenset([2])]
            ],
            'conflicts': [('<S>', 'b', frozenset([0, 1]))]
        },
        {
            'name': 'Invalid Grammar: First/Follow Conflict',
            'valid': True,
            'productions': [
                ('<S>', '<A> a b'),
                ('<A>', 'a |')
            ],
            'start': '<S>',
            'terminals': frozenset(['a', 'b']),
            'nonterminals': frozenset(['<S>', '<A>']),
            'first': {
                'a': frozenset(['a']),
                'b': frozenset(['b']),
                '<S>': frozenset(['a']),
                '<A>': frozenset(['a', 1])
            },
            'follow': {
                '<S>': frozenset([0]),
                '<A>': frozenset(['a'])
            },
            'rules': [
                (0, '<S>', ['<A>', 'a', 'b']),
                (1, '<A>', ['a']),
                (2, '<A>', [])
            ],
            'table': [
                [' ', 'a', 0, 'b'],
                ['<S>', frozenset([0]), frozenset([]), frozenset([])],
                ['<A>', frozenset([1, 2]), frozenset([]), frozenset([])]
            ],
            'conflicts': [('<A>', 'a', frozenset([1, 2]))]
        },
        {
            'name': 'Invalid Grammar: Left Recursion',
            'valid': True,
            'productions': [
                ('<E>', '<E> <A> <T> | <T>'),
                ('<A>', '+ | -'),
                ('<T>', '<T> <M> <F> | <F>'),
                ('<M>', '*'),
                ('<F>', '( <E> ) | id')
            ],
            'start': '<E>',
            'terminals': frozenset(['(', ')', '+', '*', '-', 'id']),
            'nonterminals': frozenset(['<E>', '<A>', '<T>', '<M>', '<F>']),
            'first': {
                '(': frozenset(['(']),
                ')': frozenset([')']),
                '+': frozenset(['+']),
                '-': frozenset(['-']),
                '*': frozenset(['*']),
                'id': frozenset(['id']),
                '<E>': frozenset(['(', 'id']),
                '<A>': frozenset(['+', '-']),
                '<T>': frozenset(['(', 'id']),
                '<M>': frozenset(['*']),
                '<F>': frozenset(['(', 'id'])
            },
            'follow': {
                '<E>': frozenset([0, '+', '-', ')']),
                '<A>': frozenset(['(', 'id']),
                '<T>': frozenset([0, '+', '-', '*', ')']),
                '<M>': frozenset(['(', 'id']),
                '<F>': frozenset([0, '+', '-', '*', ')'])
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
                ['<E>', frozenset([]), frozenset([0, 1]), frozenset([]),
                 frozenset([0, 1]), frozenset([]), frozenset([]),
                 frozenset([])],
                ['<A>', frozenset([]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([2]), frozenset([]), frozenset([3])],
                ['<M>', frozenset([]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([]), frozenset([6]), frozenset([])],
                ['<T>', frozenset([]), frozenset([4, 5]), frozenset([]),
                 frozenset([4, 5]), frozenset([]), frozenset([]),
                 frozenset([])],
                ['<F>', frozenset([]), frozenset([8]), frozenset([]),
                 frozenset([7]), frozenset([]), frozenset([]), frozenset([])]
            ],
            'conflicts': [
                ('<E>', 'id', frozenset([0, 1])),
                ('<E>', '(', frozenset([0, 1])),
                ('<T>', 'id', frozenset([4, 5])),
                ('<T>', '(', frozenset([4, 5]))
            ]
        },
        {
            'name': 'Valid Grammar: With Epsilon',
            'valid': True,
            'productions': [
                ('<E>', '<T> <E\'>'),
                ('<E\'>', '<A> <T> <E\'> |'),
                ('<A>', '+ | - '),
                ('<T>', '<F> <T\'>'),
                ('<T\'>', '<M> <F> <T\'> |'),
                ('<M>', '*'),
                ('<F>', '( <E> ) | id')
            ],
            'start': '<E>',
            'terminals': frozenset(['+', '-', '*', '(', ')', 'id']),
            'nonterminals': frozenset(['<E>', '<E\'>', '<A>', '<T>', '<T\'>',
                                       '<M>', '<F>']),
            'first': {
                '+': frozenset(['+']),
                '-': frozenset(['-']),
                '*': frozenset(['*']),
                '(': frozenset(['(']),
                ')': frozenset([')']),
                'id': frozenset(['id']),
                '<E>': frozenset(['(', 'id']),
                '<E\'>': frozenset(['+', '-', 1]),
                '<A>': frozenset(['+', '-']),
                '<T>': frozenset(['(', 'id']),
                '<T\'>': frozenset([1, '*']),
                '<M>': frozenset(['*']),
                '<F>': frozenset(['(', 'id'])
            },
            'follow': {
                '<E>': frozenset([0, ')']),
                '<E\'>': frozenset([0, ')']),
                '<A>': frozenset(['(', 'id']),
                '<T>': frozenset([')', '+', '-', 0]),
                '<T\'>': frozenset([')', '+', '-', 0]),
                '<M>': frozenset(['(', 'id']),
                '<F>': frozenset([')', '+', '-', '*', 0])
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
                ['<E>', frozenset([]), frozenset([0]), frozenset([]),
                 frozenset([0]), frozenset([]), frozenset([]), frozenset([])],
                ['<E\'>', frozenset([2]), frozenset([]), frozenset([2]),
                 frozenset([]), frozenset([1]), frozenset([]), frozenset([1])],
                ['<A>', frozenset([]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([3]), frozenset([]), frozenset([4])],
                ['<T>', frozenset([]), frozenset([5]), frozenset([]),
                 frozenset([5]), frozenset([]), frozenset([]), frozenset([])],
                ['<T\'>', frozenset([7]), frozenset([]), frozenset([7]),
                 frozenset([]), frozenset([7]), frozenset([6]),
                 frozenset([7])],
                ['<M>', frozenset([]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([]), frozenset([8]), frozenset([])],
                ['<F>', frozenset([]), frozenset([10]), frozenset([]),
                 frozenset([9]), frozenset([]), frozenset([]), frozenset([])]
            ],
            'conflicts': []
        },
        {
            'name': 'Valid Grammar: No Epsilon',
            'valid': True,
            'productions': [
                ('<S>', '<A> a <A> b'),
                ('<S>', '<B> b <B> a'),
                ('<A>', ''),
                ('<B>', '')
            ],
            'start': '<S>',
            'terminals': frozenset(['a', 'b']),
            'nonterminals': frozenset(['<S>', '<A>', '<B>']),
            'first': {
                'a': frozenset(['a']),
                'b': frozenset(['b']),
                '<S>': frozenset(['a', 'b']),
                '<A>': frozenset([1]),
                '<B>': frozenset([1])
            },
            'follow': {
                '<S>': frozenset([0]),
                '<A>': frozenset(['b', 'a']),
                '<B>': frozenset(['a', 'b'])
            },
            'rules': [
                (0, '<S>', ['<A>', 'a', '<A>', 'b']),
                (1, '<S>', ['<B>', 'b', '<B>', 'a']),
                (2, '<A>', []),
                (3, '<B>', [])
            ],
            'table': [
                [' ', 0, 'a', 'b'],
                ['<S>', frozenset([]), frozenset([0]), frozenset([1])],
                ['<A>', frozenset([]), frozenset([2]), frozenset([2])],
                ['<B>', frozenset([]), frozenset([3]), frozenset([3])]
            ],
            'conflicts': [],
        },
        {
            'name': 'Valid Grammar: Simple language',
            'valid': True,
            'productions': [
                ('<STMT>', 'if <EXPR> then <STMT>\
                            | while <EXPR> do <STMT>\
                            | <EXPR>'),
                ('<EXPR>', '<TERM> -> id\
                            | zero? <TERM>\
                            | not <EXPR>\
                            | ++ id\
                            | -- id'),
                ('<TERM>', 'id | constant'),
                ('<BLOCK>', '<STMT> | { <STMTS> }'),
                ('<STMTS>', '<STMT> <STMTS> |')
            ],
            'start': '<STMTS>',
            'terminals': frozenset(['if', 'then', 'while', 'do', '->', 'zero?',
                                    'not', '++', '--', 'id', 'constant', '{',
                                    '}']),
            'nonterminals': frozenset(['<STMT>', '<STMTS>', '<BLOCK>',
                                       '<TERM>', '<EXPR>']),
            'first': {
              'if': frozenset(['if']),
              'then': frozenset(['then']),
              'while': frozenset(['while']),
              'do': frozenset(['do']),
              '->': frozenset(['->']),
              'zero?': frozenset(['zero?']),
              'not': frozenset(['not']),
              '++': frozenset(['++']),
              '--': frozenset(['--']),
              'id': frozenset(['id']),
              'constant': frozenset(['constant']),
              '{': frozenset(['{']),
              '}': frozenset(['}']),
              '<STMT>': frozenset(['constant', '++', 'zero?', 'while', 'not',
                                   '--', 'id', 'if']),
              '<STMTS>': frozenset([1, 'constant', '++', 'zero?', 'while',
                                    'not', '--', 'id', 'if']),
              '<BLOCK>': frozenset(['constant', '++', 'zero?', 'while', 'not',
                                    '--', '{', 'id', 'if']),
              '<TERM>': frozenset(['constant', 'id']),
              '<EXPR>': frozenset(['++', 'not', 'constant', 'zero?', '--',
                                  'id'])
            },
            'follow': {
                '<STMT>': frozenset([0, 'constant', '++', 'not', 'while',
                                     'zero?', '--', '}', 'id', 'if']),
                '<STMTS>': frozenset([0, '}']),
                '<BLOCK>': frozenset([]),
                '<TERM>': frozenset([0, 'then', 'constant', 'do', 'not', 'id',
                                     'if', '++', '--', 'while', 'zero?', '->',
                                     '}']),
                '<EXPR>': frozenset([0, 'then', 'constant', 'do', '++', '--',
                                     'while', 'not', 'zero?', '}', 'id',
                                     'if'])
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
                ['<STMT>', frozenset([]), frozenset([]), frozenset([2]),
                 frozenset([]), frozenset([2]), frozenset([2]), frozenset([1]),
                 frozenset([2]), frozenset([2]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([2]), frozenset([0])],
                ['<EXPR>', frozenset([]), frozenset([]), frozenset([3]),
                 frozenset([]), frozenset([6]), frozenset([4]), frozenset([]),
                 frozenset([5]), frozenset([7]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([3]), frozenset([])],
                ['<BLOCK>', frozenset([]), frozenset([]), frozenset([10]),
                 frozenset([]), frozenset([10]), frozenset([10]),
                 frozenset([10]), frozenset([10]), frozenset([10]),
                 frozenset([11]), frozenset([]), frozenset([]),
                 frozenset([10]), frozenset([10])],
                ['<STMTS>', frozenset([13]), frozenset([]), frozenset([12]),
                 frozenset([]), frozenset([12]), frozenset([12]),
                 frozenset([12]), frozenset([12]), frozenset([12]),
                 frozenset([]), frozenset([]), frozenset([13]),
                 frozenset([12]), frozenset([12])],
                ['<TERM>', frozenset([]), frozenset([]), frozenset([9]),
                 frozenset([]), frozenset([]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([8]), frozenset([])]
            ],
            'conflicts': []
        },
        {
            'name': False,
            'valid': False,
            'productions': [
                ('Invalid Name Type', '<E> | <E> a'),
            ],
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
            'productions': [
                ('<S>', '<E> | <E> a'),
            ],
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
            'productions': [
                (None, '<E> | <E> a'),
            ],
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
            'productions': [
                ('<S>', None),
            ],
            'start': False,
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None,
            'conflicts': None
        }
    ]

    def cmp_deep_seq(seq1, seq2):
        """Compare two arbitrary sequences for deep equality."""
        if len(seq1) != len(seq2):
            return False
        for idx in range(0, len(seq1)):
            if not isinstance(seq1[idx], type(seq2[idx])):
                return False
            _type = type(seq1[idx])
            if _type is list or _type is tuple:
                if not cmp_deep_seq(seq1[idx], seq2[idx]):
                    return False
            else:
                if seq1[idx] != seq2[idx]:
                    return False
        return True

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
        for elem in test['first']:
            if first.get(elem, None) != test['first'][elem]:
                raise ValueError('Invalid first set produced')

        follow = grammar.follow()
        for elem in test['follow']:
            if follow.get(elem, None) != test['follow'][elem]:
                raise ValueError('Invalid follow set produced')

        rules = grammar.rules()
        if len(rules) != len(test['rules']):
            raise ValueError('Invalid number of table rules produced')

        # same ordering as test['rules']
        test['rules'].sort(key=lambda rule: rule[0])
        if not cmp_deep_seq(rules, test['rules']):
            raise ValueError('Invalid rule produced')

        table = grammar.table()
        if len(table) != len(test['table']):
            raise ValueError('Invalid number of table rows produced')

        for r in range(0, len(table)):
            if len(table[r]) != len(test['table'][r]):
                raise ValueError('Invalid number of table columns produced')

        # sort by nonterminal header
        table.sort(key=lambda row: row[0])
        test['table'].sort(key=lambda row: row[0])

        # transpose
        table = [list(row) for row in zip(*table)]
        test['table'] = [list(row) for row in zip(*test['table'])]

        # sort by terminal header
        table.sort(key=lambda row: row[0])
        test['table'].sort(key=lambda row: row[0])

        if not cmp_deep_seq(table, test['table']):
            raise ValueError('Invalid table value produced')

        conflicts = grammar.conflicts()
        conflicts.sort(key=lambda conflict: conflict[0]+conflict[1])
        test['conflicts'].sort(key=lambda conflict: conflict[0]+conflict[1])
        if not cmp_deep_seq(conflicts, test['conflicts']):
            raise ValueError('Invalid conflicts produced')
