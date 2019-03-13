"""
quick tests to develop code to read caldata.xml and find
RedWavelength and GreenWavelength
"""

import xml.etree.ElementTree as et

caldata_fn = r'I:\MSL\Private\LENGTH\EQUIPREG\cal_data.xml'
tree = et.parse(caldata_fn)
caldata = tree.getroot()

# print all locations
e = caldata.findall(".//location")
for i in e: print(i.text)
# HILGERLAB
# HILGERLAB
# TUNNEL
# Ground_floor_at_1m_height
# TUNNEL
# TUNNEL
# LASERLAB
# LONGROOM
# HILGERLAB

print()
# print the location of a specific item
i  = caldata.find("./LASERMEASUREMENTSYSTEM/laserHP5519a_US45220479/location")
print(i.text)
# HILGERLAB

print()
# print all laser measurement systems
e = caldata.findall("./LASERMEASUREMENTSYSTEM/")
for i in e: print(i.tag)
# laserHP5519a_3216A00160
# laserHP5501A_2208A02485
# laserHP5519a_US45220374
# laserHP5519a_US45220279
# laserHP5519a_US45220479
# laserHP5519a_3216A00170
# laserHP5519a_US52140451
# laserHP5519a_US40091129
# lampMERCURY

print()
# print all laser measurement systems with a location
e = caldata.findall("./LASERMEASUREMENTSYSTEM//location/..")
for i in e: print(i.tag)
# laserHP5519a_US45220479
# lampMERCURY

# print all instruments with location = HILGERLAB
e = caldata.findall('.//*[location="HILGERLAB"]')
for i in e: print(i.tag)
# laserHP5519a_US45220479
# lampMERCURY
# # humidityPTU300

# print all laser measurement systems with location = HILGERLAB
e = caldata.findall('./LASERMEASUREMENTSYSTEM/*[location="HILGERLAB"]')
for i in e: print(i.tag)
# laserHP5519a_US45220479
# lampMERCURY

# report number of laser measurement system with location = HILGERLAB and equiptype = LASER_MEASUREMENT_SYSTEM
e = caldata.findall('.//*[location="HILGERLAB"][equiptype="LASER_MEASUREMENT_SYSTEM"]')
for i in e: print(i.find('reportnumber').text)
# LENGTH/2018/1111