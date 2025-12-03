"""
create synthetic fringe images for testing fringe fraction determination
"""

from PIL import Image
import numpy as np


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
    gb_box = (0, 0, gb_size_px[1], gb_size_px[0])
    # crop shifted copy to gauge size
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
