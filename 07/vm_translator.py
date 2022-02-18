import sys
from enum import Enum, auto


class _Command(Enum):
    C_ARITHMETIC = auto()
    C_PUSH = auto()
    C_POP = auto()
    C_LABEL = auto()
    C_GOTO = auto()
    C_IF = auto()
    C_FUNCTION = auto()
    C_RETURN = auto()
    C_CALL = auto()


class Parser:
    def __init__(self, file: str):
        self._lineno = 0
        self._lines = []
        with open(file) as f:
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
        l = self._lines[self._lineno]
        print(f"l:{l}")
        if l in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]:
            return _Command.C_ARITHMETIC
        elif l.startswith("push "):
            return _Command.C_PUSH

    def arg1(self) -> str:
        args = self._lines[self._lineno].split(" ")
        print(f"arg1() args:{args}")
        if self.commandType() == _Command.C_ARITHMETIC:
            return args[0]
        else:
            return args[1]

    def arg2(self) -> str:
        args = self._lines[self._lineno].split(" ")
        print(f"arg2() args:{args}")
        return args[2]


class CodeWriter:
    def __init__(self, file: str):
        self._writer = open(file, "w")
        self._label_id = 1
        self._initialize_sp()

    def _initialize_sp(self) -> None:
        self._writer.write("\n".join([
            "// initialize SP",
            "@256",
            "D=A",
            "@SP",
            "M=D",
            "",
        ]))

    def setFileName(self, filename: str) -> None:
        pass

    def writeArithmetic(self, command: str) -> None:
        writelines = [f"// {command}"]
        if command in ["neg", "not"]:
            print(f"command: {command}")
            if command == "not":
                writelines += [
                    "@SP",
                    "A=M-1",
                    "M=!M",
                ]
            else:  # neg
                writelines += [
                    "@SP",
                    "A=M-1",
                    "M=-M",
                ]
        else:
            writelines += [
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                "@SP",
                "A=M-1",
            ]
            if command == "add":
                writelines.append("M=M+D")
            elif command == "sub":
                writelines.append("M=M-D")
            elif command == "and":
                writelines.append("M=M&D")
            elif command == "or":
                writelines.append("M=M|D")
            else:
                writelines += [
                    "D=M-D",
                    f"@TRUE{self._label_id}",
                ]
                if command == "eq":
                    writelines += [
                        "D;JEQ",
                        f"@FALSE{self._label_id}",
                        "D;JNE",
                    ]
                elif command == "gt":
                    writelines += [
                        "D;JGT",
                        f"@FALSE{self._label_id}",
                        "D;JLE",
                    ]
                else:  # lt
                    writelines += [
                        "D;JLT",
                        f"@FALSE{self._label_id}",
                        "D;JGE",
                    ]
                writelines += [
                    f"(TRUE{self._label_id})",
                    "D=-1",
                    "@SP",
                    "A=M-1",
                    "M=D",
                    f"@END{self._label_id}",
                    "0;JMP",
                    f"(FALSE{self._label_id})",
                    "@SP",
                    "A=M-1",
                    "M=0",
                    f"@END{self._label_id}",
                    "0;JMP",
                    f"(END{self._label_id})",
                ]
                self._label_id += 1
        self._writer.write("\n".join(writelines))
        self._writer.write("\n")

    def writePushPop(self, command: _Command, segment: str, index: int) -> None:
        if command == _Command.C_PUSH:
            self._writer.write("\n".join([
                f"// push {index}",
                f"@{index}",
                "D=A",
                "@SP",
                "A=M",
                "M=D",
                "@SP",
                "M=M+1",
                "",
            ]))

    def close(self) -> None:
        close(self._writer)


def main():
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    parser = Parser(input_file)
    code_writer = CodeWriter(output_file)
    while parser.hasMoreCommands():
        command_type = parser.commandType()
        if command_type == _Command.C_ARITHMETIC:
            arg1 = parser.arg1()
            print(f"arg1:{arg1}")
            code_writer.writeArithmetic(arg1)
        elif command_type == _Command.C_PUSH:
            arg1 = parser.arg1()
            arg2 = parser.arg2()
            print(f"arg1:{arg1} arg2:{arg2}")
            code_writer.writePushPop(_Command.C_PUSH, arg1, int(arg2))
        parser.advance()


if __name__ == "__main__":
    main()
