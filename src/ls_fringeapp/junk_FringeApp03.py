"""
EFH 15/12/2009
App to process whole files of images

requires python 3.5 for f strings

"""

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox


# matplotlib.use("tkagg")

import matplotlib as mpl
import matplotlib.pyplot as plt


"""
For processing gauge block interferograms
"""


def on_btn_clicked(event):
    print("Ouch!!!")
    print(f"{event=}")
    file_path = filedialog.askopenfilename(
        title="Select a File",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
    )
    print(file_path)

    message = "Wavelengths Used\n"
    message += f"red vacuum wavelength = {111.11111111} nm\n"
    message += f"green vacuum wavelength = {222.2222222} nm\n"
    messagebox.showinfo("Vacuum Wavelengths", message)


if __name__ == "__main__":
    fig_menu = plt.figure(figsize=(10, 6), num="window title")

    ax1 = fig_menu.add_axes([0.1, 0.825, 0.2, 0.075])

    btn1 = mpl.widgets.Button(ax1, "Hit Me Again!")
    btn1.label.set_fontsize(16)
    btn1.on_clicked(on_btn_clicked)

    print(f"{tk.TkVersion=}")
    for f in tk.font.names():
        ff = tk.font.nametofont(f)
        ff.config(size=16)

    plt.show()
