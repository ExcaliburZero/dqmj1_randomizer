import abc
import io
import logging
import pathlib
import random
import shutil

import ndspy.rom
import pandas as pd
from dqmj1_util import GuideData, Region, Rom, write_guide
from dqmj1_util.raw import SkillTbl
from pubsub import pub  # type: ignore

from dqmj1_randomizer.data import data_path
from dqmj1_randomizer.randomize.btl_enmy_prm import randomize_btl_enmy_prm
from dqmj1_randomizer.randomize.character_encoding import CHARACTER_ENCODINGS
from dqmj1_randomizer.randomize.evt import Event, Instruction
from dqmj1_randomizer.randomize.skill_tbl import shuffle_skill_tbl
from dqmj1_randomizer.state import State


class RandomizationError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg = msg


class NoOriginalRomError(RandomizationError):
    def __init__(self) -> None:
        super().__init__("No original ROM was selected.")


class OriginalRomDoesNotExistError(RandomizationError):
    def __init__(self, original_rom_path: pathlib.Path) -> None:
        super().__init__(f"Original ROM does not exist: {original_rom_path}")


class InvalidRomFileFormatError(RandomizationError):
    def __init__(self, original_rom_path: pathlib.Path) -> None:
        super().__init__(
            f"Original ROM file has invalid format. Make sure it is a properly formatted nds file. {original_rom_path}"
        )


class FailedToFindExpectedRomSubFileError(RandomizationError):
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
        raise NoOriginalRomError

    if not original_rom.exists():
        raise OriginalRomDoesNotExistError(original_rom)

    logging.info(f"Loading original ROM: {original_rom}")

    try:
        rom = ndspy.rom.NintendoDSRom.fromFile(original_rom)
    except Exception as e:
        raise InvalidRomFileFormatError(original_rom) from e

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

    num_steps = 2
    for task in tasks:
        num_steps += task.estimate_steps(state, rom)

    pub.sendMessage("randomize.num_steps", num_steps=num_steps)

    for task in tasks:
        task.run(state, rom)

    logging.info(f"Writing randomized ROM to: {output_rom_filepath}")
    rom.saveToFile(output_rom_filepath)

    generate_guide(state, output_rom_filepath)
    pub.sendMessage("randomize.progress")

    logging.info("Successfully wrote randomized ROM.")
    pub.sendMessage("randomize.progress")


def load_rom_files(rom: ndspy.rom.NintendoDSRom) -> None:
    # Make sure all the rom files are loaded. Not sure why this is necessary, but it is indeed
    # necessary...
    for _ in rom.files:
        pass


class RandomizeBtlEnmyPrmTbl(Task):
    def run(self, state: State, rom: ndspy.rom.NintendoDSRom) -> None:
        filepath = "BtlEnmyPrm.bin"
        try:
            original_data = rom.getFileByName(filepath)
        except ValueError as e:
            raise FailedToFindExpectedRomSubFileError(
                "BtlEnmyPrm.bin", "enemy encounters"
            ) from e

        input_stream = io.BytesIO(original_data)
        output_stream = io.BytesIO()
        randomize_btl_enmy_prm(
            state=state, input_stream=input_stream, output_stream=output_stream
        )

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
            raise FailedToFindExpectedRomSubFileError(
                "SkillTbl.bin", "skill sets"
            ) from e

        input_stream = io.BytesIO(original_data)
        skill_sets = SkillTbl.from_bin(input_stream, region=state.region)

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
        filenames = rom.filenames.files.copy()
        random.shuffle(filenames)

        # Load event files
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

        logging.info(f"Successfully updated {len(filenames)} event files.")
        pub.sendMessage("randomize.progress")

    def estimate_steps(self, state: State, rom: ndspy.rom.NintendoDSRom) -> int:
        num_tasks = 0
        for filename in rom.filenames.files:
            if not filename.endswith(".evt"):
                continue

            num_tasks += 1

        return num_tasks + 1


def generate_guide(state: State, rom_filepath: pathlib.Path) -> None:
    if state.region == Region.Europe:
        logging.warning(
            "Guide generation does not currently support Europe release, so skipping."
        )
        return

    logging.info(f"Generating guide")
    guide_directory = rom_filepath.parent / (rom_filepath.stem + "_guide")

    if guide_directory.exists():
        shutil.rmtree(guide_directory)

    guide_directory.mkdir()

    rom = Rom(rom_filepath, region=state.region)

    guide_data = GuideData(
        skills=rom.skills,
        skill_sets=rom.skill_sets,
        encounters=rom.encounters,
    )

    write_guide(guide_data, guide_directory)
    logging.info(f"Successfully wrote guide to: {guide_directory}")
