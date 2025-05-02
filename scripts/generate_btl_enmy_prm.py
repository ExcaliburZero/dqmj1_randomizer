import argparse
import pathlib
import random
import sys

MAGIC = bytes([0x42, 0x45, 0x50, 0x54])
ENTRY_SIZE_BYTES = 88

ENDIANESS = "little"


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--output_filepath", type=pathlib.Path, required=True)
    parser.add_argument("--num_entries", type=int, default=880)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args(argv)

    random.seed(args.seed)

    with args.output_filepath.open("wb") as output_stream:
        output_stream.write(MAGIC)
        output_stream.write(args.num_entries.to_bytes(4, ENDIANESS))

        for _ in range(0, args.num_entries):
            output_stream.write(random.randbytes(ENTRY_SIZE_BYTES))


if __name__ == "__main__":
    main(sys.argv[1:])
