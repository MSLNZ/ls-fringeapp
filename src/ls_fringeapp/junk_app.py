import matplotlib as mpl
import matplotlib.pyplot as plt

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox


class ButtonPanel:
    def __init__(self):
        self.make_gui()

    def make_gui(self):
        # fig_gb = plt.figure(figsize=(6, 6), dpi=80)
        # self.axes_gb = fig_gb.add_axes([0.1, 0.1, 0.8, 0.8])

        self.fig_menu = plt.figure(figsize=(10, 6))

        print(f"{tk.TkVersion=}")
        for f in tk.font.names():
            ff = tk.font.nametofont(f)
            ff.config(size=16)

        axload = self.fig_menu.add_axes([0.1, 0.825, 0.2, 0.075])

        axnext = self.fig_menu.add_axes([0.1, 0.625, 0.2, 0.075])

        bload = mpl.widgets.Button(axload, "show file")
        bload.on_clicked(self.show_file_dialog)

        bnext = mpl.widgets.Button(axnext, "show info")
        bnext.on_clicked(self.show_info_box)
        # self.show_info_box(None)
        plt.show()

    def show_file_dialog(self, event):
        print("Ouch!!!")
        print(f"{event=}")
        file_path = filedialog.askopenfilename(
            title="Select a File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        print(file_path)

    def show_info_box(self, event):
        message = "Wavelengths Used\n"
        message += f"red vacuum wavelength = {111.11111111} nm\n"
        message += f"green vacuum wavelength = {222.2222222} nm\n"
        messagebox.showinfo(
            "Vacuum Wavelengths",
            message,
        )


if __name__ == "__main__":
    btn_panel = ButtonPanel()
