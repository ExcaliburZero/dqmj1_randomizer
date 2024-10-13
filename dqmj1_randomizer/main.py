#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 1.0.5 on Sat Oct 12 20:04:52 2024
#

import random

import wx

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class Main(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: Main.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((532, 328))
        self.SetTitle("DQMJ Unofficial Randomizer")

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

        self.InputNdsBrowse = wx.Button(self.panel_1, wx.ID_ANY, "Browse")
        grid_sizer_1.Add(self.InputNdsBrowse, 0, 0, 0)

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
        grid_sizer_1.Add(self.input_seed, 0, 0, 0)

        self.notebook_1 = wx.Notebook(self.panel_1, wx.ID_ANY)
        sizer_1.Add(self.notebook_1, 1, wx.ALL | wx.EXPAND, 10)

        self.monsters_tab = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.monsters_tab, "Monsters")

        sizer_2 = wx.BoxSizer(wx.VERTICAL)

        grid_sizer_2 = wx.FlexGridSizer(2, 1, 4, 0)
        sizer_2.Add(grid_sizer_2, 1, wx.ALL | wx.EXPAND, 10)

        self.checkbox_monsters_include_bosses = wx.CheckBox(
            self.monsters_tab, wx.ID_ANY, "Include bosses"
        )
        grid_sizer_2.Add(self.checkbox_monsters_include_bosses, 0, 0, 0)

        self.checkbox_monsters_include_starters = wx.CheckBox(
            self.monsters_tab, wx.ID_ANY, "Include starters"
        )
        self.checkbox_monsters_include_starters.SetValue(1)
        grid_sizer_2.Add(self.checkbox_monsters_include_starters, 0, 0, 0)

        self.notebook_1_pane_2 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.notebook_1_pane_2, "new tab")

        self.button_1 = wx.Button(self.panel_1, wx.ID_ANY, "Randomize!")
        sizer_1.Add(self.button_1, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)

        self.monsters_tab.SetSizer(sizer_2)

        self.panel_1.SetSizer(sizer_1)

        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.select_input_nds, self.InputNdsBrowse)
        # end wxGlade

    def select_input_nds(self, event):  # wxGlade: Main.<event_handler>
        print("Hello!")
        event.Skip()


# end of class Main


class MyApp(wx.App):
    def OnInit(self):
        self.frame = Main(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
