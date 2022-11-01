import numpy as np

HEADER_DTYPE = np.dtype(
    [
        ("nx", "i4"),  # Number of columns
        ("ny", "i4"),  # Number of rows
        ("nz", "i4"),  # Number of sections
        ("pixel_type", "i4"),  # Mode; indicates type of values stored in data block
        ("nxstart", "i4"),  # Starting point of sub-image
        ("nystart", "i4"),
        ("nzstart", "i4"),
        ("mx", "i4"),  # Grid size in X, Y and Z
        ("my", "i4"),
        ("mz", "i4"),
        ("dx", "f4"),  # voxel size
        ("dy", "f4"),
        ("dz", "f4"),
        (
            "cellb",
            [  # Cell angles in degrees
                ("alpha", "f4"),
                ("beta", "f4"),
                ("gamma", "f4"),
            ],
        ),
        ("mapc", "i4"),  # map column  1=x,2=y,3=z.
        ("mapr", "i4"),  # map row     1=x,2=y,3=z.
        ("maps", "i4"),  # map section 1=x,2=y,3=z.
        ("dmin", "f4"),  # Minimum pixel value
        ("dmax", "f4"),  # Maximum pixel value
        ("dmean", "f4"),  # Mean pixel value
        ("ispg", "i4"),  # space group number
        ("nsymbt", "i4"),  # number of bytes in extended header
        ("extra1", "V8"),  # extra space, usage varies by application
        ("exttyp", "S4"),  # code for the type of extended header
        ("nversion", "i4"),  # version of the MRC format
        ("extra2", "V84"),  # extra space, usage varies by application
        ("origin", [("x", "f4"), ("y", "f4"), ("z", "f4")]),  # Origin of image
        ("map", "S4"),  # Contains 'MAP ' to identify file type
        ("machst", "u1", 4),  # Machine stamp; identifies byte order
        ("rms", "f4"),  # RMS deviation of densities from mean density
        ("nlabl", "i4"),  # Number of labels with useful data
        ("label", "S80", 10),  # 10 labels of 80 characters
    ]
)
