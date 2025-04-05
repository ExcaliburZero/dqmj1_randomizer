.PHONY: compile lint

compile:
	pyinstaller dqmj1_randomizer/main.py --add-data "dqmj1_randomizer/data:dqmj1_randomizer/data" --noconfirm -n dqmj1_randomizer
	
lint:
	mypy dqmj1_randomizer
	ruff format --check .
	ruff check dqmj1_randomizer