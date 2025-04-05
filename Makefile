.PHONY: compile format lint

compile:
	pyinstaller dqmj1_randomizer/main.py --add-data "dqmj1_randomizer/data:dqmj1_randomizer/data" --noconfirm -n dqmj1_randomizer

format:
	ruff format .
	
lint:
	mypy .
	ruff format --check .
	ruff check .