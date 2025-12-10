import numpy as np

# data type for reading in comma delimited files specifying measurement data and file names
DTRG = np.dtype(
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
        ("GreenFileName", (str, 256)),
    ]
)

DTR = np.dtype(
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
)

# numpy type for reading the output-calcs-py.txt file
# here for reference

DTRG_OUTPUT = np.dtype(
    [
        ("NominalSize", float),
        ("SerialNo", (str, 16)),
        ("meandev", float),
        ("diffdev", float),
        ("reddev", float),
        ("greendev", float),
        ("bestindex", int),
        ("RedDateTime", float),
        ("GreenDateTime", float),
        ("SetId", (str, 16)),
        ("PlatenId", int),
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
        ("ffred", float),
        ("ffgreen", float),
        ("redwavelength", float),
        ("greenwavelength", float),
        ("redindex", float),
        ("greenindex", float),
        ("RedFileName", (str, 256)),
        ("GreenFileName", (str, 256)),
    ]
)
