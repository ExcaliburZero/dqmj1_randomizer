# DQMJ1 Unofficial Randomizer
An unofficial randomizer for *Dragon Quest Monsters: Joker 1* for the Nintendo DS.

![Screenshot of the randomizer GUI](img/screenshot.png)

## Download
Download the latest release of DQMJ1 Unofficial Randomizer for your operating system at the link below:

https://github.com/ExcaliburZero/dqmj1_randomizer/releases

## Development
### Building exectuable
```bash
# Download the source code
git clone https://github.com/ExcaliburZero/dqmj1_randomizer.git
cd dqmj1_randomizer

# Install the library
pip install -e .

# Create the executable
make compile
```

### Testing without building executable (faster)
```bash
# Download the source code
git clone https://github.com/ExcaliburZero/dqmj1_randomizer.git
cd dqmj1_randomizer

# Install the library
pip install -e .

# Run the program
python dqmj1_randomizer/main.py
```