import copy
import random
from typing import cast

import pandas as pd
from dqmj1_util.raw import SkillTbl, SkillTblEntry, SkillTblEntryJp, SkillTblEntryNaEu

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


def shuffle_skill_tbl(
    state: State, data: pd.DataFrame, skill_sets_table: SkillTbl
) -> None:
    skill_sets = skill_sets_table.entries

    # Find all the skills and traits we want to randomize
    skill_and_trait_entries: dict[
        tuple[int, int], tuple[SkillTblEntry.Skills, SkillTblEntry.Traits]
    ] = {}
    for skill_set_index, skill_set in enumerate(skill_sets):
        skill_set = cast("SkillTblEntryJp | SkillTblEntryNaEu", skill_set)

        if data["exclude"][skill_set_index] == "y":
            continue

        for skill_and_trait_index, (skill, trait) in enumerate(
            zip(skill_set.skills, skill_set.traits)
        ):
            if not any(skill_id != 0 for skill_id in skill.skill_ids) and not any(
                trait_id != 0 for trait_id in trait.trait_ids
            ):
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
    shuffled_skill_sets = copy.deepcopy(skill_sets_table.entries)
    for (skill_set_index, skill_and_trait_index), (skill, trait) in zip(
        indices, values
    ):
        shuffled_skill_sets[skill_set_index].skills[skill_and_trait_index] = skill
        shuffled_skill_sets[skill_set_index].traits[skill_and_trait_index] = trait

    skill_sets_table.entries = shuffled_skill_sets
