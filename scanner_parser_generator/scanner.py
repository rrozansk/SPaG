# pylint: disable=anomalous-backslash-in-string
# pylint: disable=too-many-boolean-expressions
# pylint: disable=too-many-branches
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=unused-argument
"""
 scanner.py includes the implementation of RegularGrammar objects.

 The RegularGrammar object represents a group of formal regular expressions
 which can be programatically transformed into a minimal DFA.

 The entire transformation on the input can be visualized as:

   regular expression => epsilon NFA => DFA => minimal DFA

 The final DFA produced will have a complete delta (transition) function and
 will include an extra sink/error state to absorb all invalid input if needed.
 It will also include a dictionary mapping types (i.e. named pattern expression)
 to there corresponding final state(s) in the DFA.

 Regular expressions must be specified following these guidelines:
    - only printable ascii characters (33-126) and spaces are supported
    - supported operators:
        |                (union -> choice -> either or)
        ?                (question -> choice -> 1 or none)
        .                (concatenation -> combine)
        *                (kleene star -> repitition >= 0)
        +                (plus -> repitition >= 1)
        ()               (grouping -> disambiguation -> any expression)
        [ab]             (character class -> choice -> any specified char)
        [a-c] or [c-a]   (character range -> choice -> any char between the two)
        [^ab] or [^a-c]  (character negation -> choice -> all but the specified)
        NOTES: '^' is required to come first after the bracket for negation.
               If alone ([^]) it is translated as all alphabet characters.
               It is still legal for character ranges as well ([b-^] and
               negated as [^^-b]). Note that the reverse range was needed. If
               the first character is a '^' it will always mean negation! If a
               single '^' is wanted then there is no need to use a class/range.
               Classes and ranges can be combined between the same set of
               brackets ([abc-z]), even multiple times if wanted/needed. Due to
               this though the '-' char must come as the last character in the
               class if the literal is wanted. For literal right brackets an
               escape is needed if mentioned ([\]]). All other characters are
               treated as literals.
    - concat can be either implicit or explicit
    - supported escape sequences with a backslash (\):
        operator literals   -> ?, *, ., +, |
        grouping literals   -> (, ), [, ]
        whitespace literals -> s, t, n, r, f, v
        escape literal      -> \
"""
from uuid import uuid4
from string import printable
from copy import deepcopy


class RegularGrammar(object):
    """
    RegularGrammar represents a collection of formal regular expressions which
    can be programatically compiled into a minmal DFA.
    """

    # Map internal representation of operators -> literals
    _literals = dict(enumerate('*|.+?()[]'))

    # Map operator literals -> internal representation
    _operators = {v:k for k, v in _literals.items()}

    # Set of acceptable input characters (printable ascii) including:
    # uppercase, lowercase, digits, punctuation, whitespace
    _characters = set(printable)

    # Operator precedence for the shunting yard algorithm.
    # (higher binds tighter)
    _precedence = {
        _operators['(']: (3, None),
        _operators[')']: (3, None),
        _operators['*']: (2, False),  # right-associative
        _operators['+']: (2, False),  # right-associative
        _operators['?']: (2, False),  # right-associative
        _operators['.']: (1, True),   # left-associative
        _operators['|']: (0, True),   # left-associative
    }

    def __init__(self, name, expressions):
        """
        Attempt to initialize a RegularGrammar object with the specified name,
        recognizing the given expressions. Expr's have a type/name/descriptor
        and an associated pattern/regular expression. If creation is
        unsuccessful a TypeError or ValueError will be thrown, otherwise the
        results can be queried through the API provided below.

        Input Types:
          name:        String
          expressions: Dict[String, String]

        Output Type: None | raise ValueError | raise TypeError
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

    def name(self):
        """
        Query for the name of the grammar.

        Output Type: String
        """
        return deepcopy(self._name)

    def expressions(self):
        """
        Query for the patterns recognized by the grammar.

        Output Type: List[Tuple[String, String]]
        """
        return deepcopy(self._expressions)

    def states(self):
        """
        Query for states in the grammars equivalent minimal DFA.

        Output Type: Set[String]
        """
        return deepcopy(self._states)

    def alphabet(self):
        """
        Query for alphabet of characters recognized by the grammars DFA.

        Output Type: Set[String]
        """
        return deepcopy(self._alphas)

    def transitions(self):
        """
        Query for the state transitions defining the grammars DFA.

        Output Type: Tuple[
                           Dict[String, Int],
                           Dict[String, Int],
                           List[List[String]]
                          ]
        """
        return deepcopy(self._deltas)

    def start(self):
        """
        Query for the start state of the grammars DFA.

        Output Type: String
        """
        return deepcopy(self._start)

    def accepting(self):
        """
        Query for all accepting states of the grammars DFA.

        Output Type: Set[String]
        """
        return deepcopy(self._finals)

    def types(self):
        """
        Query for the dictionary which labels all named pattern expressions
        (types) with there corresponding associated final state(s).

        Output Type: Dict[String, Set[String]]
        """
        return deepcopy(self._types)

    @staticmethod
    def _scan(expr):
        """
        Convert an external representation of a token (regular expression) to
        an internal one. Ensures all characters and escape sequences are valid.

        Character conversions:
          meta -> internal representation (integer enum)
          escaped meta -> character
          escaped escape -> escape
          escaped whitespace -> whitespace

        Runtime: O(n) - linear to the length of expr.

        Input Type:
          expr: String

        Output Type: List[String, Int] | raise ValueError
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
        """
        Expand the internal representation of the expression so that
        character classes and ranges are eliminated.

        Runtime: O(n) - linear to the length of expr.

        Input Type:
          expr: List[String, Int]

        Output Type: List[String, Int] | raise ValueError
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
        """
        Expand the internal representation of the expression so that
        concatentation is explicit throughout.

        Runtime: O(n) - linear to the length of expr.

        Input Type:
          expr: List[String, Int]

        Output Type: List[String, Int]
        """
        output = []
        for elem in expr:
            if output and \
               output[-1] != RegularGrammar._operators['('] and \
               output[-1] != RegularGrammar._operators['|'] and \
               output[-1] != RegularGrammar._operators['.'] and \
               (elem == RegularGrammar._operators['('] or elem in RegularGrammar._characters):
                output.append(RegularGrammar._operators['.'])
            output.append(elem)
        return output

    @staticmethod
    def _shunt(expr):
        """
        Convert the input expression to be entirely in postfix notation (RPN;
        Reverse Polish Notation) allowing all parenthesis to be dropped.
        Adapted from Dijkstra's Shunting yard algorithm which can be viewed
        @https://en.wikipedia.org/wiki/Shunting-yard_algorithm.

        Runtime: O(n) - linear to the length of expr.

        Input Type:
          expr: List[String, Int]

        Output Type: List[String, Int] | raise ValueError
        """
        stack, queue = [], []  # operators, output expression

        for token in expr:
            if token in RegularGrammar._characters:
                queue.append(token)
            elif token == RegularGrammar._operators['(']:
                stack.append(RegularGrammar._operators['('])
            elif token == RegularGrammar._operators[')']:
                while stack and stack[-1] != RegularGrammar._operators['(']:
                    queue.append(stack.pop())
                if not stack:
                    raise ValueError('Error: unbalanced parenthesis')
                stack.pop()
            elif token in RegularGrammar._precedence:
                while stack and stack[-1] != RegularGrammar._operators['('] and\
                      RegularGrammar._precedence[token][0] <= \
                      RegularGrammar._precedence[stack[-1]][0]\
                      and RegularGrammar._precedence[token][1]:  # left-associative?
                    queue.append(stack.pop())
                stack.append(token)
            else:
                raise ValueError('Error: invalid input in shuting yard')

        while stack:
            token = stack.pop()
            if token == RegularGrammar._operators['('] or \
               token == RegularGrammar._operators[')']:
                raise ValueError('Error: unbalanced parenthesis')
            queue.append(token)

        return queue

    @staticmethod
    def _state():
        """
        Generate a new universally unique state name/label.

        Runtime: O(1) - constant.

        Output Type: String
        """
        return str(uuid4())

    @staticmethod
    def _nfa(name, expr):
        """
        Attempt to convert an internal representation of a regular expression
        in RPN to an epsilon NFA. Operators handled: union |, kleene star *,
        concatenation ., literals, and syntax extensions kleene plus + and
        choice ?. Adapted to a iterative stacked based evaluation algorithm
        (standard RPN evaluation algorithm) from thompson construction as
        described in section 4.1 in 'A taxonomy of finite automata construction
        algorithms' by Bruce Watson,
        located @http://alexandria.tue.nl/extra1/wskrap/publichtml/9313452.pdf

        Runtime: O(n) - linear to the length of expr.

        Input Type:
          name: String
          expr: List[String, Int]

        Output Types:
          Set[String]
          x Set[String]
          x Set[Tuple[String, String, String]]
          x Dict[String, Set[String]]
          x String
          x String
          x Dict[String, String]
        """
        Q = set()   # states
        V = set()   # input symbols (alphabet)
        T = set()   # transition relation: T in P(Q x V x Q)
        E = dict()  # e-transition relation: E in P(Q x Q)
        S = None    # start state S in Q
        F = None    # accepting state F in Q
        G = dict()  # map type to the final state(s)

        def e_update(start, final):
            """
            Small internal helper to update epsilon dictionary.
            """
            E[start] = E.get(start, set())
            E[start].add(final)

        stk = []  # NFA machine stk
        for token in expr:
            if token in RegularGrammar._characters:
                S, F = RegularGrammar._state(), RegularGrammar._state()
                V.add(token)
                T.add((S, token, F))
            elif token == RegularGrammar._operators['.']:
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
            else:
                raise ValueError('Error: invalid input in NFA construction')
            Q.update([S, F])
            stk.append((S, F))

        if len(stk) != 1:
            raise ValueError('Error: invalid expression')
        S, F = stk.pop()
        G[name] = F
        return Q, V, T, E, S, F, G

    @staticmethod
    def _merge_nfa(nfa):
        """
        Merge multiple NFAs with a new single start state containing epsilon
        transitions to each individual machine.

        Runtime: O(n) - linear in the number of NFA's.

        Input Type:
          NFAs: List[
                     Tuple[
                           Set[String],
                           Set[String],
                           Set[Tuple[String, String, String]],
                           Dict[String, Set[String]],
                           String,
                           String,
                           Dict[String, String]
                          ]
                    ]

        Output Type:
          Set[String]
          x Set[String]
          x Set[Tuple[String, String, String]]
          x Dict[String, Set[String]]
          x String
          x String
          x Dict[String, String]
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
        """
        Find the epsilon closure of state q and epsilon transitions E. A cache
        is utilized to speed things up for repeated invocations. Stated in set
        notation: { q' | q ->*e q' }, from a given start state q find all
        states q' which are reachable using only epsilon transitions, handling
        cycles appropriately.

        Runtime: O(n) - linear in the number of epsilon transitions.

        Input Types:
          q:     String
          E:     Dict[String, Set[String]]
          cache: Dict[String, Set[String]]

        Output Type: Set[String]
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
        """
        Convert the epsilon NFA to a DFA using subset construction and
        e-closure conversion. Only states wich are reachable from the start
        state are considered. This results in a minimized DFA with reguard to
        reachable states, but not with reguard to nondistinguishable states.

        Runtime: O(2^n) - exponential in the number of states.

        Input Types:
          Q: Set[String]
          V: Set[String]
          T: Set[Tuple[String, String, String]]
          E: Dict[String, Set[String]]
          S: String
          F: Set[String]
          G: Dict[String, String]

        Output Types:
          Set[Frozenset[String]]
          x Set[String]
          x Set[Tuple[Frozenset[String], String, Frozenset[String]]]
          x Frozenset[String]
          x Set[Frozenset[String]]
          x Dict[String, Set[Frozenset[String]]]
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
        """
        Make the DFA's delta function total, if not already, by adding a
        sink/error state. All unspecified state transitions are then specified
        by adding a transition to the new sink/error state. A new entry is also
        made into G to track this new sink/error type which is accessible as
        '_sink'.

        Runtime: O(n) - linear in the number of states and transitions.

        Input Types:
          Q: Set[Frozenset[String]]
          V: Set[String]
          T: Set[Tuple[Frozenset[String], String, Frozenset[String]]]
          S: Frozenset[String]
          F: Set[Frozenset[String]]
          G: Dict[String, Set[Frozenset[String]]]

        Output Types:
          Set[Frozenset[String]]
          x Set[String]
          x Tuple[
                  Dict[Frozenset[String], Int],
                  Dict[String, Int],
                  List[List[Frozenset[String]]]
                 ]
          x Frozenset[String]
          x Set[Frozenset[String]]
          x Dict[String, Set[Frozenset[String]]]
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
        """
        Minimize the DFA with reguard to indistinguishable states using
        hopcrafts algorithm, which merges states together based on partition
        refinement.

        Runtime: O(ns log n) - linear log (n=number states; s=alphabet size).

        Input Types:
          Q: Set[Frozenset[String]]
          V: Set[String]
          T: Tuple[
                   Dict[Frozenset[String], Int],
                   Dict[String, Int],
                   List[List[Frozenset[String]]]
                  ]
          S: Frozenset[String]
          F: Set[Frozenset[String]]
          G: Dict[String, Set[Frozenset[String]]]

        Output Types:
          Set[Set[Frozenset[Frozenset[String]]]]
          x Set[String]
          x Tuple[
                  Dict[Set[Frozenset[Frozenset[String]]], Int],
                  Dict[String, Int],
                  List[List[Set[Frozenset[Frozenset[String]]]]]
                 ]
          x Set[Frozenset[Frozenset[String]]]
          x Set[Set[Frozenset[Frozenset[String]]]]
          x Dict[String, Set[Set[Frozenset[Frozenset[String]]]]
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
        """
        Perform an alpha rename on all DFA states to simplify the
        representation which the end user will consume.

        Runtime: O(n) - linear in the number of states and transitions.

        Input Types:
          Q: Set[Set[Frozenset[Frozenset[String]]]]
          V: Set[String]
          T: Tuple[
                   Dict[Set[Frozenset[Frozenset[String]]], Int],
                   Dict[String,  Int],
                   List[List[Set[Frozenset[Frozenset[String]]]]]
                  ]
          S: Set[Frozenset[Frozenset[String]]]
          F: Set[Set[Frozenset[Frozenset[String]]]]
          G: Dict[String, Set[Set[Frozenset[Frozenset[String]]]]]

        Output Types:
          Set[String]
          x Set[String]
          x Tuple[Dict[String, Int], Dict[String, Int], List[List[String]]]
          x String
          x Set[String]
          x Dict[String, Set[String]]
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
