"""
Calculate gauge length from fringe fractions and gauge data
"""
import numpy
from refractiveindex import RefractiveIndex
from fringeprocess import shifthalf

#Report No./Length/2009/790,16 June 2011
RedWavelength  = 632.991470
GreenWavelength  = 546.07498
ObliquityCorrection  = 1.00000013

def frac(number):
    return number - numpy.fix(number)

def CalcGaugeLength(NominalSize_mm,
                           RTemp_C,
                           GTemp_C,
                           Pressure_mb,
                           Humidity_RH,
                           ffRed,
                           ffGreen,
                           ExpCoeff):

    #%Search the range (Nominal Size ? Nfringes * red  fringe spacing)
    #for best solution for gauge length
    Nfringes  = 5
    MinDiff = 1000

    redindex = RefractiveIndex(RTemp_C, Pressure_mb, Humidity_RH, RedWavelength)
    greenindex = RefractiveIndex(GTemp_C, Pressure_mb, Humidity_RH, GreenWavelength)
    RedFringeSpacing_nm = (RedWavelength * ObliquityCorrection) / (2.0 * redindex)
    GreenFringeSpacing_nm = GreenWavelength * ObliquityCorrection / (2.0 * greenindex)
    NominalSizeAtTR_nm = NominalSize_mm * 1000000.0 * (1 + ExpCoeff * (RTemp_C - 20))
    NominalSizeAtTG_nm = NominalSize_mm * 1000000.0 * (1 + ExpCoeff * (GTemp_C - 20))
    ffRedNominalSize = frac(NominalSizeAtTR_nm / RedFringeSpacing_nm)
    ffDiffRed = shifthalf(ffRed / 100 - ffRedNominalSize)

    RedDeviations_nm = numpy.empty(2*Nfringes+1)
    GreenDeviations_nm = numpy.empty(2*Nfringes+1)

    for i in range(-Nfringes,Nfringes+1):
        RedDeviations_nm[i+5] = (ffDiffRed + i) * RedFringeSpacing_nm
        EstSizeAtTG_nm = NominalSizeAtTG_nm + RedDeviations_nm[i+5]

        ffGreenEstSize = frac(EstSizeAtTG_nm / GreenFringeSpacing_nm)
        ffDiffGreen = shifthalf(ffGreen / 100 - ffGreenEstSize)
        GreenDeviations_nm[i+5] = ffDiffGreen * GreenFringeSpacing_nm + RedDeviations_nm[i+5]

        DeviationDiff_nm = RedDeviations_nm[i+5] - GreenDeviations_nm[i+5]
        if (abs(DeviationDiff_nm) < abs(MinDiff)):
            MinDiff = DeviationDiff_nm
            BestSolutionIndex = i+5
        #end %If
    #end %Next i

    return RedDeviations_nm,GreenDeviations_nm,BestSolutionIndex

if __name__ == '__main__':
    RD,GD,BS = CalcGaugeLength(100,20.0,20.0,1000.0,50,0.5,0.0,11.5e-6)
    print (RD)
    print (GD)
    print (RD[BS], GD[BS])

