import os
import re
import sys
from enum import Enum
from typing import List


STRING_AND_OTHERS = re.compile('([^"]*)"([^"]*)"([^"]*)')
INTEGERS = re.compile("[0-9]+")


class _TokenType(Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    IDENTIFIER = "identifier"
    INT_CONST = "integerConstant"
    STRING_CONST = "stringConstant"


class JackTokenizer:
    def __init__(self, file: str):
        self._tokens = []
        self._index = 0
        with open(file) as f:
            lines = []
            for l in f.readlines():
                l = l.split("//")[0].strip()
                lines.append(l)
        s = " ".join(lines)
        s = self._remove_comments(s)
        s_list = self._split_by_double_quotes(s)
        for s in s_list:
            self._tokens += self._to_tokens(s)

    def _remove_comments(self, s: str) -> str:
        s_split_by_comments = re.split("/\*|\*/", s)
        s_without_comments = ""
        for i, code in enumerate(s_split_by_comments):
            if i % 2 == 0:
                s_without_comments += code + " "
        return s_without_comments

    def _split_by_double_quotes(self, s: str) -> List[str]:
        split_by_double_quotes = re.split('"', s)
        s_list = []
        for i, code in enumerate(split_by_double_quotes):
            if i % 2 == 0:
                s_list.append(code.strip())
            else:
                s_list.append(f'"{code}"')
        return s_list

    def _to_tokens(self, s: str) -> List[str]:
        s = s.strip()
        tokens = []
        if not s:
            return tokens
        elif s.startswith('"'):
            tokens.append((s[1:-1], _TokenType.STRING_CONST))
            return tokens
        elif s.find(";") != -1:
            split = s.split(";")
            delimiter = ";"
        elif s.find(".") != -1:
            split = s.split(".")
            delimiter = "."
        elif s.find(",") != -1:
            split = s.split(",")
            delimiter = ","
        elif s.find("(") != -1:
            split = s.split("(")
            delimiter = "("
        elif s.find(")") != -1:
            split = s.split(")")
            delimiter = ")"
        elif s.find("[") != -1:
            split = s.split("[")
            delimiter = "["
        elif s.find("]") != -1:
            split = s.split("]")
            delimiter = "]"
        elif s.find("{") != -1:
            split = s.split("{")
            delimiter = "{"
        elif s.find("}") != -1:
            split = s.split("}")
            delimiter = "}"
        elif s.find("-") != -1:
            split = s.split("-")
            delimiter = "-"
        elif s.find("~") != -1:
            split = s.split("~")
            delimiter = "~"
        elif s.find(" ") != -1:
            split = s.split(" ")
            delimiter = " "
        else:
            if s in ["class", "constructor", 'function', 'method', 'field', 'static', 'var',
                        'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let',
                        'do', 'if', 'else', 'while', 'return']:
                tokens.append((s, _TokenType.KEYWORD))
            elif s in ['{', '}', '(', ')', '[', ']', '.',  ',', ';', '+',
                        '-', '*', '/', '&', '|', '<', '>', '=', '~']:
                tokens.append((s, _TokenType.SYMBOL))
            elif INTEGERS.match(s):
                tokens.append((int(s), _TokenType.INT_CONST))
            else:
                tokens.append((s, _TokenType.IDENTIFIER))
            return tokens
        for i, new_s in enumerate(split):
            if i != 0 and delimiter != " ":
                tokens.append((delimiter, _TokenType.SYMBOL))
            tokens += self._to_tokens(new_s)

        return tokens

    def hasMoreTokens(self) -> bool:
        if len(self._tokens) > self._index:
            return True
        else:
            return False

    def advance(self) -> None:
        self._index += 1

    def tokenType(self) -> _TokenType:
        token_and_token_type = self._tokens[self._index]
        return token_and_token_type[1]

    def keyword(self) -> None:
        token_and_token_type = self._tokens[self._index]
        return token_and_token_type[0]

    def symbol(self) -> str:
        token_and_token_type = self._tokens[self._index]
        return token_and_token_type[0]

    def identifier(self) -> str:
        token_and_token_type = self._tokens[self._index]
        return token_and_token_type[0]

    def intVal(self) -> int:
        token_and_token_type = self._tokens[self._index]
        return token_and_token_type[0]

    def stringVal(self) -> str:
        token_and_token_type = self._tokens[self._index]
        return token_and_token_type[0]


class CompilationEngine:
    def __init__(self, input_file: str, output_file: str):
        self._tokenizer = JackTokenizer(input_file)
        
        self._lines = ["<class>"]
        self.compileClass()
        self._lines += ["</class>"]
        with open(output_file, "w") as writer:
            writer.write("\n".join(self._lines))

    def compileClass(self) -> None:
        self._tokenizer.advance()  # skip `class`
        class_name = self._tokenizer.symbol()
        self._tokenizer.advance()
        self._tokenizer.advance()  # skip `{`
        self._lines += [
            f"<keyword> class </keyword>",
            f"<identifier> {class_name} </identifier>",
            "<symbol> { </symbol>",
        ]
        
        while self._tokenizer.keyword() in ["static", "field"]:
            self._lines += ["<classVarDec>"]
            self.compileClassVarDec()
            self._lines += ["</classVarDec>"]

        while self._tokenizer.keyword() in ["constructor", "function", "method"]:
            self._lines += ["<subroutineDec>"]
            self.compileSubroutine()
            self._lines += ["</subroutineDec>"]

        self._lines += ["<symbol> } </symbol>"]
        self._tokenizer.advance()


    def compileClassVarDec(self) -> None:
        static_or_field = self._tokenizer.keyword()
        self._lines += [f"<keyword> {static_or_field} </keyword>"]
        self._tokenizer.advance()
        self._compileType()
        var_name = self._tokenizer.keyword()
        self._lines += [f"<identifier> {var_name} </identifier>"]
        self._tokenizer.advance()
        while self._tokenizer.symbol() == ",":
            self._tokenizer.advance()  # skip `,`
            self._lines += [
                "<symbol> , </symbol>",
                f"<identifier> {self._tokenizer.identifier()} </identifier>",
            ]
            self._tokenizer.advance()  # skip `,`
        self._tokenizer.advance()  # skip `;`
        self._lines += ["<symbol> ; </symbol>"]

    def _compileType(self) -> None:
        if self._tokenizer.tokenType() == _TokenType.KEYWORD:
            self._lines += [f"<keyword> {self._tokenizer.keyword()} </keyword>"]
        else:
            self._lines += [f"<identifier> {self._tokenizer.identifier()} </identifier>"]
        self._tokenizer.advance()

    def compileSubroutine(self) -> None:
        constructor_function_or_method = self._tokenizer.keyword()
        self._tokenizer.advance()
        self._lines += [f"<keyword> {constructor_function_or_method} </keyword>"]
        self._compileType()
        subroutine_name = self._tokenizer.identifier()
        self._tokenizer.advance()
        self._tokenizer.advance()  # skip `(`
        self._lines += [
            f"<identifier> {subroutine_name} </identifier>",
            "<symbol> ( </symbol>",
        ]
        self.compileParameterList()
        self._tokenizer.advance()  # skip `)`
        self._tokenizer.advance()  # skip `{`
        
        self._lines += [
            "<symbol> ) </symbol>",
            "<subroutineBody>",
            "<symbol> { </symbol>",
        ]

        while self._tokenizer.keyword() == "var":
            self._lines += ["<varDec>"]
            self.compileVarDec()
            self._lines += ["</varDec>"]

        self.compileStatements()

        self._tokenizer.advance()  # skip `}`
        self._lines += [
            "<symbol> } </symbol>",
            "</subroutineBody>",
        ]

    def compileParameterList(self) -> None:
        self._lines += ["<parameterList>"]
        if not (self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == ")"):
            self._compileType()
            self._lines += [f"<identifier> {self._tokenizer.identifier()} </identifier>"]
            self._tokenizer.advance()
            while self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == ",":
                self._lines += ["<symbol> , </symbol>"]
                self._tokenizer.advance()
                self._compileType()
                self._lines += [f"<identifier> {self._tokenizer.identifier()} </identifier>"]
                self._tokenizer.advance()
        self._lines += ["</parameterList>"]

    def compileVarDec(self) -> None:
        self._lines += ["<keyword> var </keyword>"]
        self._tokenizer.advance()  # skip `var`
        self._compileType()
        var_name = self._tokenizer.identifier()
        self._tokenizer.advance()
        self._lines += [f"<identifier> {var_name} </identifier>"]
        while self._tokenizer.symbol() == ",":
            self._tokenizer.advance()  # skip `,`
            self._lines += [
                "<symbol> , </symbol>",
                f"<identifier> {self._tokenizer.identifier()} </identifier>",
            ]
            self._tokenizer.advance()
        self._lines += ["<symbol> ; </symbol>"]
        self._tokenizer.advance()

    def compileStatements(self) -> None:
        self._lines += ["<statements>"]
        while self._tokenizer.tokenType() == _TokenType.KEYWORD and self._tokenizer.keyword() in ["let", "if", "while", "do", "return"]:
            keyword = self._tokenizer.keyword()
            print(f"keyword: {keyword}")
            if keyword == "let":
                self._lines += ["<letStatement>"]
                self.compileLet()
                self._lines += ["</letStatement>"]
            elif keyword == "if":
                self.compileIf()
            elif keyword == "while":
                self.compileWhile()
            elif keyword == "do":
                self._lines += ["<doStatement>"]
                self.compileDo()
                self._lines += ["</doStatement>"]
            else:
                self.compileReturn()
        self._lines += ["</statements>"]

    def compileDo(self) -> None:
        self._lines += ["<keyword> do </keyword>"]
        self._tokenizer.advance()  # skip `do`
        subroutine_name = self._tokenizer.identifier()
        self._tokenizer.advance()
        if self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == ".":
            class_name_or_var_name = subroutine_name
            self._lines += [
                f"<identifier> {class_name_or_var_name} </identifier>",
                "<symbol> . </symbol>",
            ]
            self._tokenizer.advance()  # skip `.`
            subroutine_name = self._tokenizer.identifier()
            self._tokenizer.advance()  # skip `subroutine_name`
        self._tokenizer.advance()  # skip `(`
        self._lines += [
            f"<identifier> {subroutine_name} </identifier>",
            "<symbol> ( </symbol>",
        ]
        self.compileExpressionList()
        self._lines += [
            "<symbol> ) </symbol>",
            "<symbol> ; </symbol>",
        ]
        self._tokenizer.advance()  # skip `)`
        self._tokenizer.advance()  # skip `;`

    def compileLet(self) -> None:
        self._tokenizer.advance()  # skip `let`
        var_name = self._tokenizer.identifier()
        self._tokenizer.advance()
        self._tokenizer.advance()  # skip `=`
        self._lines += [
            "<keyword> let </keyword>",
            f"<identifier> {var_name} </identifier>",
            "<symbol> = </symbol>",
        ]
        self.compileExpression()
        self._lines += [
            "<symbol> ; </symbol>",
        ]
        self._tokenizer.advance()

    def compileWhile(self) -> None:
        self._lines += [
            "<whileStatement>",
            "<keyword> while </keyword>",
            "<symbol> ( </symbol>",
        ]
        self._tokenizer.advance()  # skip `while`
        self._tokenizer.advance()  # skip `(`
        self.compileExpression()
        self._lines += [
            "<symbol> ) </symbol>",
            "<symbol> { </symbol>",
        ]
        self._tokenizer.advance()  # skip `)`
        self._tokenizer.advance()  # skip `{`
        self.compileStatements()
        self._lines += [
            "<symbol> } </symbol>",
            "</whileStatement>",
        ]
        self._tokenizer.advance()  # skip `}`

    def compileReturn(self) -> None:
        self._tokenizer.advance()  # skip `return`
        self._lines += [
            "<returnStatement>",
            "<keyword> return </keyword>",
        ]
        if self._tokenizer.tokenType() != _TokenType.SYMBOL or self._tokenizer.symbol() != ";":
            self.compileExpression()
        self._tokenizer.advance()  # skip `;`
        self._lines += [
            "<symbol> ; </symbol>",
            "</returnStatement>",
        ]

    def compileIf(self) -> None:
        self._tokenizer.advance()  # skip `if`
        self._tokenizer.advance()  # skip `(`
        self._lines += [
            "<ifStatement>",
            "<keyword> if </keyword>",
            "<symbol> ( </symbol>",
        ]
        self.compileExpression()
        self._tokenizer.advance()  # skip `)`
        self._tokenizer.advance()  # skip `{`
        self._lines += [
            "<symbol> ) </symbol>",
            "<symbol> { </symbol>",
        ]
        self.compileStatements()
        self._lines += ["<symbol> } </symbol>"]
        print(f"must be '}}': {self._tokenizer.symbol()}")
        self._tokenizer.advance()  # skip `}`
        print(f"tokenTyle:{self._tokenizer.tokenType()} else?: {self._tokenizer.keyword()}")
        if self._tokenizer.tokenType() == _TokenType.KEYWORD and self._tokenizer.keyword() == "else":
            self._tokenizer.advance()  # skip `else`
            self._tokenizer.advance()  # skip `{`
            self._lines += [
                "<keyword> else </keyword>",
                "<symbol> { </symbol>",
            ]
            self.compileStatements()
            self._lines += ["<symbol> } </symbol>"]
            self._tokenizer.advance()  # skip `}`
        self._lines += [
            "</ifStatement>",
        ]

    def compileExpression(self) -> None:
        self._lines += ["<expression>"]
        self.compileTerm()
        while self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() in ["+", "-", "*", "/", "&", "|", "<", ">", "="]:
            op = self._tokenizer.symbol()
            self._tokenizer.advance()
            self._lines += [
                f"<symbol> {op} </symbol>",
            ]
            self.compileTerm()
        self._lines += ["</expression>"]

    def compileTerm(self) -> None:
        self._lines += ["<term>"]
        if self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() in ["(", "["]:
            self._lines += [f"<symbol> {self._tokenizer.symbol()} </symbol>"]
            self._tokenizer.advance()
            self.compileExpression()
            self._lines += [f"<symbol> {self._tokenizer.symbol()} </symbol>"]
        elif self._tokenizer.tokenType() == _TokenType.IDENTIFIER:
            self._lines += [f"<identifier> {self._tokenizer.identifier()} </identifier>"]
        else:
            self._lines += [f"<keyword> {self._tokenizer.keyword()} </keyword>"]
        self._lines += ["</term>"]
        self._tokenizer.advance()

    def compileExpressionList(self) -> None:
        self._lines += ["<expressionList>"]
        if not (self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == ")"):
            self.compileExpression()
            while self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == ",":
                self._lines += ["<symbol> , </symbol>"]
                self._tokenizer.advance()
                self.compileExpression()
        self._lines += ["</expressionList>"]


def main():
    input_file_or_dir = sys.argv[1]
    if os.path.isfile(input_file_or_dir):
        input_files = [input_file_or_dir]
    else:
        dir = input_file_or_dir
        input_files = [f"{dir}/{f}" for f in os.listdir(dir) if f.endswith(".jack")]
    for input_file in input_files:
        output_file = f"{os.path.splitext(input_file)[0]}.xml"
        CompilationEngine(input_file, output_file)


def main_orig():
    input_file_or_dir = sys.argv[1]
    if os.path.isfile(input_file_or_dir):
        input_files = [input_file_or_dir]
    else:
        dir = input_file_or_dir
        input_files = [f"{dir}/{f}" for f in os.listdir(dir) if f.endswith(".jack")]
    for input_file in input_files:
        with open(f"{os.path.splitext(input_file)[0]}T.xml", "w") as w:
            tokenizer = JackTokenizer(input_file)
            lines = ["<tokens>"]
            while tokenizer.hasMoreTokens():
                type = tokenizer.tokenType()
                if type == _TokenType.KEYWORD:
                    token = tokenizer.keyword()
                elif type == _TokenType.SYMBOL:
                    s = tokenizer.symbol()
                    if s == "<":
                        token = "&lt;"
                    elif s == ">":
                        token = "&gt;"
                    elif s == "&":
                        token = "&amp;"
                    else:
                        token = s
                elif type == _TokenType.IDENTIFIER:
                    token = tokenizer.identifier()
                elif type == _TokenType.INT_CONST:
                    token = tokenizer.intVal()
                else:
                    token = tokenizer.stringVal()
                print(f"printing type:{type.value} token:{token}")
                lines.append(f"<{type.value}> {token} </{type.value}>")
                tokenizer.advance()
            lines.append("</tokens>")
            w.write("\n".join(lines))
            w.write("\n")


if __name__ == "__main__":
    main()
