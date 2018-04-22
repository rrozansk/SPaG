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
        if name[0].isdigit():
            _name += '_'

        for idx in range(len(name)):
            if name[idx].isalnum():
                _name += name[idx]
            else:
                _name += '_'

        if _name in self._reserved:
            return '_' + _name

        return _name

    def _output_header(self, filename):
        """
        Generate the c header file (.h).
        """
        time = datetime.datetime.utcnow().isoformat("T") + "Z"

        header = (
                  ""
                  "/*\n"
                  " * File:    " + filename + ".h\n"
                  " * Author:  **AUTO GENERATED**\n"
                  " * Created: " + time + "\n"
                  " * Archive: https://github.com/rrozansk/Scanner-Parser-Generator\n"
                  " *\n"
                  " * WARNING!! AUTO GENERATED FILE, DO NOT EDIT!\n"
                  " */\n"
                 )

        if self._scanner is not None:
            scan_func = self._sanatize(self._scanner.name())
            header += (
                       "\n"
                       "// Token's ...\n"
                       "typedef struct token token_t;\n"
                       "\n"
                       "// Returns the string representation of the token.\n"
                       "char *text(token token_t);\n"
                       "\n"
                       "// Return the type of the token.\n"
                       "int type(token token_t);\n"
                       "\n"
                       "// Return the starting line the token was read on.\n"
                       "int line(token token_t);\n"
                       "\n"
                       "// Return the starting column the token was read on.\n"
                       "int column(token token_t);\n"
                       "\n"
                       "// Return the file the token was read in.\n"
                       "char *file(token token_t);\n"
                       "\n"
                       "/*\n"
                       " * A scanner ...\n"
                       " *\n"
                       " * Recognized tokens:\n"
                      )
            for name, pattern in self._scanner.expressions().items():
                header += " *  - " + name + " ::= " + pattern + "\n"
            # return's 0/1 for succ/error. mutates token passed in
            header += " */\nint " + scan_func + "(FILE *f, token_t *token);\n"

        if self._parser is not None:
            parse_func = self._sanatize(self._parser.name())
            header += (
                       "\n/*\n"
                       " *            ::BNF GRAMMMAR::\n"
                       " *\n"
                      )
            for nonterm, rule in self._parser.rules():
                header += " *  " + nonterm + " -> " + " ".join(rule) + "\n"
            header += (
                       " * \n"
                       " * Start production -> " + self._parser.start() + "\n"
                       " */\n"
                       "void " + parse_func + "(FILE *f);\n"
                      )

        return header

    def _output_source(self, filename):
        """
        Generate the c source file (.c).
        """
        time = datetime.datetime.utcnow().isoformat("T") + "Z"

        source = (
                  ""
                  "/*\n"
                  " * File:    " + filename + ".c\n"
                  " * Author:  **AUTO GENERATED**\n"
                  " * Created: " + time + "\n"
                  " * Archive: https://github.com/rrozansk/Scanner-Parser-Generator\n"
                  " *\n"
                  " * WARNING!! AUTO GENERATED FILE, DO NOT EDIT!\n"
                  " */\n"
                  "#include <stdio.h>\n"
                 )

        if self._scanner is not None:
            scan_func = self._sanatize(self._scanner.name())
            source += (
                       "\n"
                       "typedef struct token {\n"
                       "  int line;\n"
                       "  int column;\n"
                       "  enum {\n"
                       "\n"
                       "  } type;\n"
                       "  char *value;\n"
                       "} token_t;\n"
                       "\n"
                       "// Scanner source generation not yet implemented.\n"
                       "int " + scan_func + "(FILE *f, token_t *token) {\n"
                       "  return 0; // fail\n"
                       "}\n"  # TODO graph encoded as GOTOs
                      )

        if self._parser is not None:
            parse_func = self._sanatize(self._parser.name())
            source += (
                       "\n"
                       "// parser source generation not yet implemented\n"
                       "void " + parse_func + "(FILE *f) {\n"
                       "}\n"  # TODO
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
