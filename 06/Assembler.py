import sys
from enum import Enum, auto
from typing import Dict


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
                l = l.split("//")[0].strip()
                if not l:
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
        l = self._lines[self._lineno]
        if l[0] == "@":
            return l[1:]
        else:
            return l[1:-1]

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
        return f"{d1}{d2}{d3}"

    def comp(self, mnemonic: str) -> str:
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


class SymbolTable:
    def __init__(self):
        self._table: Dict[str, int] = {
            "SP": 0,
            "LCL": 1,
            "ARG": 2,
            "THIS": 3,
            "THAT": 4,
            "R0": 0,
            "R1": 1,
            "R2": 2,
            "R3": 3,
            "R4": 4,
            "R5": 5,
            "R6": 6,
            "R7": 7,
            "R8": 8,
            "R9": 9,
            "R10": 10,
            "R11": 11,
            "R12": 12,
            "R13": 13,
            "R14": 14,
            "R15": 15,
            "SCREEN": 16384,
            "KBD": 24576,
        }

    def addEntry(self, symbol: str, address: int) -> None:
        self._table[symbol] = address

    def contains(self, symbol: str) -> bool:
        return symbol in self._table.keys()

    def getAddress(self, symbol: str) -> int:
        return self._table[symbol]


def main():
    input_file = sys.argv[1]
    symbol_table = _first_pass(input_file)
    _second_pass(input_file, symbol_table)


def _first_pass(input_file: str) -> Dict[str, int]:
    parser = Parser(input_file)
    symbol_table = SymbolTable()
    rom_addr = 0
    while parser.hasMoreCommands():
        if parser.commandType() == _Command.L_COMMAND:
            symbol_table.addEntry(parser.symbol(), rom_addr)
        else:
            rom_addr += 1
        parser.advance()
    return symbol_table


def _second_pass(input_file: str, symbol_table: Dict[str, int]) -> None:
    parser = Parser(input_file)
    code = Code()
    next_ram_addr = 16
    while parser.hasMoreCommands():
        if parser.commandType() == _Command.C_COMMAND:
            dest = code.dest(parser.dest())
            comp = code.comp(parser.comp())
            jump = code.jump(parser.jump())
            print(f"111{comp}{dest}{jump}")
        elif parser.commandType() == _Command.A_COMMAND:
            s = parser.symbol()
            if symbol_table.contains(s):
                value = symbol_table.getAddress(s)
            elif s[0] in "0123456789":
                value = s
            else:
                symbol_table.addEntry(s, next_ram_addr)
                value = next_ram_addr
                next_ram_addr += 1
            print("0{:015b}".format(int(value), 2))
        parser.advance()


if __name__ == "__main__":
    main()
