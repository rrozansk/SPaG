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

        header = "" +\
                 "/*\n" +\
                 " * File:    " + filename + ".h\n" +\
                 " * Author:  **AUTO GENERATED**\n" +\
                 " * Created: " + time + "\n" +\
                 " * Archive: https://github.com/rrozansk/Grammar-Generator\n" +\
                 " *\n" +\
                 " * WARNING!! AUTO GENERATED FILE, DO NOT EDIT!\n" +\
                 " */\n"

        if self._scanner is not None:
            scan_func = self._sanatize(self._scanner.name())
            header += "\n" +\
                      "// Token's ...\n" +\
                      "typedef struct token token_t;\n" +\
                      "\n" +\
                      "// Returns the string representation of the token.\n" +\
                      "char *value(token token_t);\n" +\
                      "\n" +\
                      "// Return the type of the token.\n" +\
                      "int type(token token_t);\n" +\
                      "\n" +\
                      "// Return the starting line the token was read on.\n" +\
                      "int line(token token_t);\n" +\
                      "\n" +\
                      "// Return the starting column the token was read on.\n" +\
                      "int column(token token_t);\n" +\
                      "\n" +\
                      "/*\n" +\
                      " * A scanner ...\n" +\
                      " *\n" +\
                      " * Recognized tokens:\n"
            for name, pattern in self._scanner.expressions().items():
                header += " *  - " + name + " ::= " + pattern + "\n"
            header += " */\n" +\
                      "void " + scan_func + "(FILE *f, token_t *token);\n"

        if self._parser is not None:
            parse_func = self._sanatize(self._parser.name())
            header += "\n/*\n"
            header += " *            ::BNF GRAMMMAR::\n"
            header += " *\n"
            for (idx, nonterm, rule) in self._parser.rules():
                header += " *  " + nonterm + " -> " + " ".join(rule) + "\n"
            header += " * \n"
            header += " * Start production -> " + self._parser.start() + "\n"
            header += " */\n"
            header += "void " + parse_func + "(FILE *f);\n"

        return header

    def _output_source(self, filename):
        """
        Generate the c source file (.c).
        """
        time = datetime.datetime.utcnow().isoformat("T") + "Z"

        source = ""
        source += "/*\n"
        source += " * File:    " + filename + ".c\n"
        source += " * Author:  **AUTO GENERATED**\n"
        source += " * Created: " + time + "\n"
        source += " * Archive: https://github.com/rrozansk/Grammar-Generator\n"
        source += " *\n"
        source += " * WARNING!! AUTO GENERATED FILE, DO NOT EDIT!\n"
        source += " */\n"
        source += "#include <stdio.h>\n"

        if self._scanner is not None:
            scan_func = self._sanatize(self._scanner.name())
            source += "\n"
            source += "typedef struct token {\n"
            source += "  int line;\n"
            source += "  int column;\n"
            source += "  enum {\n"
            source += "\n"
            source += "  } type;\n"
            source += "  char *value;\n"
            source += "} token_t;\n"
            source += "\n"
            source += "// Scanner source generation not yet implemented.\n"
            source += "int " + scan_func + "(FILE *f, token_t *token) {\n"
            source += "  return 0; // fail\n"
            source += "}\n"  # TODO graph encoded as GOTOs

        if self._parser is not None:
            parse_func = self._sanatize(self._parser.name())
            source += "\n"
            source += "// parser source generation not yet implemented\n"
            source += "void " + parse_func + "(FILE *f) {\n"
            source += "}\n"  # TODO

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
