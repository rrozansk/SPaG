"""
 parser.py includes the implementation and testing of ContextFreeGrammar
 objects.

 The ContextFreeGrammar object represents a BNF style grammar which can be
 programatically transformed into a parser for the given language. While
 it is possible for any grammar to be specified, only LL1 grammars are
 supported with the following requirements to produce a parse table:
   1. No left recursion (direct and indirect)
   2. Must be left factored
   3. No ambiguity
 However, if you do specify a grammar which has any of the above do not fret,
 as everything will still run all conflict will be reported.

 Testing is implemented in a table driven fashion using the black box method.
 The test may be run at the command line with the following invocation:

   $ python parser.py

 If all tests passed no output will be produced. In the event of a failure a
 ValueError is thrown with the appropriate error/failure message.
"""


class ContextFreeGrammar(object):
    """
    ContextFreeGrammar represents a Backus Normal Form (BNF) grammar.
    """

    EOI = 0  # end of input marker
    EPS = 1  # Epsilon marker

    name = None
    starting = None     # which grammar rule is the start symbol of grammar
    productions = None  # all the production rules in the grammar

    def __init__(self, name):
        """
        Object constructor which initializes grammar name and productions.
        """
        self.name = name
        self.productions = []

    def start(self, starting):
        """
        Declare the start symbol of the grammar.
        """
        self.starting = starting

    def production(self, lhs, rhs):
        """
        Add a production rule to the grammar. Once added the production cannot
        be removed. lhs is a nonterminal symbol and rhs is a string containing
        the productions, seperated by a vertical bar (|), an empty production
        specifies an epsilon.
        """
        rule = (lhs, [productions.split() for productions in rhs.split('|')])
        self.productions.append(rule)

    def terminals(self):
        """
        report all literal symbols which appear in the grammar
        """
        terminals = frozenset()
        nonterminals = frozenset({key for (key, _) in self.productions})
        for (_, productions) in self.productions:
            for production in productions:
                for symbol in production:
                    if symbol not in nonterminals:
                        terminals |= frozenset([symbol])
        return terminals

    def nonterminals(self):
        """
        report all non terminals are just the production rules
        """
        return frozenset({production for (production, _) in self.productions})

    def _first_production(self, production, first):
        """
        compute the first set of a given productions rhs
        """
        if len(production) == 0:
            return frozenset([self.EPS])

        _first = first[production[0]] - frozenset([self.EPS])
        idk = 1
        while idk < len(production) and self.EPS in first[production[idk-1]]:
            _first |= first[production[idk]] - frozenset([self.EPS])
            idk += 1

        # epsilon only if X_1, X_2, ... X_n -> epsilon
        if self.EPS in first[production[idk-1]]:
            _first |= frozenset([self.EPS])

        return _first

    def first(self, terminals, nonterminals):
        """
        calculate the first set following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt
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

            for (nonterminal, productions) in self.productions:
                for production in productions:
                    new = self._first_production(production, first) | \
                          first[nonterminal]
                    if new != first[nonterminal]:
                        first[nonterminal] = new
                        changed = True

            if not changed:
                return first

    def follow(self, nonterminals, first):
        """
        calculate the follow set following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt
        """
        follow = {}

        # foreach elem A of NONTERMS do Follow[A] = {}
        for nonterminal in nonterminals:
            follow[nonterminal] = frozenset()

        # put $ (end of input marker) in Follow(<Start>)
        follow[self.starting] = frozenset([self.EOI])

        # loop until nothing new happens updating the First sets
        while True:
            changed = False

            for (nonterminal, productions) in self.productions:
                for prod in productions:
                    for idx in range(0, len(prod)):
                        if prod[idx] in nonterminals:
                            old = follow[prod[idx]]
                            add = self._first_production(prod[idx+1:], first)
                            follow[prod[idx]] |= add - frozenset([self.EPS])
                            if self.EPS in add:
                                follow[prod[idx]] |= follow[nonterminal]

                            if old != follow[prod[idx]]:
                                changed = True

            if not changed:
                return follow

    def _predict(self, nonterminal, production, first, follow):
        """
        calculate the predict set following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt
        """
        predict = self._first_production(production, first)
        if self.EPS in predict:
            predict |= follow[nonterminal]
        return predict - frozenset([self.EPS])

    def table(self, terminals, nonterminals, first, follow):
        """
        construct the LL(1) parsing table by finding predict sets.
        """
        # build the table with row and column headers
        terminals = list(terminals | frozenset([self.EOI]))
        nonterminals = list(nonterminals)
        table = [[n]+[frozenset() for _ in terminals] for n in nonterminals]
        table.insert(0, [' ']+terminals)

        # flatten productions, and fill in table
        productions = []
        rule = 0
        for (nonterminal, _productions) in self.productions:
            idx_n = nonterminals.index(nonterminal)+1  # acct for column header
            for production in _productions:
                predict = self._predict(nonterminal, production, first, follow)
                for terminal in predict:
                    idx_t = terminals.index(terminal)+1  # acct for row header
                    table[idx_n][idx_t] |= frozenset([rule])
                productions.append((rule, nonterminal, production))
                rule += 1

        return (table, productions)

    def conflicts(self, table):
        """
        grammar is ll(1) if parse table has (@maximum) a single entry per
        table slot conflicting for the predicitions
        """
        conflicts = []
        for row in range(1, len(table)):  # ignore column headers
            for col in range(1, len(table[row])):  # ignore row header
                if len(table[row][col]) > 1:
                    conflict = (table[row][0], table[0][col], table[row][col])
                    conflicts.append(conflict)
        return conflicts

    def make(self):
        """
        driver function to construct all the necessary information for the
        given grammar once it has been input.
        """
        terms = self.terminals()
        nonterms = self.nonterminals()
        first = self.first(terms, nonterms)
        follow = self.follow(nonterms, first)
        (table, rules) = self.table(terms, nonterms, first, follow)
        conflicts = self.conflicts(table)

        return {
            'name':         self.name,
            'start':        self.starting,
            'terminals':    terms,
            'nonterminals': nonterms,
            'first':        first,
            'follow':       follow,
            'rules':        rules,
            'table':        table,
            'conflicts':    conflicts,
        }


if __name__ == "__main__":

    TESTS = [
        {
            'name': 'Invalid Grammar: First/First Conflict',
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
    ]

    def cmp_deep_seq(seq1, seq2):
        """Compare two arbitrary sequences for deep equality."""
        if len(seq1) != len(seq2):
            return False
        for idx in range(0, len(seq1)):
            if isinstance(type(seq1[idx]), type(seq2[idx])):
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
        grammar = ContextFreeGrammar(test['name'])
        grammar.start(test['start'])
        for (nonterminal, productions) in test['productions']:
            grammar.production(nonterminal, productions)
        result = grammar.make()

        if result['name'] != test['name']:
            raise ValueError('Invalid name produced')

        if result['start'] != test['start']:
            raise ValueError('Invalid start production produced')

        if result['terminals'] != test['terminals']:
            raise ValueError('Invalid terminal set produced')

        if result['nonterminals'] != test['nonterminals']:
            raise ValueError('Invalid nonterminal set produced')

        for elem in test['first']:
            if result['first'].get(elem, None) != test['first'][elem]:
                raise ValueError('Invalid first set produced')

        for elem in test['follow']:
            if result['follow'].get(elem, None) != test['follow'][elem]:
                raise ValueError('Invalid follow set produced')

        if len(result['rules']) != len(test['rules']):
            raise ValueError('Invalid number of table rules produced')

        result['rules'].sort(key=lambda rule: rule[0])
        test['rules'].sort(key=lambda rule: rule[0])
        if not cmp_deep_seq(result['rules'], test['rules']):
            raise ValueError('Invalid rule produced')

        if len(result['table']) != len(test['table']):
            raise ValueError('Invalid number of table rows produced')

        for r in range(0, len(result['table'])):
            if len(result['table'][r]) != len(test['table'][r]):
                raise ValueError('Invalid number of table columns produced')

        # sort by nonterminal header
        result['table'].sort(key=lambda row: row[0])
        test['table'].sort(key=lambda row: row[0])

        # transpose
        result['table'] = [list(row) for row in zip(*result['table'])]
        test['table'] = [list(row) for row in zip(*test['table'])]

        # sort by terminal header
        result['table'].sort(key=lambda row: row[0])
        test['table'].sort(key=lambda row: row[0])

        if not cmp_deep_seq(result['table'], test['table']):
            raise ValueError('Invalid table value produced')

        result['conflicts'].sort(key=lambda conflict: conflict[0]+conflict[1])
        test['conflicts'].sort(key=lambda conflict: conflict[0]+conflict[1])
        if not cmp_deep_seq(result['conflicts'], test['conflicts']):
            raise ValueError('Invalid conflicts produced')
