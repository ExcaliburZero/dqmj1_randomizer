import abc
import pathlib
import shutil
import unittest

BASELINES_DIR = pathlib.Path(__file__).parent / "baselines"
INPUTS_DIR = pathlib.Path(__file__).parent / "inputs"
WORK_DIR = pathlib.Path(__file__).parent / "work_dirs"


def to_snake_case(string: str) -> str:
    updated_chars: list[str] = []
    for c in string:
        if c.isupper() and len(updated_chars) != 0:
            updated_chars.append("_")

        updated_chars.append(c.lower())

    return "".join(updated_chars)


class RegressionTest(unittest.TestCase, abc.ABC):
    @abc.abstractmethod
    def run_case(self) -> list[pathlib.Path]:
        raise NotImplementedError

    def test_case(self) -> None:
        self._clear_and_create_work_dir()
        output_filepaths = self.run_case()
        self._assert_equals_baseline(output_filepaths)

    def update_baseline(self) -> None:
        self._clear_and_create_baseline_dir()
        self._clear_and_create_work_dir()
        output_filepaths = self.run_case()

        for filepath in output_filepaths:
            if not filepath.is_relative_to(self.work_dir):
                raise AssertionError

            baseline_filepath = self.baseline_dir / filepath.relative_to(self.work_dir)
            shutil.copy(filepath, baseline_filepath)

    def _assert_equals_baseline(self, output_filepaths: list[pathlib.Path]) -> None:
        if len(output_filepaths) == 0:
            raise AssertionError

        for filepath in output_filepaths:
            if not filepath.is_relative_to(self.work_dir):
                raise AssertionError

            baseline_filepath = self.baseline_dir / filepath.relative_to(self.work_dir)

            self._assert_files_equal(filepath, baseline_filepath)

    def _assert_files_equal(
        self, actual_filepath: pathlib.Path, baseline_filepath: pathlib.Path
    ) -> None:
        self.assertTrue(actual_filepath.exists())
        self.assertTrue(actual_filepath.is_file())

        self.assertTrue(baseline_filepath.exists())
        self.assertTrue(baseline_filepath.is_file())

        self.assertEqual(
            baseline_filepath.stat().st_size, actual_filepath.stat().st_size
        )

        with actual_filepath.open("rb") as input_stream:
            actual = input_stream.read()

        with baseline_filepath.open("rb") as input_stream:
            expected = input_stream.read()

        self.assertEqual(expected, actual)

    def _clear_and_create_baseline_dir(self) -> None:
        baseline_dir = self.baseline_dir
        baseline_dir.mkdir(exist_ok=True, parents=True)

        shutil.rmtree(baseline_dir)
        baseline_dir.mkdir(exist_ok=True, parents=True)

    def _clear_and_create_work_dir(self) -> None:
        work_dir = self.work_dir
        work_dir.mkdir(exist_ok=True, parents=True)

        shutil.rmtree(work_dir)
        work_dir.mkdir(exist_ok=True, parents=True)

    @property
    def name(self) -> str:
        return to_snake_case(type(self).__name__)

    @property
    def baseline_dir(self) -> pathlib.Path:
        return BASELINES_DIR / self.name

    @property
    def inputs_dir(self) -> pathlib.Path:
        return INPUTS_DIR

    @property
    def work_dir(self) -> pathlib.Path:
        return WORK_DIR / self.name
