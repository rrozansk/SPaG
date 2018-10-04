"""Programmatic creation of scanners through RegularGrammar objects.

The RegularGrammar object represents a group of formal regular expressions
which can be programatically transformed into a minimal DFA (Deterministic
Finite Automata) recognizing the given input pattern(s). This is done through a
series of transformations on the input taking it from an expression to an
epsilon NFA and finally to a minimal DFA.
"""
from uuid import uuid4
from string import printable
from copy import deepcopy


class RegularGrammar(object):
    """The RegularGrammar object responsible for creating the minimal DFA.

    RegularGrammar represents a collection of named formal regular expressions
    which can be programatically compiled into a minmal DFA capable of
    recognizing the input patterns. The resulting DFA is encoded as a table with
    a total delta (transition) function. Once created the object cannot be
    mutated, and it will remain static for the rest of it's lifetime. All
    information to properly understand and consume the DFA table can be queried
    through the exposed API functions.
    """

    # Map internal representation of operators -> literals
    _literals = dict(enumerate('*|.+?()[]'))

    # Map operator literals -> internal representation
    _operators = {v:k for k, v in _literals.items()}

    # Set of acceptable input characters (printable ascii) including:
    # uppercase, lowercase, digits, punctuation, whitespace. needed for
    # character class/range negation
    _characters = set(printable)

    # Operator precedence for the shunting yard algorithm.
    # (higher binds tighter)
    _precedence = {
        _operators['(']: (3, None),
        _operators[')']: (3, None),
        _operators['+']: (2, False),  # right-associative
        _operators['*']: (2, False),  # right-associative
        _operators['?']: (2, False),  # right-associative
        _operators['.']: (1, True),   # left-associative
        _operators['|']: (0, True),   # left-associative
    }

    def __init__(self, name, expressions):
        """Construct a scanner DFA given the input regular expressions.

        Attempt to initialize a RegularGrammar object with the specified name,
        recognizing the given named expression(s). Regular expressions must be
        specified following these guidelines:

           * only printable ascii characters (uppercase, lowercase, digits,
             punctuation, whitespace) are supported.
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
               * character classes and ranges can be combined in the same set
                 of brackets, possibly multiple times (e.g. [abc-pqrs-z]).
               * character ranges can be specified as forward or backwards
                 (e.g. [a-c] or [c-a]).
               * '^' is required to come first after the bracket for
                 negation to properly work. In fact, '^' directly following a
                 bracket is always interpreted as negation.
               * '^' may be used with character classes or ranges.
               * if '^' is alone in the brackets (e.g. [^]) it is translated
                 as any possible input character (i.e. a 'wildcard').
               * if a literal '-' if required in a character class or range it
                 must be specified last so as to not be interpreted as a range.
               * for literal right brackets inside character ranges or classes
                 it must be escaped.
               * concatenation can be either implicit or explicit in the
                 given input expression(s).
               * operator literals (i.e. '|.?*+()[]') can be specified through
                 escape sequences using a backslash (i.e. '\').

        The input is then taken through a series of transformations taking it
        from a regular expression to an epsilon NFA and finally to a minimal
        DFA. The final minimal DFA produced will be minimized with respect to
        unreachable and nondistinguishable states. It will also have a total
        delta (transition) function, possibly including an sink/error state if
        necessary. It will also include a dictionary mapping the named input
        expressions (i.e. types) to there corresponding final state(s) within
        the resulting DFA.

        Args:
          name (str): the name of the scanner.
          expressions (dict[str, str]): token name/type and there pattern(s).

        Raises:
          TypeError: if name is not a string
          ValueError: if name is empty
          TypeError: if expressions is not a dict
          ValueError: if expressions is empty
          TypeError: if token identifier/type is not a string
          ValueError: if token identifier/type is empty
          TypeError: if token pattern is not a string
          ValueError: if token pattern is empty
          ValueError: if an invalid escape sequence is encountered.
          ValueError: if an unrecognized escape sequence is encountered.
          ValueError: if an empty escape sequence is encountered.
          ValueError: if character range has no starting bracket.
          ValueError: if character range has no ending bracket.
          ValueError: if left parenthesis are unbalanaced.
          ValueError: if right parenthesis are unbalanaced.
          ValueError: if concatentation is supplied with an improper arguments
          ValueError: if alternation is supplied with an improper arguments
          ValueError: if kleene star is supplied with an improper arguments
          ValueError: if kleene plus is supplied with an improper arguments
          ValueError: if choice is supplied with an improper arguments
          ValueError: if the input expression is invalid
        """
        if not isinstance(name, str):
            raise TypeError('name must be a string')

        if not name:
            raise ValueError('name must be non empty')

        self._name = name

        if not isinstance(expressions, dict):
            raise TypeError('expressions must be a dict')

        if not expressions:
            raise ValueError('expressions must be non empty')

        self._expressions = {}

        nfa = []
        for identifier, pattern in expressions.items():
            if not isinstance(identifier, str):
                raise TypeError('token name/type must be a string')

            if not identifier:
                raise ValueError('token name/type must be non empty')

            if not isinstance(pattern, str):
                raise TypeError('token pattern must be a string')

            if not pattern:
                raise ValueError('token pattern must be non empty')

            self._expressions[identifier] = pattern

            pattern = RegularGrammar._scan(pattern)
            pattern = RegularGrammar._expand_char_class_range(pattern)
            pattern = RegularGrammar._expand_concat(pattern)
            pattern = RegularGrammar._shunt(pattern)

            nfa.append((RegularGrammar._nfa(identifier, pattern)))

        Q, V, T, S, F, G = RegularGrammar._dfa(*RegularGrammar._merge_nfa(nfa))
        Q, V, T, S, F, G = RegularGrammar._total(Q, V, T, S, F, G)
        Q, V, T, S, F, G = RegularGrammar._alpha(*RegularGrammar._hopcroft(Q, V, T, S, F, G))

        self._states = Q
        self._alphas = V
        self._deltas = T
        self._start = S
        self._finals = F
        self._types = G

    @property
    def name(self):
        """Query for the name of the scanner.

        A readonly property which copies the scanners's name to protect against
        user mutations.

        Return:
          str: The given input name of the scanner.
        """
        return deepcopy(self._name)

    @property
    def expressions(self):
        """Query for the patterns recognized by the scanner.

        A readonly property which copies the scanners's token name/expression
        pairs to protect against user mutations.

        Return:
          list[tuple[str, str]]: the token name/expression pairs
        """
        return deepcopy(self._expressions)

    @property
    def states(self):
        """Query for states in the grammars equivalent minimal DFA.

        A readonly property which copies the scanner's states to protect against
        user mutation.

        Return:
          set[str]: all possible states in the resulting DFA.
        """
        return deepcopy(self._states)

    @property
    def alphabet(self):
        """Query for alphabet of characters recognized by the grammars DFA.

        A readonly property which copies the scannner's alphabet to protect
        against user mutation.

        Return:
          set[str]: all possible input characters to the resulting DFA.
        """
        return deepcopy(self._alphas)

    @property
    def transitions(self):
        """Query for the state transitions defining the grammars DFA.

        A readonly property which copies the scannner's transitions to protect
        against user mutation.

        Return:
          tuple[dict[str, int], dict[str, int], list[list[str]]]: the DFA
            encoded as a table.
        """
        return deepcopy(self._deltas)

    @property
    def start(self):
        """Query for the start state of the grammars DFA.

        A readonly property which copies the scanner's start state to protect
        against user manipulation.

        Return:
          str: the start state of the grammars DFA.
        """
        return deepcopy(self._start)

    @property
    def accepting(self):
        """Query for all accepting states of the grammars DFA.

        A readonly property which copies the scanner's accepting states to
        protect against user manipulation.

        Return:
          set[str]: the resulting DFA's accepting states.
        """
        return deepcopy(self._finals)

    @property
    def types(self):
        """Query for the dictionary labeling all types to ther final state(s).

        A readonly property which copies the scanner's types to protect against
        user manipulation.

        Return:
          dict[str, set[str]]: the resulting DFA's token types.
        """
        return deepcopy(self._types)

    @staticmethod
    def _scan(expr):
        """transform the external representation to an internal one.

        Convert an external representation of a token (regular expression) to
        an internal one. Ensures all characters and escape sequences are valid.

        Args:
          expr (str): an external representation of a regular expression.

        Return:
          list[str, int]: an internal representation of a regular expression.

        Raises:
          ValueError: if an invalid escape sequence is encountered.
          ValueError: if an unrecognized escape sequence is encountered.
          ValueError: if an empty escape sequence is encountered.
        """
        output = []
        escape = False
        for char in expr:
            if escape:
                escape = False
                if char in RegularGrammar._operators:
                    output.append(char)
                elif char == '\\':
                    output.append('\\')
                elif char == 's':
                    output.append(' ')
                elif char == 't':
                    output.append('\t')
                elif char == 'n':
                    output.append('\n')
                elif char == 'r':
                    output.append('\r')
                elif char == 'f':
                    output.append('\f')
                elif char == 'v':
                    output.append('\v')
                else:
                    raise ValueError('Error: invalid escape seq: \\' + char)
            else:
                if char == '\\':
                    escape = True
                elif char in RegularGrammar._operators:
                    output.append(RegularGrammar._operators[char])
                elif char in RegularGrammar._characters:
                    output.append(char)
                else:
                    raise ValueError('Error: unrecognized character: ' + char)
        if escape:
            raise ValueError('Error: empty escape sequence')
        return output

    @staticmethod
    def _expand_char_class_range(expr):
        """expand any character classes/ranges present in the expression.

        Expand the internal representation of the expression so that
        character classes and ranges are eliminated.

        Args:
          expr (list[str, int]): an internal representation of a regular
              expression possible with character ranges and/or classes.

        Return:
          list[str, int]: an internal representation of a regular expression
              with all character classes and ranges elimintated.

        Raises:
          ValueError: if character range has no starting bracket.
          ValueError: if character range has no ending bracket.
        """
        output, literals = [], []
        expansion, negation, prange = False, False, False
        for char in expr:
            if char == RegularGrammar._operators['['] and not expansion:
                expansion = True
            elif char == RegularGrammar._operators[']']:
                if not expansion:
                    raise ValueError('Error: Invalid character class/range; no start')
                expansion = False
                if prange:
                    prange = False
                    literals.append('-')
                if negation:
                    negation = False
                    literals = list(RegularGrammar._characters - set(literals))
                if literals:
                    literals = list(set(literals))
                    output.append(RegularGrammar._operators['('])
                    while literals:
                        output.append(literals.pop())
                        output.append(RegularGrammar._operators['|'])
                    output[-1] = RegularGrammar._operators[')']
            elif not expansion:
                output.append(char)
            elif char == '^' and not literals and not negation:
                negation = True
            elif char == '-' and literals and not prange:
                prange = True
            elif prange:
                prange = False
                _char = literals.pop()
                literals.extend(map(chr, range(ord(min(_char, char)), ord(max(_char, char))+1)))
            else:
                literals.append(RegularGrammar._literals.get(char, char))
        if expansion:
            raise ValueError('Error: character class/range end not specified')
        return output

    @staticmethod
    def _expand_concat(expr):
        """make concatenation explicit throughout the expression.

        Expand the internal representation of the expression so that
        concatentation is explicit throughout.

        Args:
          expr (list[str, int]): an internal representation of a regular
              expression possibly using implicit concatenation.

        Return:
          list[str, int]: an internal representation of a regular expression
              with concatenation explicit throughout.
        """
        if not expr:
            return expr

        output = [expr[0]]
        for elem in expr[1:]:
            if output[-1] != RegularGrammar._operators['('] and \
               output[-1] != RegularGrammar._operators['|'] and \
               output[-1] != RegularGrammar._operators['.'] and \
               (elem == RegularGrammar._operators['('] or
                elem not in RegularGrammar._literals):
                output.append(RegularGrammar._operators['.'])
            output.append(elem)
        return output

    @staticmethod
    def _shunt(expr):
        """Convert infix regular expression notation to postfix.

        Convert the input expression to be entirely in postfix notation (RPN;
        Reverse Polish Notation) allowing all parenthesis to be dropped.
        Adapted from Dijkstra's Shunting yard algorithm which can be viewed
        @https://en.wikipedia.org/wiki/Shunting-yard_algorithm.

        Args:
          expr (list[str, int]): an infix regular expression.

        Return:
          list[str, int]: a postfix regular expression.

        Raises:
          ValueError: if left parenthesis are unbalanaced.
          ValueError: if right parenthesis are unbalanaced.
        """
        stack, queue = [], []  # operators, output expression

        for token in expr:
            if token == RegularGrammar._operators['(']:
                stack.append(RegularGrammar._operators['('])
            elif token == RegularGrammar._operators[')']:
                while stack and stack[-1] != RegularGrammar._operators['(']:
                    queue.append(stack.pop())
                if not stack:
                    raise ValueError('Error: unbalanced right parenthesis')
                stack.pop()
            elif token in RegularGrammar._precedence:
                while stack and stack[-1] != RegularGrammar._operators['('] and\
                      RegularGrammar._precedence[token][0] <= \
                      RegularGrammar._precedence[stack[-1]][0]\
                      and RegularGrammar._precedence[token][1]:  # left-associative?
                    queue.append(stack.pop())
                stack.append(token)
            else:  # it's a character
                queue.append(token)

        while stack:
            token = stack.pop()
            if token == RegularGrammar._operators['(']:
                raise ValueError('Error: unbalanced left parenthesis')
            queue.append(token)

        return queue

    @staticmethod
    def _state():
        """Generate a new universally unique state label.

        The state label is a string prepresentation of a UUID type 4.

        Return:
          str: a unique state name
        """
        return str(uuid4())

    @staticmethod
    def _nfa(name, expr):
        """convert a postfix notation regular expression to an epsilon NFA.

        Attempt to convert an internal representation of a regular expression
        in RPN to an epsilon NFA. Operators handled: union |, kleene star *,
        concatenation ., literals, and syntax extensions kleene plus + and
        choice ?. Adapted to a iterative stacked based evaluation algorithm
        (standard RPN evaluation algorithm) from thompson construction as
        described in section 4.1 in 'A taxonomy of finite automata construction
        algorithms' by Bruce Watson,
        located @http://alexandria.tue.nl/extra1/wskrap/publichtml/9313452.pdf

        Args:
          name (str): the identifier/type of the expression.
          expr (list[str, int]): a regular expression in postfix notation.

        Return:
          set[str]: the set of states, Q
          set[str]: the set of alphabet characters, V
          set[tuple[str, str, str]]: the set of state transitions, T
          dict[str, set[str]]: the set of epsilon transitions, E
          str: the start state, S
          str: the final state, F
          dict[str, str]: map of identifier/type to final state, G

        Raises:
          ValueError: if concatentation is supplied with an improper arguments
          ValueError: if alternation is supplied with an improper arguments
          ValueError: if kleene star is supplied with an improper arguments
          ValueError: if kleene plus is supplied with an improper arguments
          ValueError: if choice is supplied with an improper arguments
          ValueError: if the input expression is invalid
        """
        Q = set()   # states
        V = set()   # input symbols (alphabet)
        T = set()   # transition relation: T in P(Q x V x Q)
        E = dict()  # e-transition relation: E in P(Q x Q)
        S = None    # start state S in Q
        F = None    # accepting state F in Q
        G = dict()  # map type to the final state(s)

        def e_update(start, final):
            """An internal helper to update the epsilon dictionary cache."""
            E[start] = E.get(start, set())
            E[start].add(final)

        stk = []  # NFA machine stk
        for token in expr:
            if token == RegularGrammar._operators['.']:
                if len(stk) < 2:
                    raise ValueError('Error: not enough args to op .')
                p, F = stk.pop()
                S, q = stk.pop()
                e_update(q, p)
            elif token == RegularGrammar._operators['|']:
                if len(stk) < 2:
                    raise ValueError('Error: not enough args to op |')
                p, q = stk.pop()
                r, t = stk.pop()
                S, F = RegularGrammar._state(), RegularGrammar._state()
                e_update(S, p)
                e_update(S, r)
                e_update(q, F)
                e_update(t, F)
            elif token == RegularGrammar._operators['*']:
                if len(stk) < 1:
                    raise ValueError('Error: not enough args to op *')
                p, q = stk.pop()
                S, F = RegularGrammar._state(), RegularGrammar._state()
                e_update(S, p)
                e_update(q, p)
                e_update(q, F)
                e_update(S, F)
            elif token == RegularGrammar._operators['+']:
                if len(stk) < 1:
                    raise ValueError('Error: not enough args to op +')
                p, q = stk.pop()
                S, F = RegularGrammar._state(), RegularGrammar._state()
                e_update(S, p)
                e_update(q, p)
                e_update(q, F)
            elif token == RegularGrammar._operators['?']:
                if len(stk) < 1:
                    raise ValueError('Error: not enough args to op ?')
                p, q = stk.pop()
                S, F = RegularGrammar._state(), RegularGrammar._state()
                e_update(S, p)
                e_update(S, F)
                e_update(q, F)
            else:  # it's a character
                S, F = RegularGrammar._state(), RegularGrammar._state()
                V.add(token)
                T.add((S, token, F))
            Q.update([S, F])
            stk.append((S, F))

        if len(stk) != 1:
            raise ValueError('Error: invalid expression')
        S, F = stk.pop()
        G[name] = F
        return Q, V, T, E, S, F, G

    @staticmethod
    def _merge_nfa(nfa):
        """merge a list of NFAs into a single NFA.

        Merge multiple NFAs into a single NFA with a new start state containing
        epsilon transitions to each individual machine's start state.

        Args:
          nfa: list[tuple[
                          set[str],
                          set[str],
                          set[tuple[str, str, str]],
                          dict[str, set[str]],
                          str,
                          str,
                          dict[str, str]
                    ]]: the input NFAs to merge together.

        Return:
          set[str]: the merged set of states, Q
          set[str]: the merged set of alphabet characters, V
          set[tuple[str, str, str]]: the merged set of state transitions, T
          dict[str, set[str]]: the merged set of epsilon transitions, E
          str: the new start state, S
          set[str]: the merged set of final states, F
          dict[str, str]: merged mapping of expression type to final state(s), G
        """
        S = RegularGrammar._state()
        Q, V, T, E, S, F, G = set(), set(), set(), dict(), S, set(), dict()
        E[S] = set()
        for _nfa in nfa:
            Q.update(_nfa[0])
            V.update(_nfa[1])
            T.update(_nfa[2])
            E[S].add(_nfa[4])
            for state, etransitions in _nfa[3].items():
                E[state] = E.get(state, set()) | etransitions
            F.add(_nfa[5])
            for name, state in _nfa[6].items():
                G[name] = state
        return Q, V, T, E, S, F, G

    @staticmethod
    def _e_closure(q, E, cache):
        """find the epsilon closure of the current state and cache the result.

        Find the epsilon closure of a given state given all epsilon transitions.
        A cache is utilized to speed things up for repeated invocations. Stated
        in set notation: { q' | q ->*e q' }, from a given start state q find all
        states q' which are reachable using only epsilon transitions, handling
        cycles appropriately.

        Args:
          q (str): the state to find the e-closure of.
          E (dict[str, set[str]]): the set of e-transitions.
          cache (dict[str, set[str]]): previously computed e-closures.

        Return:
          set[str]: the e-closure of state q.
        """
        if q in cache:
            return cache[q]

        cache[q] = closure = set()
        explore = set([q])
        while explore:
            q = explore.pop()
            if q not in closure:
                closure.add(q)
                # perform a single step: { q' | q ->e q' }
                explore.update(E.get(q, set()))

        return closure

    @staticmethod
    def _dfa(Q, V, T, E, S, F, G):
        """convert the input NFA (possibly with epsilon transitions) to a DFA.

        Convert the epsilon NFA to a DFA using subset construction and
        e-closure conversion. Only states wich are reachable from the start
        state are considered. This results in a minimized DFA with reguard to
        reachable states, but not with reguard to nondistinguishable states.

        Args:
          Q (set[str]): set of NFA states
          V (set[str]): set of NFA alphabet characters
          T (set[tuple[str, str, str]]): set of state transitions
          E (dict[str, set[str]]): set of epsilon transitions
          S (str): start state
          F (set[str]): set of final states
          G (dict[str, str]): mapping of expressions types to final states

        Return:
          set[frozenset[str]]: set of DFA states
          set[str]: set of characters in the DFA alphabet
          set[tuple[frozenset[str], str, frozenset[str]]]: the DFA transitions
          frozenset[str]: the DFA start state
          set[frozenset[str]]: set of DFA final states
          dict[str, set[frozenset[str]]]: mapping of types to final states
        """
        cache, Gp = dict(), dict()
        Sp = frozenset(RegularGrammar._e_closure(S, E, cache))
        Qp, Fp, Tp, explore = set(), set(), set(), set([Sp])
        while explore:
            in_state = explore.pop()  # DFA state; set of NFA states
            if in_state not in Qp:
                Qp.add(in_state)
                if F & in_state:
                    Fp.add(in_state)
                qps = {}
                for t in T:
                    if t[0] in in_state:
                        out_states = qps[t[1]] = qps.get(t[1], set())
                        out_states.update(RegularGrammar._e_closure(t[2], E, cache))
                for alpha, out_state in qps.items():
                    out_state = frozenset(out_state)
                    explore.add(out_state)
                    Tp.add((in_state, alpha, out_state))

        for name, nfa_final in G.items():
            for dfa_final in Fp:
                if nfa_final in dfa_final:
                    Gp[name] = Gp.get(name, set()) | set([dfa_final])

        return Qp, V, Tp, Sp, Fp, Gp

    @staticmethod
    def _total(Q, V, T, S, F, G):
        """extend the DFA's transition function, making it total.

        Make the DFA's delta function total, if not already, by adding a
        sink/error state. All unspecified state transitions are then specified
        by adding a transition to the new sink/error state. A new entry is also
        made into G to track this new sink/error type which is accessible as
        '_sink'.

        Args:
          Q (set[frozenset[str]]): set of DFA states
          V (set[str]): the DFA alphabet
          T (set[tuple[frozenset[str], str, frozenset[str]]]): DFA transitions
          S (frozenset[str]): the DFA start state
          F (set[frozenset[str]]): the set of DFA final states
          G (dict[str, set[frozenset[str]]]): DFA pattern name to final state(s)

        Return:
          set[frozenset[str]]: possibly extended set of DFA states
          set[str]: the given input alphabet
          tuple[
                dict[frozenset[str], int],
                dict[str, int],
                list[list[frozenset[str]]]
               ]: a possibly extended transition function converted to a table
          frozenset[str]: the input start state
          set[frozenset[str]]: the input final state(s)
          dict[str, set[frozenset[str]]]: the type to pattern mapping
        """
        q_err = frozenset([RegularGrammar._state()])
        if len(T) != len(Q) * len(V):
            Q.add(q_err)
            G['_sink'] = set([q_err])

        states = {v:k for k, v in enumerate(Q)}
        symbols = {v:k for k, v in enumerate(V)}
        table = [[q_err for _ in states] for _ in symbols]
        for (state, symbol, dest) in T:
            table[symbols[symbol]][states[state]] = dest

        return Q, V, (states, symbols, table), S, F, G

    @staticmethod
    def _hopcroft(Q, V, T, S, F, G):
        """reduce the DFA state complexity by merging nondistinguishable states.

        Minimize the DFA with reguard to nondistinguishable states using
        hopcrafts algorithm, which merges states together based on partition
        refinement.

        Args:
          Q (set[frozenset[str]]): the set of DFA states
          V (set[str]): the set of DFA input characters
          T (tuple[
                   dict[frozenset[str], int],
                   dict[str, int],
                   list[list[frozenset[str]]]
                  ]): the DFA transition function as a table
          S (frozenset[str]): the DFA start state
          F (set[frozenset[str]]): the set of DFA final states
          G (dict[str, set[frozenset[str]]]): map of type to DFA final state(s)

        Return:
          set[set[frozenset[frozenset[str]]]]: set of possible merged states
          set[str]: the given set of input chacters
          tuple[
                dict[set[frozenset[frozenset[str]]], int],
                dict[str, int],
                list[list[set[frozenset[frozenset[str]]]]]
               ]: possibly updated and reduced table with merged states
          set[frozenset[frozenset[str]]]: a possibly updated start state.
          set[set[frozenset[frozenset[str]]]]: a possibly updated set of final
              states.
          dict[str, set[set[frozenset[frozenset[str]]]]: a possibly updated map
              of token to final state(s).
        """
        (states, symbols, T) = T
        Q, F = frozenset(Q), frozenset(F)

        partitions = set([F, Q - F]) - set([frozenset()])  # if Q - F was empty
        explore = set([F])

        while explore:
            selection = explore.pop()
            for v_idx in symbols.values():
                _selection = {q for q, q_idx in states.items() if T[v_idx][q_idx] in selection}
                _selection = frozenset(_selection)
                _partitions = set()
                for partition in partitions:
                    split_1 = _selection & partition
                    split_2 = partition - _selection
                    if split_1 and split_2:
                        _partitions.update([split_1, split_2])
                        if partition  in explore:
                            explore.remove(partition)
                            explore.update([split_1, split_2])
                        elif len(split_1) <= len(split_2):
                            explore.update([split_1])
                        else:
                            explore.update([split_2])
                    else:
                        _partitions.add(partition)
                partitions = _partitions

        _states = dict(zip(partitions, range(len(partitions))))
        Tp = [[None for _ in partitions] for symbol in V]
        for source in states:
            for symbol in V:
                dest = T[symbols[symbol]][states[source]]
                state_1, state_2 = None, None
                for part in partitions:
                    if source in part:
                        state_1 = part
                        if state_2:
                            break
                    if dest in part:
                        state_2 = part
                        if state_1:
                            break
                Tp[symbols[symbol]][_states[state_1]] = state_2

        Sp = None
        for part in partitions:
            if S in part:
                Sp = part
                break

        Fp = {partition for partition in partitions if partition & F}

        Gp = dict()

        for name, dfa_finals in G.items():
            if name == '_sink': # special case (i.e not a final state)
                Gp[name] = {part for part in partitions if part & G['_sink']}
                continue
            for dfa_final in dfa_finals:
                for dfa_merged_final in Fp:
                    if dfa_final in dfa_merged_final:
                        Gp[name] = Gp.get(name, set()) | set([dfa_merged_final])

        return partitions, V, (_states, symbols, Tp), Sp, Fp, Gp

    @staticmethod
    def _alpha(Q, V, T, S, F, G):
        """rename/convert states for better legibility.

        Perform an alpha rename on all DFA states to simplify the
        representation which the end user will consume.

        Args:
          Q (set[set[frozenset[frozenset[str]]]]): the set of states
          V (set[str]): the input alphabet chacters
          T (tuple[
                   dict[set[frozenset[frozenset[str]]], int],
                   dict[str,  int],
                   list[list[set[frozenset[frozenset[str]]]]]
                  ]): the delta function as a table
          S (set[frozenset[frozenset[str]]]): the start state
          F (set[set[frozenset[frozenset[str]]]]): the set of final states
          G (dict[str, set[set[frozenset[frozenset[str]]]]]): the type to state
              mapping.

        Return:
          set[str]: the renamed start states
          set[str]: the input alphabet
          tuple[dict[str, int], dict[str, int], list[list[str]]]: the updated
              transition function
          str: the updated start state
          set[str]: the updated finish state(s)
          dict[str, set[str]]: the updated token to final state mapping.
        """
        rename = {q: RegularGrammar._state() for q in Q}
        Qp = set(rename.values())
        (states, symbols, table) = T
        states = {rename[state]:idx for state, idx in states.items()}
        Tp = (states, symbols, [[rename[col] for col in row] for row in table])
        Sp = rename[S]
        Fp = {rename[f] for f in F}
        Gp = {g:set([rename[s] for s in states]) for g, states in G.items()}
        return Qp, V, Tp, Sp, Fp, Gp
