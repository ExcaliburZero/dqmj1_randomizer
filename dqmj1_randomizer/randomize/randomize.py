import abc
import io
import logging
import pathlib
import random

import ndspy.rom
import pandas as pd
from pubsub import pub  # type: ignore

from dqmj1_randomizer.data import data_path
from dqmj1_randomizer.randomize.btl_enmy_prm import shuffle_btl_enmy_prm
from dqmj1_randomizer.randomize.character_encoding import CHARACTER_ENCODINGS
from dqmj1_randomizer.randomize.evt import Event, Instruction, InstructionType, Script
from dqmj1_randomizer.randomize.skill_tbl import SkillSetTable, shuffle_skill_tbl
from dqmj1_randomizer.state import State


class RandomizationException(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class FailedToFindExpectedRomSubFile(RandomizationException):
    def __init__(self, filepath: str, description: str) -> None:
        self.msg = f'Failed to find {description} file "{filepath}" in ROM. Make sure the ROM is of Dragon Quest Monsters Joker 1.'


class Task(abc.ABC):
    @abc.abstractmethod
    def run(self, state: State, rom: ndspy.rom.NintendoDSRom) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def estimate_steps(self, state: State, rom: ndspy.rom.NintendoDSRom) -> int:
        raise NotImplementedError


def randomize(state: State, output_rom_filepath: pathlib.Path) -> None:
    logging.info(f"output_rom_filepath={output_rom_filepath}")
    logging.info(f"state={state}")

    original_rom = state.original_rom

    if original_rom is None:
        raise RandomizationException("No original ROM was selected.")

    if not original_rom.exists():
        raise RandomizationException(f"Original ROM does not exist: {original_rom}")

    logging.info(f"Loading original ROM: {original_rom}")

    try:
        rom = ndspy.rom.NintendoDSRom.fromFile(original_rom)
    except Exception as e:
        raise RandomizationException(
            f"Original ROM file has invalid format. Make sure it is a properly formatted nds file. {original_rom}"
        ) from e

    load_rom_files(rom)
    logging.info("Successfully loaded original ROM.")

    logging.info(f"{len(rom.files)} files found in the original ROM.")

    tasks: list[Task] = []

    if state.monsters.randomize:
        tasks.append(RandomizeBtlEnmyPrmTbl())

    if state.skill_sets.randomize:
        tasks.append(RandomizeSkillTbl())

    if state.other.remove_dialogue:
        tasks.append(RemoveDialog())

    num_steps = 1
    for task in tasks:
        num_steps += task.estimate_steps(state, rom)

    pub.sendMessage("randomize.num_steps", num_steps=num_steps)

    for task in tasks:
        task.run(state, rom)

    logging.info(f"Writing randomized ROM to: {output_rom_filepath}")
    rom.saveToFile(output_rom_filepath)
    logging.info("Successfully wrote randomized ROM.")
    pub.sendMessage("randomize.progress")


def load_rom_files(rom: ndspy.rom.NintendoDSRom) -> None:
    # Make sure all the rom files are loaded. Not sure why this is necessary, but it is indeed
    # necessary...
    for _ in rom.files:
        pass


class RandomizeBtlEnmyPrmTbl(Task):
    def run(self, state: State, rom: ndspy.rom.NintendoDSRom) -> None:
        random.seed(state.seed)

        info_filepath = data_path / "btl_enmy_prm_info.csv"
        logging.info(f"Loading BtlEnmyPrm info file: {info_filepath}")
        data = pd.read_csv(info_filepath)
        logging.info("Successfully loaded BtlEnmyPrm info file.")

        filepath = "BtlEnmyPrm.bin"
        try:
            original_data = rom.getFileByName(filepath)
        except ValueError as e:
            raise FailedToFindExpectedRomSubFile(
                "BtlEnmyPrm.bin", "enemy encounters"
            ) from e

        start = None
        entries = []
        input_stream = io.BytesIO(original_data)
        start = input_stream.read(8)
        length = int.from_bytes(start[4:], "little")
        for _ in range(0, length):
            entries.append(bytearray(input_stream.read(88)))

        shuffle_btl_enmy_prm(state, data, entries)

        output_stream = io.BytesIO()
        output_stream.write(start)
        for entry in entries:
            output_stream.write(entry)

        rom.setFileByName(filepath, output_stream.getvalue())
        logging.info(f"Successfully updated: {filepath}")

    def estimate_steps(self, state: State, rom: ndspy.rom.NintendoDSRom) -> int:
        return 1


class RandomizeSkillTbl(Task):
    def run(self, state: State, rom: ndspy.rom.NintendoDSRom) -> None:
        random.seed(state.seed)

        info_filepath = data_path / "skill_tbl_info.csv"
        logging.info(f"Loading SkillTbl info file: {info_filepath}")
        data = pd.read_csv(info_filepath)
        logging.info("Successfully loaded SkillTbl info file.")

        filepath = "SkillTbl.bin"
        try:
            original_data = rom.getFileByName(filepath)
        except ValueError as e:
            raise FailedToFindExpectedRomSubFile("SkillTbl.bin", "skill sets") from e

        input_stream = io.BytesIO(original_data)
        skill_sets = SkillSetTable.from_bin(input_stream, region=state.region)

        shuffle_skill_tbl(state, data, skill_sets)

        output_stream = io.BytesIO()
        skill_sets.write_bin(output_stream)

        rom.setFileByName(filepath, output_stream.getvalue())
        logging.info(f"Successfully updated: {filepath}")

        pub.sendMessage("randomize.progress")

    def estimate_steps(self, state: State, rom: ndspy.rom.NintendoDSRom) -> int:
        return 1


class RemoveDialog(Task):
    def run(self, state: State, rom: ndspy.rom.NintendoDSRom) -> None:
        random.seed(state.seed)

        character_encoding = CHARACTER_ENCODINGS["North America / Europe"]

        # Shuffle the filenames in order to make the progress bar more accurate
        filenames = [filename for filename in rom.filenames.files]
        random.shuffle(filenames)

        # Load event files
        scripts: dict[str, Script] = {}
        logging.info("Loading event files.")
        for filename in filenames:
            if not filename.endswith(".evt"):
                continue

            input_stream = io.BytesIO(rom.getFileByName(filename))
            event = Event.from_evt(input_stream, character_encoding=character_encoding)

            script = event.to_script(character_encoding)

            # Replace ShowDialogue commands with Nop's of the same size
            for entry in script.entries:
                if (
                    isinstance(entry, Instruction)
                    and entry.instruction_type.name == "ShowDialog"
                ):
                    entry.instruction_type.type_id = 0xAA  # NopAA

            # Write the updated events to the ROM
            output_stream = io.BytesIO()
            script.to_event(character_encoding).write_evt(
                output_stream, character_encoding
            )

            rom.setFileByName(filename, output_stream.getbuffer())

            pub.sendMessage("randomize.progress")

        logging.info(f"Successfully updated {len(scripts)} event files.")
        pub.sendMessage("randomize.progress")

    def estimate_steps(self, state: State, rom: ndspy.rom.NintendoDSRom) -> int:
        num_tasks = 0
        for filename in rom.filenames.files:
            if not filename.endswith(".evt"):
                continue

            num_tasks += 1

        return num_tasks + 1
