from dataclasses import dataclass
from typing import Optional

import pathlib


@dataclass
class State:
    original_rom: Optional[pathlib.Path] = None
    seed: Optional[int] = None
