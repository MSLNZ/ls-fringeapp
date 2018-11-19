"""
Translation of Excel VBA module modRefractiveIndex stored in RefractiveIndex10a.xls
'Implements various formula for the refractive index of  air
'File: RefractiveIndex10a.xls!modRefractiveIndex
'Version: 1.0 a
'Author: EFH and LCF
'Date: 26/4/2007

this file
File: refractiveindex.py
Version: 1.0 a
Author: EFH
Date: 16/12/2009

"""
from numpy import exp, sqrt, log


def RefractiveIndex(Temperature,
                    Pressure,
                    Humidity,
                    Lambda=632.991,
                    Formula=0):
    """
    'Calculates refractive index of air
    'defaults to Ciddor Formula as given on NIST site
    'and wavelength of 632.991 nm
    'see http://emtoolbox.nist.gov/Wavelength/Documentation.asp

    'Temperature is in degree Celsius
    'Pressure is in millibar
    'Humidity is in % RH ie from 0 to 100
    'Lambda is in nanometres

    'in order of accuracy
    """

    if Formula == 0:
       RefractiveIndex = RefractiveIndexNIST_Ciddor(Temperature, Pressure, Humidity, Lambda)
    if Formula == 1:
       RefractiveIndex = RefractiveIndexNIST_Edlen(Temperature, Pressure, Humidity, Lambda)
    if Formula == 2:
       RefractiveIndex = RefractiveIndexBD94(Temperature, Pressure, Humidity, Lambda)
    if Formula == 3:
       RefractiveIndex = RefractiveIndexM88(Temperature, Pressure, Humidity, Lambda)
    if Formula == 4:
       RefractiveIndex = RefractiveIndexNIST_ShopFloor(Temperature, Pressure, Humidity)
    return RefractiveIndex


def RefractiveIndexM88(Temperature,
                       Pressure,
                       Humidity,
                       Lambda):
    """
    'Refractive Index of Air
    'Temperature is in degree Celsius
    'Pressure is in millibar
    'Humidity is in % RH ie from 0 to 100
    'Lambda is in nanometres

    ' {Calculated from formulas given in: R.Muijlwijk, "Update of the Edlen
    '  Formulae for the refractive index of Air", Metrologia 25, 189 (1988)}

             Dim P_kPa As Double   '{pressure in kPa }
             Dim Sigma  As Double    '{wavenumber in [1/micrometers] }
             Dim S2 As Double        '{Sigma squared}
             Dim Ns As Double       '{(n-1) at standard conditions 20 C, 100 kPa, 0% humidity}
             Dim ntp   As Double      '{(n-1) at given Temperature and Pressure, 0% humidity}
             Dim Ch As Double       '{humidity correction to be added to Ntp}
    """

    Sigma = 1000 / Lambda
    S2 = Sigma * Sigma
    P_kPa = 100 * Pressure
    Ns = (26445.9 + 148.7 * S2 + 1.205 * S2 * S2 + 0.02712 * S2 * S2 * S2) * 1e-8
    ntp = (Ns * P_kPa * 1e-5) / (1 + 0.0034198 * (Temperature - 20))
    Ch = -Humidity * (1 + 0.06 * (Temperature - 20)) * (1 - 0.008 * S2) * 1e-8
    rindex = ntp + Ch + 1
    return rindex

def RefractiveIndexBD94(Temperature,
                        Pressure,
                        Humidity,
                        Lambda):
    """
    ' K.P. Birch and M.J. Downs,
    ' "Correction to the updated Edl?n equation for the refractive index of air,"
    ' Metrologia 31, 315-316 (1994).

    'vapour pressure calculation from
    '"A Guide to the Measurement of Humidity"
    ' NPL 1996
    ' published by The Institute of Measurement and Control
    ' ISBN 0-904457-24-9

    ' see also http://emtoolbox.nist.gov/Wavelength/Documentation.asp

    'Temperature is in degree Celsius
    'Pressure is in millibar
    'Humidity is in % RH ie from 0 to 100
    'Lambda is in nanometres

    '  Wavelength in Air = Wavelength in Vacumn / RefractiveIndexBD94(20.0,1010.2,50, 632.9)

             Dim P_Pa As Double     '{pressure in Pa }
             Dim Sigma As Double    '{wavenumber in [1/micrometers] }
             Dim S2 As Double       '{Sigma squared}
             Dim Ns As Double       '{(n-1) at standard conditions 20 C, 100 kPa, 0% humidity}
             Dim ntp As Double      '{(n-1) at given Temperature and Pressure, 0% humidity}
             Dim Ch As Double       '{humidity correction to be added to Ntp}
             Dim f As Double        '{partial vapour pressure of water in Pa}
             Dim e0 As Double       '{type of water vapour pressure in Pa}
             Dim f0 As Double       '{enhancement factor for water vapour pressure}
    """
    ea0 = -6096.9385
    ea1 = 21.2409642
    ea2 = -0.02711193
    ea3 = 1.67395e-005
    ea4 = 2.433502
    a1 = 3.62183e-4
    a2 = 2.60553e-5
    A3 = 3.86501e-7
    A4 = 3.82449e-009
    b1 = -10.7604
    B2 = 0.0639725
    B3 = -2.63416e-4
    B4 = 1.67254e-6

    Sigma = 1000 / Lambda
    S2 = Sigma * Sigma
    P_Pa = 100 * Pressure
    Ns = (8342.54 + (2406147.0 / (130.0 - S2)) + (15998.0 / (38.9 - S2))) * 1e-8
    c1 = (P_Pa * 1e-8 * (0.601 - 0.00972 * Temperature))
    ntp = (Ns * P_Pa / 96095.43) * ((1 + c1) / (1.0 + 0.003661 * Temperature))
    t0 = Temperature + 273.15
    e0 = exp((ea0 / t0) + ea1 + (ea2 * t0) + ea3 * (t0 ** 2) + ea4 * log(t0))
    c2 = a1 + a2 * Temperature + A3 * Temperature ** 2 + A4 * Temperature ** 3
    c3 = b1 + B2 * Temperature + B3 * Temperature ** 2 + B4 * Temperature ** 3
    f0 = exp(c2 * (1 - e0 / P_Pa) + (exp(c3)) * (P_Pa / e0 - 1))
    f = (Humidity / 100.0) * e0 * f0
    Ch = -(292.75 / (Temperature + 273.15)) * f * (3.7345 - 0.0401 * S2) * 1e-10
    rindex = ntp + Ch + 1.0

    return rindex



def EDMRefIndexCorr(Temperature,
                    Pressure,
                    Humidity):

    """
    '  Calculate the refractive index correction factor for our Distomat
    '  DI2002 EDM at Temperature (degree C), Pressure (barometric - mb)
    '  and Humidity (relative - percent).
    '  Calculated from formulas given in the Leica/Wild DI2002 user
    '  manual, Section 9.1, p 28.
    '  Distances should be multiplied by this factor.

             Dim Ctp As Double    '{temperature and pressure part of
                                  ' correction, at 0% humidity}
             Dim Ch As Double     '{humidity part of correction}
             Dim Exp As Double    '{exponential term for humidity}
             Dim Ppm As Double    '{atmospheric correction in ppm}
    """

    Ctp = 0.29065 * Pressure
    Exp = ((7.5 * Temperature) / (237.3 + Temperature)) + 0.7857
    Ch = (4.126 * 0.0001 * Humidity) * (10.0 ** Exp)
    Ppm = 281.772087 - ((Ctp - Ch) / ((Temperature / 273.16) + 1.0))
    EDMCorr = (Ppm / 1e6) + 1.0
    return EDMCorr


def RefractiveIndexNIST_ShopFloor(Temperature,
                                  Pressure,
                                  Humidity):
    """
    'This is included as a quick check on other implementations
    'This formula is only valid for the standard, red He-Ne laser wavelength of approximately 633 nm,
    ' Over a limited range of conditions characteristic of metrology laboratories near sea level
    ' - temperature between 19.5 ?C and 20.5 ?C,
    ' - pressure from 90 kPa to 110 kPa,
    ' - 0 % to 70 % humidity,
    ' - CO2 concentration between 350 ?mol/mol and 550 ?mol/mol
    ' this equation agrees with the Ciddor equation and with the NIST version of the Edl?n equation
    ' within 5?10-8 (0.05 parts per million).

    'see http://emtoolbox.nist.gov/Wavelength/Documentation.asp

    'Temperature is in degree Celsius
    'Pressure is in millibar
    'Humidity is in % RH ie from 0 to 100

    """
    T_degC = Temperature
    P_kPa = Pressure * 0.1
    H_RH = Humidity

    n = 1 + 7.86*10**(-4) *P_kPa / (273.0 + T_degC) - 1.5*10**(-11) *H_RH* (T_degC**2 + 160.0)
    return n



def SVP(Temperature):
    """
    'calculates saturation vapour pressure of water for Temperature/degC
    'see http://emtoolbox.nist.gov/Wavelength/Documentation.asp

    'psv = SVP(20.0)
    """
    k1 = 1167.05214528
    k2 = -724213.167032
    k3 = -17.0738469401
    K4 = 12020.8247025
    K5 = -3232555.03223
    K6 = 14.9151086135
    K7 = -4823.26573616
    K8 = 405113.405421
    K9 = -0.238555575678
    K10 = 650.175348448



    #assumes T > 0
    T_degC = Temperature

    T_K = T_degC + 273.15
    Omega = T_K + K9 / (T_K - K10)
    A = Omega ** 2 + k1 * Omega + k2
    B = k3 * Omega ** 2 + K4 * Omega + K5
    C = K6 * Omega ** 2 + K7 * Omega + K8
    X = -B + sqrt(B ** 2 - 4 * A * C)
    svp = 1000000.0 * ((2 * C) / X) ** 4
    return svp


def RefractiveIndexNIST_Ciddor(Temperature,
                               Pressure,
                               Humidity,
                               Lambda):
    """
    'Refractive Index of Air
    'Temperature is in degree Celsius
    'Pressure is in millibar
    'Humidity is in % RH ie from 0 to 100
    'Lambda is in nanometres

    'see http://emtoolbox.nist.gov/Wavelength/Documentation.asp
    'Ciddor version

    'from
    'Phillip E. Ciddor,
    '"Refractive index of air: new equations for the visible and near infrared,"
    'Appl. Optics 35, 1566-1573 (1996).


    '  Wavelength in Air = Wavelength in Vacumn / RefractiveIndexNIST_Ciddor(20.0, 1010.2, 50, 632.9)
    """

    xCO2 = 450  #' CO2 concentration in ?mol/mol (could make this an optional parameter)

    alpha = 1.00062
    beta = 3.14 * 10 ** (-8)
    gamma = 5.6 * 10 ** (-7)

    w0 = 295.235
    w1 = 2.6422
    w2 = -0.03238
    w3 = 0.004028

    k0 = 238.0185
    k1 = 5792105
    k2 = 57.362
    k3 = 167917

    a0 = 1.58123 * 10 ** (-6)
    a1 = -2.9331 * 10 ** (-8)
    a2 = 1.1043 * 10 ** (-10)

    b0 = 5.707 * 10 ** (-6)
    b1 = -2.051 * 10 ** (-8)

    c0 = 1.9898 * 10 ** (-4)
    c1 = -2.376 * 10 ** (-6)

    d = 1.83 * 10 ** (-11)
    e = -0.765 * 10 ** (-8)
    p_R1 = 101325
    T_R1 = 288.15

    Z_a = 0.9995922115
    Rho_vs = 0.00985938
    R = 8.314472
    M_v = 0.018015


    T_degC = Temperature
    T_K = T_degC + 273.15
    P_Pa = Pressure * 100.0
    H_RH = Humidity
    lambda_um = Lambda / 1000.0

    f = alpha + beta * P_Pa + gamma * T_degC
    psv = SVP(T_degC)
    xv = (H_RH / 100.0) * f * psv / P_Pa

    S = 1.0 / (lambda_um) ** 2
    r_as = 10 ** (-8) * ((k1 / (k0 - S)) + (k3 / (k2 - S)))
    r_vs = 1.022 * 10 ** (-8) * (w0 + w1 * S + w2 * S ** 2 + w3 * S ** 3)
    M_a = 0.0289635 + 1.2011 * 10 ** (-8) * (xCO2 - 400)
    r_axs = r_as * (1.0 + 5.34 * 10 ** (-7) * (xCO2 - 450))
    terma = a0 + a1 * T_degC + a2 * T_degC**2
    termb = (b0 + b1 * T_degC) * xv
    termc = (c0 + c1 * T_degC) * xv**2
    Z_m = 1.0 - (P_Pa / T_K) * (terma + termb + termc) + (P_Pa / T_K)**2 * (d + e * xv**2)
    rho_axs = p_R1 * M_a / (Z_a * R * T_R1)
    rho_v = xv * P_Pa * M_v / (Z_m * R * T_K)
    rho_a = (1.0 - xv) * P_Pa * M_a / (Z_m * R * T_K)
    n = 1.0 + (rho_a / rho_axs) * r_axs + (rho_v / Rho_vs) * r_vs

    return n



def RefractiveIndexNIST_Edlen(Temperature,
                              Pressure,
                              Humidity,
                              Lambda):
    """
    'Refractive Index of Air
    'Temperature is in degree Celsius
    'Pressure is in millibar
    'Humidity is in % RH ie from 0 to 100
    'Lambda is in nanometres

    'see http://emtoolbox.nist.gov/Wavelength/Documentation.asp
    'modified Edlen version

    'B. Edl?n, "The refractive index of air," Metrologia 2, 71-80 (1966).

    'K.P. Birch and M.J. Downs, "An updated Edl?n equation for the refractive index of air," Metrologia 30, 155-162 (1993).

    'K.P. Birch and M.J. Downs, "Correction to the updated Edl?n equation for the refractive index of air," Metrologia 31, 315-316 (1994).

    'Wavelength in Air = Wavelength in Vacumn / RefractiveIndexNIST_Edlen(20.0, 1010.2, 50, 632.9)

    """
    A = 8342.54
    B = 2406147
    C = 15998
    d = 96095.43
    e = 0.601
    f = 0.00972
    G = 0.003661



    T_degC = Temperature
    P_Pa = Pressure * 100.0
    H_RH = Humidity
    lambda_um = Lambda / 1000.0

    psv = SVP(T_degC)
    #'vapour pressure
    pv = (H_RH / 100) * psv

    S = 1.0 / (lambda_um) ** 2
    n5 = 1.0 + (10 ** -8) * (A + B / (130 - S) + C / (38.9 - S))
    X = (1.0 + (10 ** -8) * (e - f * T_degC) * P_Pa) / (1.0 + G * T_degC)
    ntp = 1.0 + P_Pa * (n5 - 1) * X / d
    n = ntp - (10 ** -10) * ((292.75) / (T_degC + 273.15)) * (3.7345 - 0.0401 * S) * pv

    return n

def Ciddor_U95(Temperature,
               Pressure,
               Humidity,
               Lambda):
    """
    'calculates (empirical estimate) the expanded (k=2)uncertainty estimates for the Ciddor equation
    'see http://emtoolbox.nist.gov/Wavelength/Documentation.asp
    'does NOT include uncertainties in measurement of T,P,H
    """



    T_degC = Temperature
    P_Pa = Pressure * 100.0
    H_RH = Humidity
    lambda_um = Lambda / 1000.0

    psv = SVP(T_degC)
    #'vapour pressure
    pv = (H_RH / 100) * psv
    c1 = 0.003 * P_Pa / (T_degC + 273)
    c2 = 4.0 + 6.0 * 10 ** (-8) * (P_Pa - 10 ** 5) ** 2 + 0.06 * (T_degC - 20) ** 2
    c3 = ((8.0 * 10 ** (-4)) ** 2 + (6.0 * 10 ** (-6) / lambda_um ** 4) ** 2)
    Ciddor_U95 = 10 ** (-8) * (c1 ** 2 * c2 + pv ** 2 * c3) ** (1 / 2)

    return Ciddor_U95

def Edlen_U95(Temperature,
              Pressure,
              Humidity,
              Lambda):
    """

    'calculates (empirical estimate) the expanded (k=2)uncertainty estimates for the Edlen equation
    'see http://emtoolbox.nist.gov/Wavelength/Documentation.asp
    'does NOT include uncertainties in measurement of T,P,H
    """

    T_degC = Temperature
    P_Pa = Pressure * 100.0

    U95Ciddor = Ciddor_U95(Temperature, Pressure, Humidity, Lambda)
    A = U95Ciddor
    B = 2 * 10** (-8)
    C = (T_degC - 20.0) * P_Pa / (T_degC + 273.0)

    Edlen_U95 = sqrt(A ** 2 + B ** 2 + (1.6 * 10 ** (-16)) * C ** 2)

    return Edlen_U95

if __name__ == '__main__':
    import numpy
    #values calculated on NIST website

    data =   numpy.array([[20,0,101.325,633,1.000271800,1.000271799],
                          [20,0,60,633,1.000160924,1.000160920],
                          [20,0,120,633,1.000321916,1.000321918],
                          [50,0,100,633,1.000243285,1.000243270],
                          [5,0,100,633,1.000282756,1.000282750],
                          [-40,0,100,633,1.000337580,1.000337471],
                          [50,100,120,633,1.000287924,1.000287864],
                          [40,75,120,633,1.000299418,1.000299406],
                          [20,100,100,633,1.000267394,1.000267394],
                          [40,100,110,1700,1.000270247,1.000270237],
                          [20,0,101.325,1700,1.000268479,1.000268483],
                          [40,100,110,300,1.000289000,1.000288922],
                          [20,0,101.325,300,1.000286581,1.000286579],
                          [-40,0,120,300,1.000427233,1.000427072]])
    nindex = numpy.empty((data.shape[0],5))
    for ri, row in enumerate(data):
        for formula in range(0,5):
            nindex[ri,formula] = RefractiveIndex(row[0],10*row[2],row[1],row[3],formula)

    delta_ciddor = nindex - data[:,4:5]
    delta_edlen = nindex - data[:,5:]
    print ('max , min delta ciddor', numpy.max(delta_ciddor), numpy.min(delta_ciddor))
    print ('max , min delta edlen', numpy.max(delta_edlen), numpy.min(delta_edlen))
    print ('max , min ciddor ciddor', numpy.max(delta_ciddor[:,0]), numpy.min(delta_ciddor[:,0]))
    print ('max , min edlen edlen', numpy.max(delta_edlen[:,1]), numpy.min(delta_edlen[:,1]))
