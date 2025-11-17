"""
loads the equipment register stored in
https://github.com/MSLNZ/Length_Stds_Equipment_Register


currently assumes that a local copy has been cloned into the parent folder of this repo
that is folder structure is

ls-fringeapp
├── src
│   └── ls_fringeapp
│       ├── FringeApp03.py
...
Length_Stds_Equipment_Register
├── register.xml
...

"""

from pathlib import Path
from lxml import etree

red_id = "MSLE.L.017"
green_id = "MSLE.L.110"

fn_register = "register.xml"
code_folder = Path(__file__).parent.resolve()  # folder of this file
repo_folder = code_folder.parent.parent
path_register = repo_folder.parent / "Length_Stds_Equipment_Register" / fn_register


def get_laser_wavelengths_from_register(fn):
    tree = etree.parse(fn)
    root = tree.getroot()
    ns_reg = {"eq": "https://measurement.govt.nz/equipment-register"}

    # these look awful but work so use for now
    red_wavelength = root.xpath(
        f'//eq:equipment[eq:id="{red_id}"]/eq:calibrations/eq:measurand/eq:component/eq:report/eq:equation/eq:value/text()',
        namespaces=ns_reg,
    )[0]
    green_wavelength = root.xpath(
        f'//eq:equipment[eq:id="{green_id}"]/eq:calibrations/eq:measurand/eq:component/eq:report/eq:equation/eq:value/text()',
        namespaces=ns_reg,
    )[0]

    # do some sanity checks ...
    # add some try except robustness

    return {"red": float(red_wavelength), "green": float(green_wavelength)}


laser_wavelengths = get_laser_wavelengths_from_register(path_register)
print(f"Equipment Register loaded from {path_register.resolve()}")
print(laser_wavelengths)
