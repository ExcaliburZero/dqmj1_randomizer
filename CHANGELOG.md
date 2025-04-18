# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2025-04-18

### Fixed

- Incarnus being randomized when randomizing gift monsters, which could lead to game crashing during cutscenes. (#4)

## [0.3.0] - 2025-04-05

### Added

- "Include gift monsters" option for monster randomization.
- More helpful error messages for likely errors.

### Fixed

- Cases where failing to generate a randomized ROM would still show a success popup window.
- Output ROM file chooser dialogue having an "Open" button instead of a "Save" button.

## [0.2.1] - 2025-04-04

### Fixed

- Item drop for boss Belial not being transferred when the relevant option was set.
- Crash on Linux when trying to lookup a data file to build the randomized ROM.

## [0.2.0] - 2025-04-04

### Added

- "Transfer item drop to replacement monsters" option for monster randomization.

### Changed

- Default behavior for boss monster randomization to transfer item drops to replacement monsters.

## [0.1.0] - 2024-10-13

### Added

- Monster randomization.
- "Include bosses" option for monster randomization.
- "Include starters" option for monster randomization.
