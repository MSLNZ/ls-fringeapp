"""
create synthetic fringe images for testing fringe fraction determination
"""

import math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

from ls_fringeapp import fringeprocess as fp


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


def make_square_gauge_array_from_image(img: Image, xygb, crop_margin=(200, 50)):
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
    gb_yx = xy4[:, [1, 0]]
    # convert back to numpy array
    img_array = np.asarray(img4)
    return img_array, gb_yx


def synthetic_fringes(
    spacing_px,
    offset_px,
    size,
    amplitude=50,
    mean_intensity=50,
    finesse=5,
):
    """
    create an image as a numpy array with fringes using Airy Formula
    https://wp.optics.arizona.edu/jcwyant/wp-content/uploads/sites/13/2016/08/multiplebeaminterference.pdf
    constant across image area - that is perfetly straight fringes
    finesse determines the sharpness/contrast of the images - higher values gives narrower darker fringes,
    finesse is related to the reflectivity of the surface
    """
    x = np.arange(0, size[0])
    # delta as multiple of 2pi
    delta = 2 * np.pi * (x - offset_px) / spacing_px

    z_int = (finesse * np.sin(delta / 2) ** 2) / (1 + finesse * np.sin(delta / 2) ** 2)
    z = amplitude * (z_int - 0.5) + mean_intensity
    img_array = np.empty(size).T
    img_array[:] = z
    img_array = img_array.T
    return img_array


def synthetic_image_with_gauge(
    fringe_spacing_px,
    offset_px,
    ffrac,
    img_size_px,
    gb_size_px,
    amplitude=50,
    mean_intensity=50,
    finesse=5,
):
    """
    creates a fringe image as a numpy array
    with a central area of size gb_size_px where the fringes are offset by
    ffrac (0 to 1)
    """
    img_array = synthetic_fringes(
        fringe_spacing_px,
        offset_px,
        img_size_px,
        amplitude,
        mean_intensity,
        finesse,
    )
    # convert to PIL image
    img = Image.fromarray(img_array)
    # make a copy so the  orignal image is not altered
    img2 = img.copy()

    # shift by fringe_fraction
    yshift = (1, 0, 0, 0, 1, ffrac * fringe_spacing_px)
    img3 = img2.transform(img2.size, Image.Transform.AFFINE, data=yshift)

    # crop shifted copy to gauge size
    top_left = ((img.size[0] - gb_size_px[1]) // 2, (img.size[1] - gb_size_px[0]) // 2)

    gb_box = (
        top_left[0],
        top_left[1],
        top_left[0] + gb_size_px[1],
        top_left[1] + gb_size_px[0],
    )
    img4 = img3.crop(gb_box)
    # paste to centre of image
    top_left = ((img.size[0] - gb_size_px[1]) // 2, (img.size[1] - gb_size_px[0]) // 2)
    img2.paste(img4, top_left)
    # convert back to numpy array
    img_array = np.asarray(img2)
    # gauge coordinates in format needed for array2frac
    gb_xy = np.array(
        [
            top_left,
            (top_left[0], top_left[1] + gb_size_px[0]),
            (top_left[0] + gb_size_px[1], top_left[1] + gb_size_px[0]),
        ]
    )
    gb_yx = gb_xy[:, [1, 0]]

    return img_array, gb_yx


def blur_gauge_hole(img_array, xygb, circle_radius=0.25):
    """
    takes an image of a square gauge and adds a blured circle
    at the center of the gauge

    circle_radius:  circle is centered on gauge with radius in pixels = gauge_width  * circle_radius
    """
    # convert to PIL image
    img = Image.fromarray(img_array)
    img = img.convert("L")
    (width, length), (ccen, rcen), phi = fp.gauge_geometry(xygb)
    mask = Image.new(mode="L", size=img.size)
    draw = ImageDraw.Draw(mask)
    radius_px = circle_radius * width

    circle = (ccen - radius_px, rcen - radius_px, ccen + radius_px, rcen + radius_px)
    draw.ellipse(circle, fill="white", outline="white")
    blurred = img.filter(ImageFilter.GaussianBlur(40))
    img_sq_hole = img.copy()
    img_sq_hole.paste(blurred, mask=mask)
    img_array = np.asarray(img_sq_hole)
    return img_array
