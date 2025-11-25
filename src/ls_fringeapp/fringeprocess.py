import numpy as np

# import math
from PIL import Image, ImageDraw
import matplotlib.image
import matplotlib.mlab
from matplotlib.path import Path


def roipoly(image_array, cs, rs):
    """
    Returns a polygon mask whose vertices are given by cs,rs
    Inputs
    I a numpy array
    cs, rs the column and row indices of each vertex of a polygon

    Outputs
    mask a numpy array  where the points inside the
    polygon have value 1 and the points outside have value 0.
    now uses matplotlib.nxutils
    2014-04-28 replaced matplotlib.nxutils with matplotlib.path

    """
    verts = np.vstack((rs, cs)).T

    points = np.indices(image_array.shape).reshape(2, -1).T
    # print "points.shape ",points.shape, "verts.shape ", verts.shape

    # mask = nx.points_inside_poly(points, verts)
    p = Path(verts)
    mask = p.contains_points(points)
    mask = mask.reshape(image_array.shape).astype(int)

    return mask


def gauge_geometry(xy):
    """
    inputs
    xy :        3 row by 2 column array of Top Left, Bottom Left Bottom Right
                coordinates of GB in image numpy array s
                xy = array([[TLx, TLy],
                            [BLx, BLy],

    outputs
    (width, length):
    (ccen, rcen)   :
    phi            : angle of left hand edge to vertical
    """
    length = ((xy[0, :] - xy[1, :]) ** 2).sum() ** 0.5
    width = ((xy[1, :] - xy[2, :]) ** 2).sum() ** 0.5

    # diagonal length of GB
    diag = np.sqrt((xy[0, 1] - xy[2, 1]) ** 2 + (xy[0, 0] - xy[2, 0]) ** 2)

    # angle of diagonal to x-axis
    theta = np.arctan2((xy[2, 1] - xy[0, 1]), (xy[2, 0] - xy[0, 0]))
    # angle of left hand edge to x-axis
    phi = np.arctan2((xy[0, 1] - xy[1, 1]), (xy[0, 0] - xy[1, 0]))

    rcen = xy[2, 0] - diag * np.cos(theta) / 2
    ccen = xy[2, 1] - diag * np.sin(theta) / 2

    rcen = rcen - 1  # match matlab
    ccen = ccen - 1

    return (width, length), (ccen, rcen), phi


def gbroif(s, xy, border=(0.2, 0.1)):
    """
    inputs
    s:          an array of image values shape = (m, n) values between 0 and 255
    xy :        3 row by 2 column array of Top Left, Bottom Left Bottom Right
                coordinates of GB in image numpy array s
                xy = array([[TLx, TLy],
                            [BLx, BLy],
                            [BRx, BRy]])
    border:     area to exclude from fringe detection inside selection defined by xy
                expressd as fraction of gauge width and height
    outputs

    bwo:         array same shape as s where points on platten are 1 others 0
    co,ro:       column and row indices of each vertex of polygon defining
                 platten area, shape = (5,)
    bwi:         array same shape as s where points on gauge are 1 others 0
    ci,ri:       column and row indices of each vertex of polygon defining
                 gauge area,, shape = (5,)
    ccen,rcen:   coordinates of centre of gauge, doubles

    EFH 13/08/2008 translating into python
    Inputs

    xy 3 row by 2 column array of Top Left, Bottom Left Bottom Right coordinates
    of GB in image numpy array s
    xy = array([[TLx, TLy],
                [BLx, BLy],
                [BRx, BRy]])


    This could be replaced with a vector based approached
    the center (C) is halfway bewteen TL and BR ie C = (TL +BR)/2
    the TR corner is TR = (C-BL) + C
    The inner corners are at C + a * (C-TL) etc
    and outer corners at     C + b * (C-TL) etc
    Original code squares up roi, that is roi has square corners,
    even if TL,BR,BL don't form a right angle


    %EFH 20/5/2002

    %writing version that allows x,y as optional inputs

    % Find gauge block regions of interest: central third of
    % gauge and centre.
    % Use three corners only: TL, BL, BR.


    """
    (wid, leng), (ccen, rcen), phi = gauge_geometry(xy)

    # Outside border or buffer is 5 pixels
    ob = 5
    co = np.zeros(5)
    ro = np.zeros(5)
    ci = np.zeros(5)
    ri = np.zeros(5)

    co0 = np.zeros(5)
    ro0 = np.zeros(5)
    ci0 = np.zeros(5)
    ri0 = np.zeros(5)

    co0[0] = -wid / 2 - ob
    ro0[0] = leng / 2 + ob
    co0[1] = -wid / 2 - ob
    ro0[1] = -leng / 2 - ob
    co0[2] = wid / 2 + ob
    ro0[2] = -leng / 2 - ob
    co0[3] = wid / 2 + ob
    ro0[3] = leng / 2 + ob
    co0[4] = co0[0]
    ro0[4] = ro0[0]

    swid = border[0] * wid
    slen = border[1] * leng

    ci0[0] = -wid / 2 + swid
    ri0[0] = leng / 2 - slen
    ci0[1] = -wid / 2 + swid
    ri0[1] = -leng / 2 + slen
    ci0[2] = wid / 2 - swid
    ri0[2] = -leng / 2 + slen
    ci0[3] = wid / 2 - swid
    ri0[3] = leng / 2 - slen
    ci0[4] = ci0[0]
    ri0[4] = ri0[0]

    r = np.array([[np.cos(phi), np.sin(phi)], [-np.sin(phi), np.cos(phi)]])

    for k in range(len(co)):
        cro = np.dot(r, np.array([co0[k], ro0[k]]).T)
        cri = np.dot(r, np.array([ci0[k], ri0[k]]).T)
        # Co-ords of gauge in original frame.
        co[k] = cro[0] + ccen
        ro[k] = cro[1] + rcen
        ci[k] = cri[0] + ccen
        ri[k] = cri[1] + rcen

    bwi = roipoly(s, ci, ri)
    bwo = roipoly(s, co, ro)

    # 0 is false, 1 is true  in matlab so the rest of the code isn't executed

    return bwo, co, ro, bwi, ci, ri, ccen, rcen


def circle_mask_pklist(
    pklist,
    circle: tuple[float, float, float, float],
    img_array_shape: tuple[float, float],
):
    """
    peaks at positions within circle are deleted from pklist

    input
    pklist: output  of pkfind,  a list of numpy arrays with float values for peak maximum
    circle:     (top_left_col, top_left_row, bottom_right_col, bottom_right_row) pixel coordinates of circle mask
    img_array_shape: shape of numpy array storing image (rows, columns)

    output
    pklist_masked: a list of numpy arrays with float values for peak maximum
    """
    # create mask
    # np arrays shape and PIl.Image.Image list shape and size in oppposite order
    img_size = list(img_array_shape)
    img_size.reverse()
    mask = Image.new(mode="1", size=img_size)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(circle, fill="white", outline="white")
    mask_array = np.asarray(mask)

    pklist_masked = []
    for col_num, col in enumerate(pklist):
        col_list = list(col)
        to_delete = []
        for peak in col_list:
            try:
                in_mask = mask_array[round(peak), col_num] == 1
            except IndexError:
                # as the peaks are interpolated they can be just outside image
                continue
            if in_mask:
                to_delete.append(peak)
        col_array = np.array([item for item in col_list if item not in to_delete])
        pklist_masked.append(col_array)
    return pklist_masked


def pkfind(s):
    """
    inputs

    s :         an array of image values shape = (m, n) values between 0 and 255

    outputs
    pklist:     for each column of image, returns an array of the position of
                the darkest values. pklist is a list of one array for each
                column minima position are interpolated between rows.

    pklist{k} contains the locations of the peaks for column k.
    % Modified 24/1/02 to use fft to smooth the data.
    """
    ncol = s.shape[1]
    pklist = []
    n = s.shape[0]

    for k in range(0, ncol):
        # Get column of sub-image and remove best st line.
        y = matplotlib.mlab.detrend_linear(
            s[:, k]
        )  # remove intensity gradient down the column
        yfft = np.fft.fft(y)
        # Positive frequencies only
        ypos = np.abs(yfft[0 : (n // 2) + 1])  # find the magnitudes of each frequency

        # Find fundamental freq (num fringes per column) - it must be greater than 5 fringes per column
        ypos_trunc = ypos[5:]
        iymax = ypos_trunc.argmax()

        k0 = iymax + 5
        # Use components up to 5*f0
        nharm = 5
        yfft[(nharm * k0 + 2) : n - nharm * k0] = 0
        # Reconstruct time series from selected harmonics
        z = np.real(np.fft.ifft(yfft))
        # this is a list of arrays one array for each column

        pkloc = findpeaks2(z)
        pklist.append(pkloc)

    return pklist


def findpeaks2(y):
    """
    INPUTS:
    y :         an array (n,) consisting of 1 column of image
    OUTPUTS:
    pkloc :     an array consisting of the row position of peak (minima), peak
                is interpolated between rows.

    EFH 18/08/08 Translating to python

    %EFH 19/03/03
    %added condition if top of fitted peak is off image
    %EFH 22/05/02
    %added condition there must be at least 5 points in a peak before it is
    fitted

    % Compute locations of peaks in a function.
    % Alternative version using Matlab's polyfit

    see also notes in PythonNotes on alternative possibly faster ways to do this
    """
    # Invert y to find "peaks", convert to float
    y = -y.astype(float)
    thresh = (
        y.max() / 60
    )  # This sets the intensity level (relative to the highest value in the column) that is used select peaks including on a given fringe

    y[y <= thresh] = np.nan

    # check indexing in following line
    loc = np.arange(len(y) - 3)

    # loop version of vectorized code
    # pkloc = [0]
    #
    # j=0
    # for i in range(0,len(y)-3):
    #
    #     if ((y[i+1]>=y[i]) & (y[i+1]>=y[i+2])):
    #         pkloc[j] = i+1
    #         j=j+1
    #         pkloc.append(0)
    #
    # pkloc.pop()

    # print(len(pkloc))

    # original code
    pkloc = loc[(y[1:-2] >= y[0:-3]) & (y[1:-2] >= y[2:-1])] + 1.0

    # %EFH 15/10/02
    # %sometimes no peaks are found in transition area

    # % For each peak, do quadratic interpolation over 7 points.

    for k in range(0, len(pkloc)):
        xstart = pkloc[k] - 3
        if xstart < 0:
            xstart = 0
            xend = 7
        else:
            xend = pkloc[k] + 3

        if xend > len(y) - 1:
            xstart = -2  # 2nd to last item in list
            xend = -1  # last item in list

        xrang = np.arange(xstart, xend, dtype=int)
        yrang = y[xrang]
        # %Flag "peaks" that are close to zero. or that do not have enough points
        if (sum(np.isnan(yrang)) != 0) or (len(xrang) < 5):
            pkloc[k] = np.nan
        else:
            p = np.polyfit(xrang, yrang, 2)
            # %disp(xrange');
            pkloc[k] = -p[1] / (2 * p[0])
            # %EFF 19/03/03 added condition to remove negative fitted peaks
            if (pkloc[k] <= 0) or (pkloc[k] > len(y)):
                pkloc[k] = np.nan

    # indexes_to_delete = []
    # %EFH 15/10/02
    # %sometimes no peaks are found in transition area
    if (len(pkloc) >= 1) & np.isnan(np.sum(pkloc)):
        pkloc = pkloc[np.isnan(pkloc) == 0]  # %Remove false peaks.

    # if len(pkloc) >=1:
    #     for j in range(0,len(pkloc)):
    #         if math.isnan(pkloc[j]):
    #             indexes_to_delete.append(j)

    # pkloc = np.delete(pkloc,indexes_to_delete)

    return pkloc


def findfringes2(y, bw, pklist):
    """
    Used to trace fringes through already found peak positions, used on platen
    INPUTS:
    y:      first column of image -each value contains the intensity (grey scale value)
    BW:     array mask for platen - usually just an array of ones (masked gauges are unimplemented)
    pklist: list of peaks in each column

    OUTPUTS:
    slope:  single slope for all platen fringes
    intercepts:  array of zero intercepts for platen fringes

    deprecated
    A:      inverse of the solution matrix (not used)
    sigma2: (not used)

    %EFH 19/03/03 changing fringe fundamental frequency to find the major
    frequency larger than 5
    % corresponding to at least 5 fringes on gauge

    % Recursive linear regression for determining interferometer fringes
    % Sze Tan, 9-Sep-2000. Modified Lionel Watkins 16/02/2002.

    % Use fft to find the starting positions of the fringes.

    see Metrologia 40 (2003) 139-145 Section 3.2
    """

    n = len(pklist)
    ny = len(y)
    t = np.arange(ny)  # generates an array [0,1,2,3...num of rows in image]
    y = matplotlib.mlab.detrend_linear(
        y
    )  # removes intensity gradient in the image (notibly only in the y direction)

    yfft = np.fft.fft(y)
    # Positive frequencies only
    # CMY added an extra forward slash for int float compatability between python 2 and python 3
    # Returns an array of magnitudes (sampled at a frequency greater than the nyquist frequency i.e period must be less than (ny/2+1))
    ypos = np.abs(yfft[0 : (ny // 2) + 1])

    # %frequencies greater than at least 5 fringes in picture
    # POTENTIAL PROBLEM 1- If the fft of first column gets the Fundamental frequency wrong (due to a poor image) then the rest of this algorithm breaks
    # POTENTIAL PROBLEM 2- The actual fringe fundamental frequency is less than 5 (due to user arranging the too few fringes), then the software needs to report this.  Otherwise the algortithm will crash.
    iymax = np.abs(ypos[4:]).argmax()

    iymax = iymax + 4

    # %Fringe fundamental frequency
    f0 = (iymax - 0.0) / ny  # this is 1 over the number of pixels between fringes

    # % Make "mock" fringe with f0 and find the fringe positions.
    phi = np.arctan2(np.imag(yfft[iymax]), np.real(yfft[iymax]))  # find the phase

    yfit = 2 * np.abs(yfft[iymax]) * (np.cos(2 * np.pi * f0 * t + phi)) / ny
    yt = -yfit

    loc = np.arange(len(yt) - 3)

    # cmy code that is equivalent to single line np vectorization
    # pkloc = [0]
    # j=0
    # for i in range(0,len(yt)-3):
    #
    #     if ((yt[i+1]>=yt[i]) & (yt[i+1]>=yt[i+2])):
    #         pkloc[j] = i+1
    #         j=j+1
    #         pkloc.append(0)
    #
    # pkloc.pop()
    pkloc = loc[(yt[1:-2] >= yt[0:-3]) & (yt[1:-2] >= yt[2:-1])] + 1.0

    # % Find real fringe positions closest to the "mock" ones.
    pks = pklist[0]  # the peaks in the first column
    nfringes = len(pkloc)
    frper = 1 / f0  # num pixels between fringes

    frstart = np.zeros(nfringes)
    for k in range(nfringes):
        mindist = np.abs(
            pks - pkloc[k]
        ).min()  # find the distance the actual fringe is from the mock one
        frnum = np.abs(pks - pkloc[k]).argmin()
        if mindist <= frper / 4:
            frstart[k] = pks[frnum]
        else:
            frstart[k] = pkloc[k]

    # % Set up matrices and vectors for finding best lines
    m = np.zeros((nfringes + 1, nfringes + 1))
    rhs = np.zeros((nfringes + 1))
    peakpred = frstart
    y2sum = 0
    ny = 0
    thresh = (
        frper / 4
    )  # only choose fringes if they are close (1/4 of the spacing between fringes) to the expected position. Ignore peaks (for fitting) if they are greater than this

    # % Loop through columns, finding fringes.  i.e solve nfringes two variable linear regression equations of the form
    # % y = a + bx + e - where y is the peak position, x is the column number, b the slope, a the intercept and e the residual
    for col in range(n):
        if col == 1:
            peaks = frstart
        else:
            peaks = pklist[col]
        # BUG if no peaks are found in a column the array operation below fail "peaks - peakpred[k]).min()"
        # need to decide what to do if no peaks are found in a column

        # % Loop through fringes in a column, there will be at most nfringes but some column may have less if the
        # image quality is poor or the the column coincides with the edge of the gauge block

        for k in range(nfringes):
            if peaks.size == 0:  # CMY edit this column has no peaks detected
                break
            mindist = (
                np.abs(peaks - peakpred[k]).min()
            )  # find the minimum distance this fringe is from the estimated position
            frnum = np.abs(peaks - peakpred[k]).argmin()  # find the fringe number

            if (mindist < thresh) and (bw[int(round(peaks[frnum])), col] == 1):
                m[0, 0] = (
                    m[0, 0] + col**2
                )  # store the sum of the total number of fringes found squared in the first array first position
                m[0, k + 1] = m[0, k + 1] + col  # sum of x values for this fringe
                m[k + 1, 0] = m[k + 1, 0] + col  # sum of x values for this fringe
                m[k + 1, k + 1] = (
                    m[k + 1, k + 1] + 1
                )  # increment the number of peak occurences for this fringe
                rhs[0] = rhs[0] + col * peaks[frnum]  # sum x*y for each fringe
                rhs[k + 1] = rhs[k + 1] + peaks[frnum]  # sum y for each fringe
                y2sum = y2sum + peaks[frnum] ** 2  # sum y^2 for each fringe
                ny = ny + 1

        nextcol = col + 1
        if nextcol > 2:
            # % Solve the regression equations and make prediction of
            # fringe positions
            params = np.linalg.solve(m, rhs)
            peakpred = params[0] * nextcol + params[1:]

    # sigma2 = (y2sum - np.dot(params.T, rhs)) / ny
    # A = np.linalg.inv(m)

    slope = params[0]
    intercepts = params[1:]

    return slope, intercepts


def gauge_initial_column(circle, ci):
    """
    find the starting column for gauges with a circular mask
    """
    print(f"{circle[0]=}, {ci[3]=}")
    return (circle[0] + ci[3]) / 2.0

    pass


def findfringes4e(s, frper, ci, ccen, bw, pklist):
    """
    Used to trace fringes through already found peak positions, used on gauge

    INPUTS:
    s :         array of image values shape = (m, n) values between 0 and 255
    frper:      fringe period (as found on platen)
    ci:         column index of each vertex of polygon defining gauge
                area,, shape = (5,)
    ccen:       coordinates of column centre of gauge, doubles
    BW:         array mask for gauge (based of user selection of corners)
    pklist:     list of peaks in each column

    OUTPUTS:
    slope:  single slope for all gauge fringes
    intercepts:  array of zero intercepts for gauge fringes


    Differences between findfringes2 and findfringes4
    2 uses fft on first row to make mock fringes (used on platen)
    4 uses lsqcurvefit of c(1)+ c(2)*cos(xdata) + c(3)*sin(xdata) on middle row
    (used on gauge)



    %EFH 17/03/03
    %restrict search for real fringes closest to mock ones to length of GB
    % Recursive linear regression for determining gauge fringes
    % Use fft to find the starting positions of the fringes.
    """
    ccen = int(round(ccen))
    # %Grab central column.
    y = matplotlib.mlab.detrend_linear(s[:, ccen])
    good = np.where(
        bw[:, ccen] == 1
    )  # use the array mask to select the column values that are on the gauge
    ytrunc = y[
        good
    ]  # only use the column values within that are on the gauge block (i.e not the values above and below the gauge)
    offset = good[0][0]

    n = len(ytrunc)
    t = np.arange(0, n)
    xdata = 2 * np.pi * t / frper
    # c0 = np.array([1, 1, 1])

    mat = np.vstack((np.ones_like(xdata), np.cos(xdata), np.sin(xdata))).T
    cf = np.linalg.lstsq(mat, ytrunc, rcond=None)[0]

    # % Make "mock" fringe with accurate fringe period
    # and find the fringe positions.

    yfit = np.dot(mat, cf)

    yt = -yfit

    loc = np.arange(len(yt) - 3)

    # loop form of following vectored code
    # pkloc = [0]
    # j=0
    # for i in range(0,len(yt)-3):
    #
    #     if ((yt[i+1]>=yt[i]) & (yt[i+1]>=yt[i+2])):
    #         pkloc[j] = i+1+offset
    #         j=j+1
    #         pkloc.append(0)
    #
    #
    # pkloc.pop()

    pkloc = loc[(yt[1:-2] >= yt[0:-3]) & (yt[1:-2] >= yt[2:-1])] + 1.0 + offset

    # % Find real fringe positions closest to the "mock" ones.
    cstart = ccen
    pks = pklist[cstart]
    nfringes = len(pkloc)
    frstart = np.zeros(nfringes)

    for k in range(nfringes):
        mindist = np.abs(pks - pkloc[k]).min()
        frnum = np.abs(pks - pkloc[k]).argmin()
        if mindist <= frper / 4:
            frstart[k] = pks[frnum]
        else:
            frstart[k] = pkloc[k]

    # % crudely remove any fringes that aren't on gauge
    frstartinc = frstart[
        np.logical_and((frstart >= good[0][0]), (frstart <= good[0][-1]))
    ]

    frstart = frstartinc.T
    nfringes = len(frstart)

    # % Set up matrices and vectors for finding best lines
    m = np.zeros((nfringes + 1, nfringes + 1))
    rhs = np.zeros((nfringes + 1))
    peakpred = frstart
    y2sum = 0
    ny = 0
    thresh = frper / 4
    count = 0

    # % Loop forward through columns, finding fringes
    for col in range(cstart, int(ci.max())):
        if col == cstart:
            peaks = frstart
        else:
            peaks = pklist[col]

        for k in range(nfringes):
            if peaks.size == 0:  # CMY edit this column has no peaks detected
                break
            mindist = np.abs(peaks - peakpred[k]).min()
            frnum = np.abs(peaks - peakpred[k]).argmin()
            if (mindist < thresh) and (bw[int(round(peaks[frnum])), col] == 1):
                m[0, 0] = m[0, 0] + col**2
                m[0, k + 1] = m[0, k + 1] + col
                m[k + 1, 0] = m[k + 1, 0] + col
                m[k + 1, k + 1] = m[k + 1, k + 1] + 1
                rhs[0] = rhs[0] + col * peaks[frnum]
                rhs[k + 1] = rhs[k + 1] + peaks[frnum]
                y2sum = y2sum + peaks[frnum] ** 2
                ny = ny + 1

        count = count + 1
        if count > 2:
            # % Solve the regression equations and make prediction
            # of fringe positions
            # print np.linalg.det(m)
            params = np.linalg.solve(m, rhs)
            peakpred = params[0] * (col + 1) + params[1:]

    peakpred = params[0] * (cstart - 1) + params[1:]
    # % Loop backwards through columns, finding fringes

    for col in range(cstart - 1, int(ci.min()), -1):
        peaks = pklist[col]

        for k in range(nfringes):
            if peaks.size == 0:  # CMY edit this column has no peaks detected
                break
            mindist = np.abs(peaks - peakpred[k]).min()
            frnum = np.abs(peaks - peakpred[k]).argmin()
            if (mindist < thresh) and (bw[int(round(peaks[frnum])), col] == 1):
                m[0, 0] = m[0, 0] + col**2
                m[0, k + 1] = m[0, k + 1] + col
                m[k + 1, 0] = m[k + 1, 0] + col
                m[k + 1, k + 1] = m[k + 1, k + 1] + 1
                rhs[0] = rhs[0] + col * peaks[frnum]
                rhs[k + 1] = rhs[k + 1] + peaks[frnum]
                y2sum = y2sum + peaks[frnum] ** 2
                ny = ny + 1

        nextcol = col - 1
        # % Solve the regression equations and make prediction of fringe positions
        # print np.linalg.det(m)
        params = np.linalg.solve(m, rhs)
        peakpred = params[0] * nextcol + params[1:]

    # sigma2 = (y2sum - np.dot(params.T, rhs)) / ny
    # A = sigma2 * np.linalg.inv(M)

    #    for k in range(nfringes):
    #        b = np.zeros((1,nfringes+1))
    #        b[0,0] = ccen
    #        b[0,k+1] = 1
    #        u = np.sqrt(np.dot(b,np.dot(A,b.T)))

    slope = params[0]
    intercepts = params[1:]

    return slope, intercepts


def lines2frac(ccen, rcen, pslope, pintercepts, gslope, gintercepts):
    """
    calculates fringe fraction from slopes and intercepts.
    INPUTS:
    rcen, ccen:             coordinates of centre of gauge
    pslope, pintercepts:    slope and intercepts for platen
    gslope, gintercepts:    slope and intercepts for gauge

    OUTPUTS:
    ffrac : gauge fringe fraction between -1 and 1

    """
    yin = gintercepts + gslope * ccen
    yout = pintercepts + pslope * ccen
    frac = np.zeros_like(yin)
    # calculate fringe fraction for each gauge fringe
    for k in range(len(yin)):
        # index of fringes "above" and "below" gauge fringe yin[k]
        above = np.where(yout >= yin[k])[0]
        below = np.where(yout <= yin[k])[0]
        if below.size != 0 and above.size != 0:
            topfringe = yout[above.min()]
            botfringe = yout[below.max()]
            frac[k] = (topfringe - yin[k]) / (topfringe - botfringe)
        else:
            frac[k] = np.nan

    ffindx1 = np.max(np.where(yin <= rcen))
    ffindx2 = np.min(np.where(yin >= rcen))
    frac1 = frac[ffindx1]
    frac2 = frac[ffindx2]
    if np.abs(frac1 - frac2) > 0.5:
        frac1 = shifthalf(frac1)
        frac2 = shifthalf(frac2)

    # Linearly interpolate between nearest two fringe fractions.
    ffp = np.polyfit((yin[ffindx1], yin[ffindx2]), (frac1, frac2), 1)
    ffrac = np.polyval(ffp, rcen)

    return ffrac


def shifthalf(number):
    """
    Maps numbers in the range -1 to 1 onto the range -0.5 to +0.5
    by adding -1,0 or 1
    """
    sh = number + 1 - np.floor(number + 1.5)
    return sh


def convert_drawdata_list_to_dict(drawdata):
    """
    used for loading older (pre 2025-11-18) shelf files where drawdata was stored as list
    converted to dict so extra items can be added to plot circular mask etc.
    """
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
    info = {
        "xy": xy,
        "co": co,
        "ro": ro,
        "ci": ci,
        "ri": ri,
        "ccen": ccen,
        "rcen": rcen,
        "pklist": pklist,
        "slopep": slopep,
        "interceptsp": interceptsp,
        "slopeg": slopeg,
        "interceptsg": interceptsg,
    }
    return info


def array2frac(
    s, xy, drawinfo=False, circle_radius=None, border=(0.2, 0.1), col_start_frac=0.2
):
    """
    INPUTS
    s:          an array of image values shape = (m, n) values between 0 and 255
    xy :        3 row by 2 column array of Top Left, Bottom Left
                Bottom Right coordinates
                of GB in image np array s
                xy = array([[TLx, TLy],
                            [BLx, BLy],
                            [BRx, BRy]])
    drawinfo:   output co-ordinates for plotting in FringeManager.annotate_fig
    circle_radius:  circle is centered on gauge with radius in pixels = gauge_width  * circle_radius
    border: (col, row) fraction of gauge height and width to exclude from inside gauge
    col_start_frac: position of the colunm used to start looking for gauge fringes, as fraction of circle radius
    OUTPUTS
    ffrac : gauge fringe fraction between -1 and 1
    drawinfo: (optional) lots of info used by FringeManager.annotate_fig
    """
    # s needs to have an even number of rows for fft.
    if np.mod(s.shape[0], 2) == 1:
        s = s[:-1, :]
    bwo, co, ro, bwi, ci, ri, ccen, rcen = gbroif(s, xy, border=border)
    pklist = pkfind(s)
    col_start = ccen
    radius = None
    if circle_radius is not None:
        width = np.sqrt((xy[1, 1] - xy[2, 1]) ** 2 + (xy[1, 0] - xy[2, 0]) ** 2)
        radius = circle_radius * width
        circle = (ccen - radius, rcen - radius, ccen + radius, rcen + radius)
        pklist = circle_mask_pklist(pklist, circle, s.shape)
        col_start = circle[0] - col_start_frac * radius
    y = s[:, 0]
    bwp = np.ones_like(bwo) - bwo
    slopep, interceptsp = findfringes2(y, bwp, pklist)
    frper = np.mean(np.diff((slopep * ccen + interceptsp)))
    slopeg, interceptsg = findfringes4e(s, frper, ci, col_start, bwi, pklist)
    ffrac = lines2frac(ccen, rcen, slopep, interceptsp, slopeg, interceptsg)
    if drawinfo:
        info = {
            "xy": xy,
            "co": co,
            "ro": ro,
            "ci": ci,
            "ri": ri,
            "ccen": ccen,
            "rcen": rcen,
            "pklist": pklist,
            "slopep": slopep,
            "interceptsp": interceptsp,
            "slopeg": slopeg,
            "interceptsg": interceptsg,
            "circle": radius,  # in pixels
            "col_start": col_start,
        }
        return ffrac, info
    else:
        return ffrac
