import inspect
import pathlib
import sys

from dqmj1_randomizer.data import data_path
from dqmj1_randomizer.randomize.btl_enmy_prm import randomize_btl_enmy_prm
from dqmj1_randomizer.randomize.regions import Region
from dqmj1_randomizer.state import Monsters, State

from .util import RegressionTest


class RandomizeMonstersSimplest(RegressionTest):
    def run_case(self) -> list[pathlib.Path]:
        output_filepath = self.work_dir / "randomized_dummy_BtlEnmyPrm.bin"
        input_filepath = self.inputs_dir / "dummy_BtlEnmyPrm.bin"

        state = State(
            original_rom=None,
            seed=42,
            region=Region.NorthAmerica,
            monsters=Monsters(
                randomize=True,
                include_bosses=True,
                transfer_boss_item_drops=False,
                include_starters=True,
                include_gift_monsters=True,
            ),
        )

        with (
            input_filepath.open("rb") as input_stream,
            output_filepath.open("wb") as output_stream,
        ):
            randomize_btl_enmy_prm(
                state=state, input_stream=input_stream, output_stream=output_stream
            )

        return [output_filepath]


if __name__ == "__main__":
    for _, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if issubclass(obj, RegressionTest) and obj != RegressionTest:
            instance = obj()
            instance.update_baseline()
