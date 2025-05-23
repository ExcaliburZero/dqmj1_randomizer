import pathlib
from dataclasses import dataclass, field
from typing import Optional

from dqmj1_randomizer.randomize.regions import Region


@dataclass
class Monsters:
    randomize: bool = False
    include_bosses: Optional[bool] = None
    transfer_boss_item_drops: Optional[bool] = None
    include_starters: Optional[bool] = None
    include_gift_monsters: Optional[bool] = None


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
