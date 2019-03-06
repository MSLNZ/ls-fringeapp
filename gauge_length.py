"""
Calculate gauge length from fringe fractions and gauge data
"""
import numpy as np
from refractiveindex import RefractiveIndex
from fringeprocess import shifthalf

ObliquityCorrection  = 1.00000013


def frac(number):
    return number - np.fix(number)


def calcgaugelength(
    nominalsize_mm,
    rtemp_c,
    gtemp_c,
    pressure_mb,
    humidity_rh,
    ffred,
    ffgreen,
    expcoeff,
    redwavelength,
    greenwavelength,
    formula=0,
):

    # %Search the range (Nominal Size ? Nfringes * red  fringe spacing)
    # for best solution for gauge length
    nfringes = 5
    mindiff = 1000

    redindex = RefractiveIndex(
        rtemp_c, pressure_mb, humidity_rh, redwavelength, formula
    )
    greenindex = RefractiveIndex(
        gtemp_c, pressure_mb, humidity_rh, greenwavelength, formula
    )
    redfringespacing_nm = (redwavelength * ObliquityCorrection) / (2.0 * redindex)
    greenfringespacing_nm = (greenwavelength * ObliquityCorrection) / (2.0 * greenindex)
    nominalsizeattr_nm = nominalsize_mm * 1000000.0 * (1 + expcoeff * (rtemp_c - 20))
    nominalsizeattg_nm = nominalsize_mm * 1000000.0 * (1 + expcoeff * (gtemp_c - 20))
    ffrednominalsize = frac(nominalsizeattr_nm / redfringespacing_nm)
    ffdiffred = shifthalf(ffred / 100 - ffrednominalsize)

    reddeviations_nm = np.empty(2 * nfringes + 1)
    greendeviations_nm = np.empty(2 * nfringes + 1)

    bestsolutionindex = 0

    for i in range(-nfringes, nfringes + 1):
        reddeviations_nm[i + 5] = (ffdiffred + i) * redfringespacing_nm
        estsizeattg_nm = nominalsizeattg_nm + reddeviations_nm[i + 5]

        ffgreenestsize = frac(estsizeattg_nm / greenfringespacing_nm)
        ffdiffgreen = shifthalf(ffgreen / 100 - ffgreenestsize)
        greendeviations_nm[i + 5] = (
            ffdiffgreen * greenfringespacing_nm + reddeviations_nm[i + 5]
        )

        deviationdiff_nm = reddeviations_nm[i + 5] - greendeviations_nm[i + 5]
        if abs(deviationdiff_nm) < abs(mindiff):
            mindiff = deviationdiff_nm
            bestsolutionindex = i + 5
        # end %If
    # end %Next i

    return reddeviations_nm, greendeviations_nm, bestsolutionindex

