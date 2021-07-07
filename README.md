# mrc

[![License](https://img.shields.io/pypi/l/mrc.svg?color=green)](https://github.com/tlambert03/mrc/raw/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/mrc.svg?color=green)](https://pypi.org/project/mrc)
[![Python Version](https://img.shields.io/pypi/pyversions/mrc.svg?color=green)](https://python.org)
[![tests](https://github.com/tlambert03/mrc/workflows/tests/badge.svg)](https://github.com/tlambert03/mrc/actions)
[![codecov](https://codecov.io/gh/tlambert03/mrc/branch/master/graph/badge.svg)](https://codecov.io/gh/tlambert03/mrc)

Read and write .mrc and .dv (deltavision) image file format.

Note, this module is designed to read the MRC variant used by deltavision
microscopes (.dv) and the IVE library from UCSF. For the MRC2014 file format
frequently used for structural biology, see
[mrcfile](https://github.com/ccpem/mrcfile)

(though dv and mrc formats are very similar, priism/dv files that evolved from
the IVE library at UCSF have a slightly different header format, preventing
mrcfile from working).

This module was extracted from the
[priithon](https://github.com/sebhaase/priithon) package, written by Sebastian
Haase.

## Install

```sh
pip install mrc
```

## Usage

```python
import mrc
import numpy as np

# Read a dv file
arr = mrc.imread('/path/to/file.dv')
# just a numpy array with the data...
isinstance(arr, np.ndarray)  # True

# additional info in stored in the arr.Mrc object.
# print it
arr.Mrc.info()
# or access particular fields:
print(arr.Mrc.header)
# dv files may have additional info in the extended header:
arr.Mrc.extended_header
# for instsance, timestamps for each channel at each timepoint:
arr.Mrc.extended_header['timeStampSeconds']

# or you can write a numpy array to DV format
arr = np.random.rand(23,3,256,256).astype('single')
mrc.imsave("/path/to/output.dv", arr,
    metadata={
        'dx': 0.08,
        'dy': 0.08,
        'dz': 0.125,
        'wave': [445, 528, 615, 0, 0]
    }
)
```

## Priism (DV) MRC Header Format

*this information is archived from the no-longer-existing page at
http://www.msg.ucsf.edu/IVE/IVE4_HTML/priism_mrc_header.html*

The MRC header is 1024 bytes layed out as described below. Each field
is in one of these formats:

`n` Is a 2-byte signed integer (NPY_INT16)

`i` Is a 4-byte signed integer (NPY_INT32)

`f` Is a 4-byte floating-point value in IEEE format (NPY_FLOAT32)

`cn` Is a string of characters that is n bytes long.

| Byte Numbers | Variable Type | Variable Name | Contents                                                                                                                                  |
| :----------: | :-----------: | :------------ | :---------------------------------------------------------------------------------------------------------------------------------------- |
|    1 - 4     |       i       | NumCol        | number of columns (fastest-varying dimension; normally mapped to x)                                                                       |
|    5 - 8     |       i       | NumRow        | number of rows (second fastest-varying dimension; normally mapped to y)                                                                   |
|    9 - 12    |       i       |               | number of sections (slowest-varying dimension; normally mapped to the remaining dimensions, z, wavelength, and time)                      |
|   13 - 16    |       i       | PixelType     | data type (see Pixel Data Types)                                                                                                          |
|   17 - 20    |       i       | mxst          | index of the first column (normally mapped to x) in the data; zero by default                                                             |
|   21 - 24    |       i       | myst          | index of the first row (normally mapped to y) in the data; zero by default                                                                |
|   25 - 28    |       i       | mzst          | index of the first section (normally treated as the first z) in the data; zero by default                                                 |
|   29 - 32    |       i       | mx            | number of intervals in the fastest-varying direction (normally x)                                                                         |
|   33 - 36    |       i       | my            | number of intervals in the second fastest-varying direction (normally y)                                                                  |
|   37 - 40    |       i       | mz            | number of intervals in the slowest varying direction (normally treated as z)                                                              |
|   41 - 44    |       f       | dx            | pixel spacing times sampling interval for fastest-varying direction (first cell dimension in Angstroms for crystallographic data)         |
|   45 - 48    |       f       | dy            | pixel spacing times sampling interval for second fastest-varying direction (second cell dimension in Angstroms for crystallographic data) |
|   49 - 52    |       f       | dz            | pixel spacing times sampling interval slowest-varying direction (third cell dimension in Angstroms for crystallographic data)             |
|   53 - 56    |       f       | alpha         | cell angle (alpha) in degrees; defaults to 90                                                                                             |
|   57 - 60    |       f       | beta          | cell angle (beta) in degrees; defaults to 90                                                                                              |
|   61 - 64    |       f       | gamma         | cell angle (gamma) in degrees; defaults to 90                                                                                             |
|   65 - 68    |       i       |               | column axis (1 = x, 2 = y, 3 = z; defaults to 1)                                                                                          |
|   69 - 72    |       i       |               | row axis (1 = x, 2 = y, 3 = z; defaults to 2)                                                                                             |
|   73 - 76    |       i       |               | section axis (1 = x, 2 = y, 3 = z; defaults to 3)                                                                                         |
|   77 - 80    |       f       | min           | minimum intensity of the 1st wavelength image                                                                                             |
|   81 - 84    |       f       | max           | maximum intensity of the 1st wavelength image                                                                                             |
|   85 - 88    |       f       | mean          | mean intensity of the first wavelength image                                                                                              |
|   89 - 92    |       i       | nspg          | space group number (for crystallography)                                                                                                  |
|   93 - 96    |       i       | next          | extended header size in bytes.                                                                                                            |
|   97 - 98    |       n       | dvid          | ID value (-16224)                                                                                                                         |
|   99 - 100   |       n       | nblank        | unused                                                                                                                                    |
|  101 - 104   |       i       | ntst          | starting time index                                                                                                                       |
|  105 - 128   |      c24      | blank         | 24 bytes long blank section                                                                                                               |
|  129 - 130   |       n       | NumIntegers   | number of 4 byte integers stored in the extended header per section.                                                                      |
|  131 - 132   |       n       | NumFloats     | number of 4 byte floating-point numbers stored in the extended header per section.                                                        |
|  133 - 134   |       n       | sub           | number of sub-resolution data sets stored within the image typically 1)                                                                   |
|  135 - 136   |       n       | zfac          | reduction quotient for the z axis of the sub-resolution images                                                                            |
|  137 - 140   |       f       | min2          | minimum intensity of the 2nd wavelength image                                                                                             |
|  141 - 144   |       f       | max2          | maximum intensity of the 2nd wavelength image                                                                                             |
|  145 - 148   |       f       | min3          | minimum intensity of the 3rd wavelength image                                                                                             |
|  149 - 152   |       f       | max3          | maximum intensity of the 3rd wavelength image                                                                                             |
|  153 - 156   |       f       | min4          | minimum intensity of the 4th wavelength image                                                                                             |
|  157 - 160   |       f       | max4          | maximum intensity of the 4th wavelength image                                                                                             |
|  161 - 162   |       n       | image type    | see Image Types                                                                                                                           |
|  163 - 164   |       n       | LensNum       | lens identification number                                                                                                                |
|  165 - 166   |       n       | n1            | depends on the image type                                                                                                                 |
|  167 - 168   |       n       | n2            | depends on the image type                                                                                                                 |
|  169 - 170   |       n       | v1            | depends on the image type                                                                                                                 |
|  171 - 172   |       n       | v2            | depends on the image type                                                                                                                 |
|  173 - 176   |       f       | min5          | minimum intensity of the 5th wavelength image                                                                                             |
|  177 - 180   |       f       | max5          | maximum intensity of the 5th wavelength image                                                                                             |
|  181 - 182   |       n       | NumTimes      | number of time points                                                                                                                     |
|  183 - 184   |       n       | ImgSequence   | image sequence (0 = ZTW, 1 = WZT, 2 = ZWT)                                                                                                |
|  185 - 188   |       f       |               | x axis tilt angle (degrees)                                                                                                               |
|  189 - 192   |       f       |               | y axis tilt angle (degrees)                                                                                                               |
|  193 - 196   |       f       |               | z axis tilt angle (degrees)                                                                                                               |
|  197 - 198   |       n       | NumWaves      | number of wavelengths                                                                                                                     |
|  199 - 200   |       n       | wave1         | wavelength 1 in nm                                                                                                                        |
|  201 - 202   |       n       | wave2         | wavelength 2 in nm                                                                                                                        |
|  203 - 204   |       n       | wave3         | wavelength 3 in nm                                                                                                                        |
|  205 - 206   |       n       | wave4         | wavelength 4 in nm                                                                                                                        |
|  207 - 208   |       n       | wave5         | wavelength 5 in nm                                                                                                                        |
|  209 - 212   |       f       | z0            | z origin (um for optical, Angstroms for EM)                                                                                               |
|  213 - 216   |       f       | x0            | x origin (um for optical, Angstroms for EM)                                                                                               |
|  217 - 220   |       f       | y0            | y origin (um for optical, Angstroms for EM)                                                                                               |
|  221 - 224   |       i       | NumTitles     | number of titles (valid numbers are between 0 and 10)                                                                                     |
|  225 - 304   |      c80      |               | title 1                                                                                                                                   |
|  305 - 384   |      c80      |               | title 2                                                                                                                                   |
|  385 - 464   |      c80      |               | title 3                                                                                                                                   |
|  465 - 544   |      c80      |               | title 4                                                                                                                                   |
|  545 - 624   |      c80      |               | title 5                                                                                                                                   |
|  625 - 704   |      c80      |               | title 6                                                                                                                                   |
|  705 - 784   |      c80      |               | title 7                                                                                                                                   |
|  785 - 864   |      c80      |               | title 8                                                                                                                                   |
|  865 - 944   |      c80      |               | title 9                                                                                                                                   |
|  945 - 1024  |      c80      |               | title 10                                                                                                                                  |

### Pixel Data Types

The data type used for image pixel values, stored as a signed 32-bit integer
in bytes 13 through 16, is designated by one of the code numbers in the
following table.

| Data Type |  Numpy Type   | Description                                                   |
| :-------: | :-----------: | :------------------------------------------------------------ |
|     0     |   NPY_UINT8   | 1-byte unsigned integer                                       |
|     1     |   NPY_INT16   | 2-byte signed integer                                         |
|     2     |  NPY_FLOAT32  | 4-byte floating-point (IEEE)                                  |
|     3     |               | 4-byte complex value as 2 2-byte signed integers              |
|     4     | NPY_COMPLEX64 | 8-byte complex value as 2 4-byte floating-point (IEEE) values |
|     5     |               | 2-byte signed integer (unclear)                               |
|     6     |  NPY_UINT16   | 2-byte unsigned integer                                       |
|     7     |   NPY_INT32   | 4-byte signed integer                                         |

*Type codes 5, 6, and 7 are not standard MRC types and are not likely to
be correctly interpreted by other software that uses MRC files.*

### Image Types

The type of a Priism image is given by the signed 16-bit integer in header
bytes 161 and 162. The meaning of these types is given in the table below.
The floating-point attributes, v1 and v2, used by some image types are stored
as 16-bit signed integers in the header; to do so the values are multiplied
by 100 and rounded to the nearest integer when stored and are divided by 100
when retrieved.

##### 0 (IM_NORMAL_IMAGES)

Used for normal image data.

##### 1 (IM_TILT_SERIES)

Used for single axis tilt series with a uniform angle increment. n1 specifies
the tilt axis (1 for x, 2 for y, 3 for z) and v1 the angle increment in degrees.
n2 relates the coordinates in the tilt series to coordinates in a 3D volume: the
assumed center of rotation is the z origin from the header plus n2 times one
half of the z pixel spacing from the header. v2 is always zero.

##### 2 (IM_STEREO_TILT_SERIES)

Used for stereo tilt series. n1 specifies the tilt axis (1 for x, 2 for y, 3 for
z), v1 the angle increment in degrees, and v2 is the angular separation in
degrees for the stereo pairs. n2 is always zero.

##### 3 (IM_AVERAGED_IMAGES)

Used for averaged images. n1 is the number of averaged sections and
n2 is the number of sections between averaged sections. v1 and v2
are always zero.

##### 4 (IM_AVERAGED_STEREO_PAIRS)

Used for averaged stereo pairs. n1 is the number of averaged sections, n2 is the
number of sections between averaged sections, and v2 is the angular separation
in degrees for the stereo pairs. v2 is always zero.

##### 5 (IM_EM_TILT_SERIES)

Used for EM tomography data. The tilt angles are stored in the extended header.

##### 20 (IM_MULTIPOSITION)

Used for images of well plates. The following quantities are bit-encoded in n1
(valid range for each is show in parentheses): iwell (0-3), ishape (0-1), ibin
(0-15), ispeed (0-2), igain (0-3), and mag (0-1). n2 is the number of fields per
well. v1 is the fill factor (.01 to 1.5 in .01 steps). v2 is not used.

##### 8000 (IM_PUPIL_FUNCTION)

Used for images of pupil functions. n1 and n2 are not used. v1 is the numerical
aperture times ten. v2 is the immersion media refractive index times one
hundred. The pixel spacings and origin have units of cycles per micron rather
than microns.

## Credits

This package was created by Sebastian Haase as a part of the
[priithon](https://github.com/sebhaase/priithon) package.
It is updated and maintained by Talley Lambert.
