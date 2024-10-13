from dataclasses import dataclass, field
from typing import Optional

import pathlib


@dataclass
class Monsters:
    include_bosses: Optional[bool] = None
    include_starters: Optional[bool] = None


@dataclass
class State:
    original_rom: Optional[pathlib.Path] = None
    seed: Optional[int] = None
    monsters: Monsters = field(default_factory=lambda: Monsters())
