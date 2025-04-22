import logging
import pathlib
import threading
import traceback

from pubsub import pub  # type: ignore

from dqmj1_randomizer.randomize.randomize import RandomizationException, randomize
from dqmj1_randomizer.state import State

GITHUB_ISSUES_URL = "https://github.com/ExcaliburZero/dqmj1_randomizer/issues"


class RandomizeThread(threading.Thread):
    def __init__(self, state: State, output_rom_filepath: pathlib.Path) -> None:
        threading.Thread.__init__(self)

        self.state = state
        self.output_rom_filepath = output_rom_filepath

    def run(self) -> None:
        pub.sendMessage("randomize.start")

        try:
            randomize(self.state, self.output_rom_filepath)

            pub.sendMessage(
                "randomize.successful",
                message=f"Successfully wrote randomized ROM to: {self.output_rom_filepath}",
            )
        except RandomizationException as e:
            logging.exception(e)
            logging.error(
                f"Failed to generate randomized ROM and write it to: {self.output_rom_filepath}"
            )
            pub.sendMessage(
                "randomize.failed",
                message=f"Failed to generate randomized ROM\n\n{e.msg}",
            )
        except Exception as e:
            logging.exception(e)
            logging.error(
                f"Failed to generate randomized ROM and write it to: {self.output_rom_filepath}"
            )
            pub.sendMessage(
                "randomize.failed",
                message=f"Failed to properly generate randomized ROM due to unknown error\n\nPlease report this error to the developer: {GITHUB_ISSUES_URL}\n\n{traceback.format_exc()}",
            )
