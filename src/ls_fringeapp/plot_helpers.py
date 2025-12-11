from pathlib import Path
import matplotlib
from matplotlib.pyplot import figure, show
from matplotlib.patches import Circle
import numpy as np

from PIL import Image


import tkinter as tk
from tkinter import filedialog


from ls_fringeapp.poly_lasso import PolyLasso


# local version of FringeManager.annotate_fig
def draw_gauge(axes, img_array, drawdata: dict, peaks=True):
    axes.imshow(img_array, cmap=matplotlib.cm.gray)
    axes.axis("image")
    axes.plot(drawdata["xy"][:, 1], drawdata["xy"][:, 0], "or")
    axes.plot(drawdata["ccen"], drawdata["rcen"], "+c", ms=20)
    axes.plot(drawdata["co"], drawdata["ro"], "w-")
    axes.plot(drawdata["ci"], drawdata["ri"], "c-")
    if peaks:
        for col, peaks in enumerate(drawdata["pklist"]):
            x = col * np.ones_like(peaks)
            axes.plot(x, peaks, "+y")
    maxx = img_array.shape[1]
    for cepts in drawdata["interceptsp"]:
        axes.plot([0, maxx], [cepts, drawdata["slopep"] * maxx + cepts], "-m", lw=2)
    for cepts in drawdata["interceptsg"]:
        axes.plot([0, maxx], [cepts, drawdata["slopeg"] * maxx + cepts], "g-", lw=2)

    if drawdata["circle"] is not None:
        xy = (drawdata["ccen"], drawdata["rcen"])
        r = drawdata["circle"]
        circle_patch = Circle(xy, r, ec="c", lw=2)
        circle_patch.set_facecolor((0, 0, 0, 0))
        axes.add_artist(circle_patch)

    axes.axvline(x=drawdata["col_start"], ls="-.", c="c", lw=1)


class GetGaugeCorners:
    """
    a cut down version of fringe manager
    asks user via dialog for a list of image files
    presents images to user for user to select gauge corners via mouse clicks
    left mouse click on  top left gauge corner
    left click on bottom left gauge corner
    left click on bottom right gauge corner
    right click anywher to finish

    gauge co-ordinates are written to terminal


    """

    def __init__(self, ax, img_list=None):
        self.app_win = tk.Tk()
        self.app_win.withdraw()
        self.axes = ax
        self.figure = ax.figure
        self.canvas = ax.figure.canvas
        self.filetext = self.figure.text(0.5, 0.05, " ", horizontalalignment="center")

        self.canvas.mpl_connect("button_press_event", self.onpress)
        self.canvas.mpl_connect("key_press_event", self.keypress)

        self.img_array = []
        self.img_filename = None
        self.img_list = None
        self.lasso = None
        self.lasso_active = True

    def load_image_list(self):
        """
        prompts user to select images to process
        """
        img_list = filedialog.askopenfilenames(
            parent=self.app_win, title="Choose image files"
        )

        if img_list is None:
            return
        img_list = [Path(file) for file in img_list]
        self.image_folder = img_list[0].parent
        # split off folder name
        img_list = [name.name for name in img_list]

        img_list.sort()
        self.img_list = img_list
        self.img_index = 0
        print(f"{self.image_folder=}")
        print(f"{self.img_list=}")
        self.open_image()

    def open_image(self):
        """opens image in imagelist at position image_index"""
        img_basename = self.img_list[self.img_index]
        self.img_filename = self.image_folder / img_basename
        print(f"{self.img_filename=}")

        img = Image.open(self.img_filename)
        img.convert("L")
        self.img_array = np.asarray(img)
        if self.img_array.ndim > 2:
            self.img_array = self.img_array.mean(axis=2)
        self.axes.clear()
        self.axes.imshow(self.img_array, cmap=matplotlib.cm.gray)
        self.axes.axis("image")
        self.axes.axis("off")

        self.filetext.set_text(img_basename)

        self.lasso_active = True
        self.canvas.draw()

    def onpress(self, event):
        """set up polylasso when mouse is clicked"""
        print("in onpress")
        if self.canvas.widgetlock.locked():
            return
        if event.inaxes is None:
            return
        print(f"{self.lasso_active=}")
        if self.lasso_active:
            self.lasso = PolyLasso(event.inaxes, self.process_image)
            # acquire a lock on the widget drawing
            self.canvas.widgetlock(self.lasso)
            print("in lasso")

    def keypress(self, event):
        """maps a key to opening new file
        careful in choice of keys as event is also passed to toolbar
        will replace this with/ add interface buttons
        """
        print(event.key)

        if event.inaxes is None:
            return
        if event.key in ["N", "n"]:
            self.load_image_list()
        if event.key == "pagedown":
            self.next_image()
        if event.key == "pageup":
            self.prev_image()
        if event.key == "delete":
            self.redo_image()

    def next_image(self):
        self.img_index = self.img_index + 1
        if self.img_index >= len(self.img_list):
            self.img_index = 0
        self.open_image()

    def prev_image(self):
        self.img_index = self.img_index - 1
        if self.img_index < 0:
            self.img_index = len(self.img_list) - 1
        self.open_image()

    def redo_image(self):
        """
        reload image without annotation
        delete from shelf file and reload
        """
        self.open_image()
        self.lasso_active = True

    def process_image(self, _ax, _lasso_line, verts):
        """called after polylasso finished, processes image and prints ff"""
        # print verts
        print("process image")
        self.lasso_active = False
        xygb = np.fliplr(np.asarray(verts)[:3, :])
        self.canvas.draw_idle()
        text = (
            self.img_filename.name
            + "\t"
            + ("%.5g\t" * xygb.ravel().size) % tuple(xygb.ravel())
        )
        print(text)


if __name__ == "__main__":
    fig = figure(figsize=(6, 6), dpi=80)
    axes = fig.add_axes([0.1, 0.1, 0.8, 0.8])

    gman = GetGaugeCorners(axes)
    gman.load_image_list()
    show()
