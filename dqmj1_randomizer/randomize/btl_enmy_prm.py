import abc
import copy
import logging
import random
from dataclasses import dataclass
from typing import IO, Callable, Literal, override

import pandas as pd

from dqmj1_randomizer.data import data_path
from dqmj1_randomizer.state import (
    BiasedByStatTotalMonsterShuffle,
    FullyRandomMonsterShuffle,
    MonsterRandomizationPolicyDefinition,
    State,
)

ENDIANESS: Literal["little"] = "little"


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
            (i, entry.simple_stat_total, (a, entry))
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
            abs_diff = abs(after.simple_stat_total - before.simple_stat_total)
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
                f"For example an encounter with a stat total of {before.simple_stat_total} was swapped with a stat total of {after.simple_stat_total}. {abs(after.simple_stat_total - before.simple_stat_total)} > {self.leniency}"
            )

        if max_abs_diff == 0:
            logging.warning(
                f"The max absolute stat total diff between shuffled encounters was {max_abs_diff}. It's likely the shuffling did not work correctly."
            )


@dataclass
class ItemDrop:
    item_id: int
    chance_denominator_2_power: int

    def write_bin(self, output_stream: IO[bytes]) -> None:
        output_stream.write(self.item_id.to_bytes(2, ENDIANESS))
        output_stream.write(self.chance_denominator_2_power.to_bytes(2, ENDIANESS))

    @staticmethod
    def from_bin(input_stream: IO[bytes]) -> "ItemDrop":
        item_id = int.from_bytes(input_stream.read(2), ENDIANESS)
        chance_denominator_2_power = int.from_bytes(input_stream.read(2), ENDIANESS)

        return ItemDrop(
            item_id=item_id, chance_denominator_2_power=chance_denominator_2_power
        )


@dataclass
class EnemySkillEntry:
    unknown_a: int
    skill_id: int

    def write_bin(self, output_stream: IO[bytes]) -> None:
        output_stream.write(self.unknown_a.to_bytes(2, ENDIANESS))
        output_stream.write(self.skill_id.to_bytes(2, ENDIANESS))

    @staticmethod
    def from_bin(input_stream: IO[bytes]) -> "EnemySkillEntry":
        unknown_a = int.from_bytes(input_stream.read(2), ENDIANESS)
        skill_id = int.from_bytes(input_stream.read(2), ENDIANESS)

        return EnemySkillEntry(unknown_a=unknown_a, skill_id=skill_id)


@dataclass
class BtlEnmyPrmEntry:
    species_id: int
    unknown_a: bytes
    skills: list[EnemySkillEntry]
    item_drops: list[ItemDrop]
    gold: int
    unknown_b: bytes
    exp: int
    unknown_c: bytes
    level: int
    unknown_d: bytes
    unknown_e: int
    scout_chance: int
    max_hp: int
    max_mp: int
    attack: int
    defense: int
    agility: int
    wisdom: int
    unknown_f: bytes
    skill_set_ids: list[int]
    unknown_g: bytes

    @property
    def simple_stat_total(self) -> int:
        return self.attack + self.defense + self.agility + self.wisdom

    def write_bin(self, output_stream: IO[bytes]) -> None:
        output_stream.write(self.species_id.to_bytes(2, ENDIANESS))
        output_stream.write(self.unknown_a)
        for skill in self.skills:
            skill.write_bin(output_stream)
        for item_drop in self.item_drops:
            item_drop.write_bin(output_stream)
        output_stream.write(self.gold.to_bytes(2, ENDIANESS))
        output_stream.write(self.unknown_b)
        output_stream.write(self.exp.to_bytes(2, ENDIANESS))
        output_stream.write(self.unknown_c)
        output_stream.write(self.level.to_bytes(1, ENDIANESS))
        output_stream.write(self.unknown_d)
        output_stream.write(self.unknown_e.to_bytes(1, ENDIANESS))
        output_stream.write(self.scout_chance.to_bytes(1, ENDIANESS))
        output_stream.write(self.max_hp.to_bytes(2, ENDIANESS))
        output_stream.write(self.max_mp.to_bytes(2, ENDIANESS))
        output_stream.write(self.attack.to_bytes(2, ENDIANESS))
        output_stream.write(self.defense.to_bytes(2, ENDIANESS))
        output_stream.write(self.agility.to_bytes(2, ENDIANESS))
        output_stream.write(self.wisdom.to_bytes(2, ENDIANESS))
        output_stream.write(self.unknown_f)
        for skill_set_id in self.skill_set_ids:
            output_stream.write(skill_set_id.to_bytes(1, ENDIANESS))
        output_stream.write(self.unknown_g)

    @staticmethod
    def from_bin(input_stream: IO[bytes]) -> "BtlEnmyPrmEntry":
        species_id = int.from_bytes(input_stream.read(2), ENDIANESS)

        unknown_a = input_stream.read(6)
        skills = [EnemySkillEntry.from_bin(input_stream) for _ in range(0, 6)]
        item_drops = [ItemDrop.from_bin(input_stream) for _ in range(0, 2)]
        gold = int.from_bytes(input_stream.read(2), ENDIANESS)
        unknown_b = input_stream.read(2)
        exp = int.from_bytes(input_stream.read(2), ENDIANESS)
        unknown_c = input_stream.read(2)
        level = int.from_bytes(input_stream.read(1), ENDIANESS)
        unknown_d = input_stream.read(1)

        unknown_e = int.from_bytes(input_stream.read(1), ENDIANESS)
        scout_chance = int.from_bytes(input_stream.read(1), ENDIANESS)
        max_hp = int.from_bytes(input_stream.read(2), ENDIANESS)
        max_mp = int.from_bytes(input_stream.read(2), ENDIANESS)
        attack = int.from_bytes(input_stream.read(2), ENDIANESS)
        defense = int.from_bytes(input_stream.read(2), ENDIANESS)
        agility = int.from_bytes(input_stream.read(2), ENDIANESS)
        wisdom = int.from_bytes(input_stream.read(2), ENDIANESS)

        unknown_f = input_stream.read(20)
        skill_set_ids = [int.from_bytes(input_stream.read(1)) for _ in range(0, 3)]

        unknown_g = input_stream.read(1)

        return BtlEnmyPrmEntry(
            species_id=species_id,
            unknown_a=unknown_a,
            skills=skills,
            item_drops=item_drops,
            gold=gold,
            unknown_b=unknown_b,
            exp=exp,
            unknown_c=unknown_c,
            level=level,
            unknown_d=unknown_d,
            unknown_e=unknown_e,
            scout_chance=scout_chance,
            max_hp=max_hp,
            max_mp=max_mp,
            attack=attack,
            defense=defense,
            agility=agility,
            wisdom=wisdom,
            unknown_f=unknown_f,
            skill_set_ids=skill_set_ids,
            unknown_g=unknown_g,
        )


@dataclass
class BtlEnmyPrm:
    entries: list[BtlEnmyPrmEntry]

    def write_bin(self, output_stream: IO[bytes]) -> None:
        magic = b"\x42\x45\x50\x54"

        output_stream.write(magic)
        output_stream.write(len(self.entries).to_bytes(4, ENDIANESS))
        for entry in self.entries:
            entry.write_bin(output_stream)

    @staticmethod
    def from_bin(input_stream: IO[bytes]) -> "BtlEnmyPrm":
        int.from_bytes(input_stream.read(4), ENDIANESS)
        length = int.from_bytes(input_stream.read(4), ENDIANESS)

        entries = [BtlEnmyPrmEntry.from_bin(input_stream) for _ in range(0, length)]

        return BtlEnmyPrm(entries)

    def to_pd(self) -> pd.DataFrame:
        return pd.DataFrame(self.entries)
