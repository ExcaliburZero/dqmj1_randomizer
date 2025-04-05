from typing import List

import copy
import io
import logging
import os
import pathlib
import random

import ndspy.rom
import pandas as pd

from dqmj1_randomizer.state import State

data_path = pathlib.Path(os.path.realpath(__file__)) / ".." / "data"


def randomize(state: State, output_rom_filepath: pathlib.Path) -> bool:
    logging.info(f"output_rom_filepath={output_rom_filepath}")
    logging.info(f"state={state}")

    original_rom = state.original_rom

    if original_rom is None:
        logging.error("No original ROM was selected.")
        return False

    if not original_rom.exists():
        logging.error(f"Original ROM does not exist: {original_rom}")
        return False

    logging.info(f"Loading original ROM: {original_rom}")
    rom = ndspy.rom.NintendoDSRom.fromFile(original_rom)
    load_rom_files(rom)
    logging.info("Sucessfully loaded original ROM.")

    logging.info(f"{len(rom.files)} files found in the original ROM.")

    result = True
    result &= randomize_btl_enmy_prm_tbl(state, rom)

    if not result:
        return False

    logging.info(f"Writing randomized ROM to: {output_rom_filepath}")
    rom.saveToFile(output_rom_filepath)
    logging.info("Sucessfully wrote randomized ROM.")

    return True


def load_rom_files(rom: ndspy.rom.NintendoDSRom) -> None:
    # Make sure all the rom files are loaded. Not sure why this is necessary, but it is indeed
    # necessary...
    for _ in rom.files:
        pass


def randomize_btl_enmy_prm_tbl(state: State, rom: ndspy.rom.NintendoDSRom) -> bool:
    random.seed(state.seed)

    info_filepath = data_path / "btl_enmy_prm_info.csv"
    logging.info(f"Loading BtlEnmyPrm info file: {info_filepath}")
    data = pd.read_csv(info_filepath)
    logging.info("Successfully loaded BtlEnmyPrm info file.")

    filepath = "BtlEnmyPrm.bin"
    try:
        original_data = rom.getFileByName(filepath)
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
        entries.append(bytearray(input_stream.read(88)))

    shuffle_btlEnmy_prm(state, data, entries)

    output_stream = io.BytesIO()
    output_stream.write(start)
    for entry in entries:
        output_stream.write(entry)

    rom.setFileByName(filepath, output_stream.getvalue())
    logging.info(f"Sucessfully updated: {filepath}")

    return True


def shuffle_btlEnmy_prm(
    state: State, data: pd.DataFrame, entries: List[bytearray]
) -> None:
    # Annotate with the row indicies, so that we can use them later when setting the new values.
    # Otherwise we would lose track of the indicies because we filter when excluding specific
    # entries from the shuffle.
    entries_to_shuffle = [(i, entry) for i, entry in enumerate(entries)]

    entries_to_shuffle = [
        (i, entry)
        for (i, entry) in entries_to_shuffle
        if data["exclude"][i] != "y" and data["is_gift_monster"][i] != "y"
    ]

    assert state.monsters.include_starters is not None
    if not state.monsters.include_starters:
        entries_to_shuffle = [
            (i, entry)
            for (i, entry) in entries_to_shuffle
            if data["is_starter"][i] != "y"
        ]

    assert state.monsters.include_bosses is not None
    if not state.monsters.include_bosses:
        entries_to_shuffle = [
            (i, entry) for (i, entry) in entries_to_shuffle if data["is_boss"][i] != "y"
        ]

    logging.info(
        f"Filtered down from {len(entries)} to {len(entries_to_shuffle)} BtlEnmyPtr entries to randomize."
    )

    shuffled_entries = [e for e in entries_to_shuffle]
    random.shuffle(shuffled_entries)

    num_item_drops_swapped = 0
    for (i, prev_entry), (i_2, new_entry) in zip(entries_to_shuffle, shuffled_entries):
        entries[i] = copy.copy(new_entry)

        if state.monsters.transfer_boss_item_drops and (
            data["swap_drop"][i] == "y" or data["swap_drop"][i_2] == "y"
        ):
            set_item_drop_bytes(
                entry=entries[i],
                item_drop_bytes=get_item_drop_bytes(prev_entry),
            )
            if data["swap_drop"][i] == "y":
                num_item_drops_swapped += 1

    if state.monsters.transfer_boss_item_drops:
        logging.info(f"Swapped item drops for {num_item_drops_swapped} entries.")


def get_item_drop_bytes(entry: bytearray) -> bytes:
    return entry[32:40]


def set_item_drop_bytes(entry: bytearray, item_drop_bytes: bytes) -> None:
    assert len(item_drop_bytes) == 8
    entry[32:40] = item_drop_bytes
