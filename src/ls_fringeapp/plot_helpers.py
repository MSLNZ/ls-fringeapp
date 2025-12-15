import matplotlib

from matplotlib.patches import Circle
import numpy as np


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
