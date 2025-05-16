import copy
import logging
import random
from dataclasses import dataclass
from typing import IO, Callable, Literal

import pandas as pd

from dqmj1_randomizer.data import data_path
from dqmj1_randomizer.state import State

ENDIANESS: Literal["little"] = "little"


def randomize_btl_enmy_prm(
    state: State, input_stream: IO[bytes], output_stream: IO[bytes]
) -> None:
    random.seed(state.seed)

    info_filepath = data_path / "btl_enmy_prm_info.csv"
    logging.info(f"Loading BtlEnmyPrm info file: {info_filepath}")
    data = pd.read_csv(info_filepath)
    logging.info("Successfully loaded BtlEnmyPrm info file.")

    start = input_stream.read(8)
    length = int.from_bytes(start[4:], "little")
    entries = [bytearray(input_stream.read(88)) for _ in range(0, length)]

    shuffle_btl_enmy_prm(state, data, entries)

    output_stream.write(start)
    for entry in entries:
        output_stream.write(entry)


def shuffle_btl_enmy_prm(
    state: State, data: pd.DataFrame, entries: list[bytearray]
) -> None:
    # Annotate with the row indices, so that we can use them later when setting the new values.
    # Otherwise we would lose track of the indices because we filter when excluding specific
    # entries from the shuffle.
    entries_to_shuffle = [(i, entry) for i, entry in enumerate(entries)]

    def filter_entries(condition: Callable[[int], bool]) -> None:
        nonlocal entries_to_shuffle
        entries_to_shuffle = [
            (i, entry) for (i, entry) in entries_to_shuffle if condition(i)
        ]

    filter_entries(lambda i: data["exclude"][i] != "y")

    # Note: We always filter out the gift incarnus from randomization, because not having incarnus
    # can cause some cutscenes to crash. For more details see:
    #
    #  https://github.com/ExcaliburZero/dqmj1_randomizer/issues/4
    filter_entries(lambda i: data["is_gift_incarnus"][i] != "y")

    assert state.monsters.include_gift_monsters is not None
    if not state.monsters.include_gift_monsters:
        filter_entries(lambda i: data["is_gift_monster"][i] != "y")

    assert state.monsters.include_starters is not None
    if not state.monsters.include_starters:
        filter_entries(lambda i: data["is_starter"][i] != "y")

    assert state.monsters.include_bosses is not None
    if not state.monsters.include_bosses:
        filter_entries(lambda i: data["is_boss"][i] != "y")

    logging.info(
        f"Filtered down from {len(entries)} to {len(entries_to_shuffle)} BtlEnmyPtr entries to randomize."
    )

    shuffled_entries = entries_to_shuffle.copy()
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


@dataclass
class ItemDrop:
    item_id: int
    chance_denominator_2_power: int

    @staticmethod
    def from_bin(input_stream: IO[bytes]) -> "ItemDrop":
        item_id = int.from_bytes(input_stream.read(2), ENDIANESS)
        chance_denominator_2_power = int.from_bytes(input_stream.read(2), ENDIANESS)

        return ItemDrop(
            item_id=item_id, chance_denominator_2_power=chance_denominator_2_power
        )


@dataclass
class BtlEnmyPrmEntry:
    species_id: int
    item_drops: list[ItemDrop]
    gold: int
    exp: int
    level: int
    max_hp: int
    max_mp: int
    attack: int
    defense: int
    agility: int
    wisdom: int
    skill_set_ids: list[int]

    @staticmethod
    def from_bin(input_stream: IO[bytes]) -> "BtlEnmyPrmEntry":
        species_id = int.from_bytes(input_stream.read(2), ENDIANESS)

        input_stream.read(30)
        item_drops = [
            ItemDrop.from_bin(input_stream),
            ItemDrop.from_bin(input_stream),
        ]
        gold = int.from_bytes(input_stream.read(2), ENDIANESS)
        input_stream.read(2)
        exp = int.from_bytes(input_stream.read(2), ENDIANESS)
        input_stream.read(2)
        level = int.from_bytes(input_stream.read(1), ENDIANESS)
        input_stream.read(1), ENDIANESS

        input_stream.read(2)
        max_hp = int.from_bytes(input_stream.read(2), ENDIANESS)
        max_mp = int.from_bytes(input_stream.read(2), ENDIANESS)
        attack = int.from_bytes(input_stream.read(2), ENDIANESS)
        defense = int.from_bytes(input_stream.read(2), ENDIANESS)
        agility = int.from_bytes(input_stream.read(2), ENDIANESS)
        wisdom = int.from_bytes(input_stream.read(2), ENDIANESS)

        input_stream.read(20)
        skill_set_ids = [int.from_bytes(input_stream.read(1)) for _ in range(0, 3)]

        input_stream.read(1)

        return BtlEnmyPrmEntry(
            species_id=species_id,
            item_drops=item_drops,
            gold=gold,
            exp=exp,
            level=level,
            max_hp=max_hp,
            max_mp=max_mp,
            attack=attack,
            defense=defense,
            agility=agility,
            wisdom=wisdom,
            skill_set_ids=skill_set_ids,
        )


@dataclass
class BtlEnmyPrm:
    entries: list[BtlEnmyPrmEntry]

    @staticmethod
    def from_bin(input_stream: IO[bytes]) -> "BtlEnmyPrm":
        int.from_bytes(input_stream.read(4), ENDIANESS)
        length = int.from_bytes(input_stream.read(4), ENDIANESS)

        entries = [BtlEnmyPrmEntry.from_bin(input_stream) for _ in range(0, length)]

        return BtlEnmyPrm(entries)

    def to_pd(self) -> pd.DataFrame:
        return pd.DataFrame(self.entries)
