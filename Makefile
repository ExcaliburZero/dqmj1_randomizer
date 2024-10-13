.PHONY: compile lint

compile:
	pyinstaller dqmj1_randomizer/main.py --noconfirm
	
lint:
	mypy .
	black --check .