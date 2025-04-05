import copy
import logging
import random

import pandas as pd

from dqmj1_randomizer.state import State


def shuffle_btl_enmy_prm(
    state: State, data: pd.DataFrame, entries: list[bytearray]
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
