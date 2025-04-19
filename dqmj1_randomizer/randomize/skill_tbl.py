import abc
import logging
import random
from collections.abc import Iterable
from dataclasses import dataclass
from typing import IO, Callable, TypeVar, cast

import pandas as pd

from dqmj1_randomizer.randomize.regions import Region
from dqmj1_randomizer.state import State

NUM_SKILL_SETS = 194
SKILL_SETS_OFFSET = 8
SKILL_SET_SIZE_IN_BYTES_NA_EU = 240
SKILL_SET_SIZE_IN_BYTES_JP = 220

NUM_SKILLS_PER_SKILL_SET = 10
SKILLS_OFFSET = 44
SKILL_SIZE_IN_BYTES = 12
TRAITS_OFFSET = 164
TRAIT_SIZE_IN_BYTES = 4

T = TypeVar("T")


class Byteable(abc.ABC):
    raw: bytearray


@dataclass
class Skill(Byteable):
    raw: bytearray

    def is_empty(self) -> bool:
        return all(byte == 0x0 for byte in self.raw)


@dataclass
class Trait(Byteable):
    raw: bytearray

    def is_empty(self) -> bool:
        return all(byte == 0x0 for byte in self.raw)


@dataclass
class SkillSet(Byteable):
    raw: bytearray

    @property
    def can_upgrade(self) -> bool:
        return self.raw[0] != 0

    @property
    def skills(self) -> list[Skill]:
        return extract_data_bytes(
            all_bytes=self.raw,
            offset=SKILLS_OFFSET,
            data_size=SKILL_SIZE_IN_BYTES,
            num_data=NUM_SKILLS_PER_SKILL_SET,
            constructor=lambda b: Skill(b),
        )

    @skills.setter
    def skills(self, skills: list[Skill]) -> None:
        assert len(skills) == NUM_SKILLS_PER_SKILL_SET
        return set_data_bytes(
            all_bytes=self.raw,
            offset=SKILLS_OFFSET,
            data_size=SKILL_SIZE_IN_BYTES,
            data=skills,
        )

    @property
    def traits(self) -> list[Trait]:
        return extract_data_bytes(
            all_bytes=self.raw,
            offset=TRAITS_OFFSET,
            data_size=TRAIT_SIZE_IN_BYTES,
            num_data=NUM_SKILLS_PER_SKILL_SET,  # same number of trait and skill slots
            constructor=lambda b: Trait(b),
        )

    @traits.setter
    def traits(self, traits: list[Trait]) -> None:
        assert (
            len(traits) == NUM_SKILLS_PER_SKILL_SET
        )  # same number of trait and skill slots
        return set_data_bytes(
            all_bytes=self.raw,
            offset=TRAITS_OFFSET,
            data_size=TRAIT_SIZE_IN_BYTES,
            data=traits,
        )


@dataclass
class SkillSetTable(Byteable):
    raw: bytearray
    region: Region

    @property
    def skill_sets(self) -> list[SkillSet]:
        if self.region == Region.Japan:
            return extract_data_bytes(
                all_bytes=self.raw,
                offset=SKILL_SETS_OFFSET,
                data_size=SKILL_SET_SIZE_IN_BYTES_JP,
                num_data=NUM_SKILL_SETS,
                constructor=lambda b: SkillSet(b),
            )
        else:
            return extract_data_bytes(
                all_bytes=self.raw,
                offset=SKILL_SETS_OFFSET,
                data_size=SKILL_SET_SIZE_IN_BYTES_NA_EU,
                num_data=NUM_SKILL_SETS,
                constructor=lambda b: SkillSet(b),
            )

    @skill_sets.setter
    def skill_sets(self, new_skill_sets: list[SkillSet]) -> None:
        assert len(new_skill_sets) == NUM_SKILL_SETS
        if self.region == Region.Japan:
            set_data_bytes(
                all_bytes=self.raw,
                offset=SKILL_SETS_OFFSET,
                data_size=SKILL_SET_SIZE_IN_BYTES_JP,
                data=new_skill_sets,
            )
        else:
            set_data_bytes(
                all_bytes=self.raw,
                offset=SKILL_SETS_OFFSET,
                data_size=SKILL_SET_SIZE_IN_BYTES_NA_EU,
                data=new_skill_sets,
            )

    @staticmethod
    def from_bin(input_stream: IO[bytes], region: Region) -> "SkillSetTable":
        return SkillSetTable(raw=bytearray(input_stream.read()), region=region)

    def write_bin(self, output_stream: IO[bytes]) -> None:
        output_stream.write(self.raw)


def shuffle_skill_tbl(
    state: State, data: pd.DataFrame, skill_sets_table: SkillSetTable
) -> None:
    skill_sets = skill_sets_table.skill_sets

    # Find all the skills and traits we want to randomize
    skill_and_trait_entries = {}
    for skill_set_index, skill_set in enumerate(skill_sets):
        if data["exclude"][skill_set_index] == "y":
            continue

        for skill_and_trait_index, (skill, trait) in enumerate(
            zip(skill_set.skills, skill_set.traits)
        ):
            if skill.is_empty() and trait.is_empty():
                continue

            skill_and_trait_entries[(skill_set_index, skill_and_trait_index)] = (
                skill,
                trait,
            )

    # Perform the shuffle
    indices = skill_and_trait_entries.keys()
    values = list(skill_and_trait_entries.values())
    random.shuffle(values)

    # Apply the shuffle, making sure to do so to fully copies as to not overwrite data we want to
    # also read from.
    shuffled_skill_sets = skill_sets_table.skill_sets
    for (skill_set_index, skill_and_trait_index), (skill, trait) in zip(
        indices, values
    ):
        skill_set = shuffled_skill_sets[skill_set_index]

        skills = skill_set.skills
        traits = skill_set.traits

        skills[skill_and_trait_index] = skill
        traits[skill_and_trait_index] = trait

        skill_set.skills = skills
        skill_set.traits = traits

        shuffled_skill_sets[skill_set_index] = skill_set

    skill_sets_table.skill_sets = shuffled_skill_sets


def extract_data_bytes(
    all_bytes: bytearray,
    offset: int,
    data_size: int,
    num_data: int,
    constructor: Callable[[bytearray], T] | None = None,
) -> list[T]:
    if constructor is None:
        constructor = cast(Callable[[bytearray], T], lambda x: x)

    return [
        constructor(all_bytes[offset + i * data_size : offset + (i + 1) * data_size])
        for i in range(0, num_data)
    ]


def set_data_bytes(
    all_bytes: bytearray,
    offset: int,
    data_size: int,
    data: Iterable[Byteable],
) -> None:
    for i, d in enumerate(data):
        all_bytes[offset + i * data_size : offset + (i + 1) * data_size] = d.raw
