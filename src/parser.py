"""
 parser.py includes ContextFreeGrammar and testing...
 
 represents a BNF grammar which can be programatically
 transformed into a LL1 parse table given the following requirements:
   1. No left recursion
   2. Must be left factored
 Although, it is possible for any grammar to be specified as all conflicts will
 be reported if any exist in the grammar.

 This object can be tested by directly calling it with python like:
   $ python parser.py
 You should see no output if all test passed, otherwise a value error is thrown
 with the appropriate message.
"""


class ContextFreeGrammar(object):
    """
    doc ...
    """

    Dollar = 0
    Epsilon = 1

    name = None
    starting = None     # which grammar rule is the start symbol of grammar
    productions = None  # all the production rules in the grammar

    def __init__(self, name):
        """
        doc...
        """
        self.name = name
        self.productions = []

    def start(self, starting):
        """
        start symbol of the grammar
        """
        self.starting = starting

    def production(self, lhs, rhs):
        """
        splits a series of productions intos the form:
        (rule #, [[seq of symbols for a production] ...])
        empty list [] specifies an epsilon production.
        """
        rule = (lhs, [productions.split() for productions in rhs.split('|')])
        self.productions.append(rule)

    def __terminals__(self):
        """
        all literal symbols which appear in the grammar
        """
        terminals = frozenset()
        lhs = {key for (key, _) in self.productions}
        for (_, v) in self.productions:
            for production in v:
                for symbol in production:
                    if symbol not in lhs:
                        terminals |= frozenset([symbol])
        return terminals

    def __nonterminals__(self):
        """
        all non terminals are just the production rules
        """
        return frozenset({production for (production, _) in self.productions})

    def __firstOfProduction__(self, Xs, first):
        """
        compute the first set of a given productions rhs
        """
        if len(Xs) == 0:
            return frozenset([self.Epsilon])

        tmp = first[Xs[0]] - frozenset([self.Epsilon])
        k = 1
        while k < len(Xs) and self.Epsilon in first[Xs[k-1]]:
            tmp |= first[Xs[k]] - frozenset([self.Epsilon])
            k += 1

        # epsilon only if X_1, X_2, ... X_n -> epsilon
        if self.Epsilon in first[Xs[k-1]]:
            tmp |= frozenset([self.Epsilon])

        return tmp

    def __first__(self, terminals, nonterminals):
        """
        calculate the first set following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt
        """
        _first = {}

        # foreach elem A of TERMS do _first[A] = {A}
        for terminal in terminals:
            _first[terminal] = frozenset([terminal])

        # foreach elem A of NONTERMS do _first[A] = {}
        for nonterminal in nonterminals:
            _first[nonterminal] = frozenset()

        # loop until nothing new happens updating the _first sets
        while True:
            changed = False

            for (A, productions) in self.productions:
                for Xs in productions:
                    new = _first[A] | self.__firstOfProduction__(Xs, _first)
                    if new != _first[A]:
                        _first[A] = new
                        changed = True

            if not changed:
                return _first

    def __follow__(self, nonterminals, first):
        """
        calculate the follow set following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt
        """
        _follow = {}

        # foreach elem A of NONTERMS do Follow[A] = {}
        for nonterminal in nonterminals:
            _follow[nonterminal] = frozenset()

        # put $ (end of input marker) in Follow(<Start>)
        _follow[self.starting] = frozenset([self.Dollar])

        # loop until nothing new happens updating the First sets
        while True:
            changed = False

            for (A, productions) in self.productions:
                for Xs in productions:
                    for i in range(0, len(Xs)):
                        if Xs[i] in nonterminals:
                            old = _follow[Xs[i]]
                            add = self.__firstOfProduction__(Xs[i+1:], first)
                            _follow[Xs[i]] |= add - frozenset([self.Epsilon])
                            if self.Epsilon in add:
                                _follow[Xs[i]] |= _follow[A]

                            if old != _follow[Xs[i]]:
                                changed = True

            if not changed:
                return _follow

    def __predict__(self, A, Xs, first, follow):
        """
        calculate the predict set following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt
        """
        tmp = self.__firstOfProduction__(Xs, first)
        if self.Epsilon in tmp:
            tmp |= follow[A]
        return tmp - frozenset([self.Epsilon])

    def __table__(self, terminals, nonterminals, first, follow):
        """
        construct the LL(1) parsing table by finding predict sets
        """
        # build the table with row and column headers
        terminals = list(terminals | frozenset([self.Dollar]))
        nonterminals = list(nonterminals)
        table = [[n]+[frozenset() for t in terminals] for n in nonterminals]
        table.insert(0, [' ']+terminals)

        # flatten productions, and fill in table
        productions = []
        rule = 0
        for (A, _productions) in self.productions:
            n = nonterminals.index(A)+1  # account for column header
            for Xs in _productions:
                predict = self.__predict__(A, Xs, first, follow)
                for terminal in predict:
                    t = terminals.index(terminal)+1  # account for row header
                    table[n][t] |= frozenset([rule])
                productions.append((rule, A, Xs))
                rule += 1

        return (table, productions)

    def __conflicts__(self, table, rules):
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
        doc...
        """
        terms = self.__terminals__()
        nonterms = self.__nonterminals__()
        first = self.__first__(terms, nonterms)
        follow = self.__follow__(nonterms, first)
        (table, rules) = self.__table__(terms, nonterms, first, follow)
        conflicts = self.__conflicts__(table, rules)

        return {
            'name':         self.name,
            'start':        self.starting,
            'productions':  self.productions,
            'terminals':    terms,
            'nonterminals': nonterms,
            'first':        first,
            'follow':       follow,
            'rules':        rules,
            'table':        table,
            'conflicts':    conflicts,
        }


if __name__ == "__main__":
    def cmp_deep_seq(seq1, seq2):
        """Compare two arbitrary sequences for deep equality."""
        if len(seq1) != len(seq2):
            return False
        for i in range(0, len(seq1)):
            if isinstance(type(seq1[i]), type(seq2[i])):
                return False
            _type = type(seq1[i])
            if _type is list or _type is tuple:
                if not cmp_deep_seq(seq1[i], seq2[i]):
                    return False
            else:
                if seq1[i] != seq2[i]:
                    return False
        return True

    TESTS = [{
            'name': 'Invalid Grammar: Left Recursive',
            '_productions': [
                ('<exp>', '<exp> <addop> <term> | <term>'),
                ('<addop>', '+ | -'),
                ('<term>', '<term> <mulop> <factor> | <factor>'),
                ('<mulop>', '*'),
                ('<factor>', '( <exp> ) | num'),
            ],
            'productions': [
                ('<exp>', [['<exp>', '<addop>', '<term>'], ['<term>']]),
                ('<addop>', [['+'], ['-']]),
                ('<term>', [['<term>', '<mulop>', '<factor>'], ['<factor>']]),
                ('<mulop>', [['*']]),
                ('<factor>', [['(', '<exp>', ')'], ['num']]),
            ],
            'start': '<exp>',
            'terminals': frozenset(['(', ')', '+', '*', '-', 'num']),
            'nonterminals': frozenset(['<exp>', '<addop>', '<term>', '<mulop>',
                                       '<factor>']),
            'first': {
                '(': frozenset(['(']),
                ')': frozenset([')']),
                '+': frozenset(['+']),
                '-': frozenset(['-']),
                '*': frozenset(['*']),
                'num': frozenset(['num']),
                '<exp>': frozenset(['(', 'num']),
                '<addop>': frozenset(['+', '-']),
                '<term>': frozenset(['(', 'num']),
                '<mulop>': frozenset(['*']),
                '<factor>': frozenset(['(', 'num']),
            },
            'follow': {
                '<exp>': frozenset([0, '+', '-', ')']),
                '<addop>': frozenset(['(', 'num']),
                '<term>': frozenset([0, '+', '-', '*', ')']),
                '<mulop>': frozenset(['(', 'num']),
                '<factor>': frozenset([0, '+', '-', '*', ')']),
            },
            'rules': [
                (0, '<exp>', ['<exp>', '<addop>', '<term>']),
                (1, '<exp>', ['<term>']),
                (2, '<addop>', ['+']),
                (3, '<addop>', ['-']),
                (4, '<term>', ['<term>', '<mulop>', '<factor>']),
                (5, '<term>', ['<factor>']),
                (6, '<mulop>', ['*']),
                (7, '<factor>', ['(', '<exp>', ')']),
                (8, '<factor>', ['num']),
            ],
            'table': [
                [' ', 0, 'num', ')', '(', '+', '*', '-'],
                ['<exp>', frozenset([]), frozenset([0, 1]), frozenset([]),
                 frozenset([0, 1]), frozenset([]), frozenset([]),
                 frozenset([])],
                ['<addop>', frozenset([]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([2]), frozenset([]), frozenset([3])],
                ['<mulop>', frozenset([]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([]), frozenset([6]), frozenset([])],
                ['<term>', frozenset([]), frozenset([4, 5]), frozenset([]),
                 frozenset([4, 5]), frozenset([]), frozenset([]),
                 frozenset([])],
                ['<factor>', frozenset([]), frozenset([8]), frozenset([]),
                 frozenset([7]), frozenset([]), frozenset([]), frozenset([])]
                ],
            'conflicts': [
                ('<exp>', 'num', frozenset([0, 1])),
                ('<exp>', '(', frozenset([0, 1])),
                ('<term>', 'num', frozenset([4, 5])),
                ('<term>', '(', frozenset([4, 5]))
            ]
        },
        {
            'name': 'Valid Grammar: Epsilon Example 1',
            '_productions': [
                ('<exp>', '<term> <expx>'),
                ('<expx>', '<addop> <term> <expx> |'),
                ('<addop>', '+ | - '),
                ('<term>', '<factor> <termx>'),
                ('<termx>', '<mulop> <factor> <termx> |'),
                ('<mulop>', '*'),
                ('<factor>', '( <exp> ) | num )'),
            ],
            'productions': [
                ('<exp>', [['<term>', '<expx>']]),
                ('<expx>', [['<addop>', '<term>', '<expx>'], []]),
                ('<addop>', [['+'], ['-']]),
                ('<term>', [['<factor>', '<termx>']]),
                ('<termx>', [['<mulop>', '<factor>', '<termx>'], []]),
                ('<mulop>', [['*']]),
                ('<factor>', [['(', '<exp>', ')'], ['num', ')']]),
            ],
            'start': '<exp>',
            'terminals': frozenset(['+', '-', '*', '(', ')', 'num']),
            'nonterminals': frozenset(['<exp>', '<expx>', '<addop>', '<term>',
                                       '<termx>', '<mulop>', '<factor>']),
            'first': {
                '+': frozenset(['+']),
                '-': frozenset(['-']),
                '*': frozenset(['*']),
                '(': frozenset(['(']),
                ')': frozenset([')']),
                'num': frozenset(['num']),
                '<exp>': frozenset(['(', 'num']),
                '<expx>': frozenset(['+', '-', 1]),
                '<addop>': frozenset(['+', '-']),
                '<term>': frozenset(['(', 'num']),
                '<termx>': frozenset([1, '*']),
                '<mulop>': frozenset(['*']),
                '<factor>': frozenset(['(', 'num']),
            },
            'follow': {
                '<exp>': frozenset([0, ')']),
                '<expx>': frozenset([0, ')']),
                '<addop>': frozenset(['(', 'num']),
                '<term>': frozenset([')', '+', '-', 0]),
                '<termx>': frozenset([')', '+', '-', 0]),
                '<mulop>': frozenset(['(', 'num']),
                '<factor>': frozenset([')', '+', '-', '*', 0]),
            },
            'rules': [
                (0, '<exp>', ['<term>', '<expx>']),
                (1, '<expx>', ['<addop>', '<term>', '<expx>']),
                (2, '<expx>', []),
                (3, '<addop>', ['+']),
                (4, '<addop>', ['-']),
                (5, '<term>', ['<factor>', '<termx>']),
                (6, '<termx>', ['<mulop>', '<factor>', '<termx>']),
                (7, '<termx>', []),
                (8, '<mulop>', ['*']),
                (9, '<factor>', ['(', '<exp>', ')']),
                (10, '<factor>', ['num', ')']),
            ],
            'table': [
                [' ', 0, 'num', ')', '(', '+', '*', '-'],
                ['<exp>', frozenset([]), frozenset([0]), frozenset([]),
                 frozenset([0]), frozenset([]), frozenset([]), frozenset([])],
                ['<expx>', frozenset([2]), frozenset([]), frozenset([2]),
                 frozenset([]), frozenset([1]), frozenset([]), frozenset([1])],
                ['<addop>', frozenset([]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([3]), frozenset([]), frozenset([4])],
                ['<term>', frozenset([]), frozenset([5]), frozenset([]),
                 frozenset([5]), frozenset([]), frozenset([]), frozenset([])],
                ['<termx>', frozenset([7]), frozenset([]), frozenset([7]),
                 frozenset([]), frozenset([7]), frozenset([6]),
                 frozenset([7])],
                ['<mulop>', frozenset([]), frozenset([]), frozenset([]),
                 frozenset([]), frozenset([]), frozenset([8]), frozenset([])],
                ['<factor>', frozenset([]), frozenset([10]), frozenset([]),
                 frozenset([9]), frozenset([]), frozenset([]), frozenset([])]
            ],
            'conflicts': [],
        },
        {
            'name': 'Valid Grammar: Epsilon Example 2',
            '_productions': [
                ('<E>', '<T> <E\'>'),
                ('<E\'>', '+ <T> <E\'> |'),
                ('<T>', '<F> <T\'>'),
                ('<T\'>', '* <F> <T\'> |'),
                ('<F>', '( <E> ) | id'),
            ],
            'productions': [
                ('<E>', [['<T>', '<E\'>']]),
                ('<E\'>', [['+', '<T>', '<E\'>'], []]),
                ('<T>', [['<F>', '<T\'>']]),
                ('<T\'>', [['*', '<F>', '<T\'>'], []]),
                ('<F>', [['(', '<E>', ')'], ['id']]),
            ],
            'start': '<E>',
            'terminals': frozenset(['(', ')', '+', '*', 'id']),
            'nonterminals': frozenset(['<E>', '<E\'>', '<T>', '<T\'>', '<F>']),
            'first': {
                '(': frozenset(['(']),
                ')': frozenset([')']),
                '+': frozenset(['+']),
                '*': frozenset(['*']),
                'id': frozenset(['id']),
                '<E>': frozenset(['(', 'id']),
                "<E'>": frozenset([1, '+']),
                '<T>': frozenset(['(', 'id']),
                "<T'>": frozenset([1, '*']),
                '<F>': frozenset(['(', 'id'])
            },
            'follow': {
                '<E>': frozenset([0, ')']),
                "<E'>": frozenset([0, ')']),
                '<T>': frozenset([0, ')', '+']),
                "<T'>": frozenset([0, ')', '+']),
                '<F>': frozenset([0, ')', '+', '*'])
            },
            'rules': [
                (0, '<E>',  ['<T>', "<E'>"]),
                (1, "<E'>", ['+', '<T>', "<E'>"]),
                (2, "<E'>", []),
                (3, '<T>',  ['<F>', "<T'>"]),
                (4, "<T'>", ['*', '<F>', "<T'>"]),
                (5, "<T'>", []),
                (6, '<F>',  ['(', '<E>', ')']),
                (7, '<F>',  ['id'])
            ],
            'table': [
                [' ', 0, ')', '(', '+', '*', 'id'],
                ['<E>',  frozenset([]),  frozenset([]),  frozenset([0]),
                 frozenset([]),  frozenset([]),  frozenset([0])],
                ["<E'>", frozenset([2]), frozenset([2]), frozenset([]),
                 frozenset([1]), frozenset([]),  frozenset([])],
                ["<T>",  frozenset([]),  frozenset([]),  frozenset([3]),
                 frozenset([]),  frozenset([]),  frozenset([3])],
                ["<T'>", frozenset([5]), frozenset([5]), frozenset([]),
                 frozenset([5]), frozenset([4]), frozenset([])],
                ["<F>",  frozenset([]),  frozenset([]),  frozenset([6]),
                 frozenset([]),  frozenset([]),  frozenset([7])]
            ],
            'conflicts': [],
        }
        # TODO: { 'name': 'Valid Grammar: No Epsilon Example 1', },
        # TODO: { 'name': 'Invalid Grammar: Not Left Factored', },
    ]

    for test in TESTS:
        _test = ContextFreeGrammar(test['name'])
        _test.start(test['start'])
        for i in range(0, len(test['_productions'])):
            (A, Ps) = test['_productions'][i]
            _test.production(A, Ps)
        result = _test.make()

        if result['name'] != test['name']:
            raise ValueError('Invalid name produced')

        if result['start'] != test['start']:
            raise ValueError('Invalid start production produced')

        if len(result['productions']) != len(test['productions']):
            raise ValueError('Invalid productions produced')

        result['productions'].sort(key=lambda production: production[0])
        test['productions'].sort(key=lambda production: production[0])
        if not cmp_deep_seq(result['productions'], test['productions']):
            raise ValueError('Invalid production produced')

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

        if not cmp_deep_seq(result['conflicts'], test['conflicts']):
            raise ValueError('Invalid conflicts produced')
