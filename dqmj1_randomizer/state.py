import pathlib
import re
from dataclasses import dataclass, field
from typing import Optional

from dqmj1_util import Region


@dataclass(frozen=True)
class FullyRandomMonsterShuffle:
    pass


@dataclass(frozen=True)
class BiasedByStatTotalMonsterShuffle:
    leniency: int


MonsterRandomizationPolicyDefinition = (
    FullyRandomMonsterShuffle | BiasedByStatTotalMonsterShuffle
)


def parse_monster_randomization_policy_definition(
    definition_str: str,
) -> Optional[MonsterRandomizationPolicyDefinition]:
    if definition_str == "Fully Random":
        return FullyRandomMonsterShuffle()

    match = re.search(r"([0-9]+)", definition_str)
    if match is not None:
        return BiasedByStatTotalMonsterShuffle(int(match.groups()[0]))

    return None


@dataclass
class Monsters:
    randomize: bool = False
    include_bosses: Optional[bool] = None
    transfer_boss_item_drops: Optional[bool] = None
    include_starters: Optional[bool] = None
    include_gift_monsters: Optional[bool] = None
    swap_scout_chance: Optional[bool] = None
    swap_experience_drops: Optional[bool] = None
    swap_gold_drops: Optional[bool] = None
    randomization_policy: Optional[MonsterRandomizationPolicyDefinition] = None


@dataclass
class SkillSets:
    randomize: bool = False


@dataclass
class Other:
    remove_dialogue: bool = False


@dataclass
class State:
    original_rom: Optional[pathlib.Path] = None
    seed: Optional[int] = None
    region: Region = Region.NorthAmerica
    monsters: Monsters = field(default_factory=lambda: Monsters())
    skill_sets: SkillSets = field(default_factory=lambda: SkillSets())
    other: Other = field(default_factory=lambda: Other())
