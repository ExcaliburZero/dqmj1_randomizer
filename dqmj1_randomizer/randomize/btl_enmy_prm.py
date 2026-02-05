import abc
import copy
import logging
import random
from dataclasses import dataclass
from typing import IO, Callable, Literal, override

import pandas as pd
from dqmj1_util.raw import BtlEnmyPrm, BtlEnmyPrmEntry

from dqmj1_randomizer.data import data_path
from dqmj1_randomizer.state import (
    BiasedByStatTotalMonsterShuffle,
    FullyRandomMonsterShuffle,
    MonsterRandomizationPolicyDefinition,
    State,
)

ENDIANESS: Literal["little"] = "little"


def simple_stat_total(entry: BtlEnmyPrmEntry) -> int:
    return entry.attack + entry.defense + entry.agility + entry.wisdom


def randomize_btl_enmy_prm(
    state: State, input_stream: IO[bytes], output_stream: IO[bytes]
) -> None:
    random.seed(state.seed)

    info_filepath = data_path / "btl_enmy_prm_info.csv"
    logging.info(f"Loading BtlEnmyPrm info file: {info_filepath}")
    data = pd.read_csv(info_filepath)
    logging.info("Successfully loaded BtlEnmyPrm info file.")

    btl_enmy_prm = BtlEnmyPrm.from_bin(input_stream)
    shuffle_btl_enmy_prm(state, data, btl_enmy_prm)
    btl_enmy_prm.write_bin(output_stream)


def shuffle_btl_enmy_prm(
    state: State, data: pd.DataFrame, btl_enmy_prm: "BtlEnmyPrm"
) -> None:
    # Annotate with the row indices, so that we can use them later when setting the new values.
    # Otherwise we would lose track of the indices because we filter when excluding specific
    # entries from the shuffle.
    entries_to_shuffle = [(i, entry) for i, entry in enumerate(btl_enmy_prm.entries)]

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
        f"Filtered down from {len(btl_enmy_prm.entries)} to {len(entries_to_shuffle)} BtlEnmyPtr entries to randomize."
    )

    shuffled_entries = entries_to_shuffle.copy()
    if state.monsters.randomization_policy is None:
        raise AssertionError

    logging.info(
        f"Randomizing monster encounters using policy: {state.monsters.randomization_policy}"
    )
    policy = MonsterRandomizationPolicy.build(state.monsters.randomization_policy)
    policy.shuffle(shuffled_entries)

    num_item_drops_swapped = 0
    for (i, prev_entry), (i_2, new_entry) in zip(entries_to_shuffle, shuffled_entries):
        btl_enmy_prm.entries[i] = copy.copy(new_entry)

        if state.monsters.transfer_boss_item_drops and (
            data["swap_drop"][i] == "y" or data["swap_drop"][i_2] == "y"
        ):
            btl_enmy_prm.entries[i].item_drops = prev_entry.item_drops
            if data["swap_drop"][i] == "y":
                num_item_drops_swapped += 1

        if state.monsters.swap_scout_chance:
            btl_enmy_prm.entries[i].scout_chance = prev_entry.scout_chance

        if state.monsters.swap_experience_drops:
            btl_enmy_prm.entries[i].exp = prev_entry.exp

        if state.monsters.swap_gold_drops:
            btl_enmy_prm.entries[i].gold = prev_entry.gold

    if state.monsters.transfer_boss_item_drops:
        logging.info(f"Swapped item drops for {num_item_drops_swapped} entries.")


class MonsterRandomizationPolicy(abc.ABC):
    @abc.abstractmethod
    def shuffle(self, entries: list[tuple[int, "BtlEnmyPrmEntry"]]) -> None:
        raise NotImplementedError

    @staticmethod
    def build(
        definition: MonsterRandomizationPolicyDefinition,
    ) -> "MonsterRandomizationPolicy":
        if isinstance(definition, FullyRandomMonsterShuffle):
            return FullyRandomShuffle()
        elif isinstance(definition, BiasedByStatTotalMonsterShuffle):
            return BiasedByStatTotalShuffle(definition.leniency)

        raise TypeError


@dataclass(frozen=True)
class FullyRandomShuffle(MonsterRandomizationPolicy):
    @override
    def shuffle(self, entries: list[tuple[int, "BtlEnmyPrmEntry"]]) -> None:
        random.shuffle(entries)


@dataclass(frozen=True)
class BiasedByStatTotalShuffle(MonsterRandomizationPolicy):
    """
    Performs a random shuffle that biases based on stat totals. The degree of randomness is
    controlled by a leniency factor which places a hard limit on the stat total change between
    shuffled encounters.

    Works by treating the random shuffling as a sorting problem. Assigns each encounter a value
    to use in that sort whereby the value is the stat total (attack + defense + agility + wisdom)
    plus or minus half of the leniency factor.

    This algorithm ensures that the leniency factor enforces a hard limit on the maximum change in
    stat total for every encounter, at the cost of low leniency values leading to many encounters
    staying the same. For example a leniency of 10 means that encounters can only be shuffled with
    other encounters that are within 10 points of the same stat total.

    For information on some of the considerations and evaluation that went into the design of this
    approach, see:

        https://github.com/ExcaliburZero/dqmj1_randomizer/issues/29
    """

    """
    Factor to apply in biasing the random shuffle. Units are stat points. Higher values indicate
    more randomness. For example a leniency of 10 means that encounters can only be shuffled with
    other encounters that are within 10 points of the same stat total (ignoring max hp and max mp).
    """
    leniency: int

    @override
    def shuffle(self, entries: list[tuple[int, "BtlEnmyPrmEntry"]]) -> None:
        previous_entries = entries.copy()

        # Determine the new ordering
        weighted_entries = [
            (i, simple_stat_total(entry), (a, entry))
            for i, (a, entry) in enumerate(entries)
        ]
        weighted_entries.sort(key=lambda a: a[1])

        biased_weighted_entries = [
            (
                weight + random.uniform(-self.leniency / 2, self.leniency / 2),
                entry,
            )
            for _, weight, entry in weighted_entries
        ]
        biased_weighted_entries.sort(key=lambda a: a[0])

        # Apply the new ordering
        for k, (_, entry) in enumerate(biased_weighted_entries):
            entries[weighted_entries[k][0]] = entry

        # Check that we obeyed the hard limit on stat total change
        num_violations = 0
        example_violation = None
        max_abs_diff = 0
        for (_, before), (_, after) in zip(previous_entries, entries):
            abs_diff = abs(simple_stat_total(after) - simple_stat_total(before))
            max_abs_diff = max(max_abs_diff, abs_diff)
            if abs_diff > self.leniency:
                example_violation = (before, after)
                num_violations += 1

        if num_violations > 0:
            if example_violation is None:
                raise AssertionError

            before, after = example_violation

            logging.warning(
                f"Found {num_violations} encounter table entries that were swapped with encounters that have more stat difference than expected."
            )
            logging.warning(
                f"For example an encounter with a stat total of {simple_stat_total(before)} was swapped with a stat total of {simple_stat_total(after)}. {abs(simple_stat_total(after) - simple_stat_total(before))} > {self.leniency}"
            )

        if max_abs_diff == 0:
            logging.warning(
                f"The max absolute stat total diff between shuffled encounters was {max_abs_diff}. It's likely the shuffling did not work correctly."
            )
