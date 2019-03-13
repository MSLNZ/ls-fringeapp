# ls-fringeapp
for processing gauge block interferograms

This program takes as input a comma separated text file where each 
line represents the data on one gauge wring.

This should have no headers, with  the following columns

If both red and green images have been taken:
        [
        ("NominalSize", float),
        ("SerialNo", (str, 16)),
        ("RedDateTime", float),
        ("GreenDateTime", float),
        ("SetId", (str, 16)),
        ("PlatenId", int),
        ("Observer", (str, 16)),
        ("Side", int),
        ("ExpCoeff", float),
        ("Units", (str, 16)),
        ("TRAir", float),
        ("TGAir", float),
        ("TR", float),
        ("TG", float),
        ("PR", float),
        ("PG", float),
        ("HR", float),
        ("HG", float),
        ("RedFileName", (str, 256)),
        ("GreenFileName", (str, 256)),]

If only red images have been taken
    [
        ("NominalSize", float),
        ("SerialNo", (str, 16)),
        ("RedDateTime", float),
        ("SetId", (str, 16)),
        ("PlatenId", int),
        ("Observer", (str, 16)),
        ("Side", int),
        ("ExpCoeff", float),
        ("Units", (str, 16)),
        ("TRAir", float),
        ("TR", float),
        ("PR", float),
        ("HR", float),
        ("RedFileName", (str, 256)),
    ]
    
 It produces a comma separated text file of gauge block measurements 
 where each row represent one gauge block measurement
 
 For red and green images
    f'{gauge["NominalSize"]:f}',
    f'"{gauge["SerialNo"]:s}"',
    f"{meandev:.1f}",
    f"{diffdev:.1f}",
    f"{rd[idev]:.1f}",
    f"{gd[idev]:.1f}",
    f"{bestindex:d}",
    f'{gauge["RedDateTime"]:f}',
    f'{gauge["GreenDateTime"]:f}',
    f'"{gauge["SetId"]:s}"',
    f'{gauge["PlatenId"]:d}',
    f'{gauge["Side"]:d}',
    f'{gauge["ExpCoeff"]:e}',
    f'"{gauge["Units"]:s}"',
    f'{gauge["TRAir"]:f}',
    f'{gauge["TGAir"]:f}',
    f'{gauge["TR"]:f}',
    f'{gauge["TG"]:f}',
    f'{gauge["PR"]:f}',
    f'{gauge["PG"]:f}',
    f'{gauge["HR"]:f}',
    f'{gauge["HG"]:f}',
    f"{ffred * 100.0:.2f}",
    f"{ffgreen * 100.0:.2f}",
    f"{self.red_wavelength:.7f}",
    f"{self.green_wavelength:.7f}",
    f"{redindex:.8f}"
    f"{greenindex:.8f}"
    f'"{gauge["RedFileName"]:s}"',
    f'"{gauge["GreenFileName"]:s}"',
    
 For red only images
 
    f'{gauge["NominalSize"]:f}',
    f'"{gauge["SerialNo"]:s}"',
    f"{rd:.1f}",
    f'{gauge["RedDateTime"]:f}',
    f'"{gauge["SetId"]:s}"',
    f'{gauge["PlatenId"]:d}',
    f'{gauge["Side"]:d}',
    f'{gauge["ExpCoeff"]:e}',
    f'"{gauge["Units"]:s}"',
    f'{gauge["TRAir"]:f}',
    f'{gauge["TR"]:f}',
    f'{gauge["PR"]:f}',
    f'{gauge["HR"]:f}',
    f"{ffred * 100.0:.2f}",
    f"{self.red_wavelength:.7f}",
    f"{redindex:.8f}",
    f'"{gauge["RedFileName"]:s}"',
    
  The red and green values are red from "I:\MSL\Private\LENGTH\EQUIPREG\cal_data.xml"
    