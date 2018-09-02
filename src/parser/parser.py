"""
 parser.py includes the implementation of ContextFreeGrammar objects.

 The ContextFreeGrammar object represents a BNF (Backus-Naur form) input grammar
 programatically transformed into a parse table. While it is possible for any
 grammar to be specified, only LL(1) grammars are supported with the following
 requirements to successfully produce a parse table:

   1. No left recursion (direct or indirect)
   2. Must be left factored
   3. No ambiguity

 If any of the above requirements are violated, or the grammar specified is not
 LL(1), there will be a conflict in the table. This manifests itself as an entry
 with more than one member. This means with the given set of input productions
 and with the aid of a single look ahead token it cannot be known what rule to
 choose in order to successfully produce a parse.

 BNF grammars must be specified following these guidelines:
    - no syntax rules are enforced on nonterminals, but by conventions should be
      delimited by a pair of angle brackets '< >'
    - multiple productions per nonterminal may be specified, but each must be
      delimited by a '|'
    - production symbols must be delimited by whitespace
    - epsilon may be specified by declaring an empty production
"""
from copy import deepcopy


class ContextFreeGrammar(object):
    """
    ContextFreeGrammar represents a Backus-Naur form (BNF) input grammar
    programatically transformed into a parse table.
    """

    EOI = 0  # end of input marker ($)
    EPS = 1  # Epsilon marker

    def __init__(self, name, productions, start):
        """
        Attempt to initialize a ContextFreeGramamr object with the specified
        name, production rules and start rule name. Production rules are a dict
        where each key is a nonterminal and the corresponding value is the
        production rule. Multiple productions may be specified by seperating
        them by a vertical bar (|). An empty production specifies an epsilon.

        If creation is unsuccessful a TypeError or ValueError will be thrown,
        otherwise the results can be queried through the API provided below.

        Input Type:
          name:        String
          productions: Dict[String, String]
          start:       String

        Output Type: None | raise TypeError | raise ValueError
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

            if not isinstance(rhs, str):
                raise TypeError('production rule(s) must be a string')

            for rule in rhs.split('|'):
                self._rules.append((nonterminal, rule.split()))

        self._terminals, self._nonterminals = self._symbols(self._rules)
        self._first_set = self._first(self._terminals, self._nonterminals, self._rules)
        self._follow_set = self._follow(self._nonterminals, self._start,
                                        self._first_set, self._rules)
        self._parse_table, self._rows, self._cols = \
          self._table(self._terminals, self._nonterminals,
                      self._first_set, self._follow_set, self._rules)

    def name(self):
        """
        Query for the name of the grammar.

        Output Type: String
        """
        return deepcopy(self._name)

    def start(self):
        """
        Query for the start state of the grammar.

        Output Type: String
        """
        return deepcopy(self._start)

    def terminals(self):
        """
        Query for the terminals of the grammar.

        Output Type: Set[String]
        """
        return deepcopy(self._terminals)

    def nonterminals(self):
        """
        Query for the nonterminals of the grammar.

        Output Type: Set[String]
        """
        return deepcopy(self._nonterminals)

    def first(self):
        """
        Query for the first set's of the grammar's terminals and nonterminals.

        Output Type: Dict[String, Set[String, Int]]
        """
        return deepcopy(self._first_set)

    def follow(self):
        """
        Query for the follow set's of the grammar's nonterminals.

        Output Type: Dict[String, Set[String, Int]]
        """
        return deepcopy(self._follow_set)

    def rules(self):
        """
        Query for the production rules of the grammar.

        Output Type: List[Tuple[String, List[String]]]
        """
        return deepcopy(self._rules)

    def table(self):
        """
        Query for the parse table of the grammar.

        Output Type: List[List[Set[Int]]] x Dict[String, Int] x Dict[String, Int]
        """
        return deepcopy(self._parse_table), deepcopy(self._rows), deepcopy(self._cols)

    @staticmethod
    def _symbols(productions):
        """
        Report all literal terminal symbols and non terminal production symbols
        appearing  in the grammar.

        Runtime: O(n) - linear to the number symbols in the grammar.

        Input Type:
          productions: List[Tuple[String, List[String]]]

        Output Type: Set[String] x Set[String]
        """
        terminals, nonterminals = set(), set()
        for nonterminal, rule in productions:
            terminals.update(rule)
            nonterminals.add(nonterminal)
        terminals = terminals - nonterminals
        return terminals, nonterminals

    @staticmethod
    def _first_production(production, first):
        """
        Compute the first set of a single nonterminal's rhs/production following
        the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Runtime: O(n) - linear to the length of the production rule.

        Input Type:
          production: List[String]
          first:      Dict[String, Set[String, Int]]

        Output Type: Set[String, Int]
        """
        _first = set([ContextFreeGrammar.EPS])
        for symbol in production:
            _first.update(first[symbol])
            if ContextFreeGrammar.EPS not in first[symbol]:
                _first.discard(ContextFreeGrammar.EPS)
                break
        return _first

    @staticmethod
    def _first(terminals, nonterminals, productions):
        """
        Calculate the first set for each terminal and nonterminal in the grammar
        following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Runtime: O(?) - ?

        Input Type:
          terminals:    Set[String]
          nonterminals: Set[String]
          productions:  List[Tuple[String, List[String]]]

        Output Type: Dict[String, Set[String, Int]]
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
        """
        Calculate the follow set for each nonterminal in the grammar following
        the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Runtime: O(?) - ?

        Input Type:
          nonterminals: Set[String]
          first:        Dict[String, Set[String, Int]]
          productions:  List[Tuple[String, List[String]]]

        Output Type: Dict[String, Set[String, Int]]
        """
        # foreach elem A of NONTERMS do follow[A] = {}
        follow = {nonterminal: set() for nonterminal in nonterminals}

        # put $ (end of input marker) in follow(<Start>)
        follow[start] = set([ContextFreeGrammar.EOI])

        # loop until nothing new happens updating the follow sets
        while True:
            changed = False

            for nonterminal, production in productions:
                for (idx, elem) in enumerate(production):
                    if elem in nonterminals:
                        new = ContextFreeGrammar._first_production(production[idx+1:], first)
                        if ContextFreeGrammar.EPS in new:
                            new.discard(ContextFreeGrammar.EPS)
                            new.update(follow[nonterminal])

                        new = new - follow[elem]
                        if new:
                            follow[elem].update(new)
                            changed = True

            if not changed:
                return follow

    @staticmethod
    def _table(terminals, nonterminals, first, follow, productions):
        """
        Construct the LL(1) parse table indexed by nonterminal x terminal by
        finding the predict sets following the algorithm at:
        http://marvin.cs.uidaho.edu/Teaching/CS445/firstfollow.txt

        Runtime: O(?) - ?

        Input Type:
          terminals:    Set[String]
          nonterminals: Set[String]
          first:        Dict[String, Set[String, Int]]
          follow:       Dict[String, Set[String, Int]]
          productions:  List[Tuple[String, List[String]]]

        Output Type: List[List[Set[Int]]] x Dict[String] x Dict[String, Int]
        """
        rows = {n:i for i, n in enumerate(nonterminals)}
        cols = {t:i for i, t in enumerate(terminals | set([ContextFreeGrammar.EOI]))}

        table = [[set() for _ in cols] for _ in rows]

        for (rule, (nonterminal, production)) in enumerate(productions):
            predict = ContextFreeGrammar._first_production(production, first)
            if ContextFreeGrammar.EPS in predict:
                predict.discard(ContextFreeGrammar.EPS)
                predict.update(follow[nonterminal])
            for terminal in predict:
                table[rows[nonterminal]][cols[terminal]].add(rule)

        return table, rows, cols
