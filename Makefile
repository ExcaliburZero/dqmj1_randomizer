.PHONY: compile format lint test create_input_files

compile:
	pyinstaller dqmj1_randomizer/main.py --add-data "dqmj1_randomizer/data:dqmj1_randomizer/data" --noconfirm -n dqmj1_randomizer

format:
	ruff check --select I --fix .
	ruff format .
	
lint:
	mypy .
	ruff format --check .
	ruff check .

test:
	pytest regression_tests

create_input_files:
	python scripts/generate_btl_enmy_prm.py \
		--output_filepath regression_tests/inputs/dummy_BtlEnmyPrm.bin