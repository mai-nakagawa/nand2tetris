import os
import re
import sys
from enum import Enum, auto
from typing import List, Tuple


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
        print(f"without_comments:{s}")
        s_list = self._split_by_double_quotes(s)
        print(f"split_by_double_quotes:{s_list}")
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
        print(f"s:{s}")
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
            print(f"token:{s}")
            if s in ["class", "constructor", 'function', 'method', 'field', 'static', 'var',
                        'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let',
                        'do', 'if', 'else', 'while', 'return']:
                tokens.append((s, _TokenType.KEYWORD))
            elif s in ['{', '}', '(', ')', '[', ']', '.',  ',', ';', '+',
                        '-', '*', '/', '&', '|', '<', '>', '=', '~']:
                print(f"adding symbol:{s}")
                tokens.append((s, _TokenType.SYMBOL))
            elif INTEGERS.match(s):
                tokens.append((int(s), _TokenType.INT_CONST))
            else:
                print(f"adding identifier:{s}")
                tokens.append((s, _TokenType.IDENTIFIER))
            return tokens
        for i, new_s in enumerate(split):
            print(f"i:{i} new_s:{new_s} delimiter:{delimiter}")
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
    pass


def main():
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
