.PHONY: compile format lint test coverage_report update_baselines create_input_files

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
	pytest unit_tests regression_tests

coverage_report:
	pytest --cov-report=html:coverage --cov-report=xml:coverage.xml --cov=dqmj1_randomizer unit_tests regression_tests

update_baselines:
	python -m regression_tests.test_btl_enmy_prm

create_input_files:
	python scripts/generate_btl_enmy_prm.py \
		--output_filepath regression_tests/inputs/dummy_BtlEnmyPrm.bin