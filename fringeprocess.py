import numpy
import math

import matplotlib.image
#import matplotlib.nxutils as nx
import matplotlib.mlab

cos = numpy.cos
sin = numpy.sin
pi = numpy.pi
from matplotlib.path import Path


def roipoly(I, cs, rs):

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
    verts = numpy.vstack((rs, cs)).T

    points = numpy.indices(I.shape).reshape(2, -1).T
    #print "points.shape ",points.shape, "verts.shape ", verts.shape

    #mask = nx.points_inside_poly(points, verts)
    p = Path(verts)
    mask = p.contains_points(points)
    mask = mask.reshape(I.shape).astype(numpy.int)

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

    #TODO the readability of this could be improved by using more
    #numpy type arrays

    #diagonal length of GB
    lh = numpy.sqrt((xy[0,1]-xy[2,1])**2 + (xy[0,0]-xy[2,0])**2)
    #left hand length of GB
    leng = numpy.sqrt((xy[0,1]-xy[1,1])**2 + (xy[0,0]-xy[1,0])**2)
    #bottom width of GB
    wid = numpy.sqrt((xy[1,1]-xy[2,1])**2 + (xy[1,0]-xy[2,0])**2)
    #angle of diagonal to x-axis
    theta = numpy.arctan2((xy[2,1]-xy[0,1]),(xy[2,0]-xy[0,0]))
    #angle of left hand edge to x-axis
    phi = numpy.arctan2((xy[0,1]-xy[1,1]),(xy[0,0]-xy[1,0]))



    rcen = xy[2,0] - lh*numpy.cos(theta)/2
    ccen = xy[2,1] - lh*numpy.sin(theta)/2

    rcen = rcen -1  #match matlab
    ccen = ccen -1

    #Outside border or buffer is 5 pixels
    ob = 5
    co = numpy.zeros(5)
    ro = numpy.zeros(5)
    ci = numpy.zeros(5)
    ri = numpy.zeros(5)

    co0 = numpy.zeros(5)
    ro0 = numpy.zeros(5)
    ci0 = numpy.zeros(5)
    ri0 = numpy.zeros(5)


    co0[0] = -wid/2 - ob
    ro0[0] = leng/2 + ob
    co0[1] = -wid/2 - ob
    ro0[1] = -leng/2 - ob
    co0[2] = wid/2 + ob
    ro0[2] = -leng/2 - ob
    co0[3] = wid/2 + ob
    ro0[3] = leng/2 + ob
    co0[4] = co0[0]
    ro0[4] = ro0[0]


    swid = wid/5
    #EFH 15/10/02 changing this from slen = len/20 to slen = len/10
    slen = leng/10
    ci0[0] = -wid/2 + swid
    ri0[0] = leng/2 - slen
    ci0[1] = -wid/2 + swid
    ri0[1] = -leng/2 + slen
    ci0[2] = wid/2 - swid
    ri0[2] = -leng/2 + slen
    ci0[3] = wid/2 -swid
    ri0[3] = leng/2 - slen
    ci0[4] = ci0[0]
    ri0[4] = ri0[0]


    R = numpy.array([[numpy.cos(phi), numpy.sin(phi)],
                     [-numpy.sin(phi), numpy.cos(phi)]])


    for k in range(len(co)):
        cro = numpy.dot(R,numpy.array([co0[k],ro0[k]]).T)
        cri = numpy.dot(R,numpy.array([ci0[k],ri0[k]]).T)
        #Co-ords of gauge in original frame.
        co[k] = cro[0] + ccen
        ro[k] = cro[1] + rcen
        ci[k] = cri[0] + ccen
        ri[k] = cri[1] + rcen



    BWi = roipoly(s,ci,ri)
    BWo = roipoly(s,co,ro)

    # 0 is false, 1 is true  in matlab so the rest of the code isn't executed

    return BWo,co,ro,BWi,ci,ri,ccen,rcen



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
    N = s.shape[0]



    for k in range(0, ncol):
        #Get column of sub-image and remove best st line.
        y = matplotlib.mlab.detrend_linear(s[:,k])
        Y = numpy.fft.fft(y)
        #Positive frequencies only
        Ypos = numpy.abs(Y[0:(N//2) + 1])
        #Find fundamental freq.
        Ym = Ypos.max()
        I = Ypos.argmax()
        k0 = I
        #Use components up to 5*f0
        nharm = 5
        Y[nharm*k0+2:N-nharm*k0] = 0
        #Reconstruct time series from selected harmonics
        z = numpy.real(numpy.fft.ifft(Y))
        #this is a list of arrays one array for each column
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
    #Invert y to find "peaks", convert to float
    y = -y.astype(numpy.float)
    thresh = y.max()/5

    y[y <= thresh] = numpy.nan

    # check indexing in following line
    loc = numpy.arange(len(y) - 3)

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
       
    #print(len(pkloc))    
     
    #original code
    pkloc = loc[(y[1:-2] >= y[0:-3]) & (y[1:-2] >= y[2:-1])] + 1.0
    


    #%EFH 15/10/02
    #%sometimes no peaks are found in transition area

    #% For each peak, do quadratic interpolation over 7 points.


    for k in range(0,len(pkloc)):
        xstart = pkloc[k] - 3
        if xstart < 0:
            xstart = 0
            xend = 7

        xend = pkloc[k] + 3
        if xend > len(y) - 1 :
            xstart = -2  # 2nd to last item in list
            xend = -1   # last item in list

        xrang = numpy.arange(xstart,xend, dtype=numpy.int)
        yrang = y[xrang]
        #%Flag "peaks" that are close to zero. or that do not have enough points
        if (sum(numpy.isnan(yrang)) != 0) or (len(xrang) < 5):
            pkloc[k] = numpy.nan
        else:
            p = numpy.polyfit(xrang,yrang,2)
            #%disp(xrange');
            pkloc[k] = -p[1]/(2*p[0])
            #%EFF 19/03/03 added condition to remove negative fitted peaks
            if (pkloc[k] <= 0) or (pkloc[k] > len(y)):
                pkloc[k] = numpy.nan


    # indexes_to_delete = []
    #%EFH 15/10/02
    #%sometimes no peaks are found in transition area
    if (len(pkloc) >= 1) & numpy.isnan(numpy.sum(pkloc)):
        pkloc = pkloc[numpy.isnan(pkloc) == 0]  # %Remove false peaks.

    # if len(pkloc) >=1:
    #     for j in range(0,len(pkloc)):
    #         if math.isnan(pkloc[j]):
    #             indexes_to_delete.append(j)

    # pkloc = numpy.delete(pkloc,indexes_to_delete)

    return pkloc

def findfringes2(y,BW,pklist):
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
    N = len(y)
    t = numpy.arange(N)
    y = matplotlib.mlab.detrend_linear(y)

    Y = numpy.fft.fft(y)
    #Positive frequencies only CMY added an extra forward slash for int float compatability between python 2 and python 3
    Ypos = numpy.abs(Y[0:(N//2) + 1])

    #%frequencies greater than at least 5 fringes in picture
    Ym = numpy.abs(Ypos[4:]).max()
    I = numpy.abs(Ypos[4:]).argmax()

    I = I + 4
    #%Fringe fundamental frequency
    f0 = (I - 0.0)/N

    #% Make "mock" fringe with f0 and find the fringe positions.
    phi = numpy.arctan2(numpy.imag(Y[I]),numpy.real(Y[I]))

    yfit = 2*numpy.abs(Y[I])*(cos(2*pi*f0*t + phi))/N
    yt = -yfit

    loc = numpy.arange(len(yt) - 3)

    #cmy code that is equivalent to single line numpy vectorization
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
    pkloc = loc[(yt[1:-2]>=yt[0:-3]) & (yt[1:-2]>=yt[2:-1])] + 1.0



    #% Find real fringe positions closest to the "mock" ones.
    pks = pklist[0]
    nfringes = len(pkloc)
    frper = 1/f0

    frstart = numpy.zeros((nfringes))
    for k in range(nfringes):
        mindist= numpy.abs(pks-pkloc[k]).min()
        frnum = numpy.abs(pks-pkloc[k]).argmin()
        if mindist <= frper/4:
            frstart[k] = pks[frnum]
        else:
            frstart[k] = pkloc[k]



    #% Set up matrices and vectors for finding best lines
    M = numpy.zeros((nfringes+1, nfringes+1))
    rhs = numpy.zeros((nfringes+1))
    peakpred = frstart
    y2sum = 0; ny = 0
    thresh = frper/4

    #% Loop through columns, finding fringes
    for col in range(n):
        if col == 1:
            peaks = frstart
        else:
            peaks = pklist[col]

        for k in range(nfringes):
            mindist = numpy.abs(peaks-peakpred[k]).min()
            frnum = numpy.abs(peaks-peakpred[k]).argmin()

            if (mindist < thresh) and  (BW[int(round(peaks[frnum])),col]==1 ):
                M[0,0] = M[0,0] + col**2
                M[0,k+1] = M[0,k+1] + col
                M[k+1,0] = M[k+1,0] + col
                M[k+1,k+1] = M[k+1,k+1] + 1
                rhs[0] = rhs[0] + col*peaks[frnum]
                rhs[k+1] = rhs[k+1] + peaks[frnum]
                y2sum = y2sum + peaks[frnum]**2
                ny = ny + 1


        nextcol = col+1
        if nextcol > 2:
            #% Solve the regression equations and make prediction of
            #fringe positions
            params = numpy.linalg.solve(M, rhs)
            peakpred =params[0]*nextcol + params[1:]


    sigma2 =(y2sum - numpy.dot(params.T,rhs))/ny
    A = numpy.linalg.inv(M)
    slope = params[0]
    intercepts = params[1:]

    return slope,intercepts

def findfringes4E(s,frper,ci,ri,ccen,rcen,BW,pklist):

    """
    Used to trace fringes through already found peak positions, used on gauge

    INPUTS:
    s :         array of image values shape = (m, n) values between 0 and 255
    frper:      fringe period (as found on platen)
    ri,ci:      column and row indices of each vertex of polygon defining gauge
                area,, shape = (5,)
    rcen,ccen:  coordinates of centre of gauge, doubles
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
    #%Grab central column.
    y = matplotlib.mlab.detrend_linear(s[:, ccen])
    good = numpy.where(BW[:,ccen]==1)
    ytrunc = y[good]
    offset = good[0][0]

    N = len(ytrunc)
    t = numpy.arange(0,N)
    xdata = 2*pi*t/frper
    c0 = numpy.array([1, 1, 1])


    mat = numpy.vstack((numpy.ones_like(xdata),
                        numpy.cos(xdata),
                        numpy.sin(xdata))).T
    cf = numpy.linalg.lstsq(mat, ytrunc, rcond=None)[0]



    #% Make "mock" fringe with accurate fringe period
    #and find the fringe positions.

    yfit = numpy.dot(mat,cf)


    yt = -yfit

    loc = numpy.arange(len(yt) - 3)

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

    pkloc = loc[(yt[1:-2]>=yt[0:-3]) & (yt[1:-2]>=yt[2:-1])] + 1.0 + offset

    #% Find real fringe positions closest to the "mock" ones.
    cstart = ccen
    pks = pklist[cstart]
    nfringes = len(pkloc)
    frstart = numpy.zeros((nfringes))

    for k in range(nfringes):
        mindist = numpy.abs(pks-pkloc[k]).min()
        frnum = numpy.abs(pks-pkloc[k]).argmin()
        if mindist <= frper/4:
            frstart[k] = pks[frnum]
        else:
            frstart[k] = pkloc[k]

    #% crudely remove any fringes that aren't on gauge
    frstartinc = frstart[numpy.logical_and((frstart >= good[0][0]),
                        (frstart <= good[0][-1]))]

    frstart = frstartinc.T
    nfringes = len(frstart)

    #% Set up matrices and vectors for finding best lines
    M = numpy.zeros((nfringes+1, nfringes+1))
    rhs = numpy.zeros((nfringes+1))
    peakpred = frstart
    y2sum = 0
    ny = 0
    thresh = frper/4
    count = 0

    #% Loop forward through columns, finding fringes
    for col in  range(cstart, int(ci.max())):
        if col == cstart:
            peaks = frstart
        else:
            peaks = pklist[col]

        for k in range(nfringes):
            mindist = numpy.abs(peaks-peakpred[k]).min()
            frnum = numpy.abs(peaks-peakpred[k]).argmin()
            if (mindist < thresh) and (BW[int(round(peaks[frnum])),col]==1 ):
               M[0,0] = M[0,0] + col**2
               M[0,k+1] = M[0,k+1] + col
               M[k+1,0] = M[k+1,0] + col
               M[k+1,k+1] = M[k+1,k+1] + 1
               rhs[0] = rhs[0] + col*peaks[frnum]
               rhs[k+1] = rhs[k+1] + peaks[frnum]
               y2sum = y2sum + peaks[frnum]**2
               ny = ny + 1


        count = count+1
        if count > 2:
            #% Solve the regression equations and make prediction
            #of fringe positions
            #print numpy.linalg.det(M)
            params = numpy.linalg.solve(M,rhs)
            peakpred = params[0]*(col+1) + params[1:]



    peakpred = params[0]*(cstart-1) + params[1:]
    #% Loop backwards through columns, finding fringes

    for col in range(cstart-1,int(ci.min()),-1):
        peaks = pklist[col]
        for k in range(nfringes):
            mindist = numpy.abs(peaks-peakpred[k]).min()
            frnum = numpy.abs(peaks-peakpred[k]).argmin()
            if (mindist < thresh) and (BW[int(round(peaks[frnum])), col]==1 ):
               M[0, 0] = M[0, 0] + col**2
               M[0, k+1] = M[0, k+1] + col
               M[k+1, 0] = M[k+1, 0] + col
               M[k+1, k+1] = M[k+1, k+1] + 1
               rhs[0] = rhs[0] + col*peaks[frnum]
               rhs[k+1] = rhs[k+1] + peaks[frnum]
               y2sum = y2sum + peaks[frnum]**2
               ny = ny + 1

        nextcol = col - 1
        #% Solve the regression equations and make prediction of fringe positions
        #print numpy.linalg.det(M)
        params = numpy.linalg.solve(M,rhs)
        peakpred = params[0]*nextcol + params[1:]


    sigma2 = (y2sum - numpy.dot(params.T,rhs))/ny
    A = sigma2*numpy.linalg.inv(M)

##    for k in range(nfringes):
##        b = numpy.zeros((1,nfringes+1))
##        b[0,0] = ccen
##        b[0,k+1] = 1
##        u = numpy.sqrt(numpy.dot(b,numpy.dot(A,b.T)))


    slope = params[0]
    intercepts = params[1:]

    return slope,intercepts

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
    yin = gintercepts + gslope*ccen
    yout = pintercepts + pslope*ccen
    frac = numpy.zeros_like(yin)
    #calculate fringe fraction for each gauge fringe
    for k in range(len(yin)):
        #index of fringes "above" and "below" gauge fringe yin[k]
        above = numpy.where(yout >= yin[k])[0]
        below = numpy.where(yout <= yin[k])[0]
        if below.size != 0 and above.size != 0:
           topfringe = yout[above.min()]
           botfringe = yout[below.max()]
           frac[k] = (topfringe - yin[k])/(topfringe - botfringe)
        else:
           frac[k] = numpy.NaN


    ffindx1 = numpy.max(numpy.where(yin <= rcen))
    ffindx2 = numpy.min(numpy.where(yin >= rcen))
    frac1 = frac[ffindx1]
    frac2 = frac[ffindx2]
    if numpy.abs(frac1-frac2) > 0.5:
        frac1 = shifthalf(frac1)
        frac2 = shifthalf(frac2)

    #Linearly interpolate between nearest two fringe fractions.
    ffp = numpy.polyfit((yin[ffindx1], yin[ffindx2]), (frac1, frac2), 1)
    ffrac = numpy.polyval(ffp, rcen)

    return ffrac

def shifthalf(number):
    """
    Maps numbers in the range -1 to 1 onto the range -0.5 to +0.5
    by adding -1,0 or 1
    """
    sh = number + 1 - numpy.floor(number + 1.5)
    return sh

def array2frac(s, xy, drawinfo=False):
    """
    INPUTS
    s:          an array of image values shape = (m, n) values between 0 and 255
    xy :        3 row by 2 column array of Top Left, Bottom Left
                Bottom Right coordinates
                of GB in image numpy array s
                xy = array([[TLx, TLy],
                            [BLx, BLy],
                            [BRx, BRy]])
    OUTPUTS
    ffrac : gauge fringe fraction between -1 and 1
    """
    #s needs to have an even number of rows for fft.
    if numpy.mod(s.shape[0], 2) == 1:
        s = s[:-1, :]
    BWo, co, ro, BWi, ci, ri, ccen, rcen = gbroif(s, xy)
    pklist = pkfind(s)
    y = s[:, 0]
    BWp = numpy.ones_like(BWo) - BWo
    slopep,interceptsp = findfringes2(y,BWp,pklist)
    frper = numpy.mean(numpy.diff((slopep*ccen+interceptsp)))
    slopeg, interceptsg = findfringes4E(s,frper,ci,ri,ccen,rcen,BWi,pklist)
    ffrac = lines2frac(ccen, rcen, slopep, interceptsp, slopeg, interceptsg)
    if drawinfo:
        info = [xy,co,ro,ci,ri,ccen,rcen,pklist,slopep,interceptsp,slopeg,interceptsg]
        return ffrac, info
    else:
        return ffrac


