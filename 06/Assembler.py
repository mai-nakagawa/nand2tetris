import sys
from enum import Enum, auto


def main():
    parser = Parser(sys.argv[1])
    code = Code()
    while parser.hasMoreCommands():
        print(f"line: {parser._lines[parser._lineno]}")
        if parser.commandType() == _Command.C_COMMAND:
            dest = code.dest(parser.dest())
            comp = code.comp(parser.comp())
            jump = code.jump(parser.jump())
            print(f"111{comp}{dest}{jump}")
        else:
            print(f"parser.symbol: {parser.symbol()}")
            print(f"0{int(parser.symbol()):015b}".format(int(parser.symbol()), 2))
        parser.advance()


class _Command(Enum):
    A_COMMAND = auto()
    C_COMMAND = auto()
    L_COMMAND = auto()


class Parser:
    def __init__(self, p: str):
        self._lineno = 0
        with open(p) as f:
            self._lines = []
            for l in f.readlines():
                l = l.strip()
                if not l:
                    continue
                if l.startswith("//"):
                    continue
                self._lines.append(l)

    def hasMoreCommands(self) -> bool:
        if len(self._lines) > self._lineno:
            return True
        else:
            return False

    def advance(self) -> None:
        self._lineno += 1

    def commandType(self) -> _Command:
        if self._lines[self._lineno][0] == "@":
            return _Command.A_COMMAND
        elif self._lines[self._lineno][0] == "(":
            return _Command.L_COMMAND
        else:
            return _Command.C_COMMAND

    def symbol(self) -> str:
        return self._lines[self._lineno][1:]

    def dest(self) -> str:
        mnemonics = self._lines[self._lineno].split("=")
        if len(mnemonics) == 1:
            return ""
        else:
            return mnemonics[0]

    def comp(self) -> str:
        dest_and_comp = self._lines[self._lineno].split(";")[0]
        dest_and_comp = dest_and_comp.split("=")
        if len(dest_and_comp) == 1:
            return dest_and_comp[0]
        else:
            return dest_and_comp[1]

    def jump(self) -> str:
        dest_comp_and_jump = self._lines[self._lineno].split(";")
        if len(dest_comp_and_jump) == 1:
            return ""
        else:
            return dest_comp_and_jump[1]


class Code:
    def dest(self, mnemonic: str) -> str:
        print(f"dest mnemonic: {mnemonic}")
        d1 = 0
        d2 = 0
        d3 = 0
        for c in mnemonic:
            if c == "A":
                d1 = 1
            elif c == "D":
                d2 = 1
            elif c == "M":
                d3 = 1
        print(f"dest returns: {d1}{d2}{d3}")
        return f"{d1}{d2}{d3}"

    def comp(self, mnemonic: str) -> str:
        print(f"comp mnemonic: {mnemonic}")
        if mnemonic == "0":
            return "0101010"
        elif mnemonic == "1":
            return "0111111"
        elif mnemonic == "-1":
            return "0111010"
        elif mnemonic == "D":
            return "0001100"
        elif mnemonic == "A":
            return "0110000"
        elif mnemonic == "!D":
            return "0001101"
        elif mnemonic == "!A":
            return "0110001"
        elif mnemonic == "-D":
            return "0001111"
        elif mnemonic == "-A":
            return "0110001"
        elif mnemonic == "D+1":
            return "0011111"
        elif mnemonic == "A+1":
            return "0110111"
        elif mnemonic == "D-1":
            return "0001110"
        elif mnemonic == "A-1":
            return "0110010"
        elif mnemonic == "D+A":
            return "0000010"
        elif mnemonic == "D-A":
            return "0010011"
        elif mnemonic == "A-D":
            return "0000111"
        elif mnemonic == "D&A":
            return "0000000"
        elif mnemonic == "D|A":
            return "0010101"
        elif mnemonic == "M":
            return "1110000"
        elif mnemonic == "!M":
            return "1110001"
        elif mnemonic == "-M":
            return "1110011"
        elif mnemonic == "M+1":
            return "1110111"
        elif mnemonic == "M-1":
            return "1110010"
        elif mnemonic == "D+M":
            return "1000010"
        elif mnemonic == "D-M":
            return "1010011"
        elif mnemonic == "M-D":
            return "1000111"
        elif mnemonic == "D&M":
            return "1000000"
        elif mnemonic == "D|M":
            return "1010101"

    def jump(self, mnemonic: str) -> str:
        if mnemonic == "JGT":
            return "001"
        elif mnemonic == "JEQ":
            return "010"
        elif mnemonic == "JGE":
            return "011"
        elif mnemonic == "JLT":
            return "100"
        elif mnemonic == "JNE":
            return "101"
        elif mnemonic == "JLE":
            return "110"
        elif mnemonic == "JMP":
            return "111"
        else:
            return "000"


if __name__ == "__main__":
    main()
