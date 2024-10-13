import wx


SUCCESS = 0
FAILURE = 1


def main() -> None:
    app = wx.App(False)

    frame = wx.Frame(None, wx.ID_ANY, "Hello WOrld!")
    frame.Show(True)

    app.MainLoop()


if __name__ == "__main__":
    main()
