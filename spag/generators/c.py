"""C generator.

A scanner/parser generator targeting c. Generates header (.h) and source (.c)
files.
"""
import datetime
from spag.generator import Generator


class C(Generator):
    """C generator.

    A simple object for compiling scanner's and/or parser's to c programs.
    """

    _reserved = {
        "auto", "break", "case", "char", "const", "continue", "default", "do",
        "int", "long", "register", "return", "short", "signed", "sizeof",
        "static", "struct", "switch", "typedef", "union", "unsigned", "void",
        "volatile", "while", "double", "else", "enum", "extern", "float", "for",
        "goto", "if"
    }

    def _sanatize(self, name):
        """
        Sanatize the name so it is safe for c compilation following the rules:
         1. Characters other than a-z, A-Z, 0-9, or _ become '_'
         2. Names beginning with a number will be prefixed with a '_'
         3. Reserved c keyword will be prefixed with a '_'
        """
        _name = ''
        for char in name:
            if char.isalnum():
                _name += char
            else:
                _name += '_'

        if _name in self._reserved or name[0].isdigit():
            _name = '_' + _name

        return _name

    def _generate_file_header(self, filename, author, source, message, libs):
        time = datetime.datetime.utcnow().isoformat("T") + "Z"
        libs = ['#include <{0}.h>'.format(lib) for lib in libs]
        return """\
/******************************************************************************
 * File:    {0: <66}*
 * Author:  {1: <66}*
 * Created: {2: <66}*
 * Archive: {3: <66}*
 *                                                                            *
 *{4: ^76}*
 ******************************************************************************/

{6}{5}

""".format(filename, author, time, source, message,
           '\n'.join(libs), self._generate_section_header("imports"))

    @staticmethod
    def _generate_section_header(name):
        return """\
/******************************************************************************
 *{0: ^76}*
 ******************************************************************************/
""".format(name.upper())


    def _generate_token_api(self, name):
        types = []
        for token_name, pattern in self.scanner.expressions.items():
            types.append('  {0: <23} // {1}'.format(token_name.upper()+",", pattern))
        return """\
{2}
// Token's abstract over the character input stream.
typedef struct {0}_token {0}_token_t;

// Token's are associated to one of the types below.
typedef enum {{
{1}
}} {0}_token_type_t;

// Attempt construction of a new {0} token.
{0}_token_t *new_{0}_token({0}_token_type_t type,
                           char *text,
                           unsigned long text_len,
                           char *source,
                           unsigned long source_len,
                           unsigned long line,
                           unsigned long column);

// Free a token constructed using new_{0}_token.
void free_{0}_token({0}_token_t *{0}_token);

// Query for the tokens associated type.
{0}_token_type_t type({0}_token_t *{0}_token);

// Query for the string representation of the token.
char *text({0}_token_t *{0}_token);

// Query for the file in which the token was read.
char *source({0}_token_t *{0}_token);

// Query for the starting line on which the token was read.
unsigned long line({0}_token_t *{0}_token);

// Query for the starting column on which the token was read.
unsigned long column({0}_token_t *{0}_token);

""".format(name, "\n".join(types), self._generate_section_header("tokens")), """\
{1}
typedef struct {0}_token {{
  {0}_token_type_t type;
  char *text;
  char *source;
  unsigned long line;
  unsigned long column;
}} {0}_token_t;

{0}_token_t *new_{0}_token({0}_token_type_t type,
                           char *text,
                           unsigned long text_len,
                           char *source,
                           unsigned long source_len,
                           unsigned long line,
                           unsigned long column) {{
  {0}_token_t *{0}_token;
  if(!(({0}_token = calloc(1, sizeof({0}_token_t))) &&
       ({0}_token->text = malloc(sizeof(char)*(text_len+1))) &&
       ({0}_token->source = malloc(sizeof(char)*(source_len+1))))) {{
    free({0}_token->source);
    free({0}_token->text);
    free({0}_token);
    return NULL;
  }}

  {0}_token->type = type;
  {0}_token->line = line;
  {0}_token->column = column;
  strncpy({0}_token->text, text, sizeof(char)*text_len);
  {0}_token->text[text_len] = 0;
  strncpy({0}_token->source, source, sizeof(char)*source_len);
  {0}_token->source[source_len] = 0;

  return {0}_token;
}}

void free_{0}_token({0}_token_t *{0}_token) {{
  free({0}_token->text);
  free({0}_token->source);
  free({0}_token);
}}

char *text({0}_token_t *{0}_token) {{ return {0}_token->text; }}

char *source({0}_token_t *{0}_token) {{ return {0}_token->source; }}

unsigned long line({0}_token_t *{0}_token) {{ return {0}_token->line; }}

unsigned long column({0}_token_t *{0}_token) {{ return {0}_token->column; }}

{0}_token_type_t type({0}_token_t *{0}_token) {{ return {0}_token->type; }}

""".format(name, self._generate_section_header("tokens"))

    def _encode_dfa(self, name):
        state, symbol, T = self.scanner.transitions
        final_states = self.scanner.accepting
        expressions = self.scanner.expressions
        types = self.scanner.types

        labels, label = {}, 0
        for state_id in state.keys():
            label += 1
            labels[state_id] = "L{0}".format(label)

        program = """\
  goto {0};

""".format(labels[self.scanner.start])

        for in_state, state_key in state.items():
            if in_state in types.get('_sink', set()):
                continue  # NOTE: Don't encode error state explicitly.
            fallthrough = dict()
            for char, sym_key in symbol.items():
                _char = ord(char)
                if _char < 0 or _char > 255:
                    raise ValueError("Invalid Input: encountered non ascii character\n")
                end_state = T[sym_key][state_key]
                if end_state in fallthrough:
                    fallthrough[end_state].append(char)
                else:
                    fallthrough[end_state] = [char]

            cases = ""
            for end_state, char_list in fallthrough.items():
                if end_state in types.get('_sink', set()):
                    continue  # NOTE: Don't encode error transitions explicitly.
                char_list = [(hex(ord(char)), repr(char)) for char in char_list]
                for hex_repr, char_repr in sorted(char_list, key=lambda x: chr(int(x[0], base=16))):
                    cases += """\
    case {0: <5} // {1}
""".format("{0}:".format(hex_repr), char_repr)
                if end_state in final_states:
                    _type = None
                    for pname, _ in expressions.items():
                        if end_state in types[pname]:
                            _type = pname
                            break
                    cases += """\
      {0}_scanner->last_final_pos = ftell({0}_scanner->input);
      {0}_scanner->last_final_type = {1};
      goto {2};
""".format(name, _type.upper(), labels[end_state])
                else:
                    cases += """\
      goto {0};
""".format(labels[end_state])
            # NOTE: Uses 'default' as catch all to revert to last valid final state.
            # This implementes maximal munch. If not final state was found an
            # error is returned which means 1 of 2 possibilities: unrecognized or invalid input.
            program += """\
{0}:
  if(feof({1}_scanner->input)) {{ return {1}_EOF; }}

  switch({1}_peek({1}_scanner)) {{
{2}    default:
      if({1}_scanner->last_final_pos) {{
        fprintf(stdout, "TYPE: %d @%ld\\n", {1}_scanner->last_final_type, {1}_scanner->last_final_pos);
        return {1}_read_token({1}_scanner, {1}_scanner->last_final_type);
      }}
      return {1}_INVALID_INPUT;
  }}

""".format(labels[in_state], name, cases)

        return program

    # NOTE:
    # - switch to internal buffer, allowing for pipes.
        # -> more scanner state and a buffer API?
        # - NFA to be updated with types in final state for uniqueness when ->dfa->hopcroft??
        #   - cannot be done. example is most langs do relop -> < | > | <= | >= ...
    def _generate_scanner_api(self, name):
        return """\
{1}
// Abstract over the reading of {0}_token_t's.
typedef struct {0}_scanner {0}_scanner_t;

// Attempt the creation of a new scanner given the path to a file.
{0}_scanner_t *new_{0}_scanner(char *fpath);

// Free the scanner and close the associated file.
void free_{0}_scanner({0}_scanner_t *{0}_scanner);

// Return most recently read token of the given scanner.
{0}_token_t *{0}_token({0}_scanner_t *{0}_scanner);

// Errors associated with scanning.
typedef enum {{
  {0}_NIL,                 // no error.
  {0}_EOF,                 // end of file.
  {0}_INVALID_INPUT,       // input not recognized by scanner.
  {0}_OUT_OF_MEMORY,       // failed to allocate memory.
  {0}_UNKNOWN_ERROR,       // error not known.
}} {0}_scan_error_t;

// Attempt to scan a token from the file. 1 if successful, otherwise 0.
// If failure occurs the token will still contain the relevant details of the
// unrecognized token except for its type.
{0}_scan_error_t {0}_scan({0}_scanner_t *{0}_scanner);
""".format(name, self._generate_section_header("scanner")), """\
{2}
typedef struct {0}_scanner {{
  FILE *input;
  int peek;
  long int offset;
  char *text;
  char *source;
  unsigned int length;
  unsigned int line;
  unsigned int column;
  {0}_token_t *token;
  long int last_final_pos;
  {0}_token_type_t last_final_type;
}} {0}_scanner_t;

{0}_scanner_t *new_{0}_scanner(char *fpath) {{
  FILE *f = fopen(fpath, "r");
  if(!f) {{ return NULL; }}

  {0}_scanner_t *{0}_scanner;
  if(!({0}_scanner = calloc(1, sizeof({0}_scanner_t))) &&
      ({0}_scanner->token = malloc(sizeof({0}_token_t)))) {{
    free({0}_scanner->token);
    free({0}_scanner);
    return NULL;
  }}

  {0}_scanner->input = f;
  //{0}_scanner->peek = fgetc(f);
  {0}_scanner->offset = 0;
  {0}_scanner->text = NULL;
  {0}_scanner->source = fpath;
  {0}_scanner->length = 0;
  {0}_scanner->line = 0;
  {0}_scanner->column = 0;
  {0}_scanner->last_final_pos = -1;
  //{0}_scanner->last_final_type = 0;

  return {0}_scanner;
}}

void free_{0}_scanner({0}_scanner_t *{0}_scanner) {{
  fclose({0}_scanner->input);
  free({0}_scanner->text);
  free({0}_scanner->token);
  free({0}_scanner);
}}

{0}_token_t *{0}_token({0}_scanner_t *{0}_scanner) {{
  return {0}_scanner->token;
}}

int {0}_peek({0}_scanner_t *{0}_scanner) {{
  {0}_scanner->peek = fgetc({0}_scanner->input);
  {0}_scanner->column++;
  if({0}_scanner->peek == '\\n') {{
    {0}_scanner->line++;
    {0}_scanner->column = 0;
  }}
  return {0}_scanner->peek;
}}

{0}_scan_error_t {0}_read_token({0}_scanner_t *{0}_scanner,
                                {0}_token_type_t {0}_type) {{
  {0}_scanner->length = ftell({0}_scanner->input) - {0}_scanner->offset;

  {0}_scanner->text = realloc({0}_scanner->text, sizeof(char)*{0}_scanner->length);
  if(!{0}_scanner->text) {{ return {0}_OUT_OF_MEMORY; }}

  fseek({0}_scanner->input, {0}_scanner->offset, SEEK_SET);
  if(fread({0}_scanner->text,
           sizeof(char),
           sizeof(char)*{0}_scanner->length,
           {0}_scanner->input) != sizeof(char)*{0}_scanner->length) {{
    return {0}_UNKNOWN_ERROR;
  }}

  if(!({0}_scanner->token = new_{0}_token({0}_type,
                                          {0}_scanner->text,
                                          {0}_scanner->length,
                                          {0}_scanner->source,
                                          0,
                                          {0}_scanner->line,
                                          {0}_scanner->column))) {{
    return {0}_OUT_OF_MEMORY;
  }}

  return {0}_NIL;
}}

{0}_scan_error_t {0}_scan({0}_scanner_t *{0}_scanner) {{
  {0}_scanner->offset = ftell({0}_scanner->input);

{1}}}
""".format(name, self._encode_dfa(name), self._generate_section_header("scanner"))

    def _generate_ast_api(self, name):
        # NOTE: define AST prototypes and defs
        _ = name
        _ = self
        ast_header, ast_source = "", ""
        return ast_header, ast_source

    def _encode_bnf(self, name):
        # NOTE: graph encoded as GOTOs;
        # automatically throw away tokens not in the bnf (whitespace, comments, etc)
        _ = name
        _ = self
        return ""
        #production_rules = ""
        #for nonterm, rule in self._parser.rules():
        #    production_rules += "// {0: <30} ::= {1}\n".format(nonterm, " ".join(rule))
        # """\
        # // Start production ::= {2}
        #
        # {3}
        #
        # // Attempt to parse into an AST of tokens. 1 if successful, otherwise 0.
        # int {0}(FILE *f);
        # """.format(parse_func, self._generate_section_header("::BNF GRAMMMAR::"),
        #            self._parser.start(), production_rules)

    def _generate_parser_api(self, name):
        # NOTE: define parser prototypes and defs
        parser_header, parser_source = "", """\
        {0} {1} {2}
        """.format(name, self._encode_bnf(name), self._generate_section_header("parser"))
        return parser_header, parser_source

    def _translate(self):
        """Override the superclass method to generate source code.

        Attempt to generate the c source(.c) and header(.h) files for the
        corresponding scanner and/or parser currently set in the object.
        """
        author = '**AUTO GENERATED**'
        source = 'https://github.com/rrozansk/Scanner-Parser-Generator'
        warning = 'WARNING!! AUTO GENERATED FILE, DO NOT EDIT!'
        libs = ['stdio']
        filename = self._sanatize(self.filename)
        if self.scanner:
            filename += self._sanatize('_'+self.scanner.name)
        if self.parser:
            filename += self._sanatize('_'+self.parser.name)

        header = self._generate_file_header(filename+".h",
                                            author,
                                            source,
                                            warning,
                                            libs)

        libs.extend(["stdlib", "string", filename])
        source = self._generate_file_header(filename+".c",
                                            author,
                                            source,
                                            warning,
                                            libs)

        if self.scanner is not None:
            scan_func = self._sanatize(self.scanner.name)
            token_header, token_source = self._generate_token_api(scan_func)
            scanner_header, scanner_source = self._generate_scanner_api(scan_func)

            header += token_header + scanner_header
            source += token_source + scanner_source


        if self.parser is not None:
            parse_func = self._sanatize(self.parser.name)
            ast_header, ast_source = self._generate_ast_api(parse_func)
            parser_header, parser_source = self._generate_parser_api(parse_func)

            header += ast_header + parser_header
            source += ast_source + parser_source

        header = """\
#ifndef {0}
#define {0}

{1}
#endif
""".format(filename, header)

        return {
            filename+'.h': header,
            filename+'.c': source,
        }
