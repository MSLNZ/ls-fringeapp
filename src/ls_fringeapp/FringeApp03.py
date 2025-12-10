"""
EFH 15/12/2009
App to process whole files of images

requires python 3.5 for f strings

"""

from pathlib import Path, PureWindowsPath

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

import datetime
import shelve

from PIL import Image
import numpy as np


import matplotlib as mpl
import matplotlib.pyplot as plt


from ls_fringeapp.poly_lasso import PolyLasso
from ls_fringeapp import fringeprocess
from ls_fringeapp import gauge_length

from ls_fringeapp import load_equipment_data
from ls_fringeapp.file_formats import DTRG, DTR

mpl.use("tkagg")
mpl.rcParams["toolbar"] = "None"

DPI = 150
# slider colors
OFF_COLOR = (0.83, 0.83, 0.83, 1.0)
ON_COLOR = (0.12, 0.47, 0.71, 1.0)

USE_GREEN = True
ObliquityCorrection = 1.00000013
CalDataFileName = (
    r"C:\Users\c.young\OneDrive - Callaghan Innovation\EQUIPREG\XML Files\cal_data.xml"
)
WorkingDir = r"C:\Users\c.young\OneDrive - Callaghan Innovation\Jobs"


"""
For processing gauge block interferograms
"""


class FringeManager:
    """simple gauge block picking interface and ff calculator"""

    def __init__(self):
        self.ffrac = {}
        self.gauge_data = []
        self.gauge_data_filename: Path
        self.img_array = []
        self.img_filename: Path  # current image being processed
        self.img_index = 0
        self.img_list = list[str]  # file names only
        self.image_folder: Path
        self.lasso = None
        self.lasso_active = True
        self.ff_text_dict = {}
        self.gn_text_dict = {}
        self.shelf_filename: Path
        self.red_green = USE_GREEN

        # attributes for square gauges with hole
        self.circle_radius = None
        self.border = (0.2, 0.1)
        self.col_start_frac = 0.2

        self.check_wavelengths()
        self.make_gui()

    def make_gui(self):
        # self.app_win = tk.Tk()
        # self.app_win.withdraw()

        self.fig_menu = plt.figure(figsize=(10, 6), num="Control Panel", dpi=DPI)

        fig_gb = plt.figure(figsize=(6, 6), num="Gauge Image", dpi=DPI)
        self.axes_gb = fig_gb.add_axes([0.1, 0.1, 0.8, 0.8])

        self.figure = self.axes_gb.figure
        self.canvas = self.figure.canvas

        self.canvas.mpl_connect("button_press_event", self.onpress)
        self.canvas.mpl_connect("key_press_event", self.keypress)

        # control panel text
        self.filetext = self.figure.text(0.5, 0.05, " ", horizontalalignment="center")
        self.fftext = self.figure.text(0.5, 0.02, " ", horizontalalignment="center")

        self.input_file_path = self.fig_menu.text(
            0.5,
            0.95,
            "",
            horizontalalignment="center",
            fontsize=12,
        )

        if self.red_wavelength:
            message = f"Wavelengths loaded from\n{load_equipment_data.path_register}\n"
            message += f"red      {self.red_wavelength} nm\n"
            message += f"green    {self.green_wavelength} nm\n"
        else:
            message = (
                f"Problem loading wavlengths from\n{load_equipment_data.path_register}"
            )

        self.fig_menu.text(0.6, 0.0, message, fontsize=8)

        # fix the fonts for tkinter dialog boxes
        for f in tk.font.names():
            ff = tk.font.nametofont(f)
            ff.config(size=16)

        # add button controls
        axload = self.fig_menu.add_axes([0.1, 0.825, 0.2, 0.075])
        axprev = self.fig_menu.add_axes([0.1, 0.725, 0.2, 0.075])
        axnext = self.fig_menu.add_axes([0.1, 0.625, 0.2, 0.075])
        axredo = self.fig_menu.add_axes([0.1, 0.525, 0.2, 0.075])
        axcalc0 = self.fig_menu.add_axes([0.1, 0.425, 0.2, 0.075])
        axcalcAll = self.fig_menu.add_axes([0.1, 0.325, 0.2, 0.075])

        bload = mpl.widgets.Button(axload, "Load")
        bload.on_clicked(self.load)

        bnext = mpl.widgets.Button(axnext, "Next")
        bnext.on_clicked(self.next)

        bprev = mpl.widgets.Button(axprev, "Previous")
        bprev.on_clicked(self.prev)

        bredo = mpl.widgets.Button(axredo, "Redo")
        bredo.on_clicked(self.redo)

        bcalc0 = mpl.widgets.Button(axcalc0, "Calculate Zero Order")
        bcalc0.on_clicked(self.calc0)

        bcalcAll = mpl.widgets.Button(axcalcAll, "Calculate All Orders")
        bcalcAll.on_clicked(self.calcall)

        # check box for square gauges with hole
        sq_check = self.fig_menu.add_axes([0.1, 0.225, 0.2, 0.075])
        self.check_box = mpl.widgets.CheckButtons(
            ax=sq_check,
            labels=["square with hole"],
        )
        self.check_box._checks.set_sizes(np.array([100]), dpi=150)
        self.check_box._frames.set_sizes(np.array([100]), dpi=150)

        self.check_box.on_clicked(self.sq_check_change)

        # three sliders for border and hole size

        ax08 = self.fig_menu.add_axes([0.1, 0.18, 0.2, 0.03])
        self.hole_size_slider = mpl.widgets.Slider(
            ax=ax08,
            label="hole radius",
            valmin=0.05,
            valmax=0.3,
            valinit=0.25,
        )
        # disable slider initially
        self.hole_size_slider.set_active(False)
        self.hole_size_slider.poly.set_facecolor(OFF_COLOR)
        self.hole_size_slider.on_changed(self.hole_size_change)

        self.fig_menu.text(0.1, 0.13, "gauge border", fontsize=10)
        ax09 = self.fig_menu.add_axes([0.1, 0.08, 0.2, 0.03])
        self.xborder_size_slider = mpl.widgets.Slider(
            ax=ax09,
            label="X",
            valmin=0.05,
            valmax=0.3,
            valinit=0.2,
        )

        self.xborder_size_slider.on_changed(self.border_change)
        ax10 = self.fig_menu.add_axes([0.1, 0.03, 0.2, 0.03])
        self.yborder_size_slider = mpl.widgets.Slider(
            ax=ax10,
            label="Y",
            valmin=0.05,
            valmax=0.3,
            valinit=0.1,
        )
        self.yborder_size_slider.on_changed(self.border_change)

        plt.show()

    def sq_check_change(self, label):
        if self.check_box.get_status()[0]:
            self.circle_radius = self.hole_size_slider.val
            # make hole size slider active and change color
            self.hole_size_slider.poly.set_facecolor(ON_COLOR)
            self.hole_size_slider.set_active(True)
            # set border to default for square gauges
            self.xborder_size_slider.set_val(0.1)
            self.yborder_size_slider.set_val(0.1)
            self.border = (0.1, 0.1)
        else:
            self.circle_radius = None
            # make hole size slider inactive and change color
            self.hole_size_slider.poly.set_facecolor(OFF_COLOR)
            self.hole_size_slider.set_active(False)
            # set border to default for rectangular gauges
            self.xborder_size_slider.set_val(0.2)
            self.yborder_size_slider.set_val(0.1)
            self.border = (0.2, 0.1)
        # change value of hol e size slider to update color
        self.hole_size_slider.set_val(self.hole_size_slider.val)

    def hole_size_change(self, val):
        self.circle_radius = self.hole_size_slider.val

    def border_change(self, val):
        self.border = (self.xborder_size_slider.val, self.yborder_size_slider.val)

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
        img_basename = self.img_filename.name
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
        logfile = open(self.img_filename.with_name("fflog.txt"), "a")
        logfile.write(text + "\n")
        logfile.close()
        # also shelve ffrac, drawdata, timestr, notes with img_filename as key

        db = shelve.open(self.shelf_filename.as_posix())
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
        print("in FringeManger.load")
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
        db = shelve.open(self.shelf_filename.as_posix())
        img_basename = self.img_filename.name

        if img_basename in db:
            del db[img_basename]
        db.close()
        self.open_image()
        self.lasso_active = True

    def open_image(self):
        """opens image in imagelist at position image_index"""
        img_basename = self.img_list[self.img_index]
        self.img_filename = self.image_folder / img_basename
        print(self.img_filename)

        img = Image.open(self.img_filename)

        self.img_array = fringeprocess.img2greyarray(img)
        self.axes_gb.clear()
        self.axes_gb.imshow(self.img_array, cmap=mpl.cm.gray)
        self.axes_gb.axis("image")
        self.axes_gb.axis("off")

        self.filetext.set_text(img_basename)
        self.fftext.set_text(" ")
        self.lasso_active = True
        # check if image has an entry in directory's shelf file
        # if so use it to annotate image

        db = shelve.open(self.shelf_filename.as_posix())
        if img_basename in db:
            print("found ", img_basename, " on shelf")
            [ffrac, drawdata, timestr, notes] = db[img_basename]
            self.ffrac[img_basename] = ffrac
            self.annotate_fig(drawdata)
            self.lasso_active = False
        db.close()
        self.canvas.draw()

    def load_gauge_data_from_file(self, txt_name):
        """
        load self.gauge_data from file
        """
        self.gauge_data_filename = Path(txt_name)

        # load gauge data
        if self.red_green:
            self.gauge_data = np.loadtxt(txt_name, delimiter=",", dtype=DTRG)
        else:
            self.gauge_data = np.loadtxt(txt_name, dtype=DTR, delimiter=",")

    def make_image_list(self, image_folder):
        self.image_folder = Path(image_folder)

        # make list of red images
        img_list = list(self.gauge_data[:]["RedFileName"])
        # add green images
        if self.red_green:
            img_list.extend(list(self.gauge_data[:]["GreenFileName"]))

        # convert to Path objects - assume writen from windows system
        img_list = [PureWindowsPath(name) for name in img_list]

        # split off folder name
        img_list = [name.name for name in img_list]

        img_list.sort()
        self.img_list = img_list
        self.img_index = 0

    def load_shelf_file(self):
        """
        data to display the lines drawn on an image is stored in a "shelf" file
        if this file does not exist its created in self.image_folder
        """
        self.shelf_filename = self.image_folder / "info.shf"

        print(f"loading {self.shelf_filename}")
        db = shelve.open(self.shelf_filename.as_posix())
        for key in list(db.keys()):
            [ffrac, drawdata, timestr, notes] = db[key]
            self.ffrac[key] = ffrac
        db.close()

    def check_wavelengths(self):
        "load wavelengths"
        wavelengths = load_equipment_data.laser_wavelengths
        print(self.red_green)
        print(wavelengths)
        self.red_wavelength = wavelengths.get("red", None)
        self.green_wavelength = wavelengths.get("green", None)

    def make_text_for_control_window(self):
        # make list of images on left of figure
        # remove any previous text
        for text in iter(self.gn_text_dict.values()):
            text.text = ""
        for text in iter(self.ff_text_dict.values()):
            text.text = ""

        text = self.fig_menu.text(
            0.35,
            0.85,
            self.image_folder.as_posix(),
            horizontalalignment="left",
            fontsize=12,
            color="black",
        )

        ypos = 0.8
        for gauge in self.gauge_data:
            img_basename = PureWindowsPath(gauge["RedFileName"]).name
            redtext = img_basename
            text = self.fig_menu.text(
                0.65, ypos, redtext, horizontalalignment="left", fontsize=12
            )
            self.gn_text_dict[img_basename] = text
            try:
                fftext = "%6.3f" % (self.ffrac[img_basename])
            except KeyError:
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
                img_basename = PureWindowsPath(gauge["GreenFileName"]).name
                greentext = img_basename
                text = self.fig_menu.text(
                    0.35, ypos, greentext, horizontalalignment="left", fontsize=12
                )
                self.gn_text_dict[img_basename] = text
                try:
                    fftext = "%6.3f" % (self.ffrac[img_basename])
                except KeyError:
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

    def load_gauge_data(self):
        """
        prompts user to open file written by Gauge Block Writer App, reads it and creates
        a list of images to process
        """
        # Build a list of tuples for each file type the file dialog should display
        my_filetypes = [("all files", ".*"), ("text files", ".txt")]
        txt_name = filedialog.askopenfilename(
            initialdir=WorkingDir,
            title="Select text file written Gauge Block File Writer App",
            filetypes=my_filetypes,
        )

        if txt_name is None:
            return

        self.load_gauge_data_from_file(txt_name)

        file0 = Path(PureWindowsPath(list(self.gauge_data[:]["RedFileName"])[0]))
        print(f"{file0=}")
        image_folder = file0.parent
        print(f"{image_folder=}")
        if image_folder.as_posix() == ".":
            # if no folder names use images in same folder as input txt file
            image_folder = Path(txt_name).parent
            file0 = image_folder / file0
        # check if can access image files
        if not file0.exists():
            message = f"Can not access files at {file0}\n"
            message += "Do you want to use files in same folder as text file?"
            # buttons yes, no, cancel
            answer = messagebox.askyesnocancel("Missing Image Files", message)
            if answer is None:
                # "Cancel"
                return
            if answer is True:
                # "YES"
                # use images in same folder as input txt file
                image_folder = Path(txt_name).parent
            if answer is False:
                # "No"
                # open dialog to select root folder
                image_folder = filedialog.askdirectory(mustexist=True)
                if image_folder is None:
                    return

        print(f"image folder (after dialog): {image_folder}")

        print(f"{self.gauge_data_filename=}")
        self.input_file_path.set_text(str(self.gauge_data_filename))

        self.make_image_list(image_folder)
        self.load_shelf_file()
        self.make_text_for_control_window()
        self.fig_menu.canvas.draw()
        self.open_image()

    def annotate_fig(self, drawdata: [dict | list]):
        if isinstance(drawdata, list):
            # reading older shelf file
            drawdata = fringeprocess.convert_drawdata_list_to_dict(drawdata)

        self.axes_gb.plot(drawdata["xy"][:, 1], drawdata["xy"][:, 0], "or")
        self.axes_gb.plot(drawdata["ccen"], drawdata["rcen"], "+c", ms=20)
        self.axes_gb.plot(drawdata["co"], drawdata["ro"], "w-")
        self.axes_gb.plot(drawdata["ci"], drawdata["ri"], "c-")
        for col, peaks in enumerate(drawdata["pklist"]):
            x = col * np.ones_like(peaks)
            self.axes_gb.plot(x, peaks, "+y")
        maxx = self.img_array.shape[1]
        for cepts in drawdata["interceptsp"]:
            self.axes_gb.plot(
                [0, maxx], [cepts, drawdata["slopep"] * maxx + cepts], "-m"
            )
        for cepts in drawdata["interceptsg"]:
            self.axes_gb.plot(
                [0, maxx], [cepts, drawdata["slopeg"] * maxx + cepts], "g-"
            )

        if drawdata.get("circle", None) is not None:
            xy = (drawdata["ccen"], drawdata["rcen"])
            r = drawdata["circle"]
            circle_patch = mpl.widgets.Circle(xy, r, ec="c", lw=2)
            circle_patch.set_facecolor((0, 0, 0, 0))
            self.axes_gb.add_artist(circle_patch)
        if drawdata.get("col_start", None) is not None:
            self.axes_gb.axvline(x=drawdata["col_start"], ls="-.", c="c", lw=1)

        key = self.img_filename.name
        print(key, type(key))
        fftitle = "%6.3f" % (self.ffrac[key])
        self.fftext.set_text(fftitle)

    def calculate_output(self, output_all_orders=False):
        # Build a list of tuples for each file type the file dialog should display
        my_filetypes = [("all files", ".*"), ("text files", ".txt")]

        out_filename = self.gauge_data_filename.with_name("output-calcs-py.txt")

        out_filename = filedialog.asksaveasfilename(
            parent=self.app_win,
            initialfile=out_filename,
            title="Select text file to save calculated resuts to",
            filetypes=my_filetypes,
        )

        if out_filename:
            fid = open(out_filename, "w")
            for gauge in self.gauge_data:
                redkey = PureWindowsPath(gauge["RedFileName"]).name
                ffred = self.ffrac[redkey]
                if self.red_green:
                    greenkey = PureWindowsPath(gauge["GreenFileName"]).name
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
    lman = FringeManager()
