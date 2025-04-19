import io
import logging
import pathlib
import random

import ndspy.rom
import pandas as pd

from dqmj1_randomizer.data import data_path
from dqmj1_randomizer.randomize.btl_enmy_prm import shuffle_btl_enmy_prm
from dqmj1_randomizer.randomize.skill_tbl import SkillSetTable, shuffle_skill_tbl
from dqmj1_randomizer.state import State


class RandomizationException(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class FailedToFindExpectedRomSubFile(RandomizationException):
    def __init__(self, filepath: str, description: str) -> None:
        self.msg = f'Failed to find {description} file "{filepath}" in ROM. Make sure the ROM is of Dragon Quest Monsters Joker 1.'


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

    randomize_btl_enmy_prm_tbl(state, rom)
    randomize_skill_tbl(state, rom)

    logging.info(f"Writing randomized ROM to: {output_rom_filepath}")
    rom.saveToFile(output_rom_filepath)
    logging.info("Successfully wrote randomized ROM.")


def load_rom_files(rom: ndspy.rom.NintendoDSRom) -> None:
    # Make sure all the rom files are loaded. Not sure why this is necessary, but it is indeed
    # necessary...
    for _ in rom.files:
        pass


def randomize_btl_enmy_prm_tbl(state: State, rom: ndspy.rom.NintendoDSRom) -> None:
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


def randomize_skill_tbl(state: State, rom: ndspy.rom.NintendoDSRom) -> None:
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
    skill_sets = SkillSetTable.from_bin(input_stream)

    shuffle_skill_tbl(state, data, skill_sets)

    output_stream = io.BytesIO()
    skill_sets.write_bin(output_stream)

    rom.setFileByName(filepath, output_stream.getvalue())
    logging.info(f"Successfully updated: {filepath}")
