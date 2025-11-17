from matplotlib.lines import Line2D
from matplotlib.widgets import Widget


class PolyLasso(Widget):
    """
    A lasso widget that allows the user to define a lasso region by
    clicking to form a polygon.
    """

    def __init__(self, ax, callback=None, line_to_next=True, useblit=True):
        """
        Create a new lasso.

        *ax* is the axis on which to draw

        *callback* is a function that will be called with arguments (*ax*, *line*, *verts*).
        *verts* is a list of (x,y) pairs that define the polygon, with the first and
        last entries equal.

        *line_to_next* controls whether or not a line is drawn to the current
        cursor position as the polygon is created

        *useblit* = *True* is the only thorougly tested option.

        """
        print("in poly lasso init", callback)
        self.axes = ax
        self.figure = ax.figure
        self.canvas = self.figure.canvas
        self.useblit = useblit
        self.line_to_next = line_to_next
        if useblit:
            self.background = self.canvas.copy_from_bbox(self.axes.bbox)

        self.verts = []
        self.line = None
        self.callback = callback
        self.cids = []
        self.cids.append(
            self.canvas.mpl_connect("button_release_event", self.onrelease)
        )
        self.cids.append(self.canvas.mpl_connect("motion_notify_event", self.onmove))
        self.cids.append(self.canvas.mpl_connect("draw_event", self.ondraw))

    def ondraw(self, event):
        """draw_event callback, to take care of some blit artifacts"""
        self.background = self.canvas.copy_from_bbox(self.axes.bbox)
        if self.line:
            self.axes.draw_artist(self.line)
        self.canvas.blit(self.axes.bbox)

    def cleanup(self):
        """Remove the lasso line."""
        # Clear out callbacks
        for cid in self.cids:
            self.canvas.mpl_disconnect(cid)
        # self.axes.lines.remove(self.line)
        self.canvas.draw()

    def finalize(self):
        """Called when user makes the final right click"""
        # all done with callbacks pertaining to adding verts to the polygon
        for cid in self.cids:
            self.canvas.mpl_disconnect(cid)
        self.cids = []
        # print 'right click'
        # Greater than three verts, since a triangle
        # has a duplicate point to close the poly.
        if len(self.verts) > 3:
            # Matplotlib will not draw the closed polygon until we step completely
            # out of this routine. It is desirable to see the closed polygon on screen
            # in the event that *callback* takes a long time. So, delay callback until
            # we get an idle event, which will signal that the closed polygon has also
            # been drawn.
            # 2014-04-28 idle_event dosen't seem to happen
            # polygon is drawn any way so call do_callback directly
            # print 'before callback'
            # self.cids.append(self.canvas.mpl_connect('idle_event', self.do_callback))

            # print 'just before callback'
            self.callback(self.axes, self.line, self.verts)
            self.cleanup()

        else:
            print("Need at least three vertices to make a polygon")
            self.cleanup()

    def draw_update(self):
        """Adjust the polygon line, and blit it to the screen"""
        self.line.set_data(zip(*self.verts))
        if self.useblit:
            self.canvas.restore_region(self.background)
            self.axes.draw_artist(self.line)
            self.canvas.blit(self.axes.bbox)
        else:
            self.canvas.draw_idle()

    def onmove(self, event):
        """Update the next vertex position"""
        if self.line == None:
            return
        self.verts[-1] = (event.xdata, event.ydata)
        if self.line_to_next:
            self.draw_update()

    def onrelease(self, event):
        """User clicked the mouse. Add a vertex or finalize depending on mouse button."""
        if self.verts is None:
            return
        if event.inaxes != self.axes:
            return

        if event.button == 3:
            # Right click - close the polygon
            # Set the dummy point to the first point
            self.verts[-1] = self.verts[0]
            self.draw_update()
            self.finalize()
            return

        # The rest pertains to left click only
        if event.button != 1:
            return

        if self.line == None:
            # Deal with the first click
            self.line = Line2D(
                [event.xdata],
                [event.ydata],
                linestyle="-",
                marker="s",
                color="black",
                lw=1,
                ms=4,
                animated=True,
            )
            self.axes.add_line(self.line)
            self.verts.append((event.xdata, event.ydata))

        # finalize vertex at this click, set up a new on that changes as mouse moves
        self.verts[-1] = (event.xdata, event.ydata)
        self.verts.append((event.xdata, event.ydata))

        self.draw_update()
