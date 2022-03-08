import os
import re
import sys
from enum import Enum, auto
from typing import Any, Dict, List, Optional


STRING_AND_OTHERS = re.compile('([^"]*)"([^"]*)"([^"]*)')
INTEGERS = re.compile("[0-9]+")


class _TokenType(Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    IDENTIFIER = "identifier"
    INT_CONST = "integerConstant"
    STRING_CONST = "stringConstant"


class _Kind(Enum):
    STATIC = "static"
    FIELD = "field"
    ARG = "argument"
    VAR = "var"


class _Segment(Enum):
    CONST = "constant"
    ARG = "argument"
    STATIC = "static"
    THIS = "this"
    THAT = "that"
    POINTER = "pointer"
    TEMP = "temp"


class _Command(Enum):
    ADD = "add"
    SUB = "sub"
    NEG = "neg"
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    AND = "and"
    OR = "or"
    NOT = "not"


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
    def __init__(self, input_file: str, output_file_prefix: str):
        self._tokenizer = JackTokenizer(input_file)
        self._table = SymbolTable()

        self._lines = ["<class>"]
        self._writer = VMWriter(f"{output_file_prefix}.vm")
        self._class = os.path.basename(os.path.splitext(input_file)[0])
        self.compileClass()
        self._lines += ["</class>"]
        with open(f"{output_file_prefix}.xml", "w") as writer:
            writer.write("\n".join(self._lines))
        self._writer.close()

    def compileClass(self) -> None:
        self._tokenizer.advance()  # skip `class`
        self._tokenizer.advance()  # skip `class_name`
        self._tokenizer.advance()  # skip `{`
        while self._tokenizer.keyword() in ["static", "field"]:
            self.compileClassVarDec()
        while self._tokenizer.keyword() in ["constructor", "function", "method"]:
            self.compileSubroutine()
        self._tokenizer.advance()  # skip `}`

    def compileClassVarDec(self) -> None:
        static_or_field = self._tokenizer.keyword()
        self._lines += [f"<keyword> {static_or_field} </keyword>"]
        self._tokenizer.advance()
        t = self._compileType()
        var_name = self._tokenizer.keyword()
        self._lines += [f"<identifier> {var_name} </identifier>"]
        self._tokenizer.advance()
        self._table.define(var_name, t, static_or_field)
        while self._tokenizer.symbol() == ",":
            self._tokenizer.advance()  # skip `,`
            var_name = self._tokenizer.identifier()
            self._lines += [
                "<symbol> , </symbol>",
                f"<identifier> {var_name} </identifier>",
            ]
            self._tokenizer.advance()  # skip `,`
            self._table.define(var_name, t, static_or_field)
        self._tokenizer.advance()  # skip `;`
        self._lines += ["<symbol> ; </symbol>"]

    def _compileType(self) -> str:
        if self._tokenizer.tokenType() == _TokenType.KEYWORD:
            t = self._tokenizer.keyword()
            self._lines += [f"<keyword> {t} </keyword>"]
        else:
            t = self._tokenizer.identifier()
            self._lines += [f"<identifier> {t} </identifier>"]
        self._tokenizer.advance()
        return t

    def compileSubroutine(self) -> None:
        self._table.startSubroutine()
        constructor_function_or_method = self._tokenizer.keyword()
        self._tokenizer.advance()
        self._compileType()
        subroutine_name = self._tokenizer.identifier()
        self._tokenizer.advance()  # skip subroutine name
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

        n_locals = self._table.varCount(_Kind.VAR)
        if constructor_function_or_method == "constructor":
            # TODO
            pass
        elif constructor_function_or_method == "function":
            self._writer.writeFunction(f"{self._class}.{subroutine_name}", n_locals)
        else:
            # TODO
            pass

        self.compileStatements()

        self._tokenizer.advance()  # skip `}`
        self._lines += [
            "<symbol> } </symbol>",
            "</subroutineBody>",
        ]

    def compileParameterList(self) -> None:
        self._lines += ["<parameterList>"]
        if not (self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == ")"):
            t = self._compileType()
            name = self._tokenizer.identifier()
            self._lines += [f"<identifier> {name} </identifier>"]
            self._tokenizer.advance()
            self._table.define(name, t, _Kind.ARG.value)
            self._output_identifier(_Kind.ARG.value, "defined", _Kind.ARG.value, self._table.indexOf(name))
            while self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == ",":
                self._lines += ["<symbol> , </symbol>"]
                self._tokenizer.advance()
                t = self._compileType()
                name = self._tokenizer.identifier()
                self._lines += [f"<identifier> {name} </identifier>"]
                self._table.define(name, t, _Kind.ARG.value)
                self._output_identifier(_Kind.ARG.value, "defined", _Kind.ARG.value, self._table.indexOf(name))
                self._tokenizer.advance()
        self._lines += ["</parameterList>"]

    def compileVarDec(self) -> None:
        self._lines += ["<keyword> var </keyword>"]
        self._tokenizer.advance()  # skip `var`
        t = self._compileType()
        var_name = self._tokenizer.identifier()
        self._tokenizer.advance()
        self._lines += [f"<identifier> {var_name} </identifier>"]
        self._table.define(var_name, t, _Kind.ARG.value)
        self._output_identifier(_Kind.ARG.value, "defined", _Kind.ARG.value, self._table.indexOf(var_name))
        while self._tokenizer.symbol() == ",":
            self._tokenizer.advance()  # skip `,`
            var_name = self._tokenizer.identifier()
            self._lines += [
                "<symbol> , </symbol>",
                f"<identifier> {var_name} </identifier>",
            ]
            self._tokenizer.advance()
            self._table.define(var_name, t, _Kind.ARG.value)
            self._output_identifier(_Kind.ARG.value, "defined", _Kind.ARG.value, self._table.indexOf(var_name))
        self._lines += ["<symbol> ; </symbol>"]
        self._tokenizer.advance()

    def compileStatements(self) -> None:
        self._lines += ["<statements>"]
        while self._tokenizer.tokenType() == _TokenType.KEYWORD and self._tokenizer.keyword() in ["let", "if", "while", "do", "return"]:
            keyword = self._tokenizer.keyword()
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
        self._tokenizer.advance()  # skip `subroutine_name`
        self._compileSubroutineCall(subroutine_name)
        self._writer.writePop(_Segment.TEMP, 0)
        self._lines += ["<symbol> ; </symbol>"]
        self._tokenizer.advance()  # skip `;`

    def _compileSubroutineCall(self, subroutine_name: str) -> None:
        if self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == ".":
            class_name_or_var_name = subroutine_name
            self._lines += [
                f"<identifier> {class_name_or_var_name} </identifier>",
                "<symbol> . </symbol>",
            ]
            self._tokenizer.advance()  # skip `.`
            subroutine_name = self._tokenizer.identifier()
            self._tokenizer.advance()  # skip `subroutine_name`
            full_subroutine_name = f"{class_name_or_var_name}.{subroutine_name}"
        else:
            full_subroutine_name = subroutine_name
        self._tokenizer.advance()  # skip `(`
        self._lines += [
            f"<identifier> {subroutine_name} </identifier>",
            "<symbol> ( </symbol>",
        ]
        num_expressions = self.compileExpressionList()
        self._lines += ["<symbol> ) </symbol>"]
        self._tokenizer.advance()  # skip `)`
        self._writer.writeCall(full_subroutine_name, num_expressions)

    def compileLet(self) -> None:
        self._tokenizer.advance()  # skip `let`
        var_name = self._tokenizer.identifier()
        self._tokenizer.advance()        
        self._lines += [
            "<keyword> let </keyword>",
            f"<identifier> {var_name} </identifier>",
        ]
        if self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == "[":
            self._lines += ["<symbol> [ </symbol>"]
            self._tokenizer.advance()
            self.compileExpression()
            self._lines += ["<symbol> ] </symbol>"]
            self._tokenizer.advance()
        self._lines += [
            "<symbol> = </symbol>",
        ]
        self._tokenizer.advance()  # skip `=`
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
        else:
            self._writer.writePush(_Segment.CONST, 0)
        self._tokenizer.advance()  # skip `;`
        self._lines += [
            "<symbol> ; </symbol>",
            "</returnStatement>",
        ]
        self._writer.writeReturn()

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
        self._tokenizer.advance()  # skip `}`
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
            if op == "<":
                op = "&lt;"
            elif op == ">":
                op = "&gt;"
            elif op == "&":
                op = "&amp;"
            self._lines += [f"<symbol> {op} </symbol>"]
            self.compileTerm()
            if op in ["+", "-", "&", "|", "<", ">", "="]:
                if op == "<":
                    command = _Command.LT
                elif op == ">":
                    command = _Command.GT
                elif op == "&":
                    command = _Command.AND
                elif op == "+":
                    command = _Command.ADD
                elif op == "-":
                    command = _Command.SUB
                elif op == "=":
                    command = _Command.EQ
                else:  # op == "|"
                    command = _Command.OR
                self._writer.writeArithmetic(command.value)
            else:  # op in ["*", "/"]
                if op == "*":
                    f_name = "Math.multiply"
                else:
                    f_name = "Math.divide"
                self._writer.writeCall(f_name, 2)
        self._lines += ["</expression>"]

    def compileTerm(self) -> None:
        self._lines += ["<term>"]

        current_token_type = self._tokenizer.tokenType()
        if current_token_type == _TokenType.SYMBOL:
            current_value = self._tokenizer.symbol()
        elif current_token_type == _TokenType.IDENTIFIER:
            current_value = self._tokenizer.identifier()
        elif current_token_type == _TokenType.INT_CONST:
            current_value = self._tokenizer.intVal()
        elif current_token_type == _TokenType.STRING_CONST:
            current_value = self._tokenizer.stringVal()
        else:
            current_value = self._tokenizer.keyword()
        self._tokenizer.advance()

        if current_token_type == _TokenType.IDENTIFIER and self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() in [".", "("]:
            self._compileSubroutineCall(current_value)
        else:
            if current_token_type == _TokenType.SYMBOL and current_value == "(":
                self._lines += [f"<symbol> ( </symbol>"]
                self.compileExpression()
                self._lines += [f"<symbol> ) </symbol>"]
                self._tokenizer.advance()  # skip `)`
            elif current_token_type == _TokenType.SYMBOL and current_value in ["-", "~"]:
                self._lines += [f"<symbol> {current_value} </symbol>"]
                self.compileTerm()
                if current_value == "-":
                    command = _Command.NEG
                else:
                    command = _Command.NOT
                self._writer.writeArithmetic(command)
            elif current_token_type == _TokenType.IDENTIFIER:
                self._lines += [f"<identifier> {current_value} </identifier>"]
                if self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == "[":
                    self._lines += [f"<symbol> [ </symbol>"]
                    self._tokenizer.advance()
                    self.compileExpression()
                    self._lines += [f"<symbol> ] </symbol>"]
                    self._tokenizer.advance()  # skip `]`
            elif current_token_type == _TokenType.KEYWORD:
                self._lines += [f"<keyword> {current_value} </keyword>"]
            elif current_token_type == _TokenType.INT_CONST:
                self._lines += [f"<integerConstant> {current_value} </integerConstant>"]
                self._writer.writePush(_Segment.CONST, int(current_value))
            elif current_token_type == _TokenType.STRING_CONST:
                self._lines += [f"<stringConstant> {current_value} </stringConstant>"]
        self._lines += ["</term>"]

    def compileExpressionList(self) -> int:
        self._lines += ["<expressionList>"]
        num_expressions = 0
        if not (self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == ")"):
            self.compileExpression()
            num_expressions += 1
            while self._tokenizer.tokenType() == _TokenType.SYMBOL and self._tokenizer.symbol() == ",":
                self._lines += ["<symbol> , </symbol>"]
                self._tokenizer.advance()
                self.compileExpression()
                num_expressions += 1
        self._lines += ["</expressionList>"]
        return num_expressions


class SymbolTable:
    def __init__(self) -> None:
        self._table_for_class = {}
        self._table_for_subroutine = {}
        self._subroutine_started = False
        self._indices_for_class = {}
        self._indices_for_subroutine = {}
        for kind in _Kind:
            self._indices_for_class[kind.value] = 0
        self._reset_table_for_subroutine()
    
    def _reset_table_for_subroutine(self) -> None:
        self._table_for_subroutine = {}
        self._indices_for_subroutine = {}
        for kind in _Kind:
            self._indices_for_subroutine[kind.value] = 0

    def startSubroutine(self) -> None:
        self._subroutine_started = True
        self._reset_table_for_subroutine()

    def define(self, name: str, t: str, kind: _Kind) -> None:
        if self._subroutine_started:
            table = self._table_for_subroutine
            indices = self._indices_for_subroutine
        else:
            table = self._table_for_class
            indices = self._indices_for_class
        index = indices[kind]
        table[name] = {
            "type": t,
            "kind": kind,
            "index": index,
        }
        indices[kind] = index + 1

    def varCount(self, kind: _Kind) -> int:
        count = 0
        if self._subroutine_started:
            table = self._table_for_subroutine
        else:
            table = self._table_for_class
        for v in table.values():
            if v["kind"] == kind:
                count += 1
        return count

    def kindOf(self, name: str) -> Optional[_Kind]:
        entry = self._fine(name)
        if entry:
            return entry["kind"]
        else:
            return None

    def typeOf(self, name: str) -> str:
        self._fine(name)["type"]

    def indexOf(self, name: str) -> int:
        return self._find(name)["index"]

    def _find(self, name: str) -> Optional[Dict[str, Any]]:
        if self._subroutine_started:
            table = self._table_for_subroutine
        else:
            table = self._table_for_class
        return table.get(name, None)


class VMWriter:
    def __init__(self, output_file: str) -> None:
        self._writer = open(output_file, "w")

    def writePush(self, segment: _Segment, index: int) -> None:
        self._writer.write(f"  push {segment.value} {index}")
        self._writer.write("\n")

    def writePop(self, segment: _Segment, index: int) -> None:
        self._writer.write(f"  pop {segment.value} {index}")
        self._writer.write("\n")

    def writeArithmetic(self, command: _Command) -> None:
        self._writer.write(f"  {command}")
        self._writer.write("\n")

    def writeLabel(self, label: str) -> None:
        self._writer.write(f"{label}:")
        self._writer.write("\n")

    def writeGoto(self, label: str) -> None:
        self._writer.write(f"  goto {label}")
        self._writer.write("\n")

    def writeIf(self, label: str) -> None:
        self._writer.write(f"  if-goto {label}")
        self._writer.write("\n")

    def writeCall(self, name: str, nArgs: int) -> None:
        self._writer.write(f"  call {name} {nArgs}")
        self._writer.write("\n")

    def writeFunction(self, name: str, nLocals: int) -> None:
        self._writer.write(f"function {name} {nLocals}")
        self._writer.write("\n")

    def writeReturn(self) -> None:
        self._writer.write("  return")
        self._writer.write("\n")

    def close(self) -> None:
        self._writer.close()


def main():
    input_file_or_dir = sys.argv[1]
    if os.path.isfile(input_file_or_dir):
        input_files = [input_file_or_dir]
    else:
        dir = input_file_or_dir
        input_files = [f"{dir}/{f}" for f in os.listdir(dir) if f.endswith(".jack")]
    for input_file in input_files:
        output_file_prefix = f"{os.path.splitext(input_file)[0]}"
        CompilationEngine(input_file, output_file_prefix)


if __name__ == "__main__":
    main()
