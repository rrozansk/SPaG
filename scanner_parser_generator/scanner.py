"""
 scanner.py includes the implementation and testing of RegularGrammar objects.

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
    - supported escape sequences:
        operator literals   -> \?, \*, \., \+, \|
        grouping literals   -> \(, \), \[, \]
        whitespace literals -> \s, \t, \n, \r, \f, \v
        escape literal      -> \\\\

 Testing is implemented in a table driven fashion using the black box method.
 The tests may be run at the command line with the following invocation:

   $ python scanner.py

 If all tests passed no output will be produced. In the event of a failure a
 ValueError is thrown with the appropriate error/failure message. Both positive
 and negative tests cases are extensively tested.
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
        unsuccessful a value error will be thrown, otherwise the results can be
        queried through the API provided below.

        Input Types:
          name:        String
          expressions: List[Tuple[String, String]]

        Output Type: None | raise ValueError
        """
        if not isinstance(name, str):
            raise ValueError('Invalid Input: name must be a string')

        self._name = name

        if not isinstance(expressions, list):
            raise ValueError('Invalid Input: expressions must be a list')

        nfa = []
        self._exprs = []
        for element in expressions:
            if not isinstance(element, tuple):
                raise ValueError('Invalid Input: items in expressions must be tuples')

            name, pattern = element

            if not isinstance(name, str):
                raise ValueError('Invalid Input: name must be a string')

            if not isinstance(pattern, str):
                raise ValueError('Invalid Input: pattern must be a string')

            self._exprs.append((name, pattern))

            pattern = RegularGrammar._scan(pattern)
            pattern = RegularGrammar._expand_char_class_range(pattern)
            pattern = RegularGrammar._expand_concat(pattern)
            pattern = RegularGrammar._shunt(pattern)

            nfa.append((RegularGrammar._nfa(name, pattern)))

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
        return deepcopy(self._exprs)

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

# disable pylint spacing error to enable 'pretty/readable' transition tables.
# pylint: disable=bad-whitespace, line-too-long, anomalous-backslash-in-string
if __name__ == '__main__':

    TESTS = [
        {
            'name': 'Single Alpha',
            'valid': True,
            'expressions': [
                ('alpha', 'a')
            ],
            'DFA': {
                'Q': set(['S', 'A', 'Err']),
                'V': set('a'),
                'T': [
                    [' ', 'S', 'A',   'Err'],
                    ['a', 'A', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['A']),
                'G': {
                    'alpha': set(['A']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Explicit Concatenation',
            'valid': True,
            'expressions': [
                ('concat', 'a.b')
            ],
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S',   'A',   'B',   'Err'],
                    ['a', 'A',   'Err', 'Err', 'Err'],
                    ['b', 'Err', 'B',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['B']),
                'G': {
                    'concat': set(['B']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Alternation',
            'valid': True,
            'expressions': [
                ('alt', 'a|b')
            ],
            'DFA': {
                'Q': set(['S', 'AB', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S',  'AB',  'Err'],
                    ['a', 'AB', 'Err', 'Err'],
                    ['b', 'AB', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['AB']),
                'G': {
                    'alt': set(['AB']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Kleene Star',
            'valid': True,
            'expressions': [
                ('star', 'a*')
            ],
            'DFA': {
                'Q': set(['A']),
                'V': set('a'),
                'T': [
                    [' ', 'A'],
                    ['a', 'A']
                ],
                'S': 'A',
                'F': set(['A']),
                'G': {
                    'star': set(['A'])
                }
            }
        },
        {
            'name': 'Kleene Plus',
            'valid': True,
            'expressions': [
                ('plus', 'a+')
            ],
            'DFA': {
                'Q': set(['S', 'A']),
                'V': set('a'),
                'T': [
                    [' ', 'S', 'A'],
                    ['a', 'A', 'A']
                ],
                'S': 'S',
                'F': set(['A']),
                'G': {
                    'plus': set(['A'])
                }
            }
        },
        {
            'name': 'Choice',
            'valid': True,
            'expressions': [
                ('maybe', 'a?')
            ],
            'DFA': {
                'Q': set(['S', 'A', 'Err']),
                'V': set('a'),
                'T': [
                    [' ', 'S', 'A',   'Err'],
                    ['a', 'A', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['S', 'A']),
                'G': {
                    'maybe': set(['S', 'A']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Grouping',
            'valid': True,
            'expressions': [
                ('group', '(a|b)*')
            ],
            'DFA': {
                'Q': set(['AB*']),
                'V': set('ab'),
                'T': [
                    [' ', 'AB*'],
                    ['a', 'AB*'],
                    ['b', 'AB*']
                ],
                'S': 'AB*',
                'F': set(['AB*']),
                'G': {
                    'group': set(['AB*'])
                }
            }
        },
        {
            'name': 'Association',
            'valid': True,
            'expressions': [
                ('assoc', 'a|b*')
            ],
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S', 'A',   'B',   'Err'],
                    ['a', 'A', 'Err', 'Err', 'Err'],
                    ['b', 'B', 'Err', 'B',   'Err']
                ],
                'S': 'S',
                'F': set(['S', 'A', 'B']),
                'G': {
                    'assoc': set(['S', 'A', 'B']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Operator Alpha Literals',
            'valid': True,
            'expressions': [
                ('concat', '\.'),
                ('alt', '\|'),
                ('star', '\*'),
                ('question', '\?'),
                ('plus', '\+'),
                ('slash', '\\\\'),
                ('lparen', '\('),
                ('rparen', '\)'),
                ('lbracket', '\['),
                ('rbracket', '\]')
            ],
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('.|*?+\\()[]'),
                'T': [
                    [' ',  'S', 'F',   'Err'],
                    ['.',  'F', 'Err', 'Err'],
                    ['|',  'F', 'Err', 'Err'],
                    ['*',  'F', 'Err', 'Err'],
                    ['?',  'F', 'Err', 'Err'],
                    ['+',  'F', 'Err', 'Err'],
                    ['\\', 'F', 'Err', 'Err'],
                    ['(',  'F', 'Err', 'Err'],
                    [')',  'F', 'Err', 'Err'],
                    ['[',  'F', 'Err', 'Err'],
                    [']',  'F', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F']),
                'G': {
                    'concat': set(['F']),
                    'alt': set(['F']),
                    'star': set(['F']),
                    'question': set(['F']),
                    'plus': set(['F']),
                    'slash': set(['F']),
                    'lparen': set(['F']),
                    'rparen': set(['F']),
                    'lbracket': set(['F']),
                    'rbracket': set(['F']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Implicit Concatenation Characters',
            'valid': True,
            'expressions': [
                ('permutation1', 'ab'),
                ('permutation2', 'a(b)'),
                ('permutation3', '(a)b'),
                ('permutation4', '(a)(b)')
            ],
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S',   'A',   'B',   'Err'],
                    ['a', 'A',   'Err', 'Err', 'Err'],
                    ['b', 'Err', 'B',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['B']),
                'G': {
                    'permutation1': set(['B']),
                    'permutation2': set(['B']),
                    'permutation3': set(['B']),
                    'permutation4': set(['B']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Implicit Concatenation Star Operator',
            'valid': True,
            'expressions': [
                ('permutation1', 'a*b'),
                ('permutation2', 'a*(b)'),
                ('permutation3', '(a)*b'),
                ('permutation4', '(a)*(b)')
            ],
            'DFA': {
                'Q': set(['A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'A', 'B',   'Err'],
                    ['a', 'A', 'Err', 'Err'],
                    ['b', 'B', 'Err', 'Err']
                ],
                'S': 'A',
                'F': set(['B']),
                'G': {
                    'permutation1': set(['B']),
                    'permutation2': set(['B']),
                    'permutation3': set(['B']),
                    'permutation4': set(['B']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Implicit Concatenation Plus Operator',
            'valid': True,
            'expressions': [
                ('permutation1', 'a+b'),
                ('permutation2', 'a+(b)'),
                ('permutation3', '(a)+b'),
                ('permutation4', '(a)+(b)')
            ],
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S',   'A', 'B',   'Err'],
                    ['a', 'A',   'A', 'Err', 'Err'],
                    ['b', 'Err', 'B', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['B']),
                'G': {
                    'permutation1': set(['B']),
                    'permutation2': set(['B']),
                    'permutation3': set(['B']),
                    'permutation4': set(['B']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Implicit Concatenation Question Operator',
            'valid': True,
            'expressions': [
                ('permutation1', 'a?b'),
                ('permutation2', 'a?(b)'),
                ('permutation3', '(a)?b'),
                ('permutation4', '(a)?(b)')
            ],
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S', 'A',   'B',   'Err'],
                    ['a', 'A', 'Err', 'Err', 'Err'],
                    ['b', 'B', 'B',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['B']),
                'G': {
                    'permutation1': set(['B']),
                    'permutation2': set(['B']),
                    'permutation3': set(['B']),
                    'permutation4': set(['B']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Implicit Concatenation 10 - Mixed',
            'valid': True,
            'expressions': [
                ('concat', 'a.bc.de')
            ],
            'DFA': {
                'Q': set(['S', 'A', 'B', 'C', 'D', 'E', 'Err']),
                'V': set('abcde'),
                'T': [
                    [' ', 'S',   'A',   'B',   'C',   'D',   'E',   'Err'],
                    ['a', 'A',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['b', 'Err', 'B',   'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['c', 'Err', 'Err', 'C',   'Err', 'Err', 'Err', 'Err'],
                    ['d', 'Err', 'Err', 'Err', 'D',   'Err', 'Err', 'Err'],
                    ['e', 'Err', 'Err', 'Err', 'Err', 'E',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['E']),
                'G': {
                    'concat': set(['E']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Randomness 1',
            'valid': True,
            'expressions': [
                ('random', 'a*(b|cd)*')
            ],
            'DFA': {
                'Q': set(['AC', 'B', 'DE', 'Err']),
                'V': set('abcd'),
                'T': [
                    [' ', 'AC',  'B',   'DE',  'Err'],
                    ['a', 'AC',  'Err', 'Err', 'Err'],
                    ['b', 'DE',  'Err', 'DE',  'Err'],
                    ['c', 'B',   'Err', 'B',   'Err'],
                    ['d', 'Err', 'DE',  'Err', 'Err']
                ],
                'S': 'AC',
                'F': set(['AC', 'DE']),
                'G': {
                    'random': set(['AC', 'DE']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Randomness 2',
            'valid': True,
            'expressions': [
                ('random', 'a?b*')
            ],
            'DFA': {
                'Q': set(['A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'A',  'B',   'Err'],
                    ['a', 'B',  'Err', 'Err'],
                    ['b', 'B',  'B',   'Err']
                ],
                'S': 'A',
                'F': set(['A', 'B']),
                'G': {
                    'random': set(['A', 'B']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Randomness 3',
            'valid': True,
            'expressions': [
                ('random', '(a*b)|(a.bcd.e)')
            ],
            'DFA': {
                'Q': set(['S', 'A', 'A*', 'B', 'C', 'D', 'F', 'Err']),
                'V': set('abcde'),
                'T': [
                    [' ', 'S',   'A',   'A*',  'B',   'C',   'D',   'F',   'Err'],
                    ['a', 'A',   'A*',  'A*',  'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['b', 'F',   'B',   'F',   'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['c', 'Err', 'Err', 'Err', 'C',   'Err', 'Err', 'Err', 'Err'],
                    ['d', 'Err', 'Err', 'Err', 'Err', 'D',   'Err', 'Err', 'Err'],
                    ['e', 'Err', 'Err', 'Err', 'Err', 'Err', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F', 'B']),
                'G': {
                    'random': set(['F', 'B']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Randomness 4',
            'valid': True,
            'expressions': [
                ('random', '(foo)?(bar)+')
            ],
            'DFA': {
                'Q': set(['S', 'F', 'FO', 'FOO', 'B', 'BA', 'BAR', 'Err']),
                'V': set('fobar'),
                'T': [
                    [' ', 'S',   'F',   'FO',  'FOO', 'B',   'BA',  'BAR', 'Err'],
                    ['f', 'F',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['o', 'Err', 'FO',  'FOO', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['b', 'B',   'Err', 'Err', 'B',   'Err', 'Err', 'B',   'Err'],
                    ['a', 'Err', 'Err', 'Err', 'Err', 'BA',  'Err', 'Err', 'Err'],
                    ['r', 'Err', 'Err', 'Err', 'Err', 'Err', 'BAR', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['BAR']),
                'G': {
                    'random': set(['BAR']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Forward Character Range',
            'valid': True,
            'expressions': [
                ('range', '[a-c]')
            ],
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('abc'),
                'T': [
                    [' ', 'S',   'F',   'Err'],
                    ['a', 'F',   'Err', 'Err'],
                    ['b', 'F',   'Err', 'Err'],
                    ['c', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F']),
                'G': {
                    'range': set(['F']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Backward Character Range',
            'valid': True,
            'expressions': [
                ('range', '[c-a]')
            ],
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('abc'),
                'T': [
                    [' ', 'S',   'F',   'Err'],
                    ['a', 'F',   'Err', 'Err'],
                    ['b', 'F',   'Err', 'Err'],
                    ['c', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F']),
                'G': {
                    'range': set(['F']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Literal Negation Character Range',
            'valid': True,
            'expressions': [
                ('range', '[a-^]')
            ],
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('^_`a'),
                'T': [
                    [' ', 'S',   'F',   'Err'],
                    ['^', 'F',   'Err', 'Err'],
                    ['_', 'F',   'Err', 'Err'],
                    ['`', 'F',   'Err', 'Err'],
                    ['a', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F']),
                'G': {
                    'range': set(['F']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Negated Character Range',
            'valid': True,
            'expressions': [
                ('range', '[^!-~]*')
            ],
            'DFA': {
                'Q': set(['S']),
                'V': set(' \t\n\r\f\v'),
                'T': [
                    [' ',  'S'],
                    [' ',  'S'],
                    ['\t', 'S'],
                    ['\n', 'S'],
                    ['\r', 'S'],
                    ['\f', 'S'],
                    ['\v', 'S']
                ],
                'S': 'S',
                'F': set(['S']),
                'G': {
                    'range': set(['S'])
                }
            }
        },
        {
            'name': 'Character Class',
            'valid': True,
            'expressions': [
                ('class', '[abc]')
            ],
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('abc'),
                'T': [
                    [' ', 'S',   'F',   'Err'],
                    ['a', 'F',   'Err', 'Err'],
                    ['b', 'F',   'Err', 'Err'],
                    ['c', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F']),
                'G': {
                    'class': set(['F']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Character Class with Copies',
            'valid': True,
            'expressions': [
                ('class', '[aaa]')
            ],
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('a'),
                'T': [
                    [' ', 'S',   'F',   'Err'],
                    ['a', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F']),
                'G': {
                    'class': set(['F']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Character Class with Literal Right Bracket',
            'valid': True,
            'expressions': [
                ('class', '[\]]*')
            ],
            'DFA': {
                'Q': set(['S']),
                'V': set(']'),
                'T': [
                    [' ', 'S'],
                    [']', 'S']
                ],
                'S': 'S',
                'F': set(['S']),
                'G': {
                    'class': set(['S'])
                }
            }
        },
        {
            'name': 'Negated Character Class',
            'valid': True,
            'expressions': [
                ('class', '[^^!"#$%&\'()*+,./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\\]_`abcdefghijklmnopqrstuvwxyz{|}~-]*')
            ],
            'DFA': {
                'Q': set(['S']),
                'V': set(' \t\n\r\f\v'),
                'T': [
                    [' ',  'S'],
                    [' ',  'S'],
                    ['\t', 'S'],
                    ['\n', 'S'],
                    ['\r', 'S'],
                    ['\f', 'S'],
                    ['\v', 'S']
                ],
                'S': 'S',
                'F': set(['S']),
                'G': {
                    'class': set(['S'])
                }
            }
        },
        {
            'name': 'Character Class Range Combo',
            'valid': True,
            'expressions': [
                ('class', '[abc-e]*')
            ],
            'DFA': {
                'Q': set(['S']),
                'V': set('abcde'),
                'T': [
                    [' ', 'S'],
                    ['a', 'S'],
                    ['b', 'S'],
                    ['c', 'S'],
                    ['d', 'S'],
                    ['e', 'S']
                ],
                'S': 'S',
                'F': set(['S']),
                'G': {
                    'class': set(['S'])
                }
            }
        },
        {
            'name': 'Character Range Class Combo',
            'valid': True,
            'expressions': [
                ('class', '[a-cde]*')
            ],
            'DFA': {
                'Q': set(['S']),
                'V': set('abcde'),
                'T': [
                    [' ', 'S'],
                    ['a', 'S'],
                    ['b', 'S'],
                    ['c', 'S'],
                    ['d', 'S'],
                    ['e', 'S']
                ],
                'S': 'S',
                'F': set(['S']),
                'G': {
                    'class': set(['S'])
                }
            }
        },
        {
            'name': 'Integer',
            'valid': True,
            'expressions': [
                ('int', "0|([-+]?[1-9][0-9]*)")
            ],
            'DFA': {
                'Q': set(['S', 'Zero', 'Sign', 'Int', 'Err']),
                'V': set('+-0123456789'),
                'T': [
                    [' ', 'S',    'Zero', 'Sign', 'Int', 'Err'],
                    ['+', 'Sign', 'Err',  'Err',  'Err', 'Err'],
                    ['-', 'Sign', 'Err',  'Err',  'Err', 'Err'],
                    ['0', 'Zero', 'Err',  'Err',  'Int', 'Err'],
                    ['1', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['2', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['3', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['4', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['5', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['6', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['7', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['8', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['9', 'Int',  'Err',  'Int',  'Int', 'Err']
                ],
                'S': 'S',
                'F': set(['Zero', 'Int']),
                'G': {
                    'int': set(['Zero', 'Int']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Float',
            'valid': True,
            'expressions': [
                ('float', '[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?')
            ],
            'DFA': {
                'Q': set(['S', 'WholePart', 'ExpPart', 'FractionPart', 'eSignum', 'Sigfrac', 'Sigexp', 'Signum', 'Err']),
                'V': set('+-.0123456789eE'),
                'T': [
                    [' ', 'S',         'WholePart', 'ExpPart', 'FractionPart', 'eSignum', 'Sigfrac',      'Sigexp',  'Signum',    'Err'],
                    ['+', 'Signum',    'Err',       'Err',     'Err',          'Err',     'Err',          'eSignum', 'Err',       'Err'],
                    ['-', 'Signum',    'Err',       'Err',     'Err',          'Err',     'Err',          'eSignum', 'Err',       'Err'],
                    ['.', 'Sigfrac',   'Sigfrac',   'Err',     'Err',          'Err',     'Err',          'Err',     'Sigfrac',   'Err'],
                    ['0', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['1', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['2', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['3', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['4', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['5', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['6', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['7', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['8', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['9', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['E', 'Err',       'Sigexp',    'Err',     'Sigexp',       'Err',     'Err',          'Err',     'Err',       'Err'],
                    ['e', 'Err',       'Sigexp',    'Err',     'Sigexp',       'Err',     'Err',          'Err',     'Err',       'Err']
                ],
                'S': 'S',
                'F': set(['WholePart', 'ExpPart', 'FractionPart']),
                'G': {
                    'float': set(['WholePart', 'ExpPart', 'FractionPart']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'White Space',
            'valid': True,
            'expressions': [
                ('white', '( |\t|\n|\r|\f|\v)*')
            ],
            'DFA': {
                'Q': set(['S']),
                'V': set(' \t\n\r\f\v'),
                'T': [
                    [' ',  'S'],
                    [' ',  'S'],
                    ['\t', 'S'],
                    ['\n', 'S'],
                    ['\r', 'S'],
                    ['\f', 'S'],
                    ['\v', 'S']
                ],
                'S': 'S',
                'F': set(['S']),
                'G': {
                    'white': set(['S'])
                }
            }
        },
        {
            'name': 'Boolean',
            'valid': True,
            'expressions': [
                ('bool', '(true)|(false)')
            ],
            'DFA': {
                'Q': set(['S', 'T', 'R', 'F', 'A', 'L', 'US', 'E', 'Err']),
                'V': set('truefals'),
                'T': [
                    [' ', 'S',   'T',   'R',   'F',   'A',   'L',   'US',  'E',   'Err'],
                    ['t', 'T',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['r', 'Err', 'R',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['u', 'Err', 'Err', 'US',  'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['e', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'E',   'Err', 'Err'],
                    ['f', 'F',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['a', 'Err', 'Err', 'Err', 'A',   'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['l', 'Err', 'Err', 'Err', 'Err', 'L',   'Err', 'Err', 'Err', 'Err'],
                    ['s', 'Err', 'Err', 'Err', 'Err', 'Err', 'US',  'Err', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['E']),
                'G': {
                    'bool': set(['E']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Line Comment',
            'valid': True,
            'expressions': [
                ('comment', '(#|;)[^\n]*\n')
            ],
            'DFA': {
                'Q': set(['S', '_', 'F', 'Err']),
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
                'T': [
                    [' ',  'S',   '_', 'F',   'Err'],
                    ['#',  '_',   '_', 'Err', 'Err'],
                    [';',  '_',   '_', 'Err', 'Err'],
                    ['\n', 'Err', 'F', 'Err', 'Err'],
                    ['0',  'Err', '_', 'Err', 'Err'],
                    ['1',  'Err', '_', 'Err', 'Err'],
                    ['2',  'Err', '_', 'Err', 'Err'],
                    ['3',  'Err', '_', 'Err', 'Err'],
                    ['4',  'Err', '_', 'Err', 'Err'],
                    ['5',  'Err', '_', 'Err', 'Err'],
                    ['6',  'Err', '_', 'Err', 'Err'],
                    ['7',  'Err', '_', 'Err', 'Err'],
                    ['8',  'Err', '_', 'Err', 'Err'],
                    ['9',  'Err', '_', 'Err', 'Err'],
                    [' ',  'Err', '_', 'Err', 'Err'],
                    ['\t', 'Err', '_', 'Err', 'Err'],
                    ['\v', 'Err', '_', 'Err', 'Err'],
                    ['\f', 'Err', '_', 'Err', 'Err'],
                    ['\r', 'Err', '_', 'Err', 'Err'],
                    ['a',  'Err', '_', 'Err', 'Err'],
                    ['b',  'Err', '_', 'Err', 'Err'],
                    ['c',  'Err', '_', 'Err', 'Err'],
                    ['d',  'Err', '_', 'Err', 'Err'],
                    ['e',  'Err', '_', 'Err', 'Err'],
                    ['f',  'Err', '_', 'Err', 'Err'],
                    ['g',  'Err', '_', 'Err', 'Err'],
                    ['h',  'Err', '_', 'Err', 'Err'],
                    ['i',  'Err', '_', 'Err', 'Err'],
                    ['j',  'Err', '_', 'Err', 'Err'],
                    ['k',  'Err', '_', 'Err', 'Err'],
                    ['l',  'Err', '_', 'Err', 'Err'],
                    ['m',  'Err', '_', 'Err', 'Err'],
                    ['n',  'Err', '_', 'Err', 'Err'],
                    ['o',  'Err', '_', 'Err', 'Err'],
                    ['p',  'Err', '_', 'Err', 'Err'],
                    ['q',  'Err', '_', 'Err', 'Err'],
                    ['r',  'Err', '_', 'Err', 'Err'],
                    ['s',  'Err', '_', 'Err', 'Err'],
                    ['t',  'Err', '_', 'Err', 'Err'],
                    ['u',  'Err', '_', 'Err', 'Err'],
                    ['v',  'Err', '_', 'Err', 'Err'],
                    ['w',  'Err', '_', 'Err', 'Err'],
                    ['x',  'Err', '_', 'Err', 'Err'],
                    ['y',  'Err', '_', 'Err', 'Err'],
                    ['z',  'Err', '_', 'Err', 'Err'],
                    ['A',  'Err', '_', 'Err', 'Err'],
                    ['B',  'Err', '_', 'Err', 'Err'],
                    ['C',  'Err', '_', 'Err', 'Err'],
                    ['D',  'Err', '_', 'Err', 'Err'],
                    ['E',  'Err', '_', 'Err', 'Err'],
                    ['F',  'Err', '_', 'Err', 'Err'],
                    ['G',  'Err', '_', 'Err', 'Err'],
                    ['H',  'Err', '_', 'Err', 'Err'],
                    ['I',  'Err', '_', 'Err', 'Err'],
                    ['J',  'Err', '_', 'Err', 'Err'],
                    ['K',  'Err', '_', 'Err', 'Err'],
                    ['L',  'Err', '_', 'Err', 'Err'],
                    ['M',  'Err', '_', 'Err', 'Err'],
                    ['N',  'Err', '_', 'Err', 'Err'],
                    ['O',  'Err', '_', 'Err', 'Err'],
                    ['P',  'Err', '_', 'Err', 'Err'],
                    ['Q',  'Err', '_', 'Err', 'Err'],
                    ['R',  'Err', '_', 'Err', 'Err'],
                    ['S',  'Err', '_', 'Err', 'Err'],
                    ['T',  'Err', '_', 'Err', 'Err'],
                    ['U',  'Err', '_', 'Err', 'Err'],
                    ['V',  'Err', '_', 'Err', 'Err'],
                    ['W',  'Err', '_', 'Err', 'Err'],
                    ['X',  'Err', '_', 'Err', 'Err'],
                    ['Y',  'Err', '_', 'Err', 'Err'],
                    ['Z',  'Err', '_', 'Err', 'Err'],
                    ['!',  'Err', '_', 'Err', 'Err'],
                    ['"',  'Err', '_', 'Err', 'Err'],
                    ['$',  'Err', '_', 'Err', 'Err'],
                    ['%',  'Err', '_', 'Err', 'Err'],
                    ['&',  'Err', '_', 'Err', 'Err'],
                    ['\'', 'Err', '_', 'Err', 'Err'],
                    ['(',  'Err', '_', 'Err', 'Err'],
                    [')',  'Err', '_', 'Err', 'Err'],
                    ['*',  'Err', '_', 'Err', 'Err'],
                    ['+',  'Err', '_', 'Err', 'Err'],
                    [',',  'Err', '_', 'Err', 'Err'],
                    ['-',  'Err', '_', 'Err', 'Err'],
                    ['.',  'Err', '_', 'Err', 'Err'],
                    ['/',  'Err', '_', 'Err', 'Err'],
                    [':',  'Err', '_', 'Err', 'Err'],
                    ['<',  'Err', '_', 'Err', 'Err'],
                    ['=',  'Err', '_', 'Err', 'Err'],
                    ['>',  'Err', '_', 'Err', 'Err'],
                    ['?',  'Err', '_', 'Err', 'Err'],
                    ['@',  'Err', '_', 'Err', 'Err'],
                    ['[',  'Err', '_', 'Err', 'Err'],
                    ['\\', 'Err', '_', 'Err', 'Err'],
                    [']',  'Err', '_', 'Err', 'Err'],
                    ['^',  'Err', '_', 'Err', 'Err'],
                    ['_',  'Err', '_', 'Err', 'Err'],
                    ['`',  'Err', '_', 'Err', 'Err'],
                    ['{',  'Err', '_', 'Err', 'Err'],
                    ['|',  'Err', '_', 'Err', 'Err'],
                    ['}',  'Err', '_', 'Err', 'Err'],
                    ['~',  'Err', '_', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F']),
                'G': {
                    'comment': set(['F']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Block Comment',
            'valid': True,
            'expressions': [
                ('comment', '/[*][^]*[*]/')
            ],
            'DFA': {
                'Q': set(['BEGIN', 'SINK', 'FSLASH', 'SIGEND', 'END', 'ERR']),
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
                'T': [
                    [' ',  'BEGIN',  'SINK',   'FSLASH', 'SIGEND', 'END',    'ERR'],
                    ['/',  'FSLASH', 'SINK',   'ERR',    'END',    'SINK',   'ERR'],
                    ['*',  'ERR',    'SIGEND', 'SINK',   'SIGEND', 'SIGEND', 'ERR'],
                    ['#',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [';',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\n', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['0',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['1',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['2',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['3',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['4',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['5',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['6',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['7',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['8',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['9',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [' ',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\t', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\v', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\f', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\r', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['a',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['b',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['c',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['d',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['e',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['f',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['g',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['h',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['i',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['j',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['k',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['l',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['m',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['n',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['o',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['p',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['q',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['r',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['s',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['t',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['u',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['v',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['w',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['x',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['y',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['z',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['A',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['B',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['C',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['D',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['E',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['F',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['G',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['H',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['I',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['J',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['K',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['L',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['M',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['N',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['O',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['P',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['Q',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['R',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['S',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['T',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['U',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['V',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['W',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['X',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['Y',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['Z',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['!',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['"',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['$',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['%',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['&',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\'', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['(',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [')',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['+',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [',',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['-',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['.',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [':',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['<',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['=',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['>',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['?',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['@',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['[',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\\', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [']',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['^',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['_',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['`',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['{',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['|',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['}',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['~',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR']
                ],
                'S': 'BEGIN',
                'F': set(['END']),
                'G': {
                    'comment': set(['END']),
                    '_sink': set(['ERR'])
                }
            }
        },
        {
            'name': 'Character',
            'valid': True,
            'expressions': [
                ('char', "'[^]'")
            ],
            'DFA': {
                'Q': set(['S', '_1', '_2', 'F', 'Err']),
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
                'T': [
                    [' ',  'S',   '_1', '_2',  'F',   'Err'],
                    ['#',  'Err', '_2', 'Err', 'Err', 'Err'],
                    [';',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\n', 'Err', '_2', 'Err', 'Err', 'Err'],
                    ['0',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['1',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['2',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['3',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['4',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['5',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['6',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['7',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['8',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['9',  'Err', '_2', 'Err', 'Err', 'Err'],
                    [' ',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\t', 'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\v', 'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\f', 'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\r', 'Err', '_2', 'Err', 'Err', 'Err'],
                    ['a',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['b',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['c',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['d',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['e',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['f',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['g',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['h',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['i',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['j',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['k',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['l',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['m',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['n',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['o',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['p',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['q',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['r',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['s',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['t',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['u',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['v',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['w',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['x',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['y',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['z',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['A',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['B',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['C',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['D',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['E',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['F',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['G',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['H',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['I',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['J',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['K',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['L',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['M',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['N',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['O',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['P',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['Q',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['R',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['S',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['T',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['U',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['V',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['W',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['X',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['Y',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['Z',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['!',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['"',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['$',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['%',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['&',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\'', '_1',  '_2', 'F',   'Err', 'Err'],
                    ['(',  'Err', '_2', 'Err', 'Err', 'Err'],
                    [')',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['*',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['+',  'Err', '_2', 'Err', 'Err', 'Err'],
                    [',',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['-',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['.',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['/',  'Err', '_2', 'Err', 'Err', 'Err'],
                    [':',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['<',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['=',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['>',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['?',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['@',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['[',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\\', 'Err', '_2', 'Err', 'Err', 'Err'],
                    [']',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['^',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['_',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['`',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['{',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['|',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['}',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['~',  'Err', '_2', 'Err', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F']),
                'G': {
                    'char': set(['F']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'String',
            'valid': True,
            'expressions': [
                ('str', '"[^"]*"')
            ],
            'DFA': {
                'Q': set(['S', '_', 'F', 'Err']),
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
                'T': [
                    [' ',  'S',   '_', 'F',   'Err'],
                    ['#',  'Err', '_', 'Err', 'Err'],
                    [';',  'Err', '_', 'Err', 'Err'],
                    ['\n', 'Err', '_', 'Err', 'Err'],
                    ['0',  'Err', '_', 'Err', 'Err'],
                    ['1',  'Err', '_', 'Err', 'Err'],
                    ['2',  'Err', '_', 'Err', 'Err'],
                    ['3',  'Err', '_', 'Err', 'Err'],
                    ['4',  'Err', '_', 'Err', 'Err'],
                    ['5',  'Err', '_', 'Err', 'Err'],
                    ['6',  'Err', '_', 'Err', 'Err'],
                    ['7',  'Err', '_', 'Err', 'Err'],
                    ['8',  'Err', '_', 'Err', 'Err'],
                    ['9',  'Err', '_', 'Err', 'Err'],
                    [' ',  'Err', '_', 'Err', 'Err'],
                    ['\t', 'Err', '_', 'Err', 'Err'],
                    ['\v', 'Err', '_', 'Err', 'Err'],
                    ['\f', 'Err', '_', 'Err', 'Err'],
                    ['\r', 'Err', '_', 'Err', 'Err'],
                    ['a',  'Err', '_', 'Err', 'Err'],
                    ['b',  'Err', '_', 'Err', 'Err'],
                    ['c',  'Err', '_', 'Err', 'Err'],
                    ['d',  'Err', '_', 'Err', 'Err'],
                    ['e',  'Err', '_', 'Err', 'Err'],
                    ['f',  'Err', '_', 'Err', 'Err'],
                    ['g',  'Err', '_', 'Err', 'Err'],
                    ['h',  'Err', '_', 'Err', 'Err'],
                    ['i',  'Err', '_', 'Err', 'Err'],
                    ['j',  'Err', '_', 'Err', 'Err'],
                    ['k',  'Err', '_', 'Err', 'Err'],
                    ['l',  'Err', '_', 'Err', 'Err'],
                    ['m',  'Err', '_', 'Err', 'Err'],
                    ['n',  'Err', '_', 'Err', 'Err'],
                    ['o',  'Err', '_', 'Err', 'Err'],
                    ['p',  'Err', '_', 'Err', 'Err'],
                    ['q',  'Err', '_', 'Err', 'Err'],
                    ['r',  'Err', '_', 'Err', 'Err'],
                    ['s',  'Err', '_', 'Err', 'Err'],
                    ['t',  'Err', '_', 'Err', 'Err'],
                    ['u',  'Err', '_', 'Err', 'Err'],
                    ['v',  'Err', '_', 'Err', 'Err'],
                    ['w',  'Err', '_', 'Err', 'Err'],
                    ['x',  'Err', '_', 'Err', 'Err'],
                    ['y',  'Err', '_', 'Err', 'Err'],
                    ['z',  'Err', '_', 'Err', 'Err'],
                    ['A',  'Err', '_', 'Err', 'Err'],
                    ['B',  'Err', '_', 'Err', 'Err'],
                    ['C',  'Err', '_', 'Err', 'Err'],
                    ['D',  'Err', '_', 'Err', 'Err'],
                    ['E',  'Err', '_', 'Err', 'Err'],
                    ['F',  'Err', '_', 'Err', 'Err'],
                    ['G',  'Err', '_', 'Err', 'Err'],
                    ['H',  'Err', '_', 'Err', 'Err'],
                    ['I',  'Err', '_', 'Err', 'Err'],
                    ['J',  'Err', '_', 'Err', 'Err'],
                    ['K',  'Err', '_', 'Err', 'Err'],
                    ['L',  'Err', '_', 'Err', 'Err'],
                    ['M',  'Err', '_', 'Err', 'Err'],
                    ['N',  'Err', '_', 'Err', 'Err'],
                    ['O',  'Err', '_', 'Err', 'Err'],
                    ['P',  'Err', '_', 'Err', 'Err'],
                    ['Q',  'Err', '_', 'Err', 'Err'],
                    ['R',  'Err', '_', 'Err', 'Err'],
                    ['S',  'Err', '_', 'Err', 'Err'],
                    ['T',  'Err', '_', 'Err', 'Err'],
                    ['U',  'Err', '_', 'Err', 'Err'],
                    ['V',  'Err', '_', 'Err', 'Err'],
                    ['W',  'Err', '_', 'Err', 'Err'],
                    ['X',  'Err', '_', 'Err', 'Err'],
                    ['Y',  'Err', '_', 'Err', 'Err'],
                    ['Z',  'Err', '_', 'Err', 'Err'],
                    ['!',  'Err', '_', 'Err', 'Err'],
                    ['"',  '_',   'F', 'Err', 'Err'],
                    ['$',  'Err', '_', 'Err', 'Err'],
                    ['%',  'Err', '_', 'Err', 'Err'],
                    ['&',  'Err', '_', 'Err', 'Err'],
                    ['\'', 'Err', '_', 'Err', 'Err'],
                    ['(',  'Err', '_', 'Err', 'Err'],
                    [')',  'Err', '_', 'Err', 'Err'],
                    ['*',  'Err', '_', 'Err', 'Err'],
                    ['+',  'Err', '_', 'Err', 'Err'],
                    [',',  'Err', '_', 'Err', 'Err'],
                    ['-',  'Err', '_', 'Err', 'Err'],
                    ['.',  'Err', '_', 'Err', 'Err'],
                    ['/',  'Err', '_', 'Err', 'Err'],
                    [':',  'Err', '_', 'Err', 'Err'],
                    ['<',  'Err', '_', 'Err', 'Err'],
                    ['=',  'Err', '_', 'Err', 'Err'],
                    ['>',  'Err', '_', 'Err', 'Err'],
                    ['?',  'Err', '_', 'Err', 'Err'],
                    ['@',  'Err', '_', 'Err', 'Err'],
                    ['[',  'Err', '_', 'Err', 'Err'],
                    ['\\', 'Err', '_', 'Err', 'Err'],
                    [']',  'Err', '_', 'Err', 'Err'],
                    ['^',  'Err', '_', 'Err', 'Err'],
                    ['_',  'Err', '_', 'Err', 'Err'],
                    ['`',  'Err', '_', 'Err', 'Err'],
                    ['{',  'Err', '_', 'Err', 'Err'],
                    ['|',  'Err', '_', 'Err', 'Err'],
                    ['}',  'Err', '_', 'Err', 'Err'],
                    ['~',  'Err', '_', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F']),
                'G': {
                    'str': set(['F']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Identifiers',
            'valid': True,
            'expressions': [
                ('id', '[_a-zA-Z][_a-zA-Z0-9]*')
            ],
            'DFA': {
                'Q': set(['Char', 'DigitOrChar', 'Err']),
                'V': set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'),
                'T': [
                    [' ',  'Char',        'DigitOrChar', 'Err'],
                    ['a',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['b',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['c',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['d',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['e',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['f',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['g',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['h',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['i',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['j',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['k',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['l',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['m',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['n',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['o',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['p',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['q',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['r',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['s',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['t',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['u',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['v',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['w',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['x',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['y',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['z',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['A',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['B',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['C',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['D',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['E',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['F',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['G',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['H',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['I',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['J',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['K',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['L',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['M',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['N',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['O',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['P',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['Q',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['R',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['S',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['T',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['U',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['V',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['W',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['X',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['Y',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['Z',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['0',  'Err',         'DigitOrChar', 'Err'],
                    ['1',  'Err',         'DigitOrChar', 'Err'],
                    ['2',  'Err',         'DigitOrChar', 'Err'],
                    ['3',  'Err',         'DigitOrChar', 'Err'],
                    ['4',  'Err',         'DigitOrChar', 'Err'],
                    ['5',  'Err',         'DigitOrChar', 'Err'],
                    ['6',  'Err',         'DigitOrChar', 'Err'],
                    ['7',  'Err',         'DigitOrChar', 'Err'],
                    ['8',  'Err',         'DigitOrChar', 'Err'],
                    ['9',  'Err',         'DigitOrChar', 'Err'],
                    ['_',  'DigitOrChar', 'DigitOrChar', 'Err']
                ],
                'S': 'Char',
                'F': set(['DigitOrChar']),
                'G': {
                    'id': set(['DigitOrChar']),
                    '_sink': set(['Err'])
                }
            }
        },
        {
            'name': 'Unbalanced Left Paren',
            'valid': False,
            'expressions': [
                ('invalid', '(foo|bar')
            ],
            'DFA': {}
        },
        {
            'name': 'Unbalanced Right Paren',
            'valid': False,
            'expressions': [
                ('invalid', 'foo|bar)')
            ],
            'DFA': {}
        },
        {
            'name': 'Invalid Escape Sequence',
            'valid': False,
            'expressions': [
                ('invalid', '\j')
            ],
            'DFA': {}
        },
        {
            'name': 'Empty Escape Sequence',
            'valid': False,
            'expressions': [
                ('invalid', '\\')
            ],
            'DFA': {}
        },
        {
            'name': 'Empty Expression',
            'valid': False,
            'expressions': [
                ('invalid', '')
            ],
            'DFA': {}
        },
        {
            'name': 'Empty Character Range/Class',
            'valid': False,
            'expressions': [
                ('class/range', '[]')
            ],
            'DFA': {}
        },
        {
            'name': 'Invalid Character',
            'valid': False,
            'expressions': [
                ('invalid', '\x99')
            ],
            'DFA': {}
        },
        {
            'name': ['Invalid Scanner Name'],
            'valid': False,
            'expressions': [
                ('invalid', 'foo')
            ],
            'DFA': {}
        },
        {
            'name': 'Invalid Scanner Tokens',
            'valid': False,
            'expressions': ["invalid"],
            'DFA': {}
        },
        {
            'name': 'Invalid Scanner Token Key',
            'valid': False,
            'expressions': [
                (True, 'invalid')
            ],
            'DFA': {}
        },
        {
            'name': 'Invalid Scanner Token Value',
            'valid': False,
            'expressions': [
                ('invalid', True)
            ],
            'DFA': {}
        },
        {
            'name': 'Invalid Expression * Arity',
            'valid': False,
            'expressions': [
                ('invalid', '*')
            ],
            'DFA': {}
        },
        {
            'name': 'Invalid Expression + Arity',
            'valid': False,
            'expressions': [
                ('invalid', '+')
            ],
            'DFA': {}
        },
        {
            'name': 'Invalid Expression ? Arity',
            'valid': False,
            'expressions': [
                ('invalid', '?')
            ],
            'DFA': {}
        },
        {
            'name': 'Invalid Expression | Arity',
            'valid': False,
            'expressions': [
                ('invalid', 'a|')
            ],
            'DFA': {}
        },
        {
            'name': 'Invalid Expression . Arity',
            'valid': False,
            'expressions': [
                ('invalid', 'a.')
            ],
            'DFA': {}
        },
    ]

# re-enable pylint errors.
# pylint: enable=bad-whitespace, line-too-long, anomalous-backslash-in-string

    from itertools import permutations

    for test in TESTS:
        try:
            regular_grammar = RegularGrammar(test['name'], test['expressions'])
        except ValueError as regular_grammar_exception:
            if test['valid']:                   # test type (input output)
                raise regular_grammar_exception # Unexpected Failure (+-)
            continue                            # Expected Failure   (--)

        if not test['valid']:                   # Unexpected Pass    (-+)
            raise ValueError('Panic: Negative test passed without error')

        # Failure checking for:  Expected Pass      (++)

        if regular_grammar.name() != test['name']:
            raise ValueError('Error: Incorrect DFA name returned')

        expressions = regular_grammar.expressions()

        if len(expressions) != len(test['expressions']):
            raise ValueError('Error: Incorrect expression count in grammar')

        idx = 0
        expressions = sorted(expressions, key=lambda x: x[0])
        test['expressions'] = sorted(test['expressions'], key=lambda x: x[0])
        for name, pattern in test['expressions']:
            _name, _pattern = expressions[idx]
            idx += 1
            if _name != name or _pattern != pattern:
                raise ValueError('Error: Incorrect token name/pattern created')

        V = regular_grammar.alphabet()
        if V != test['DFA']['V']:
            raise ValueError('Error: Incorrect alphabet produced')

        Q = regular_grammar.states()
        if len(Q) != len(test['DFA']['Q']):
            raise ValueError('Error: Incorrect number of states produced')

        F = regular_grammar.accepting()
        if len(F) != len(test['DFA']['F']):
            raise ValueError('Error: Incorrect number of finish states')

        G = regular_grammar.types()
        if len(G) != len(test['DFA']['G']):
            raise ValueError('Error: Incorrect number of types')

        state, symbol, T = regular_grammar.transitions()
        if len(T) != len(test['DFA']['T'])-1 or \
           (T and len(T[0]) != len(test['DFA']['T'][0])-1):
            raise ValueError('Error: Incorrect number of transitions produced')

        # Check if DFA's are isomorphic by attempting to find a bijection
        # between them since they both already look very 'similar'.
        _Q = test['DFA']['Q']
        S = regular_grammar.start()

        _state, _symbol, _T = dict(), dict(), list()
        if T:
            _state = {s:idx for idx, s in enumerate(test['DFA']['T'].pop(0)[1:])}
            _symbol = {s:idx for idx, s in enumerate([row.pop(0) for row in test['DFA']['T']])}
            _T = test['DFA']['T']

        found = False
        for _map in (dict(zip(Q, perm)) for perm in permutations(_Q, len(_Q))):
            if _map[S] != test['DFA']['S']:
                continue
            if not all([_map[f] in test['DFA']['F'] for f in F]):
                continue
            if not all([{_map[s] for s in types} == \
               test['DFA']['G'].get(name, set()) for name, types in G.items()]):
                continue
            if not all([all([_map[T[symbol[v]][state[q]]] == \
               _T[_symbol[v]][_state[_map[q]]] for q in Q]) for v in V]):
                continue
            found = True
            break

        if not found:
            raise ValueError('Error: Non-isomorphic DFA produced')