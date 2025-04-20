import collections
import copy
import csv
import enum
import io
import os
import pathlib
import re
from dataclasses import dataclass
from typing import IO, Any, Literal, Optional

from dqmj1_randomizer.randomize.character_encoding import CharacterEncoding

ENDIANESS: Literal["little"] = "little"

STRING_END = 0xFF
STRING_END_PADDING = 0xCC

LabelDict = dict[str, int]


class ArgumentType(enum.Enum):
    U32 = enum.auto()
    String = enum.auto()
    AsciiString = enum.auto()
    Bytes = enum.auto()
    ValueLocation = enum.auto()
    InstructionLocation = enum.auto()


class ValueLocation(enum.Enum):
    Zero = 0
    One = 1
    Constant = 2
    Three = 3

    def to_script(self) -> str:
        if self == ValueLocation.Zero:
            return "Pool_0"
        elif self == ValueLocation.One:
            return "Pool_1"
        elif self == ValueLocation.Constant:
            return "Const"
        elif self == ValueLocation.Three:
            return "Pool_3"

    @staticmethod
    def from_script(name: str) -> "ValueLocation":
        if name == "Pool_0":
            return ValueLocation.Zero
        elif name == "Pool_1":
            return ValueLocation.One
        elif name == "Const":
            return ValueLocation.Constant
        elif name == "Pool_3":
            return ValueLocation.Three

        raise ValueError(f'Unrecognized ValueLocation name: "{name}"')


at = ArgumentType


@dataclass
class RawInstruction:
    instruction_type: int
    data: bytes

    @staticmethod
    def from_evt(input_stream: IO[bytes]) -> Optional["RawInstruction"]:
        type_bytes = input_stream.read(4)
        if len(type_bytes) != 4:
            return None

        instruction_type = int.from_bytes(type_bytes, ENDIANESS)
        length = int.from_bytes(input_stream.read(4), ENDIANESS)

        data = input_stream.read(length - 8)

        return RawInstruction(instruction_type=instruction_type, data=data)


@dataclass
class InstructionType:
    type_id: int
    name: str
    arguments: list[ArgumentType]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "InstructionType":
        type_id = int(d["Id"][2:], 16)
        name = d["Name"]
        arguments = [
            ArgumentType[arg.strip()]
            for arg in d["Arguments"][1:-1].split(",")
            if arg.strip() != ""
        ]

        return InstructionType(
            type_id=type_id,
            name=name,
            arguments=arguments,
        )


# Load the instruction type info from csv file
CURRENT_DIRECTORY = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
with open(CURRENT_DIRECTORY / ".." / "data" / "event_instructions.csv") as input_stream:
    reader = csv.DictReader(input_stream)
    INSTRUCTION_TYPES = [InstructionType.from_dict(line) for line in reader]

INSTRUCTION_TYPES_BY_TYPE = {
    cmd_type.type_id: cmd_type for cmd_type in INSTRUCTION_TYPES
}
INSTRUCTION_TYPES_BY_NAME = {cmd_type.name: cmd_type for cmd_type in INSTRUCTION_TYPES}


@dataclass
class Instruction:
    instruction_type: InstructionType
    arguments: list[Any]

    @property
    def type_id(self) -> int:
        return self.instruction_type.type_id

    def length(self, character_encoding: CharacterEncoding) -> int:
        stream = io.BytesIO()
        self.write_evt(stream, collections.defaultdict(lambda: 0), character_encoding)

        return len(stream.getbuffer())

    @staticmethod
    def from_evt(
        input_stream: IO[bytes], character_encoding: CharacterEncoding
    ) -> Optional[tuple["Instruction", LabelDict]]:
        raw = RawInstruction.from_evt(input_stream)
        if raw is None:
            return None

        results = Instruction.from_raw(
            raw=raw,
            instruction_type=Instruction.get_instruction_type(raw.instruction_type),
            character_encoding=character_encoding,
        )
        if results is not None:
            instruction, _ = results
            if instruction.length(character_encoding) != len(raw.data) + 8:
                stream = io.BytesIO()
                instruction.write_evt(
                    stream, collections.defaultdict(lambda: 0), character_encoding
                )

                bs = stream.getbuffer()
                raise ValueError(
                    f"{instruction.length(character_encoding)} != {len(raw.data) + 8} for instruction: {instruction}\nwritten={[hex(b) for b in bs[8:]]!s}\nraw=    {[hex(b) for b in raw.data]}"
                )

        return results

    @staticmethod
    def get_instruction_type_by_name(instruction_name: str) -> InstructionType:
        instructions_by_name = Instruction.instructions_by_name()
        if instruction_name in instructions_by_name:
            return instructions_by_name[instruction_name]

        raise ValueError(f'Unrecognized instruction: "{instruction_name}"')

    @staticmethod
    def get_instruction_type(instruction_id: int) -> InstructionType:
        instructions_by_type = Instruction.instructions_by_type_id()
        if instruction_id in instructions_by_type:
            return instructions_by_type[instruction_id]

        return InstructionType(instruction_id, "UNKNOWN", [at.Bytes])

    def write_evt(
        self,
        output_stream: IO[bytes],
        labels: LabelDict,
        character_encoding: CharacterEncoding,
    ) -> None:
        instruction_id_bytes = self.type_id.to_bytes(4, ENDIANESS)

        data = []
        for argument, argument_type in zip(
            self.arguments, self.instruction_type.arguments
        ):
            if argument_type == at.Bytes:
                for b in argument:
                    data.append(b)
            elif argument_type == at.AsciiString:
                for c in argument:
                    data.append(ord(c))
                data.append(0x00)

                num_string_bytes = len(argument) + 1
                num_padding_bytes = (
                    0 if num_string_bytes % 4 == 0 else 4 - num_string_bytes % 4
                )
                for _ in range(0, num_padding_bytes):
                    data.append(0xCC)
            elif argument_type == at.U32:
                for b in argument.to_bytes(4, ENDIANESS):
                    data.append(b)
            elif argument_type == at.ValueLocation:
                assert isinstance(argument, ValueLocation)
                for b in argument.value.to_bytes(4, ENDIANESS):
                    data.append(b)
            elif argument_type == at.InstructionLocation:
                assert isinstance(argument, str)
                position = labels[argument]

                for b in position.to_bytes(4, ENDIANESS):
                    data.append(b)
            elif argument_type == at.String:
                string_bytes = character_encoding.string_to_bytes(argument)
                for b in string_bytes:
                    data.append(b)

                num_padding_bytes = (
                    0 if len(string_bytes) % 4 == 0 else 4 - len(string_bytes) % 4
                )
                for _ in range(0, num_padding_bytes):
                    data.append(0xCC)
            else:
                raise NotImplementedError(f"{argument_type}")

        length = len(data) + 8
        length_bytes = length.to_bytes(4, ENDIANESS)

        data_bytes = bytearray(data)

        output_stream.write(instruction_id_bytes)
        output_stream.write(length_bytes)
        output_stream.write(data_bytes)

    @staticmethod
    def from_raw(
        raw: RawInstruction,
        instruction_type: InstructionType,
        character_encoding: CharacterEncoding,
    ) -> Optional[tuple["Instruction", LabelDict]]:
        arguments: list[Any] = []

        labels = {}

        current = 0
        for argument_type in instruction_type.arguments:
            if argument_type == at.Bytes:
                arguments.append(raw.data[current:])
                current += len(raw.data)
            elif argument_type == at.AsciiString:
                string_bytes = raw.data[current:]
                string_character_bytes = []
                for b in string_bytes:
                    if b == 0x00:
                        break

                    string_character_bytes.append(b)

                arguments.append("".join(chr(b) for b in string_character_bytes))
                current += len(string_bytes)
            elif argument_type == at.String:
                string = character_encoding.bytes_to_string(raw.data[current:])

                arguments.append(string)
                current += len(raw.data)
            elif argument_type == at.U32:
                value = int.from_bytes(raw.data[current : current + 4], ENDIANESS)

                arguments.append(value)
                current += 4
            elif argument_type == at.ValueLocation:
                value = int.from_bytes(raw.data[current : current + 4], ENDIANESS)

                arguments.append(ValueLocation(value))
                current += 4
            elif argument_type == at.InstructionLocation:
                value = int.from_bytes(raw.data[current : current + 4], ENDIANESS)

                label = f"0x{value:x}"
                labels[label] = value

                arguments.append(label)
                current += 4
            else:
                raise AssertionError(f"Unhandled arg type: {argument_type}")

        return (
            Instruction(instruction_type=instruction_type, arguments=arguments),
            labels,
        )

    @staticmethod
    def from_script(line: str) -> Optional["Instruction"]:
        # Split on spaces, but ignore spaces in quotes
        # https://stackoverflow.com/questions/2785755/how-to-split-but-ignore-separators-in-quoted-strings-in-python
        PATTERN = re.compile(r"""((?:[^ "']|"[^"]*"|'[^']*')+)""")

        parts = PATTERN.split(line.strip())
        parts = [p for p in parts if len(p.strip()) > 0]

        instruction_name = parts[0]
        instruction_type = Instruction.get_instruction_type_by_name(instruction_name)

        arguments: list[Any] = []
        for i, arg_type in enumerate(instruction_type.arguments):
            try:
                if arg_type == at.ValueLocation:
                    arguments.append(ValueLocation.from_script(parts[i + 1]))
                elif arg_type == at.InstructionLocation:
                    arguments.append(parts[i + 1])
                else:
                    arguments.append(eval(parts[i + 1]))
            except IndexError as e:
                raise ValueError(f"Failed to parse index {i + 1} in: {parts}") from e

        return Instruction(instruction_type=instruction_type, arguments=arguments)

    def to_script(self) -> str:
        stream = io.StringIO()
        stream.write(f"{self.instruction_type.name:<12}")

        if len(self.arguments) > 0:
            stream.write(" ")
            stream.write(
                " ".join(
                    (
                        Instruction.value_to_script_literal(a, t)
                        for i, (a, t) in enumerate(
                            zip(self.arguments, self.instruction_type.arguments)
                        )
                    )
                )
            )

        return stream.getvalue().rstrip()

    @staticmethod
    def value_to_script_literal(
        value: Any,
        value_type: ArgumentType,
    ) -> str:
        if value_type == at.U32:
            return hex(value)
        elif value_type == at.Bytes:
            return bytes_repr(value)
        elif value_type == at.ValueLocation:
            assert isinstance(value, ValueLocation)
            return value.to_script()
        elif value_type == at.InstructionLocation:
            return str(value)
        elif value_type == at.String or value_type == at.AsciiString:
            # TODO: implement this more properly
            return repr(value).replace("'", '"')

        return repr(value)

    @staticmethod
    def instructions_by_type_id() -> dict[int, InstructionType]:
        return INSTRUCTION_TYPES_BY_TYPE

    @staticmethod
    def instructions_by_name() -> dict[str, InstructionType]:
        return INSTRUCTION_TYPES_BY_NAME


def bytes_repr(bs: bytes) -> str:
    return 'b"' + "".join([f"\\x{b:02x}" for b in bs]) + '"'


@dataclass
class Script:
    entries: list[Instruction | str]
    data: bytes

    def to_event(self, character_encoding: CharacterEncoding) -> "Event":
        instructions = []
        labels = {}
        position = 0x0
        for entry in self.entries:
            if isinstance(entry, Instruction):
                instructions.append(copy.deepcopy(entry))
                position += entry.length(character_encoding)
            else:
                labels[entry] = position

        return Event(instructions=instructions, data=self.data, labels=labels)


@dataclass
class Event:
    instructions: list[Instruction]
    data: bytes
    labels: LabelDict

    @property
    def labels_by_position(self) -> dict[int, str]:
        return {pos: label for label, pos in self.labels.items()}

    def to_script(self, character_encoding: CharacterEncoding) -> Script:
        entries: list[Instruction | str] = []

        labels_by_position = self.labels_by_position

        position = 0x0
        for instruction in self.instructions:
            if position in labels_by_position:
                label = labels_by_position[position]
                entries.append(label)

            entries.append(copy.deepcopy(instruction))
            position += instruction.length(character_encoding)

        return Script(entries=entries, data=self.data)

    @staticmethod
    def from_evt(
        input_stream: IO[bytes], character_encoding: CharacterEncoding
    ) -> "Event":
        input_stream.read(4)
        data = input_stream.read(0x1004 - 4)

        instructions = []
        labels = {}
        while True:
            try:
                result = Instruction.from_evt(input_stream, character_encoding)
            except Exception as e:
                position = input_stream.tell()
                raise ValueError(
                    f"Failed to parse instruction at: 0x{position:x}"
                ) from e
            if result is None:
                break

            instruction, new_labels = result
            instructions.append(instruction)
            labels.update(new_labels)

        return Event(instructions=instructions, data=data, labels=labels)

    @staticmethod
    def from_script(
        input_stream: IO[str], character_encoding: CharacterEncoding
    ) -> "Event":
        data: Optional[Any] = None
        instructions: list[Instruction] = []
        labels: LabelDict = {}
        current_section: Optional[str]
        current_instruction_ptr = 0x0
        for line in input_stream:
            line = line.strip()
            if line == "":
                continue

            if line.startswith("."):
                assert line.endswith(":")

                section_name = line[1:-1]
                assert section_name in ["data", "code"]

                current_section = section_name
                continue

            if line.endswith(":"):
                label_name = line[:-1]
                assert label_name not in labels

                labels[label_name] = current_instruction_ptr
                continue

            if current_section == "data":
                assert line.startswith('b"')

                data = eval(line)
                continue
            elif current_section == "code":
                instruction = Instruction.from_script(line)
                assert instruction is not None

                instructions.append(instruction)
                current_instruction_ptr += instruction.length(character_encoding)
            else:
                raise AssertionError()

        assert data is not None
        assert isinstance(data, bytes)

        return Event(data=data, instructions=instructions, labels=labels)

    def write_script(
        self, output_stream: IO[str], character_encoding: CharacterEncoding
    ) -> None:
        output_stream.write(".data:\n")
        output_stream.write("    ")
        output_stream.write(bytes_repr(self.data))
        output_stream.write("\n")

        labels_by_position = self.labels_by_position

        output_stream.write(".code:\n")

        outputted_labels = []
        position = 0x0
        for instruction in self.instructions:
            if position in labels_by_position:
                label = labels_by_position[position]
                output_stream.write(f"  {label}:\n")

                outputted_labels.append(label)

            output_stream.write(f"    {instruction.to_script()}\n")
            position += instruction.length(character_encoding)

        assert len(outputted_labels) == len(set(outputted_labels))
        if len(outputted_labels) != len(self.labels):
            unprinted_labels = set(self.labels) - set(outputted_labels)
            raise ValueError(
                f"Did not output labels: {', '.join(sorted(unprinted_labels))}\nStopped at: 0x{position:x}"
            )

    def write_evt(
        self, output_stream: IO[bytes], character_encoding: CharacterEncoding
    ) -> None:
        output_stream.write(b"\x53\x43\x52\x00")
        output_stream.write(self.data)
        for instruction in self.instructions:
            instruction.write_evt(output_stream, self.labels, character_encoding)

    def get_instruction_at_ptr(
        self, pointer: int, character_encoding: CharacterEncoding
    ) -> Optional[Instruction]:
        start = 0x1004
        offsetted_pointer = pointer + start

        current_location = start
        for instruction in self.instructions:
            if current_location == offsetted_pointer:
                return instruction

            current_location += instruction.length(character_encoding)

        return None
