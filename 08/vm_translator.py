import os
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


_SEGMENT_TO_LABEL = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
}

_SEGMENT_BASE = {
    "pointer": 3,
    "temp": 5,
}


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
        if l in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]:
            return _Command.C_ARITHMETIC
        elif l.startswith("push "):
            return _Command.C_PUSH
        elif l.startswith("pop "):
            return _Command.C_POP
        elif l.startswith("label "):
            return _Command.C_LABEL
        elif l.startswith("if-goto "):
            return _Command.C_IF
        elif l.startswith("goto "):
            return _Command.C_GOTO
        elif l.startswith("function "):
            return _Command.C_FUNCTION
        elif l.startswith("return"):
            return _Command.C_RETURN
        elif l.startswith("call "):
            return _Command.C_CALL

    def arg1(self) -> str:
        args = self._lines[self._lineno].split(" ")
        if self.commandType() == _Command.C_ARITHMETIC:
            return args[0]
        else:
            return args[1]

    def arg2(self) -> str:
        args = self._lines[self._lineno].split(" ")
        return args[2]


class CodeWriter:
    def __init__(self, file: str):
        self._writer = open(file, "w")
        self._label_id = 1

    def setFileName(self, filename: str) -> None:
        self._filename = os.path.splitext(os.path.basename(filename))[0]

    def writeArithmetic(self, command: str) -> None:
        writelines = []
        if command in ["neg", "not"]:
            if command == "not":
                writelines += [
                    f"@SP  // {command}",
                    "A=M-1",
                    "M=!M",
                ]
            else:  # neg
                writelines += [
                    f"@SP  // {command}",
                    "A=M-1",
                    "M=-M",
                ]
        else:
            writelines += [
                f"@SP  // {command}",
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
            writelines = [
                f"@{index}  // push {segment} {index}",
                "D=A",
            ]
            if segment in ["temp", "pointer"]:
                writelines += [
                    f"@{_SEGMENT_BASE[segment] + index}",
                    "D=M",
                ]
            elif segment == "static":
                writelines += [
                    f"@{self._filename}.{index}",
                    "D=M",
                ]
            elif segment != "constant":
                writelines += [
                    f"@{_SEGMENT_TO_LABEL[segment]}",
                    "A=M+D",
                    "D=M",
                ]
            writelines += [
                "@SP",
                "A=M",
                "M=D",
                "@SP",
                "M=M+1",
            ]
        else:  # C_POP
            if segment in ["temp", "pointer"]:
                writelines = [
                    f"@{_SEGMENT_BASE[segment] + index}  // pop {segment} {index}",
                    "D=A",
                ]
            elif segment == "static":
                writelines = [
                    f"@{self._filename}.{index}  // pop {segment} {index}",
                    "D=A",
                ]
            else:
                writelines = [
                    f"@{index}  // pop {segment} {index}",
                    "D=A",
                    f"@{_SEGMENT_TO_LABEL[segment]}",
                    "D=M+D",
                ]
            writelines += [
                "@SP",
                "A=M",
                "M=D",
                "A=A-1",
                "D=M",
                "A=A+1",
                "A=M",
                "M=D",
                "@SP",
                "M=M-1",
            ]
        self._writer.write("\n".join(writelines))
        self._writer.write("\n")

    def writeInit(self) -> None:
        self._writer.write("\n".join([
            # SP=256
            "@256  // initialize",
            "D=A",
            "@SP",
            "M=D",
        ]))
        self._writer.write("\n")
        self.writeCall("Sys.init", 0)

    def writeLabel(self, label: str) -> None:
        self._writer.write("\n".join([
            f"({self._filename}.{label})  // label {label}",
        ]))
        self._writer.write("\n")

    def writeGoto(self, label: str) -> None:
        self._writer.write("\n".join([
            f"@{self._filename}.{label}  // goto {label}",
            "0;JMP",
        ]))
        self._writer.write("\n")

    def writeIf(self, label: str) -> None:
        self._writer.write("\n".join([
            f"@SP  // if-goto {label}",
            "M=M-1",
            "A=M",
            "D=M",
            f"@{self._filename}.{label}",
            "D;JNE",
        ]))
        self._writer.write("\n")

    def writeCall(self, functionName: str, numArgs: int) -> None:
        self._writer.write("\n".join([
            # push return-address
            f"@{functionName}.RETURN_ADDRESS.{self._label_id}  // call {functionName} {numArgs}",
            "D=A",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",

            # push LCL
            f"@LCL",
            "D=M",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",

            # push ARG
            f"@ARG",
            "D=M",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",

            # push THIS
            f"@THIS",
            "D=M",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",

            # push THAT
            f"@THAT",
            "D=M",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",

            # ARG = SP - n - 5
            "@SP",
            "D=M",
            f"@{numArgs}",
            "D=D-A",
            "@5",
            "D=D-A",
            "@ARG",
            "M=D",

            # LCL = SP
            "@SP",
            "D=M",
            "@LCL",
            "M=D",

            # goto f
            f"@{functionName}",
            "0;JMP",

            # (return-address)
            f"({functionName}.RETURN_ADDRESS.{self._label_id})",
        ]))
        self._writer.write("\n")
        self._label_id += 1

    def writeFunction(self, functionName: str, numLocals: int) -> None:
        writelines = [
            f"({functionName}) // function {functionName} {numLocals}",
        ]
        for _ in range(numLocals):
            writelines += [
                # push 0
                "@SP",
                "A=M",
                "M=0",
                "@SP",
                "M=M+1",
            ]
        self._writer.write("\n".join(writelines))
        self._writer.write("\n")

    def writeReturn(self) -> None:
        writelines = [
            # FRAME (R13) = LCL
            "@LCL  // return",
            "D=M",
            "@R13",
            "M=D",

            # RET (R14) = *(FRAME - 5)
            "@5",
            "A=D-A",
            "D=M",
            "@R14",
            "M=D",

            # *ARG = pop()
            "@SP",
            "A=M-1",
            "D=M",
            "@ARG",
            "A=M",
            "M=D",

            # SP = ARG + 1
            "@ARG",
            "D=M",
            "@SP",
            "M=D+1",

            # THAT = *(FRAME-1)
            "@R13",
            "A=M-1",
            "D=M",
            "@THAT",
            "M=D",

            # THIS = *(FRAME-2)
            "@R13",
            "A=M-1",
            "A=A-1",
            "D=M",
            "@THIS",
            "M=D",

            # ARG = *(FRAME-3)
            "@R13",
            "A=M-1",
            "A=A-1",
            "A=A-1",
            "D=M",
            "@ARG",
            "M=D",

            # LCL = *(FRAME-4)
            "@R13",
            "A=M-1",
            "A=A-1",
            "A=A-1",
            "A=A-1",
            "D=M",
            "@LCL",
            "M=D",

            # TODO; goto RET
            "@R14",
            "A=M",
            "0;JMP",
        ]
        self._writer.write("\n".join(writelines))
        self._writer.write("\n")

    def close(self) -> None:
        self._writer.close()


def main():
    input_file_or_dir = sys.argv[1]
    output_file = sys.argv[2]
    if os.path.isfile(input_file_or_dir):
        input_files = [input_file_or_dir]
    else:
        dir = input_file_or_dir
        input_files = [f"{dir}/{f}" for f in os.listdir(dir) if f.endswith("vm")]
    code_writer = CodeWriter(output_file)
    code_writer.writeInit()
    for input_file in input_files:
        parser = Parser(input_file)
        code_writer.setFileName(input_file)
        while parser.hasMoreCommands():
            command_type = parser.commandType()
            if command_type == _Command.C_ARITHMETIC:
                arg1 = parser.arg1()
                code_writer.writeArithmetic(arg1)
            elif command_type in [_Command.C_PUSH, _Command.C_POP]:
                arg1 = parser.arg1()
                arg2 = parser.arg2()
                code_writer.writePushPop(command_type, arg1, int(arg2))
            elif command_type == _Command.C_LABEL:
                arg1 = parser.arg1()
                code_writer.writeLabel(arg1)
            elif command_type == _Command.C_IF:
                arg1 = parser.arg1()
                code_writer.writeIf(arg1)
            elif command_type == _Command.C_GOTO:
                arg1 = parser.arg1()
                code_writer.writeGoto(arg1)
            elif command_type == _Command.C_FUNCTION:
                arg1 = parser.arg1()
                arg2 = parser.arg2()
                code_writer.writeFunction(arg1, int(arg2))
            elif command_type == _Command.C_RETURN:
                code_writer.writeReturn()
            elif command_type == _Command.C_CALL:
                arg1 = parser.arg1()
                arg2 = parser.arg2()
                code_writer.writeCall(arg1, int(arg2))
            parser.advance()
    code_writer.close()


if __name__ == "__main__":
    main()
