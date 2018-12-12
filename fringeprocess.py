import numpy as np

# import math

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
    mask = mask.reshape(image_array.shape).astype(np.int)

    return mask


def gbroif(s, xy):
    """
    inputs
    s:          an array of image values shape = (m, n) values between 0 and 255
    xy :        3 row by 2 column array of Top Left, Bottom Left Bottom Right
                coordinates of GB in image numpy array s
                xy = array([[TLx, TLy],
                            [BLx, BLy],
                            [BRx, BRy]])
    outputs

    BWo:         array same shape as s where points on platten are 1 others 0
    xo,yo:       column and row indices of each vertex of polygon defining
                 platten area, shape = (5,)
    BWi:         array same shape as s where points on gauge are 1 others 0
    xi,yi:       column and row indices of each vertex of polygon defining
                 gauge area,, shape = (5,)
    xcen,ycen:   coordinates of centre of gauge, doubles

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

    # TODO the readability of this could be improved by using more
    # numpy type arrays

    # diagonal length of GB
    lh = np.sqrt((xy[0, 1] - xy[2, 1]) ** 2 + (xy[0, 0] - xy[2, 0]) ** 2)
    # left hand length of GB
    leng = np.sqrt((xy[0, 1] - xy[1, 1]) ** 2 + (xy[0, 0] - xy[1, 0]) ** 2)
    # bottom width of GB
    wid = np.sqrt((xy[1, 1] - xy[2, 1]) ** 2 + (xy[1, 0] - xy[2, 0]) ** 2)
    # angle of diagonal to x-axis
    theta = np.arctan2((xy[2, 1] - xy[0, 1]), (xy[2, 0] - xy[0, 0]))
    # angle of left hand edge to x-axis
    phi = np.arctan2((xy[0, 1] - xy[1, 1]), (xy[0, 0] - xy[1, 0]))

    rcen = xy[2, 0] - lh * np.cos(theta) / 2
    ccen = xy[2, 1] - lh * np.sin(theta) / 2

    rcen = rcen - 1  # match matlab
    ccen = ccen - 1

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

    swid = wid / 5
    # EFH 15/10/02 changing this from slen = len/20 to slen = len/10
    slen = leng / 10
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
        y = matplotlib.mlab.detrend_linear(s[:, k])
        yfft = np.fft.fft(y)
        # Positive frequencies only
        ypos = np.abs(yfft[0: (n // 2) + 1])
        # Find fundamental freq.
        iymax = ypos.argmax()
        k0 = iymax
        # Use components up to 5*f0
        nharm = 5
        yfft[(nharm * k0 + 2): n - nharm * k0] = 0
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
    y = -y.astype(np.float)
    thresh = y.max() / 5

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

        xrang = np.arange(xstart, xend, dtype=np.int)
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
    y:      first column of image
    BW:     array mask for platen
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
    t = np.arange(ny)
    y = matplotlib.mlab.detrend_linear(y)

    yfft = np.fft.fft(y)
    # Positive frequencies only
    # CMY added an extra forward slash for int float compatability between python 2 and python 3
    ypos = np.abs(yfft[0: (ny // 2) + 1])

    # %frequencies greater than at least 5 fringes in picture
    # Ym = np.abs(ypos[4:]).max()
    iymax = np.abs(ypos[4:]).argmax()

    iymax = iymax + 4
    # %Fringe fundamental frequency
    f0 = (iymax - 0.0) / ny

    # % Make "mock" fringe with f0 and find the fringe positions.
    phi = np.arctan2(np.imag(yfft[iymax]), np.real(yfft[iymax]))

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
    pks = pklist[0]
    nfringes = len(pkloc)
    frper = 1 / f0

    frstart = np.zeros(nfringes)
    for k in range(nfringes):
        mindist = np.abs(pks - pkloc[k]).min()
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
    thresh = frper / 4

    # % Loop through columns, finding fringes
    for col in range(n):
        if col == 1:
            peaks = frstart
        else:
            peaks = pklist[col]

        for k in range(nfringes):
            mindist = np.abs(peaks - peakpred[k]).min()
            frnum = np.abs(peaks - peakpred[k]).argmin()

            if (mindist < thresh) and (bw[int(round(peaks[frnum])), col] == 1):
                m[0, 0] = m[0, 0] + col ** 2
                m[0, k + 1] = m[0, k + 1] + col
                m[k + 1, 0] = m[k + 1, 0] + col
                m[k + 1, k + 1] = m[k + 1, k + 1] + 1
                rhs[0] = rhs[0] + col * peaks[frnum]
                rhs[k + 1] = rhs[k + 1] + peaks[frnum]
                y2sum = y2sum + peaks[frnum] ** 2
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


def findfringes4e(s, frper, ci, ccen, bw, pklist):

    """
    Used to trace fringes through already found peak positions, used on gauge

    INPUTS:
    s :         array of image values shape = (m, n) values between 0 and 255
    frper:      fringe period (as found on platen)
    ci:         column index of each vertex of polygon defining gauge
                area,, shape = (5,)
    ccen:       coordinates of column centre of gauge, doubles
    BW:         array mask for gauge
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
    good = np.where(bw[:, ccen] == 1)
    ytrunc = y[good]
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
            mindist = np.abs(peaks - peakpred[k]).min()
            frnum = np.abs(peaks - peakpred[k]).argmin()
            if (mindist < thresh) and (bw[int(round(peaks[frnum])), col] == 1):
                m[0, 0] = m[0, 0] + col ** 2
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
            mindist = np.abs(peaks - peakpred[k]).min()
            frnum = np.abs(peaks - peakpred[k]).argmin()
            if (mindist < thresh) and (bw[int(round(peaks[frnum])), col] == 1):
                m[0, 0] = m[0, 0] + col ** 2
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
            frac[k] = np.NaN

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


def array2frac(s, xy, drawinfo=False):
    """
    INPUTS
    s:          an array of image values shape = (m, n) values between 0 and 255
    xy :        3 row by 2 column array of Top Left, Bottom Left
                Bottom Right coordinates
                of GB in image np array s
                xy = array([[TLx, TLy],
                            [BLx, BLy],
                            [BRx, BRy]])
    OUTPUTS
    ffrac : gauge fringe fraction between -1 and 1
    """
    # s needs to have an even number of rows for fft.
    if np.mod(s.shape[0], 2) == 1:
        s = s[:-1, :]
    bwo, co, ro, bwi, ci, ri, ccen, rcen = gbroif(s, xy)
    pklist = pkfind(s)
    y = s[:, 0]
    bwp = np.ones_like(bwo) - bwo
    slopep, interceptsp = findfringes2(y, bwp, pklist)
    frper = np.mean(np.diff((slopep * ccen + interceptsp)))
    slopeg, interceptsg = findfringes4e(s, frper, ci, ccen, bwi, pklist)
    ffrac = lines2frac(ccen, rcen, slopep, interceptsp, slopeg, interceptsg)
    if drawinfo:
        info = [
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
        ]
        return ffrac, info
    else:
        return ffrac
