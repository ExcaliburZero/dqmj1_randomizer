#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 1.0.5 on Sat Oct 12 20:04:52 2024
#
from typing import Any

import logging
import pathlib
import random

import wx  # type: ignore

from dqmj1_randomizer.setup_logging import setup_logging
from dqmj1_randomizer.randomize import randomize
from dqmj1_randomizer.state import State

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class Main(wx.Frame):
    def __init__(self, *args: Any, **kwds: Any) -> None:
        # begin wxGlade: Main.__init__
        setup_logging(pathlib.Path("log.txt"))
        self.state = State()
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((532, 328))
        self.SetTitle("DQMJ1 Unofficial Randomizer")

        self.panel_1 = wx.Panel(self, wx.ID_ANY)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        grid_sizer_1 = wx.FlexGridSizer(1, 6, 10, 10)
        sizer_1.Add(grid_sizer_1, 0, wx.ALL, 10)

        original_rom = wx.StaticText(self.panel_1, wx.ID_ANY, "Original ROM (*.nds)")
        original_rom.SetFont(
            wx.Font(
                9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""
            )
        )
        original_rom.SetToolTip('".nds" file of the ROM to randomize')
        grid_sizer_1.Add(original_rom, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 0)

        self.input_original_rom = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        grid_sizer_1.Add(self.input_original_rom, 0, 0, 0)

        self.OriginalRomBrowse = wx.Button(self.panel_1, wx.ID_ANY, "Browse")
        grid_sizer_1.Add(self.OriginalRomBrowse, 0, 0, 0)

        grid_sizer_1.Add((0, 0), 0, 0, 0)

        label_seed = wx.StaticText(self.panel_1, wx.ID_ANY, "Seed")
        label_seed.SetFont(
            wx.Font(
                9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""
            )
        )
        label_seed.SetToolTip("Number to use to control the randomness")
        grid_sizer_1.Add(label_seed, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 0)

        self.input_seed = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.input_seed.SetValue(str(random.randint(0, (2**32) - 1)))
        self.state.seed = int(self.input_seed.GetValue())
        grid_sizer_1.Add(self.input_seed, 0, 0, 0)

        self.notebook_1 = wx.Notebook(self.panel_1, wx.ID_ANY)
        sizer_1.Add(self.notebook_1, 1, wx.ALL | wx.EXPAND, 10)

        self.monsters_tab = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.monsters_tab, "Monsters")

        sizer_2 = wx.BoxSizer(wx.VERTICAL)

        grid_sizer_2 = wx.FlexGridSizer(3, 1, 4, 0)
        sizer_2.Add(grid_sizer_2, 1, wx.ALL | wx.EXPAND, 10)

        self.checkbox_monsters_include_bosses = wx.CheckBox(
            self.monsters_tab, wx.ID_ANY, "Include bosses"
        )
        self.state.monsters.include_bosses = (
            self.checkbox_monsters_include_bosses.GetValue() == 1
        )
        grid_sizer_2.Add(self.checkbox_monsters_include_bosses, 0, 0, 0)

        grid_sizer_3 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(grid_sizer_3, 1, wx.EXPAND, 0)

        grid_sizer_3.Add((20, 0), 0, 0, 0)

        self.checkbox_transfer_item_drop_to_replacement_monster = wx.CheckBox(
            self.monsters_tab, wx.ID_ANY, "Transfer item drop to replacement monsters"
        )
        self.checkbox_transfer_item_drop_to_replacement_monster.SetToolTip(
            "If checked, then the monsters that replace each boss will drop the same items as the boss monster. Useful for keeping player spell book drops the same."
        )
        self.checkbox_transfer_item_drop_to_replacement_monster.Enable(False)
        self.checkbox_transfer_item_drop_to_replacement_monster.SetValue(1)
        self.state.monsters.transfer_boss_item_drops = (
            self.checkbox_transfer_item_drop_to_replacement_monster.GetValue() == 1
        )
        grid_sizer_3.Add(
            self.checkbox_transfer_item_drop_to_replacement_monster, 0, 0, 0
        )

        self.checkbox_monsters_include_starters = wx.CheckBox(
            self.monsters_tab, wx.ID_ANY, "Include starters"
        )
        self.checkbox_monsters_include_starters.SetValue(1)
        self.state.monsters.include_starters = (
            self.checkbox_monsters_include_starters.GetValue() == 1
        )
        grid_sizer_2.Add(self.checkbox_monsters_include_starters, 0, 0, 0)

        self.button_1 = wx.Button(self.panel_1, wx.ID_ANY, "Randomize!")
        sizer_1.Add(self.button_1, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)

        self.monsters_tab.SetSizer(sizer_2)

        self.panel_1.SetSizer(sizer_1)

        self.Layout()

        self.Bind(wx.EVT_TEXT, self.changed_original_rom, self.input_original_rom)
        self.Bind(wx.EVT_BUTTON, self.select_original_rom, self.OriginalRomBrowse)
        self.Bind(wx.EVT_TEXT, self.changed_seed, self.input_seed)
        self.Bind(
            wx.EVT_CHECKBOX,
            self.changed_monsters_include_bosses,
            self.checkbox_monsters_include_bosses,
        )
        self.Bind(
            wx.EVT_CHECKBOX,
            self.changed_ter_im_drop_to_rep_mon,
            self.checkbox_transfer_item_drop_to_replacement_monster,
        )
        self.Bind(
            wx.EVT_CHECKBOX,
            self.changed_monsters_include_starters,
            self.checkbox_monsters_include_starters,
        )
        self.Bind(wx.EVT_BUTTON, self.create_output_rom, self.button_1)
        # end wxGlade

    def changed_seed(self, event):  # wxGlade: Main.<event_handler>
        raw_value = self.input_seed.GetValue()
        try:
            value = int(raw_value)
            self.state.seed = value
            logging.info(f"Changed seed to: {value}")
        except ValueError:
            logging.warning(f"Invalid seed: {raw_value}")

    def changed_original_rom(self, event):  # wxGlade: Main.<event_handler>
        raw_value = self.input_original_rom.GetValue()
        value = pathlib.Path(raw_value)
        self.state.original_rom = value
        logging.info(f"Changed original ROM to: {value}")

    def select_original_rom(self, event):  # wxGlade: Main.<event_handler>
        with wx.FileDialog(
            self,
            "Open original ROM",
            wildcard="NDS ROM files (*.nds)|*.nds",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            self.input_original_rom.SetValue(file_dialog.GetPath())

    def create_output_rom(self, event):  # wxGlade: Main.<event_handler>
        logging.info('User clicked "Randomize!"')

        with wx.FileDialog(
            self,
            "Create output ROM",
            wildcard="NDS ROM files (*.nds)|*.nds",
            style=wx.FD_OPEN,
        ) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                logging.info("User did not choose a file to write the output ROM to.")
                return

            output_rom_filepath = pathlib.Path(file_dialog.GetPath())
            try:
                result = randomize(self.state, output_rom_filepath)
                if not result:
                    logging.error(
                        f"Failed to generate randomized ROM and write it to: {output_rom_filepath}"
                    )

                wx.MessageBox(
                    f"Sucessfully wrote randomized ROM to: {output_rom_filepath}",
                    "Success",
                    wx.OK | wx.ICON_INFORMATION,
                )
            except Exception as e:
                logging.exception(e)
                logging.error(
                    f"Failed to generate randomized ROM and write it to: {output_rom_filepath}"
                )

    def changed_monsters_include_starters(self, event):  # wxGlade: Main.<event_handler>
        raw_value = self.checkbox_monsters_include_starters.GetValue()
        logging.info(f"User set monsters include starters: {raw_value}")

        assert isinstance(raw_value, int)
        self.state.monsters.include_starters = raw_value == 1

    def changed_monsters_include_bosses(self, event):  # wxGlade: Main.<event_handler>
        raw_value = self.checkbox_monsters_include_bosses.GetValue()
        logging.info(f"User set monsters include bosses: {raw_value}")

        assert isinstance(raw_value, int)
        self.state.monsters.include_bosses = raw_value == 1

        if raw_value == 1:
            self.checkbox_transfer_item_drop_to_replacement_monster.Enable()
        else:
            self.checkbox_transfer_item_drop_to_replacement_monster.Disable()

    def changed_ter_im_drop_to_rep_mon(self, event):  # wxGlade: Main.<event_handler>
        raw_value = self.checkbox_transfer_item_drop_to_replacement_monster.GetValue()
        logging.info(f"User set transfer item drop to replacement monster: {raw_value}")

        assert isinstance(raw_value, int)
        self.state.monsters.transfer_boss_item_drops = raw_value == 1


# end of class Main


class MyApp(wx.App):
    def OnInit(self) -> bool:
        self.frame = Main(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
