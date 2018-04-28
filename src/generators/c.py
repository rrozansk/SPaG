"""
A scanner/parser generator targeting c.
Generates header (.h) and source (.c) files.
"""
import datetime
from .. import generator as generator


class C(generator.Generator):
    """
    A simple object for compiling scanner's and/or parser's to c.
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
            if char.isalnum(): _name += char
            else: _name += '_'

        if _name in self._reserved or name[0].isdigit():
            _name = '_' + _name

        return _name

    def _generate_comment_block_file_header(self, filename):
        time = datetime.datetime.utcnow().isoformat("T") + "Z"
        return (
                "/******************************************************************************\n"
                " * File:    {0: <66}*\n"
                " * Author:  **AUTO GENERATED**                                                *\n"
                " * Created: {1: <66}*\n"
                " * Archive: https://github.com/rrozansk/Scanner-Parser-Generator              *\n"
                " *                                                                            *\n"
                " *                WARNING!! AUTO GENERATED FILE, DO NOT EDIT!                 *\n"
                " ******************************************************************************/\n"
               ).format(filename, time)

    def _generate_comment_block_named_header(self, name):
        return (
                "/******************************************************************************\n"
                " *{0: ^76}*\n".format(name) +
                " ******************************************************************************/\n"
               )

    def _encode_dfa(self):
        return "" # TODO: graph encoded as GOTOs

    def _encode_bnf(self):
        return "" # TODO: graph encoded as GOTOs

    def _output_header(self, filename):
        """
        Generate the c header file (.h).
        """
        header = self._generate_comment_block_file_header(filename+".h")
        header += "#include <stdio.h>\n\n"

        if self._scanner is not None:
            scan_func = self._sanatize(self._scanner.name())
            token_rows = ""
            for name, pattern in self._scanner.expressions().items():
                token_rows += "// {0: <27}{1: <48}\n".format(name.upper(), pattern)
            header += (
                       "// Token's abstract over the character input stream.\n"
                       "typedef struct token token_t;\n"
                       "\n"
                       "// Query for the string representation of the token.\n"
                       "char *text(token_t token);\n"
                       "\n"
                       "// Query for the file in which the token was read.\n"
                       "char *source(token_t token);\n"
                       "\n"
                       "// Query for the starting line on which the token was read.\n"
                       "unsigned long line(token_t token);\n"
                       "\n"
                       "// Query for the starting column on which the token was read.\n"
                       "unsigned long column(token_t token);\n"
                       "\n"
                       "// Query for the tokens associated type.\n"
                       "unsigned int type(token_t token);\n"
                       "\n"
                       + self._generate_comment_block_named_header("::TOKENS::")
                       + token_rows +
                       "\n"
                       "// Attempt to scan a token from the file. 1 if successful, otherwise 0.\n"
                       "// If failure occurs the token will still contain the relevant details of the\n"
                       "// unrecognized token except for its type.\n"
                       "int {0}(FILE *f, token_t *token);\n".format(scan_func)
                     )

        if self._parser is not None:
            parse_func = self._sanatize(self._parser.name())
            start_production = "// Start production ::= " + self._parser.start() + "\n"
            production_rules = ""
            for nonterm, rule in self._parser.rules():
                production_rules += "// {0: <30} ::= {1}\n".format(nonterm, " ".join(rule))
            header += (
                       # TODO: define AST API
                       "\n"
                       + self._generate_comment_block_named_header("::BNF GRAMMMAR::")
                       + start_production +
                       "\n"
                       + production_rules +
                       "\n"
                       "// Attempt to parse into an AST of tokens. 1 if successful, otherwise 0.\n"
                       "int {0}(FILE *f);\n".format(parse_func)
                      )

        return header

    def _output_source(self, filename):
        """
        Generate the c source file (.c).
        """
        source = self._generate_comment_block_file_header(filename+".c")
        source += "#include <stdio.h>\n\n"

        if self._scanner is not None:
            scan_func = self._sanatize(self._scanner.name())

            types = ""
            for type in self._scanner.types():
                types += ("    " + type.upper() + ",\n")
            source += (
                       "typedef struct token {\n"
                       "  char *text;\n"
                       "  char *source;\n"
                       "  unsigned long line;\n"
                       "  unsigned long column;\n"
                       "  enum {\n"
                       + types +
                       "  } type;\n"
                       "} token_t;\n"
                       "\n"
                       "char *text(token_t token) { return token.text; }\n"
                       "\n"
                       "char *source(token_t token) { return token.source; }\n"
                       "\n"
                       "unsigned long line(token_t token) { return token.line; }\n"
                       "\n"
                       "unsigned long column(token_t token) { return token.column; }\n"
                       "\n"
                       "unsigned int type(token_t token) { return token.type; }\n"
                       "\n"
                       "int " + scan_func + "(FILE *f, token_t *token) {\n"
                       + self._encode_dfa() +
                       "  return 0; // fail\n"
                       "}\n"
                      )

        if self._parser is not None:
            parse_func = self._sanatize(self._parser.name())
            source += (
                       # TODO: typedef AST struct
                       # TODO: define AST API implementation
                       "\n"
                       "void " + parse_func + "(FILE *f) {\n"
                       + self._encode_bnf() +
                       "}\n"
                      )

        return source

    def output(self, filename):
        """
        Attempt to generate and write the c source(.c) and header(.h) files for
        the corresponding scanner and/or parser currently set in the object.
        """
        if type(filename) != str:
            raise ValueError('Invalid Input: filename must be a string')

        if filename == "":
            raise ValueError('Invalid Input: filename must be non empty')

        with open(filename+".h", 'w') as _file:
            _file.write(self._output_header(filename))

        with open(filename+".c", 'w') as _file:
            _file.write(self._output_source(filename))
