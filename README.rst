MRC
===

.. image:: https://img.shields.io/pypi/v/mrc.svg
        :target: https://pypi.python.org/pypi/mrc

.. image:: https://travis-ci.com/tlambert03/mrc.svg?branch=master
        :target: https://travis-ci.com/tlambert03/mrc


Read and write .mrc and .dv (deltavision) image file format

Note, this module is designed to read the MRC variant used by
deltavision microscopes (.dv). For the MRC file format frequently
used for structural biology, see https://github.com/ccpem/mrcfile

(thought dv and mrc formats are very similar, dv files have a slightly
different header, and lack the character string "MAP" in bytes 209-212
in the `header <http://www.ccpem.ac.uk/mrc_format/mrc2014.php>`_, preventing mrcfile from working).


MRC Header Format
~~~~~~~~~~~~~~~~~

*this information is archived from the no-longer-existing page at http://www.msg.ucsf.edu/IVE/IVE4_HTML/priism_mrc_header.html*

The MRC header is 1024 bytes layed out as described below. Each field is in one of these formats:

n Is a 2-byte signed integer (NPY_INT16)

i Is a 4-byte signed integer (NPY_INT32)

f Is a 4-byte floating-point value in IEEE format (NPY_FLOAT32)

cn Is a string of characters that is n bytes long.

.. csv-table::
   :header: Byte Numbers,Variable Type,Variable Name,Contents
   :widths: 15, 10, 30, 30

    1 - 4,i,NumCol,number of columns (fastest-varying dimension; normally mapped to x)
    5 - 8,i,NumRow,number of rows (second fastest-varying dimension; normally mapped to y)
    9 - 12,i,NumSections,"number of sections (slowest-varying dimension; normally mapped to the remaining dimensions, z, wavelength, and time)"
    13 - 16,i,PixelType,format of each pixel value (the Pixel Data Types section of the Imsubs reference manual lists the defined options)
    17 - 20,i,mxst,index of the first column (normally mapped to x) in the data; zero by default
    21 - 24,i,myst,index of the first row (normally mapped to y) in the data; zero by default
    25 - 28,i,mzst,index of the first section (normally treated as the first z) in the data; zero by default
    29 - 32,i,mx,number of intervals in the fastest-varying direction (normally x)
    33 - 36,i,my,number of intervals in the second fastest-varying direction (normally y)
    37 - 40,i,mz,number of intervals in the slowest varying direction (normally treated as z)
    41 - 44,f,dx,pixel spacing times sampling interval for fastest-varying direction (first cell dimension in Angstroms for crystallographic data)
    45 - 48,f,dy,pixel spacing times sampling interval for second fastest-varying direction (second cell dimension in Angstroms for crystallographic data)
    49 - 52,f,dz,pixel spacing times sampling interval slowest-varying direction (third cell dimension in Angstroms for crystallographic data)
    53 - 56,f,alpha,cell angle (alpha) in degrees; defaults to 90
    57 - 60,f,beta,cell angle (beta) in degrees; defaults to 90
    61 - 64,f,gamma,cell angle (gamma) in degrees; defaults to 90
    65 - 68,i,,"column axis (1 = x, 2 = y, 3 = z; defaults to 1)"
    69 - 72,i,,"row axis (1 = x, 2 = y, 3 = z; defaults to 2)"
    73 - 76,i,,"section axis (1 = x, 2 = y, 3 = z; defaults to 3)"
    77 - 80,f,min,minimum intensity of the 1st wavelength image
    81 - 84,f,max,maximum intensity of the 1st wavelength image
    85 - 88,f,mean,mean intensity of the first wavelength image
    89 - 92,i,nspg,space group number (for crystallography)
    93 - 96,i,next,extended header size in bytes.
    97 - 98,n,dvid,ID value (-16224)
    99 - 100,n,nblank,unused
    101 - 104,i,ntst,starting time index
    105 - 128,c24,blank,24 bytes long blank section
    129 - 130,n,NumIntegers,number of 4 byte integers stored in the extended header per section.
    131 - 132,n,NumFloats,number of 4 byte floating-point numbers stored in the extended header per section.
    133 - 134,n,sub,number of sub-resolution data sets stored within the image typically 1)
    135 - 136,n,zfac,reduction quotient for the z axis of the sub-resolution images
    137 - 140,f,min2,minimum intensity of the 2nd wavelength image
    141 - 144,f,max2,maximum intensity of the 2nd wavelength image
    145 - 148,f,min3,minimum intensity of the 3rd wavelength image
    149 - 152,f,max3,maximum intensity of the 3rd wavelength image
    153 - 156,f,min4,minimum intensity of the 4th wavelength image
    157 - 160,f,max4,maximum intensity of the 4th wavelength image
    161 - 162,n,type,image type (the Image Types section of the Imsubs reference manual lists types that have been defined)
    163 - 164,n,LensNum,lens identification number
    165 - 166,n,n1,depends on the image type
    167 - 168,n,n2,depends on the image type
    169 - 170,n,v1,depends on the image type
    171 - 172,n,v2,depends on the image type
    173 - 176,f,min5,minimum intensity of the 5th wavelength image
    177 - 180,f,max5,maximum intensity of the 5th wavelength image
    181 - 182,n,NumTimes,number of time points
    183 - 184,n,ImgSequence,"image sequence (0 = ZTW, 1 = WZT, 2 = ZWT)"
    185 - 188,f,,x axis tilt angle (degrees)
    189 - 192,f,,y axis tilt angle (degrees)
    193 - 196,f,,z axis tilt angle (degrees)
    197 - 198,n,NumWaves,number of wavelengths
    199 - 200,n,wave1,wavelength 1 in nm
    201 - 202,n,wave2,wavelength 2 in nm
    203 - 204,n,wave3,wavelength 3 in nm
    205 - 206,n,wave4,wavelength 4 in nm
    207 - 208,n,wave5,wavelength 5 in nm
    209 - 212,f,z0,"z origin (um for optical, Angstroms for EM)"
    213 - 216,f,x0,"x origin (um for optical, Angstroms for EM)"
    217 - 220,f,y0,"y origin (um for optical, Angstroms for EM)"
    221 - 224,i,NumTitles,number of titles (valid numbers are between 0 and 10)
    225 - 304,c80,,title 1
    305 - 384,c80,,title 2
    385 - 464,c80,,title 3
    465 - 544,c80,,title 4
    545 - 624,c80,,title 5
    625 - 704,c80,,title 6
    705 - 784,c80,,title 7
    785 - 864,c80,,title 8
    865 - 944,c80,,title 9
    945 - 1024,c80,,title 10


Credits
-------

This package was created by Sebastian Haase as a part of the
`priithon <https://github.com/sebhaase/priithon/blob/master/Priithon/Mrc.py>`_ package.  It is mostly just repackaged here and updated
for python 3.
