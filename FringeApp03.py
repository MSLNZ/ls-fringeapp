"""
EFH 15/12/2009
App to process whole files of images

requires python 3.5 for f strings

"""

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import os
import os.path
import datetime
import shelve

from PIL import Image
import numpy as np
import matplotlib

matplotlib.use("qtagg")

from matplotlib.pyplot import figure, show
from matplotlib.widgets import Button

from poly_lasso import PolyLasso
import fringeprocess
import gauge_length

import load_equipment_data

ObliquityCorrection = 1.00000013
CalDataFileName = (
    r"C:\Users\c.young\OneDrive - Callaghan Innovation\EQUIPREG\XML Files\cal_data.xml"
)
WorkingDir = r"C:\Users\c.young\OneDrive - Callaghan Innovation\Jobs"


"""
For processing gauge block interferograms
"""

# data type for reading in comma delimited files specifying measurement data and file names
DTRG = np.dtype(
    [
        ("NominalSize", float),
        ("SerialNo", (str, 16)),
        ("RedDateTime", float),
        ("GreenDateTime", float),
        ("SetId", (str, 16)),
        ("PlatenId", int),
        ("Observer", (str, 16)),
        ("Side", int),
        ("ExpCoeff", float),
        ("Units", (str, 16)),
        ("TRAir", float),
        ("TGAir", float),
        ("TR", float),
        ("TG", float),
        ("PR", float),
        ("PG", float),
        ("HR", float),
        ("HG", float),
        ("RedFileName", (str, 256)),
        ("GreenFileName", (str, 256)),
    ]
)

DTR = np.dtype(
    [
        ("NominalSize", float),
        ("SerialNo", (str, 16)),
        ("RedDateTime", float),
        ("SetId", (str, 16)),
        ("PlatenId", int),
        ("Observer", (str, 16)),
        ("Side", int),
        ("ExpCoeff", float),
        ("Units", (str, 16)),
        ("TRAir", float),
        ("TR", float),
        ("PR", float),
        ("HR", float),
        ("RedFileName", (str, 256)),
    ]
)


class FringeManager:
    """simple gauge block picking interface and ff calculator"""

    def __init__(self, ax, menu):
        self.app_win = tk.Tk()
        self.axes = ax
        self.figure = ax.figure
        self.canvas = ax.figure.canvas
        self.filetext = self.figure.text(0.5, 0.05, " ", horizontalalignment="center")
        self.fftext = self.figure.text(0.5, 0.02, " ", horizontalalignment="center")
        self.canvas.mpl_connect("button_press_event", self.onpress)
        self.canvas.mpl_connect("key_press_event", self.keypress)

        self.ffrac = {}
        self.gauge_data = []
        self.gauge_data_filename = ""
        self.img_array = []
        self.img_filename = ""
        self.img_index = 0
        self.img_list = []
        self.lasso = None
        self.lasso_active = True
        self.ff_text_dict = {}
        self.gn_text_dict = {}
        self.shelf_filename = ""
        self.red_green = True

        self.fig_menu = menu

    def process_image(self, _ax, _lasso_line, verts):
        """called after polylasso finished, processes image and prints ff"""
        # print verts
        print("process image")
        self.lasso_active = False
        xygb = np.fliplr(np.asarray(verts)[:3, :])
        self.canvas.draw_idle()
        self.canvas.widgetlock.release(self.lasso)
        del self.lasso
        ffrac, drawdata = fringeprocess.array2frac(self.img_array, xygb, drawinfo=True)
        img_basename = os.path.basename(self.img_filename)
        self.ffrac[img_basename] = ffrac
        self.annotate_fig(drawdata)
        self.ff_text_dict[img_basename].set_text("%6.3f" % ffrac)
        self.fig_menu.canvas.draw()
        self.canvas.draw()
        text = (
            "%.6g\t" % ffrac
            + img_basename
            + "\t"
            + ("%.5g\t" * xygb.ravel().size) % tuple(xygb.ravel())
        )
        print(text)
        # notes = EasyDialogs.AskString('Notes on fitting')
        notes = " "
        timestr = datetime.datetime.now().isoformat(" ")

        text = text + "\t" + timestr + "\t" + notes
        logfile = open(
            os.path.join(os.path.dirname(self.img_filename), "fflog.txt"), "a"
        )
        logfile.write(text + "\n")
        logfile.close()
        # also shelve ffrac, drawdata, timestr, notes with img_filename as key

        db = shelve.open(self.shelf_filename)
        db[img_basename] = [ffrac, drawdata, timestr, notes]
        db.close()

    def onpress(self, event):
        """set up polylasso when mouse is clicked"""
        if self.canvas.widgetlock.locked():
            return
        if event.inaxes is None:
            return
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
            self.load_gauge_data()
        if event.key == "pagedown":
            self.next_image()
        if event.key == "pageup":
            self.prev_image()
        if event.key == "end":
            self.calculate_output()
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

    def next(self, _):
        self.next_image()

    def prev(self, _):
        self.prev_image()

    def load(self, _):
        self.load_gauge_data()

    def redo(self, _):
        self.redo_image()

    def calc0(self, _):
        self.calculate_output(False)

    def calcall(self, _):
        if self.red_green:
            self.calculate_output(True)
        else:
            messagebox.showinfo(
                "Info", "Can't calculate mutliple orders without green images"
            )

    def redo_image(self):
        """
        reload image without annotation
        delete from shelf file and reload
        """
        shelfnm = os.path.join(os.path.dirname(self.img_filename), "info.shf")
        db = shelve.open(shelfnm)
        img_basename = os.path.basename(self.img_filename)

        if img_basename in db:
            del db[img_basename]
        db.close()
        self.open_image()
        self.lasso_active = True

    def open_image(self):
        """opens image in imagelist at position image_index"""
        img_filename = self.img_list[self.img_index]
        print(img_filename)
        parts = os.path.split(img_filename)

        # self.img_filename = os.path.join(parts[0], "cropped", parts[1])
        self.img_filename = os.path.normpath(img_filename)
        img = Image.open(self.img_filename)
        img.convert("L")
        self.img_array = np.asarray(img)
        if self.img_array.ndim > 2:
            self.img_array = self.img_array.mean(axis=2)
        self.axes.clear()
        self.axes.imshow(self.img_array, cmap=matplotlib.cm.gray)
        self.axes.axis("image")
        self.axes.axis("off")
        img_basename = os.path.basename(self.img_filename)
        self.filetext.set_text(img_basename)
        self.fftext.set_text(" ")
        self.lasso_active = True
        # check if image has an entry in directory's shelf file
        # if so use it to annotate image

        db = shelve.open(self.shelf_filename)
        if img_basename in db:
            print("found ", img_basename, " on shelf")
            [ffrac, drawdata, timestr, notes] = db[img_basename]
            self.ffrac[img_basename] = ffrac
            self.annotate_fig(drawdata)
            self.lasso_active = False
        db.close()
        self.canvas.draw()

    def load_gauge_data(self):
        """
        prompts user to open file written by excel program, reads it and creates
        a list of images to process
        """
        # Build a list of tuples for each file type the file dialog should display
        my_filetypes = [("all files", ".*"), ("text files", ".txt")]
        txt_name = filedialog.askopenfilename(
            parent=self.app_win,
            initialdir=WorkingDir,
            title="Select text file written Gauge Block File Writer App",
            filetypes=my_filetypes,
        )

        if txt_name:
            self.gauge_data_filename = txt_name
            # determine if we're using green as well as red
            # use _r as last two characters of file if red only
            # anything else is assumed to include red
            with open(txt_name) as f:
                line1 = f.readline()
            self.red_green = not (os.path.splitext(txt_name)[0][-2:] == "_r")

            parts = os.path.split(txt_name)

            if self.red_green:
                self.gauge_data = np.loadtxt(txt_name, delimiter=",", dtype=DTRG)
            else:
                self.gauge_data = np.loadtxt(txt_name, dtype=DTR, delimiter=",")
            img_list = list(self.gauge_data[:]["RedFileName"])
            img_list = [
                os.path.join(parts[0], os.path.split(name)[1])
                if os.path.split(name)[0] == ""
                else name
                for name in img_list
            ]
            self.gauge_data[:]["RedFileName"] = img_list
            if self.red_green:
                img_list_g = list(self.gauge_data[:]["GreenFileName"])
                img_list_g = [
                    os.path.join(parts[0], os.path.split(name)[1])
                    if os.path.split(name)[0] == ""
                    else name
                    for name in img_list_g
                ]
                self.gauge_data[:]["GreenFileName"] = img_list_g
                img_list.extend(img_list_g)

            img_list = [name.strip('"') for name in img_list]

            parts = os.path.split(txt_name)

            img_list = [
                os.path.join(parts[0], os.path.split(name)[1])
                if os.path.split(name)[0] == ""
                else name
                for name in img_list
            ]
            print(img_list)
            img_list.sort()
            self.img_list = img_list
            self.img_index = 0

            self.shelf_filename = os.path.join(parts[0], "info.shf")
            print(self.shelf_filename)

            print("loading info.shf")
            db = shelve.open(self.shelf_filename)
            for key in list(db.keys()):
                [ffrac, drawdata, timestr, notes] = db[key]
                self.ffrac[key] = ffrac
            db.close()
            print(self.ffrac)
            # make list of images on left of figure
            # remove any previous text
            for text in iter(self.gn_text_dict.values()):
                text.text = ""
            for text in iter(self.ff_text_dict.values()):
                text.text = ""

            ypos = 0.9
            for gauge in self.gauge_data:
                img_basename = os.path.basename(gauge["RedFileName"]).strip('"')
                redtext = img_basename[:-17]
                text = self.fig_menu.text(
                    0.65, ypos, redtext, horizontalalignment="left", fontsize=12
                )
                self.gn_text_dict[img_basename] = text
                try:
                    fftext = "%6.3f" % (self.ffrac[img_basename])
                except:
                    fftext = "NA"

                text = self.fig_menu.text(
                    0.85,
                    ypos,
                    fftext,
                    horizontalalignment="left",
                    fontsize=12,
                    color="red",
                )
                self.ff_text_dict[img_basename] = text
                if self.red_green:
                    img_basename = os.path.basename(gauge["GreenFileName"]).strip('"')
                    greentext = img_basename[:-17]
                    text = self.fig_menu.text(
                        0.35, ypos, greentext, horizontalalignment="left", fontsize=12
                    )
                    self.gn_text_dict[img_basename] = text
                    try:
                        fftext = "%6.3f" % (self.ffrac[img_basename])
                    except:
                        fftext = "NA"

                    text = self.fig_menu.text(
                        0.55,
                        ypos,
                        fftext,
                        horizontalalignment="left",
                        fontsize=12,
                        color="green",
                    )
                    self.ff_text_dict[img_basename] = text

                ypos = ypos - 0.03

            "load wavelengths and display to user"
            wavelengths = load_equipment_data.laser_wavelengths
            print(self.red_green)
            print(wavelengths)
            if wavelengths["red"]:
                message = "Wavelengths Used\n"
                self.red_wavelength = wavelengths["red"]
                message += f"red vacuum wavelength = {self.red_wavelength} nm\n"
                if self.red_green:
                    self.green_wavelength = wavelengths["green"]
                    message += f"green vacuum wavelength = {self.green_wavelength} nm\n"
            else:
                message = "Problem loading vacuumn wavelengths"
            messagebox.showinfo("Vacuum Wavelengths", message)

            self.open_image()

    def annotate_fig(self, drawdata):
        [
            xy,
            co,
            ro,
            ci,
            ri,
            ccen,
            rcen,
            pklist,
            slopep,
            interceptsp,
            slopeg,
            interceptsg,
        ] = drawdata

        # imgplot = ax.imshow(SF2,aspect='equal')
        # imgplot.set_cmap('gray')
        self.axes.plot(xy[:, 1], xy[:, 0], "or")
        self.axes.plot(ccen, rcen, "+c", ms=20)
        self.axes.plot(co, ro, "w-")
        self.axes.plot(ci, ri, "c-")
        for col, peaks in enumerate(pklist):
            x = col * np.ones_like(peaks)
            self.axes.plot(x, peaks, "+y")
        maxx = self.img_array.shape[1]
        for cepts in interceptsp:
            self.axes.plot([0, maxx], [cepts, slopep * maxx + cepts], "-m")
        for cepts in interceptsg:
            self.axes.plot([0, maxx], [cepts, slopeg * maxx + cepts], "g-")
        key = os.path.basename(self.img_filename)
        print(key, type(key))
        fftitle = "%6.3f" % (self.ffrac[key])
        self.fftext.set_text(fftitle)

    def calculate_output(self, output_all_orders=False):
        # Build a list of tuples for each file type the file dialog should display
        my_filetypes = [("all files", ".*"), ("text files", ".txt")]

        out_filename = os.path.join(
            os.path.splitext(self.gauge_data_filename)[0] + "-calcs-py.txt"
        )

        out_filename = filedialog.asksaveasfilename(
            parent=self.app_win,
            initialfile=out_filename,
            title="Select text file to save calculated resuts to",
            filetypes=my_filetypes,
        )

        if out_filename:
            fid = open(out_filename, "w")
            for gauge in self.gauge_data:
                redkey = os.path.basename(gauge["RedFileName"]).strip('"')
                ffred = self.ffrac[redkey]
                if self.red_green:
                    greenkey = os.path.basename(gauge["GreenFileName"]).strip('"')
                    ffgreen = self.ffrac[greenkey]
                # calculation is always done in metric
                if gauge["Units"].strip('"') != "Metric":
                    nomsize = gauge["NominalSize"] * 25.4

                else:
                    nomsize = gauge["NominalSize"]
                    # print "Calculating in Metric System"
                print(nomsize)
                if self.red_green:
                    rd, gd, bestindex, redindex, greenindex = (
                        gauge_length.calcgaugelength(
                            nomsize,
                            gauge["TRAir"],
                            gauge["TGAir"],
                            gauge["TR"],
                            gauge["TG"],
                            gauge["PR"],
                            gauge["HR"],
                            ffred * 100,
                            ffgreen * 100,
                            gauge["ExpCoeff"],
                            self.red_wavelength,
                            self.green_wavelength,
                        )
                    )
                else:
                    rd, redindex = gauge_length.calcgaugelength_red_only(
                        nomsize,
                        gauge["TRAir"],
                        gauge["TR"],
                        gauge["PR"],
                        gauge["HR"],
                        ffred * 100,
                        gauge["ExpCoeff"],
                        self.red_wavelength,
                    )

                # translate metric values for deviations (nanometres) to imperial values (microinches)
                if gauge["Units"].strip('"') != "Metric":
                    rd = rd / 25.4
                    if self.red_green:
                        gd = gd / 25.4

                # Observer = "MTL"

                if output_all_orders:
                    orders = range(0, 10)
                else:
                    orders = [5]

                for idev in orders:
                    if self.red_green:
                        diffdev = rd[idev] - gd[idev]
                        meandev = (rd[idev] + gd[idev]) / 2.0
                        outtext = (
                            f"{gauge['NominalSize']:f}",
                            f'"{gauge["SerialNo"]:s}"',
                            f"{meandev:.1f}",
                            f"{diffdev:.1f}",
                            f"{rd[idev]:.1f}",
                            f"{gd[idev]:.1f}",
                            f"{bestindex:d}",
                            f"{gauge['RedDateTime']:f}",
                            f"{gauge['GreenDateTime']:f}",
                            f'"{gauge["SetId"]:s}"',
                            f"{gauge['PlatenId']:d}",
                            f"{gauge['Side']:d}",
                            f"{gauge['ExpCoeff']:e}",
                            f'"{gauge["Units"]:s}"',
                            f"{gauge['TRAir']:f}",
                            f"{gauge['TGAir']:f}",
                            f"{gauge['TR']:f}",
                            f"{gauge['TG']:f}",
                            f"{gauge['PR']:f}",
                            f"{gauge['PG']:f}",
                            f"{gauge['HR']:f}",
                            f"{gauge['HG']:f}",
                            f"{ffred * 100.0:.2f}",
                            f"{ffgreen * 100.0:.2f}",
                            f"{self.red_wavelength:.11f}",
                            f"{self.green_wavelength:.9f}",
                            f"{redindex:.9f}",
                            f"{greenindex:.9f}",
                            f'"{gauge["RedFileName"]:s}"',
                            f'"{gauge["GreenFileName"]:s}"',
                        )
                    else:
                        outtext = (
                            f"{gauge['NominalSize']:f}",
                            f'"{gauge["SerialNo"]:s}"',
                            f"{rd:.1f}",
                            f"{gauge['RedDateTime']:f}",
                            f'"{gauge["SetId"]:s}"',
                            f"{gauge['PlatenId']:d}",
                            f"{gauge['Side']:d}",
                            f"{gauge['ExpCoeff']:e}",
                            f'"{gauge["Units"]:s}"',
                            f"{gauge['TRAir']:f}",
                            f"{gauge['TR']:f}",
                            f"{gauge['PR']:f}",
                            f"{gauge['HR']:f}",
                            f"{ffred * 100.0:.2f}",
                            f"{self.red_wavelength:.7f}",
                            f"{redindex:.9f}",
                            f'"{gauge["RedFileName"]:s}"',
                        )

                    fid.write(", ".join(outtext))
                    fid.write("\n")
            fid.close()


if __name__ == "__main__":
    fig = figure(figsize=(8, 6), dpi=80)
    axes = fig.add_axes([0.1, 0.1, 0.8, 0.8])
    fig_menu = figure(figsize=(8, 6), dpi=80)

    lman = FringeManager(axes, fig_menu)

    axload = fig_menu.add_axes([0.1, 0.825, 0.3, 0.075])
    axprev = fig_menu.add_axes([0.1, 0.725, 0.3, 0.075])
    axnext = fig_menu.add_axes([0.1, 0.625, 0.3, 0.075])
    axredo = fig_menu.add_axes([0.1, 0.525, 0.3, 0.075])
    axcalc0 = fig_menu.add_axes([0.1, 0.425, 0.3, 0.075])
    axcalcAll = fig_menu.add_axes([0.1, 0.325, 0.3, 0.075])

    bload = Button(axload, "Load")
    bload.on_clicked(lman.load)

    bnext = Button(axnext, "Next")
    bnext.on_clicked(lman.next)

    bprev = Button(axprev, "Previous")
    bprev.on_clicked(lman.prev)

    bredo = Button(axredo, "Redo")
    bredo.on_clicked(lman.redo)

    bcalc0 = Button(axcalc0, "Calculate Zero Order")
    bcalc0.on_clicked(lman.calc0)

    bcalcAll = Button(axcalcAll, "Calculate All Orders")
    bcalcAll.on_clicked(lman.calcall)

    lman.load_gauge_data()

    show()
