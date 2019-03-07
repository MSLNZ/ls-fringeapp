"""
reads the cal_data.xml file and returns a red and green wavelength
"""
import xml.etree.ElementTree as et


def read_cal_wavelengths(caldata_fn, red_green=True):
    tree = et.parse(caldata_fn)
    caldata = tree.getroot()
    e = caldata.findall(
        './/*[location="HILGERINTERFEROMETER"][equiptype="LASER_MEASUREMENT_SYSTEM"]'
    )
    if len(e) != 1:
        return None  # would be more pythonic to raise error
    else:
        red = (e[0].find("reportnumber").text, float(e[0].find("vacuum_wavelength").text))
    if not red_green:
        return red
    else:
        e = caldata.findall(
            './/*[location="HILGERINTERFEROMETER"][equiptype="MERCURY_EMISSION_LAMP"]'
        )
        if len(e) != 1:
            return None  # would be more pythonic to raise error
        else:
            green = (
                e[0].find("reportnumber").text,
                float(e[0].find("vacuum_wavelength").text,)
            )
            return red, green
