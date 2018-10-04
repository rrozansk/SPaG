"""Programmatic creation of parsers through ContextFreeGrammar objects.

The ContextFreeGrammar object represents a BNF (Backus-[Naur/Normal] Form)
grammar which is programmatically transformed into a parse table. This is done
by utilizing the grammars first and follow sets, which are computed internally,
and applying that information to properly construct the resulting parse table.
"""
from copy import deepcopy


class ContextFreeGrammar(object):
    """The ContextFreeGrammar object responsible for creating parse tables.

    ContextFreeGrammar represents a Backus-[Naur/Normal] Form (BNF) language
    grammar which is programmatically transformed into a parse table by finding
    and utilizing the languages first and follow sets. Once created the object
    cannot be mutated, and it will remain static for the rest of it's lifetime.
    All information to properly understand and consume the parse table can be
    queried through the exposed API functions.

    Attributes:
      END_OF_INPUT (int): The marker to use for End Of Input (i.e. '$').
      EPSILON      (int): The marker to use for Epsilon.
    """

    END_OF_INPUT = 0
    EPSILON = 1

    def __init__(self, name, productions, start):
        """Construct a parse table for the given BNF grammar.

        Attempt to initialize a ContextFreeGramamr object with the specified
        name, production rule(s) and start rule identifier. While it is possible
        for any type of grammar to be specified, only left factored LL(1)
        grammars will produce a parse table with a single member per entry. To
        properly specify a LL(1) grammar the following requirements must be met:

          * No left recursion (direct or indirect)
          * Must be left factored
          * No ambiguity

        If any of the above requirements are violated, or the grammar specified
        is not LL(1), there will be a conflict in the table. This means with the
        given set of input productions and with the aid of a single look ahead
        token it cannot be known what rule to choose in order to successfully
        produce a parse without backtracking.

        Args:
          name (str): The name of the input grammar.
          productions (dict[str, list[list[str]]): The production rules of the
              grammar. Dictionary keys are nonterminals and values are a list of
              rules, which are a series of [non]terminal string identifiers. An
              empty rule can be used for epsilon.
          start (str): The start productions nonterminal identifier of the grammar.

        Raises:
          TypeError: if `name` is not a string
          ValueError: if `name` is empty
          TypeError: if `start` is not a string
          ValueError: if `start` is empty
          TypeError: if `productions` is not a dict
          ValueError: if `productions` is empty
          ValueError: if `start` not in `productions`
          TypeError: if any `productions` nonterminal is not a string
          ValueError: if any `productions` nonterminal is empty
          TypeError: if any `productions` nonterminal rules is not a list
          ValueError: if any `productions` nonterminal rules is empty
          TypeError: if any `productions` nonterminal rule is not a list
          TypeError: if any `productions` nonterminal rule contain non strings
          ValueError: if any `productions` nonterminal rule contain empty strings
        """
        if not isinstance(name, str):
            raise TypeError('name must be a string')

        if not name:
            raise ValueError('name must be non empty')

        self._name = name

        if not isinstance(start, str):
            raise TypeError('start must be a string')

        if not start:
            raise ValueError('start must be non empty')

        self._start = start

        if not isinstance(productions, dict):
            raise TypeError('productions must be a dict')

        if not productions:
            raise ValueError('productions must be non empty')

        if self._start not in productions:
            raise ValueError('start production not present in given productions')

        self._rules = []
        for nonterminal, rhs in productions.items():
            if not isinstance(nonterminal, str):
                raise TypeError('production nonterminal must be a string')

            if not nonterminal:
                raise ValueError('production nonterminal must be non empty')

            if not isinstance(rhs, list):
                raise TypeError('production rules must be a list')

            if not rhs:
                raise ValueError('production rules must be non empty')

            for rule in rhs:
                if not isinstance(rule, list):
                    raise TypeError('production rule must be a list')

                for symbol in rule:
                    if not isinstance(symbol, str):
                        raise TypeError('production rule symbol must be a string')

                    if not symbol:
                        raise ValueError('production rule symbol must be non empty')

                self._rules.append((nonterminal, rule))

        self._terminals, self._nonterminals = self._symbols(self._rules)
        self._first_set = self._first(self._terminals, self._nonterminals, self._rules)
        self._follow_set = self._follow(self._nonterminals, self._start,
                                        self._first_set, self._rules)
        self._parse_table, self._rows, self._cols = \
          self._table(self._terminals, self._nonterminals,
                      self._first_set, self._follow_set, self._rules)

    @property
    def name(self):
        """Query for the name of the grammar.

        A readonly property which copies the grammar's name to protect against
        user mutations.

        Return:
          str: The given input name of the grammar.
        """
        return deepcopy(self._name)

    @property
    def start(self):
        """Query for the start production's nonterminal of the grammar.

        A readonly property which copies the grammar's start production
        nonterminal to protect against user mutations.

        Return:
          str: The given start production nonterminal.
        """
        return deepcopy(self._start)

    @property
    def terminals(self):
        """Query for the terminal set of the grammar.

        A readonly property which copies the grammar's terminal set to protect
        against user mutations.

        Return:
          set[str]: The set of terminal symbols contained in the grammar.
        """
        return deepcopy(self._terminals)

    @property
    def nonterminals(self):
        """Query for the nonterminal set of the grammar.

        A readonly property which copies the grammar's nonterminal set to
        protect against user mutations.

        Return:
          set[str]: The set of nonterminal production symbols in the grammar.
        """
        return deepcopy(self._nonterminals)

    @property
    def first(self):
        """Query for the first set(s) of the grammar's [non]terminal(s).

        A readonly property which copies the first set(s) of the grammar's
        [non]terminal(s) to protect against user mutations.

        Return:
          dict[str, set[str, int]]: The first set of every [non]terminal.
        """
        return deepcopy(self._first_set)

    @property
    def follow(self):
        """Query for the follow set(s) of the grammar's nonterminal(s).

        A readonly property which copies the follow set(s) grammar's
        nonterminals to protect against user mutations.

        Return:
          dict[str, set[str, int]]: The follow set of every nonterminal.
        """
        return deepcopy(self._follow_set)

    @property
    def rules(self):
        """Query for the production rules of the grammar.

        A readonly property which copies the grammar's flattened production
        rules to protect against user mutations.

        Return:
          list[tuple[str, list[str]]]: A flattened list of production rules.
        """
        return deepcopy(self._rules)

    @property
    def table(self):
        """Query for the parse table of the given input grammar.

        A readonly property which copies the grammar's parse table to protect
        against user mutations.

        Return:
          list[list[set[int]]]: row-major parse table with list rule
            inidice(s) entries. (i.e. Table[nonterminal][terminal] -> rules)
          dict[str, int]: Mapping for row (nonterminal) symbol to table index.
          dict[str, int]: Mapping for column (terminal) symbol to table index.
        """
        return deepcopy(self._parse_table), \
               deepcopy(self._rows), \
               deepcopy(self._cols)

    @staticmethod
    def _symbols(productions):
        """Collect the [non]terminals from the given input productions.

        Report all literal terminal symbols and non terminal production symbols
        appearing in the productions present.

        Args:
          productions (list[tuple[str, list[str]]]): The input production rules.

        Return:
          set[str]: The set of terminal symbols contained in the grammar.
          set[str]: The set of nonterminal production symbols in the grammar.
        """
        terminals, nonterminals = set(), set()
        for nonterminal, rule in productions:
            terminals.update(rule)
            nonterminals.add(nonterminal)
        terminals = terminals - nonterminals
        return terminals, nonterminals

    @staticmethod
    def _first_production(production, first):
        """Derive the first set given a single production rule.

        Compute the first set for a single nonterminal's production rule
        following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Args:
          production (list[str]): a series of [non]terminal symbols.
          first (dict[str, set[str, int]]): first sets for [non]terminals.

        Return:
          set[str, int]: possible symbols first encountered for `production`.
        """
        _first = set([ContextFreeGrammar.EPSILON])
        for symbol in production:
            _first.update(first[symbol])
            if ContextFreeGrammar.EPSILON not in first[symbol]:
                _first.discard(ContextFreeGrammar.EPSILON)
                break
        return _first

    @staticmethod
    def _first(terminals, nonterminals, productions):
        """Derive the grammars first sets.

        Calculate the first set for each [non]terminal in the grammar following
        the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Args:
          terminals (set[str]): set of grammar terminal symbols.
          nonterminals (set[str]): set of grammar nonterminal symbols.
          productions (list[tuple[str, list[str]]]): flattened list of rules.

        Return:
          dict[str, set[str, int]]: The first set of every [non]terminal.
        """
        first = {}

        # foreach elem A of TERMS do first[A] = {A}
        for terminal in terminals:
            first[terminal] = set([terminal])

        # foreach elem A of NONTERMS do first[A] = {}
        for nonterminal in nonterminals:
            first[nonterminal] = set()

        # loop until nothing new happens updating the first sets
        while True:
            changed = False

            for nonterminal, production in productions:
                new = ContextFreeGrammar._first_production(production, first) - first[nonterminal]
                if new:
                    first[nonterminal].update(new)
                    changed = True

            if not changed:
                return first

    @staticmethod
    def _follow(nonterminals, start, first, productions):
        """Derive the grammars follow sets.

        Calculate the follow set for each nonterminal in the grammar following
        the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Args:
          nonterminals (set[str]): set of grammar nonterminal symbols.
          start (str): The given start production nonterminal.
          first (dict[str, set[str, int]]): first sets for [non]terminals.
          productions (list[tuple[str, list[str]]]): flattened list of rules.

        Return:
          dict[str, set[str, int]]: The follow set of every nonterminal.
        """
        # foreach elem A of NONTERMS do follow[A] = {}
        follow = {nonterminal: set() for nonterminal in nonterminals}

        # put $ (end of input marker) in follow(<Start>)
        follow[start] = set([ContextFreeGrammar.END_OF_INPUT])

        # loop until nothing new happens updating the follow sets
        while True:
            changed = False

            for nonterminal, production in productions:
                for (idx, elem) in enumerate(production):
                    if elem in nonterminals:
                        new = ContextFreeGrammar._first_production(production[idx+1:], first)
                        if ContextFreeGrammar.EPSILON in new:
                            new.discard(ContextFreeGrammar.EPSILON)
                            new.update(follow[nonterminal])

                        new = new - follow[elem]
                        if new:
                            follow[elem].update(new)
                            changed = True

            if not changed:
                return follow

    @staticmethod
    def _table(terminals, nonterminals, first, follow, productions):
        """Programmatically construct the grammars parse table.

        Construct the parse table indexed by nonterminal x terminal. This is
        done by finding the predict sets, derived from the first sets,
        following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Args:
          terminals (set[str]): set of grammar terminal symbols.
          nonterminals (set[str]): set of grammar nonterminal symbols.
          first (dict[str, set[str, int]]): first sets for [non]terminals.
          follow (dict[str, set[str, int]]): follow sets for terminals.
          productions (list[tuple[str, list[str]]]): flattened list of rules.

        Return:
          list[list[set[int]]]: row-major parse table with list rule
            inidice(s) entries. (i.e. Table[nonterminal][terminal] -> rules)
          dict[str, int]: Mapping for row (nonterminal) symbol to table index.
          dict[str, int]: Mapping for column (terminal) symbol to table index.
        """
        rows = {n:i for i, n in enumerate(nonterminals)}
        cols = {t:i for i, t in enumerate(terminals | set([ContextFreeGrammar.END_OF_INPUT]))}

        table = [[set() for _ in cols] for _ in rows]

        for (rule, (nonterminal, production)) in enumerate(productions):
            predict = ContextFreeGrammar._first_production(production, first)
            if ContextFreeGrammar.EPSILON in predict:
                predict.discard(ContextFreeGrammar.EPSILON)
                predict.update(follow[nonterminal])
            for terminal in predict:
                table[rows[nonterminal]][cols[terminal]].add(rule)

        return table, rows, cols
