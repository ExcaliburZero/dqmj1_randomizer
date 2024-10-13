import io
import logging
import pathlib
import random

import ndspy.rom

from dqmj1_randomizer.state import State


def randomize(state: State, output_rom_filepath: pathlib.Path) -> bool:
    original_rom = state.original_rom

    if original_rom is None:
        logging.error(f"No original ROM was selected.")
        return False

    if not original_rom.exists():
        logging.error(f"Original ROM does not exist: {original_rom}")
        return False

    logging.info(f"Loading original ROM: {original_rom}")
    rom = ndspy.rom.NintendoDSRom.fromFile(original_rom)
    logging.info(f"Sucessfully loaded original ROM.")

    logging.info(f"{len(rom.files)} files found in the original ROM.")

    # Make sure all the rom files are loaded. Not sure why this is necessary, but it is indeed
    # necessary...
    for _ in rom.files:
        pass

    result = True
    result &= randomize_btl_enmy_prm_tbl(state, rom)

    if not result:
        return False

    logging.info(f"Writing randomized ROM to: {output_rom_filepath}")
    rom.saveToFile(output_rom_filepath)
    logging.info("Sucessfully wrote randomized ROM.")

    return True


def randomize_btl_enmy_prm_tbl(state: State, rom: ndspy.rom.NintendoDSRom) -> bool:
    random.seed(state.seed)

    filepath = "BtlEnmyPrm.bin"
    try:
        original_data = rom.getFileByName("BtlEnmyPrm.bin")
    except ValueError as e:
        logging.exception(e)
        logging.error(f"Failed to find BtlEnmyPrm in ROM. ({filepath})")
        return False

    start = None
    entries = []
    input_stream = io.BytesIO(original_data)
    start = input_stream.read(8)
    length = int.from_bytes(start[4:], "little")
    for _ in range(0, length):
        entries.append(input_stream.read(88))

    random.shuffle(entries)

    output_stream = io.BytesIO()
    output_stream.write(start)
    for entry in entries:
        output_stream.write(entry)

    rom.setFileByName(filepath, output_stream.getvalue())
    logging.info(f"Sucessfully updated: {filepath}")

    return True
