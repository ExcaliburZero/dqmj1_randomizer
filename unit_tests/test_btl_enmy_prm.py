import io
import unittest

from dqmj1_randomizer.randomize.btl_enmy_prm import (
    BtlEnmyPrm,
    BtlEnmyPrmEntry,
    EnemySkillEntry,
    ItemDrop,
)


class TestItemDrop(unittest.TestCase):
    def test_from_bin(self) -> None:
        input_stream = io.BytesIO(b"\x01\x00\x02\x00")

        actual = ItemDrop.from_bin(input_stream)

        expected = ItemDrop(1, 2)
        self.assertEqual(expected, actual)

    def test_write_bin(self) -> None:
        item_drop = ItemDrop(1, 2)
        output_stream = io.BytesIO()

        item_drop.write_bin(output_stream)

        actual = output_stream.getbuffer().tobytes()

        expected = b"\x01\x00\x02\x00"
        self.assertEqual(expected, actual)


class TestEnemySkillEntry(unittest.TestCase):
    def test_from_bin(self) -> None:
        input_stream = io.BytesIO(b"\x01\x00\x02\x00")

        actual = EnemySkillEntry.from_bin(input_stream)

        expected = EnemySkillEntry(1, 2)
        self.assertEqual(expected, actual)

    def test_write_bin(self) -> None:
        enemy_skill_entry = EnemySkillEntry(1, 2)
        output_stream = io.BytesIO()

        enemy_skill_entry.write_bin(output_stream)

        actual = output_stream.getbuffer().tobytes()

        expected = b"\x01\x00\x02\x00"
        self.assertEqual(expected, actual)


class TestBtlEnmyPrmEntry(unittest.TestCase):
    def test_from_bin(self) -> None:
        input_stream = io.BytesIO(
            # species_id
            b"\x01\x00"
            # unknown_a
            b"\x00\x00\x00\x00\x00\x00"
            # skills
            b"\x00\x00\x01\x00"
            b"\x00\x00\x02\x00"
            b"\x00\x00\x03\x00"
            b"\x00\x00\x04\x00"
            b"\x00\x00\x05\x00"
            b"\x00\x00\x06\x00"
            # item_drops
            b"\x01\x00\x00\x00"
            b"\x02\x00\x07\x00"
            # gold
            b"\x20\x01"
            # unknown_b
            b"\x00\x00"
            # exp
            b"\x02\x00"
            # unknown_c
            b"\x00\x00"
            # level
            b"\x10"
            # unknown_d
            b"\x00"
            # unknown_e
            b"\x00"
            # scout_chance
            b"\x05"
            # max_hp
            b"\x05\x00"
            # max_mp
            b"\x06\x00"
            # attack
            b"\x07\x00"
            # defense
            b"\x08\x00"
            # agility
            b"\x09\x00"
            # wisdom
            b"\x0a\x00"
            # unknown_f
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            # skill_set_ids
            b"\x01\x02\x03"
            # unknown_g
            b"\x00"
        )

        actual = BtlEnmyPrmEntry.from_bin(input_stream)

        expected = BtlEnmyPrmEntry(
            species_id=1,
            unknown_a=b"\x00\x00\x00\x00\x00\x00",
            skills=[
                EnemySkillEntry(0, 1),
                EnemySkillEntry(0, 2),
                EnemySkillEntry(0, 3),
                EnemySkillEntry(0, 4),
                EnemySkillEntry(0, 5),
                EnemySkillEntry(0, 6),
            ],
            item_drops=[
                ItemDrop(1, 0),
                ItemDrop(2, 7),
            ],
            gold=288,
            unknown_b=b"\x00\x00",
            exp=2,
            unknown_c=b"\x00\x00",
            level=16,
            unknown_d=b"\x00",
            unknown_e=0,
            scout_chance=5,
            max_hp=5,
            max_mp=6,
            attack=7,
            defense=8,
            agility=9,
            wisdom=10,
            unknown_f=b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            skill_set_ids=[1, 2, 3],
            unknown_g=b"\x00",
        )
        self.assertEqual(expected, actual)

    def test_write_bin(self) -> None:
        btl_enmy_prm_entry = BtlEnmyPrmEntry(
            species_id=1,
            unknown_a=b"\x00\x00\x00\x00\x00\x00",
            skills=[
                EnemySkillEntry(0, 1),
                EnemySkillEntry(0, 2),
                EnemySkillEntry(0, 3),
                EnemySkillEntry(0, 4),
                EnemySkillEntry(0, 5),
                EnemySkillEntry(0, 6),
            ],
            item_drops=[
                ItemDrop(1, 0),
                ItemDrop(2, 7),
            ],
            gold=288,
            unknown_b=b"\x00\x00",
            exp=2,
            unknown_c=b"\x00\x00",
            level=16,
            unknown_d=b"\x00",
            unknown_e=0,
            scout_chance=5,
            max_hp=5,
            max_mp=6,
            attack=7,
            defense=8,
            agility=9,
            wisdom=10,
            unknown_f=b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            skill_set_ids=[1, 2, 3],
            unknown_g=b"\x00",
        )
        output_stream = io.BytesIO()

        btl_enmy_prm_entry.write_bin(output_stream)

        actual = output_stream.getbuffer().tobytes()

        expected = (
            # species_id
            b"\x01\x00"
            # unknown_a
            b"\x00\x00\x00\x00\x00\x00"
            # skills
            b"\x00\x00\x01\x00"
            b"\x00\x00\x02\x00"
            b"\x00\x00\x03\x00"
            b"\x00\x00\x04\x00"
            b"\x00\x00\x05\x00"
            b"\x00\x00\x06\x00"
            # item_drops
            b"\x01\x00\x00\x00"
            b"\x02\x00\x07\x00"
            # gold
            b"\x20\x01"
            # unknown_b
            b"\x00\x00"
            # exp
            b"\x02\x00"
            # unknown_c
            b"\x00\x00"
            # level
            b"\x10"
            # unknown_d
            b"\x00"
            # unknown_e
            b"\x00"
            # scout_chance
            b"\x05"
            # max_hp
            b"\x05\x00"
            # max_mp
            b"\x06\x00"
            # attack
            b"\x07\x00"
            # defense
            b"\x08\x00"
            # agility
            b"\x09\x00"
            # wisdom
            b"\x0a\x00"
            # unknown_f
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            # skill_set_ids
            b"\x01\x02\x03"
            # unknown_g
            b"\x00"
        )
        self.assertEqual(expected, actual)


class TestBtlEnmyPrm(unittest.TestCase):
    def test_from_bin(self) -> None:
        input_stream = io.BytesIO(
            # magic
            b"\x42\x45\x50\x54"
            # length
            b"\x01\x00\x00\x00"
            # species_id
            b"\x01\x00"
            # unknown_a
            b"\x00\x00\x00\x00\x00\x00"
            # skills
            b"\x00\x00\x01\x00"
            b"\x00\x00\x02\x00"
            b"\x00\x00\x03\x00"
            b"\x00\x00\x04\x00"
            b"\x00\x00\x05\x00"
            b"\x00\x00\x06\x00"
            # item_drops
            b"\x01\x00\x00\x00"
            b"\x02\x00\x07\x00"
            # gold
            b"\x20\x01"
            # unknown_b
            b"\x00\x00"
            # exp
            b"\x02\x00"
            # unknown_c
            b"\x00\x00"
            # level
            b"\x10"
            # unknown_d
            b"\x00"
            # unknown_e
            b"\x00"
            # scout_chance
            b"\x05"
            # max_hp
            b"\x05\x00"
            # max_mp
            b"\x06\x00"
            # attack
            b"\x07\x00"
            # defense
            b"\x08\x00"
            # agility
            b"\x09\x00"
            # wisdom
            b"\x0a\x00"
            # unknown_f
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            # skill_set_ids
            b"\x01\x02\x03"
            # unknown_g
            b"\x00"
        )

        actual = BtlEnmyPrm.from_bin(input_stream)

        expected = BtlEnmyPrm(
            [
                BtlEnmyPrmEntry(
                    species_id=1,
                    unknown_a=b"\x00\x00\x00\x00\x00\x00",
                    skills=[
                        EnemySkillEntry(0, 1),
                        EnemySkillEntry(0, 2),
                        EnemySkillEntry(0, 3),
                        EnemySkillEntry(0, 4),
                        EnemySkillEntry(0, 5),
                        EnemySkillEntry(0, 6),
                    ],
                    item_drops=[
                        ItemDrop(1, 0),
                        ItemDrop(2, 7),
                    ],
                    gold=288,
                    unknown_b=b"\x00\x00",
                    exp=2,
                    unknown_c=b"\x00\x00",
                    level=16,
                    unknown_d=b"\x00",
                    unknown_e=0,
                    scout_chance=5,
                    max_hp=5,
                    max_mp=6,
                    attack=7,
                    defense=8,
                    agility=9,
                    wisdom=10,
                    unknown_f=b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    skill_set_ids=[1, 2, 3],
                    unknown_g=b"\x00",
                )
            ]
        )
        self.assertEqual(expected, actual)

    def test_write_bin(self) -> None:
        btl_enmy_prm = BtlEnmyPrm(
            [
                BtlEnmyPrmEntry(
                    species_id=1,
                    unknown_a=b"\x00\x00\x00\x00\x00\x00",
                    skills=[
                        EnemySkillEntry(0, 1),
                        EnemySkillEntry(0, 2),
                        EnemySkillEntry(0, 3),
                        EnemySkillEntry(0, 4),
                        EnemySkillEntry(0, 5),
                        EnemySkillEntry(0, 6),
                    ],
                    item_drops=[
                        ItemDrop(1, 0),
                        ItemDrop(2, 7),
                    ],
                    gold=288,
                    unknown_b=b"\x00\x00",
                    exp=2,
                    unknown_c=b"\x00\x00",
                    level=16,
                    unknown_d=b"\x00",
                    unknown_e=0,
                    scout_chance=5,
                    max_hp=5,
                    max_mp=6,
                    attack=7,
                    defense=8,
                    agility=9,
                    wisdom=10,
                    unknown_f=b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    skill_set_ids=[1, 2, 3],
                    unknown_g=b"\x00",
                )
            ]
        )
        output_stream = io.BytesIO()

        btl_enmy_prm.write_bin(output_stream)

        actual = output_stream.getbuffer().tobytes()

        expected = (
            # magic
            b"\x42\x45\x50\x54"
            # length
            b"\x01\x00\x00\x00"
            # species_id
            b"\x01\x00"
            # unknown_a
            b"\x00\x00\x00\x00\x00\x00"
            # skills
            b"\x00\x00\x01\x00"
            b"\x00\x00\x02\x00"
            b"\x00\x00\x03\x00"
            b"\x00\x00\x04\x00"
            b"\x00\x00\x05\x00"
            b"\x00\x00\x06\x00"
            # item_drops
            b"\x01\x00\x00\x00"
            b"\x02\x00\x07\x00"
            # gold
            b"\x20\x01"
            # unknown_b
            b"\x00\x00"
            # exp
            b"\x02\x00"
            # unknown_c
            b"\x00\x00"
            # level
            b"\x10"
            # unknown_d
            b"\x00"
            # unknown_e
            b"\x00"
            # scout_chance
            b"\x05"
            # max_hp
            b"\x05\x00"
            # max_mp
            b"\x06\x00"
            # attack
            b"\x07\x00"
            # defense
            b"\x08\x00"
            # agility
            b"\x09\x00"
            # wisdom
            b"\x0a\x00"
            # unknown_f
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            # skill_set_ids
            b"\x01\x02\x03"
            # unknown_g
            b"\x00"
        )
        self.assertEqual(expected, actual)
