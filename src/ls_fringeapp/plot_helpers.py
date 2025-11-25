import math
from pathlib import Path
import matplotlib
from matplotlib.pyplot import figure, show
from matplotlib.patches import Circle
import numpy as np

from PIL import Image, ImageDraw, ImageFilter


import tkinter as tk
from tkinter import filedialog


from ls_fringeapp.poly_lasso import PolyLasso
from ls_fringeapp import fringeprocess as fp


# local version of FringeManager.annotate_fig
def draw_gauge(axes, img_array, drawdata: dict):
    axes.imshow(img_array, cmap=matplotlib.cm.gray)
    axes.axis("image")
    axes.plot(drawdata["xy"][:, 1], drawdata["xy"][:, 0], "or")
    axes.plot(drawdata["ccen"], drawdata["rcen"], "+c", ms=20)
    axes.plot(drawdata["co"], drawdata["ro"], "w-")
    axes.plot(drawdata["ci"], drawdata["ri"], "c-")
    for col, peaks in enumerate(drawdata["pklist"]):
        x = col * np.ones_like(peaks)
        axes.plot(x, peaks, "+y")
    maxx = img_array.shape[1]
    for cepts in drawdata["interceptsp"]:
        axes.plot([0, maxx], [cepts, drawdata["slopep"] * maxx + cepts], "-m", lw=5)
    for cepts in drawdata["interceptsg"]:
        axes.plot([0, maxx], [cepts, drawdata["slopeg"] * maxx + cepts], "g-", lw=5)

    if drawdata["circle"] is not None:
        xy = (drawdata["ccen"], drawdata["rcen"])
        r = drawdata["circle"]
        circle_patch = Circle(xy, r, ec="c", lw=2)
        circle_patch.set_facecolor((0, 0, 0, 0))
        axes.add_artist(circle_patch)

    axes.axvline(x=drawdata["col_start"], ls="-.", c="c", lw=1)


# def affine_coeffs(pa, pb):
#     """
#     find the affine coeffs needed by PIL transform, to map pa to pb

#     pa : 3 or more points on original plane
#     pb : points on transformed plane
#     finds the coefficients needed in
#     PIL.Image.transform(size, PIL.Image.AFFINE, a_coeffs, PIL.Image.BICUBIC)
#     to transform the pixels in an image from pa to pb,
#     these are the coordinates of a transform matrix A

#     A = [a, b, c]
#         [d, e, f]
#         [0, 0, 1]

#     where a_coeffs = (a, b, c, d, e, f)
#     and X1 * inv(A) = X2  - check multiplication order
#     could probably simplify and remove the 2nd inverse calculation
#     """
#     pa = pa.reshape(-1, 2)
#     X1 = np.hstack((pa, np.ones((pa.shape[0], 1))))
#     pb = pb.reshape(-1, 2)
#     X2 = np.hstack((pb, np.ones((pb.shape[0], 1))))
#     X1_inv = np.linalg.pinv(X1)
#     A = np.dot(X1_inv, X2)
#     inv_A = np.linalg.inv(A)
#     a_coeffs = inv_A[:, :2].T.flatten()
#     return a_coeffs


def rotate(
    img,
    angle: float,
    resample=Image.BICUBIC,
    expand: int | bool = False,
    center: tuple[float, float] | None = None,
    translate: tuple[int, int] | None = None,
    fillcolor: float | tuple[float, ...] | str | None = None,
    points: np.ndarray = None,  # n rows,  2 columns or n columns 2 rows
) -> Image:
    """
    local version based on this code
    https://github.com/python-pillow/Pillow/blob/ec40c546d7d38efebcb228745291bd3ba6233196/src/PIL/Image.py#L2340

    edited to return points transformed by the same rotation



    Returns a rotated copy of this image.  This method returns a
    copy of this image, rotated the given number of degrees counter
    clockwise around its centre.

    :param angle: In degrees counter clockwise.
    :param resample: An optional resampling filter.  This can be
       one of :py:data:`Resampling.NEAREST` (use nearest neighbour),
       :py:data:`Resampling.BILINEAR` (linear interpolation in a 2x2
       environment), or :py:data:`Resampling.BICUBIC` (cubic spline
       interpolation in a 4x4 environment). If omitted, or if the image has
       mode "1" or "P", it is set to :py:data:`Resampling.NEAREST`.
       See :ref:`concept-filters`.
    :param expand: Optional expansion flag.  If true, expands the output
       image to make it large enough to hold the entire rotated image.
       If false or omitted, make the output image the same size as the
       input image.  Note that the expand flag assumes rotation around
       the center and no translation.
    :param center: Optional center of rotation (a 2-tuple).  Origin is
       the upper left corner.  Default is the center of the image.
    :param translate: An optional post-rotate translation (a 2-tuple).
    :param fillcolor: An optional color for area outside the rotated image.
    :returns: An :py:class:`~PIL.Image.Image` object.
    """

    angle = angle % 360.0

    w, h = img.size

    if translate is None:
        post_trans = (0, 0)
    else:
        post_trans = translate
    if center is None:
        center = (w / 2, h / 2)

    angle = -math.radians(angle)
    matrix = [
        round(math.cos(angle), 15),
        round(math.sin(angle), 15),
        0.0,
        round(-math.sin(angle), 15),
        round(math.cos(angle), 15),
        0.0,
    ]

    def transform(x: float, y: float, matrix: list[float]) -> tuple[float, float]:
        (a, b, c, d, e, f) = matrix
        return a * x + b * y + c, d * x + e * y + f

    matrix[2], matrix[5] = transform(
        -center[0] - post_trans[0], -center[1] - post_trans[1], matrix
    )
    matrix[2] += center[0]
    matrix[5] += center[1]

    if expand:
        # calculate output size
        xx = []
        yy = []
        for x, y in ((0, 0), (w, 0), (w, h), (0, h)):
            transformed_x, transformed_y = transform(x, y, matrix)
            xx.append(transformed_x)
            yy.append(transformed_y)
        nw = math.ceil(max(xx)) - math.floor(min(xx))
        nh = math.ceil(max(yy)) - math.floor(min(yy))

        # We multiply a translation matrix from the right.  Because of its
        # special form, this is the same as taking the image of the
        # translation vector as new translation vector.
        matrix[2], matrix[5] = transform(-(nw - w) / 2.0, -(nh - h) / 2.0, matrix)
        w, h = nw, nh
        new_img = img.transform(
            (w, h), Image.AFFINE, matrix, resample, fillcolor=fillcolor
        )
        # additional code EFH 2025-11-24
        if points is None:
            return new_img

        M1 = np.array(matrix).reshape(2, 3)
        M1 = np.vstack((M1, [0, 0, 1]))
        shape = points.shape
        if shape[0] == 2:
            points = points.T
        X1 = np.hstack((points, np.ones((points.shape[0], 1))))
        X2 = np.dot(np.linalg.inv(M1), X1.T)
        new_points = X2[:2, :]
        if shape[1] == 2:
            new_points = new_points.T

    return new_img, new_points


def make_square_gauge(img: Image, xygb, crop_margin=(200, 50)):
    """
    create a square gauge image by scaling and rotating a
    rectangular gauge image.

    gauge in new image should have equal length sides and 90 degree corners.
    """
    (width, length), (ccen, rcen), phi = fp.gauge_geometry(xygb)
    # rotate gauge square to axis
    # swap x and y axis
    pa = pa = xygb[:, [1, 0]]
    img1, xy1 = rotate(img, angle=-180 - np.rad2deg(phi), expand=True, points=pa)
    # scale along x
    scale = length / width
    size = (int(scale * img1.size[0]), img1.size[1])
    img2 = img1.resize(size)
    S = np.array(((scale, 0), (0, 1)))
    xy2 = np.dot(S, xy1.T).T
    # rotate back
    img3, xy3 = rotate(img2, angle=180 + np.rad2deg(phi), expand=True, points=xy2)
    # crop to a little outside square
    box = (
        min(xy3[:, 0]) - crop_margin[0],
        min(xy3[:, 1]) - crop_margin[1],
        max(xy3[:, 0]) + crop_margin[0],
        max(xy3[:, 1]) + crop_margin[1],
    )
    img4 = img3.crop(box)
    xy4 = xy3 - (box[0], box[1])
    # swap x and y axis back
    xygb4 = xy4[:, [1, 0]]
    return img4, xygb4


def blur_gauge_hole(img, xygb, circle_radius=0.25):
    """
    takes an image of a square gauge and adds a blured circle
    at the center of the gauge

    circle_radius:  circle is centered on gauge with radius in pixels = gauge_width  * circle_radius
    """
    (width, length), (ccen, rcen), phi = fp.gauge_geometry(xygb)
    mask = Image.new(mode="L", size=img.size)
    draw = ImageDraw.Draw(mask)
    radius_px = circle_radius * width

    circle = (ccen - radius_px, rcen - radius_px, ccen + radius_px, rcen + radius_px)
    draw.ellipse(circle, fill="white", outline="white")
    blurred = img.filter(ImageFilter.GaussianBlur(40))
    img_sq_hole = img.copy()
    img_sq_hole.paste(blurred, mask=mask)
    return img_sq_hole


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
