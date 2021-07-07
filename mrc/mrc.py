# -*- coding: utf-8 -*-
"""
This file was extracted from the priithon library by Sebastian Haase
https://github.com/sebhaase/priithon

another MRC file reader:
https://github.com/ccpem/mrcfile

MRC file format: refer to
http://www.ccpem.ac.uk/mrc_format/mrc2014.php
but note that the Deltavision format is slightly different.

Mrc class uses memory mapping (file size limit about 1GB (more or less)
Mrc2 class section wise file/array I/O
"""

import os
import weakref

import numpy as np

try:
    input = raw_input
except NameError:
    pass


def bindFile(fn, writable=0):
    """open existing Mrc file
    returns memmaped array
    array has special 'Mrc' attribute
    """
    mode = "r"
    if writable:
        mode = "r+"
    a = Mrc(fn, mode)

    # if a.extension == ".dv":  # flip data for orientation?˝˝˝
    #     return np.fliplr(a.data_withMrc(fn))
    return a.data_withMrc(fn)


class Mrc:
    def __init__(
        self, path, mode="r", extHdrSize=0, extHdrNints=0, extHdrNfloats=0, dv=False
    ):
        """mode can be 'r' or 'r+'"""

        self.path = os.path.abspath(path)
        self.dv = dv
        if path.endswith(".dv"):
            self.dv = True
        self.filename = os.path.basename(path)
        self.extension = os.path.splitext(path)[1]
        if extHdrSize and extHdrSize % 1024:
            raise ValueError(
                "extended header size needs to be integer multiple of 1024"
            )
        self.m = np.memmap(path, mode=mode)
        self.h = self.m[:1024]
        self.hdr = makeHdrArray(self.h)
        nzBeforeByteOrder = self.hdr.Num[0]
        if nzBeforeByteOrder < 0 or nzBeforeByteOrder > 10000:
            self.hdr._array.dtype = self.hdr._array.dtype.newbyteorder()
            self.isByteSwapped = True
        else:
            self.isByteSwapped = False
        self.data_offset = 1024 + self.hdr.next
        self.d = self.m[self.data_offset :]
        self.e = self.m[1024 : self.data_offset]  # extended header bytes
        self.doDataMap()
        self.numInts = self.hdr.NumIntegers
        self.numFloats = self.hdr.NumFloats
        if self.numInts > 0 or self.numFloats > 0:
            self.doExtHdrMap()
        else:
            self.extHdrArray = None

    # alias
    @property
    def header(self):
        return self.hdr

    @property
    def shape(self):
        return self.data.shape

    @property
    def dtype(self):
        return self.data.dtype

    # this could prevent garbage collector ...
    # http://arctrix.com/nas/python/gc/
    # Circular references which are garbage are detected when the optional cycle
    # detector is enabled (it's on by default), but can only be cleaned up if there are
    # no Python-level __del__() methods involved. Refer to the documentation for the
    # 'gc' module for more information about how __del__() methods are handled by the
    # cycle detector, particularly the description of the garbage value. Notice:
    # [warning] Due to the precarious circumstances under which __del__() methods are
    # invoked, exceptions that occur during their execution are ignored, and a warning
    # is printed to sys.stderr instead. Also, when __del__() is invoked in response to a
    # module being deleted (e.g., when execution of the program is done), other globals
    # referenced by the __del__() method may already have been deleted. For this reason,
    # __del__() methods should do the absolute minimum needed to maintain external
    # invariants.
    #   def __del__(self):
    #       print "debug: Mrc.__del__ (close()) called !"
    #       try:
    #           #self.m.close()
    #           self.close()
    #       except:
    #           pass
    def insertExtHdr(self, numInts, numFloats, nz=-1):
        """20051201 - test failed - data did NOT get shifted my next bytes !!!"""
        if numInts == numFloats == 0:
            raise "what ??"
        if self.data_offset != 1024:
            raise "what 2 ??"
        if self.hdr.next != 0:
            raise "what 3 ??"
        if nz <= 0:
            nz = self.hdr.Num[-1]
        bytes = 4 * (numInts + numFloats) * nz
        next = 1024 * ((bytes % 1024 != 0) + bytes // 1024)
        self.hdr.next = next
        self.hdr.NumIntegers = numInts
        self.hdr.NumFloats = numFloats
        self.numInts = numInts
        self.numFloats = numFloats
        self.data_offset = 1024 + next
        self.e = self.m.insert(1024, next)
        self.doExtHdrMap()

    def doExtHdrMap(self, nz=0):
        """maps the extended header space to a recarray
        if nz==0: then it maps 'NumSecs' tuples
        if nz==-1 then it maps the _maximal_ available space
             then self.extHdrArray will likely have more entries then the 'NumSecs'
        """
        if nz == 0:
            nz = self.hdr.Num[-1]
        # check to make sure the header isn't shorter than predicted
        maxnz = int(len(self.e) / ((self.numInts + self.numFloats) * 4))
        if nz < 0 or nz > maxnz:
            nz = maxnz
        byteorder = "="
        # 20070206 self.isByteSwapped and '>' or '<'
        # self.extHdrArray = np.rec.frombuffer(
        #   self.e, formats="%di4,%df4"%(self.numInts,self.numFloats),
        #   names='int,float',
        #   shape=nz,
        #   byteorder=byteorder
        # )

        _fmt = "%sf4" % (byteorder)
        dv_floats = []
        names = (
            "photosensorReading",
            "timeStampSeconds",
            "stageXCoord",
            "stageYCoord",
            "stageZCoord",
            "minInten",
            "maxInten",
            "meanInten",
            "expTime",
            "ndFilter",
            "exWavelen",
            "emWavelen",
            "intenScaling",
            "energyConvFactor",
        )
        for name in names:
            dv_floats.append((name, _fmt))
        for i in range(self.numFloats - len(names)):
            dv_floats.append(("empty%d" % i, _fmt))
        dv_floats = np.dtype(dv_floats)

        type_descr = np.dtype(
            [
                ("int", "%s%di4" % (byteorder, self.numInts)),
                (
                    "float",
                    dv_floats if self.dv else "%s%df4" % (byteorder, self.numFloats),
                ),
            ]
        )

        self.extHdrArray = np.recarray(shape=nz, dtype=type_descr, buf=self.e)
        if self.isByteSwapped:
            self.extHdrArray = self.extHdrArray.newbyteorder()
        self.extInts = self.extHdrArray.field("int")
        self.extFloats = self.extHdrArray.field("float")

    @property
    def extended_header(self):
        """ended Header, reshaped to (# timepoints, # wavelengths)
        for dv files, can index as such:
          mrc.extHdr['timeStampSeconds'][t, c]
        where t and c are the timepoint and channel respectively
        """
        if hasattr(self, "extFloats"):
            return np.squeeze(self.extFloats.reshape((-1, self.hdr.NumWaves)))
        return None

    def doDataMap(self):
        dtype = MrcMode2dtype(self.hdr.PixelType)
        shape = shapeFromHdr(self.hdr)
        self.data = self.d.view()
        self.data.dtype = dtype
        n0 = self.data.shape[0]
        if n0 != np.prod(shape):  # file contains INCOMPLETE sections
            print("** WARNING **: file truncated - shape from header:", shape)
            n1 = np.prod(shape[1:])
            s0 = n0 // n1  # //-int-division (rounds down)
            # if s0 == 1:
            #    shape = shape[1:]
            # else:
            shape = (s0,) + shape[1:]
            self.data = self.data[: np.prod(shape)]
        self.data.shape = shape
        if self.isByteSwapped:
            self.data = self.data.newbyteorder()

    def setTitle(self, s, i=-1):
        """set title i (i==-1 means "append") to s"""
        setTitle(self.hdr, s, i)

    def axisOrderStr(self, onlyLetters=True):
        """return string indicating meaning of shape dimensions
        ##
        ## ZTW   <- non-interleaved
        ## WZT   <- OM1 ( easy on stage)
        ## ZWT   <- added by API (used at all ??)
        ## ^
        ## |
        ## +--- first letter 'fastest'
        fixme: possibly wrong when doDataMap found bad file-size
        """
        return axisOrderStr(self.hdr, onlyLetters)

    def looksOK(self, verbose=1):
        """do some basic checks like filesize, ..."""
        # print "TODO"
        shape = self.data.shape
        b = self.data.dtype.itemsize
        eb = np.prod(shape) * b
        ab = len(self.d)
        secb = np.prod(shape[-2:]) * b
        anSecs = ab / float(secb)
        enSecs = eb / float(secb)
        if verbose >= 3:
            print("expected total data bytes:", eb)
            print("data bytes in file       :", ab)
            print("expected total secs:", enSecs)
            print("file has total secs:", anSecs)
        if eb == ab:
            if verbose >= 2:
                print("OK")
            return 1
        elif eb < ab:
            if verbose >= 1:
                print(
                    "* we have %.2f more (hidden) section in file" % (anSecs - enSecs)
                )
            return 0
        else:
            if verbose >= 1:
                print("* file MISSES %.2f sections " % (enSecs - anSecs))
                print("PLEASE SET shape to ", anSecs, "sections !!! ")
            return 0

    def info(self):
        """print useful information from header"""
        hdrInfo(self.hdr)

    def data_withMrc(self, fn):
        """use this to get 'spiffed up' array"""

        # NOT-WORKING:  self.data.Mrc = weakref.proxy( self )
        # 20071123: http://www.scipy.org/Subclasses
        class ndarray_inMrcFile(np.ndarray):
            def __array_finalize__(self, obj):
                self.Mrc = getattr(obj, "Mrc", None)

        #         class ndarray_inMrcFile(np.memmap):
        #             pass
        #             def __new__(subtype, data, info=None, dtype=None, copy=False):
        #                 #subarr = np.array(data, dtype=dtype, copy=copy)
        #                 #subarr = subarr.view(subtype)
        #                 subarr = data.view(subtype)
        #                 return subarr
        #             def __array_finalize__(self,obj):
        #                 self.Mrc = getattr(obj, 'Mrc', None)
        data = self.data
        data.__class__ = ndarray_inMrcFile
        ddd = weakref.proxy(data)
        self.data = ddd
        data.Mrc = self
        return data

    def close(self):
        self.m.close()


###########################################################################
###########################################################################
###########################################################################
###########################################################################
def open(path, mode="r"):
    return Mrc2(path, mode)


def load(fn):
    """return 3D array filled with the data
    (non memmap)
    """
    m = open(fn)
    a = m.readStack(m.hdr.Num[2])
    return a


def mmm(a):
    # calculate (min, max, mean) of array
    mi = np.min(a)
    ma = np.max(a)
    mean = np.mean(a)
    return np.array([mi, ma, mean], dtype="f")


def mm(a):
    # calculate (min, max) of array
    mi = np.min(a)
    ma = np.max(a)
    return np.array([mi, ma], dtype="f")


def calculate_mmm(a, m):
    # add min/max/mean info to m.hdr
    wAxis = axisOrderStr(m.hdr).find("w")
    if wAxis < 0:
        if a.dtype != np.complex64 and a.dtype != np.complex128:
            m.hdr.mmm1 = mmm(a)
        else:
            m.hdr.mmm1 = mmm(np.abs(a))
    else:
        nw = m.hdr.NumWaves
        m.hdr.mmm1 = mmm(a.take((0,), wAxis))
        if nw >= 2:
            m.hdr.mm2 = mm(a.take((1,), wAxis))
        if nw >= 3:
            m.hdr.mm3 = mm(a.take((2,), wAxis))
        if nw >= 4:
            m.hdr.mm4 = mm(a.take((3,), wAxis))
        if nw >= 5:
            m.hdr.mm5 = mm(a.take((4,), wAxis))


def save(
    a,
    fn,
    ifExists="overwrite",
    zAxisOrder=None,
    hdr=None,
    # hdrEval="",
    calcMMM=True,
    extInts=None,
    extFloats=None,
    metadata=None,
):
    """
    ifExists shoud be one of
       ask
       raise
       overwrite
    (only first letter is checked)
     use zAxisOrder if arr.ndim > 3:
       zAxisOrder is given in order conform to python(last is fastest)
          (spaces,commas,dots,minuses  are ignored)
       examples:
          4D: time,z,y,x          -->  zAxisOrder= 't z'
          5D: time, wave, z,y,x   -->  zAxisOrder= 't,z,w'
       refer to Mrc spec 'ImgSequence' (interleaved or not)
       zAxisOrder None means:
          3D: 'z'
          4D: 'tz'
          5D: 'tzw'
    if hdr is not None:  copy all fields(except 'Num',...)
    if calcMMM:  calculate min,max,mean of data set and set hdr field
    TODO: not implemented yet, extInts=None, extFloats=None

    metadata (dict): fields to overwrite in the header, accepts all field names in hdr
    """
    # removed:
    # if hdrEval:  exec this string ("hdr" refers to the 'new' header)

    if os.path.exists(fn):
        if ifExists[0] == "o":
            pass
        elif ifExists[0] == "a":
            yes = input("overwrite?").lower() == "y"
            if not yes:
                raise "not overwriting existing file '%s'" % fn
        else:
            raise "not overwriting existing file '%s'" % fn
    m = Mrc2(fn, mode="w")
    m.initHdrForArr(a, zAxisOrder)
    if hdr is not None:
        copyHdrInfo(m.hdr, hdr)
    else:
        # added by Talley to detect whether array is Mrc format and copy header if so
        if hasattr(a, "Mrc"):
            if hasattr(a.Mrc, "hdr"):
                copyHdrInfo(m.hdr, a.Mrc.hdr)
    if calcMMM:
        calculate_mmm(a, m)
    if metadata is not None:
        add_metadata(metadata, m.hdr)
    if extInts is not None or extFloats is not None:
        raise NotImplementedError("todo: implement ext hdr")
    # if hdrEval:
    #     import sys
    #     fr = sys._getframe(1)
    #     loc = {"hdr": m.hdr}
    #     loc.update(fr.f_locals)
    #     glo = fr.f_globals
    #     exec(hdrEval, globals=glo, locals=loc)
    m.writeHeader()
    m.writeStack(a)
    m.close()


def add_metadata(metadata, hdr):
    for key, value in metadata.items():
        if key in ("Num", "PixelType", "NumTimes", "NumWaves"):
            import warnings

            warnings.warn(
                "Refusing to override metadata field derived from array: %s" % key
            )
            continue
        if key not in mrcHdrNames:
            if key == "dx":
                hdr.d[0] = value
            elif key == "dy":
                hdr.d[1] = value
            elif key == "dz":
                hdr.d[2] = value
            elif key == "dxy":
                hdr.d[:2] = value
            elif key == "dxyz":
                hdr.d[:3] = value
            elif key in ("wave0", "wave1", "wave2", "wave3", "wave4", "wave5"):
                hdr.wave[int(key[-1])] = value
            else:
                raise ValueError(
                    'Unrecognized header field: "{}"... must be one of {}'.format(
                        key, ", ".join(mrcHdrNames)
                    )
                )
            continue
        setattr(hdr, key, value)


def pick_zAxisOrder(arr):
    if hasattr(arr, "Mrc"):
        # if arr.Mrc exists... was likely opened from an existing file
        # hdr.ImgSequence (0 = ZTW, 1 = WZT, 2 = ZWT)
        orderlookup = ["wtz", "tzw", "twz"]
        return orderlookup[arr.Mrc.hdr.ImgSequence]

    shape = arr.shape
    if arr.ndim == 3:
        if shape[0] <= 4:
            # assume this is a multi-channel image, rather than z/t stack
            return "w"
        elif shape[0] > 500:
            # that many planes is unlikely to be a z-stack
            return "t"
        return "z"

    argmin = np.argmin(arr.shape)  # probably the wavelength channel
    if arr.ndim == 4:
        if shape[argmin] <= 4:
            if argmin == 0:
                return "wz"
            if argmin == 1:
                return "zw"
        return "tz"

    if argmin == 0:
        return "wzt"
    elif argmin == 1:
        return "twz"
    return "tzw"


###########################################################################
class Mrc2:
    """
    this class is for NON-memmapped access of Mrc files
    sections can be read and written on a by-need basis
    the Mrc2 object itself only handles
       the file-object and
       the header and
       extended header data
       BUT NOT ANY image data
    mode indicates how the file is to be opened:
        'r' for reading,
        'w' for writing (truncating an existing file),
        ['a' does not really make sense here]
        Modes 'r+', 'w+' [and 'a+'] open the file for updating (note that 'w+' truncates
        the file).
     ('b' for binary mode, is implicitely appended)
    """

    def __init__(self, path, mode="r"):
        """
        path is filename
        mode: same as for Python's open function
            ('b' is implicitely appended !)
            'r'   read-only
            'r+'  read-write
            'w'   write - erases old file !!
        """

        import builtins

        self._f = builtins.open(path, mode + "b")
        self._path = path
        self._name = os.path.basename(path)
        self._mode = mode
        self._hdrSize = 1024
        self._dataOffset = self._hdrSize
        self._fileIsByteSwapped = False
        if mode in ("r", "r+"):
            self._initFromExistingFile()
            # 111 - now we will have real extHdr support
            # 111 self._dataOffset += self.hdr.next #HACK
            self.seekSec(0)
        else:
            # 20060818 self._hdrArray = makeHdrArray()
            # 20060818 self.hdr = implement_hdr( self._hdrArray )
            self.hdr = makeHdrArray()
            self._shape = None
            self._shape2d = None
            self._dtype = None  # scalar data type of pixels
            self._secByteSize = 0

    def initHdrForArr(self, arr, zAxisOrder=None):

        if zAxisOrder is None:
            zAxisOrder = pick_zAxisOrder(arr)
        else:
            import re

            # remove delimiter characters '-., '
            zAxisOrder = re.sub("[-., ]", "", zAxisOrder)
        mrcmode = dtype2MrcMode(arr.dtype.type)
        init_simple(self.hdr, mrcmode, arr.shape)
        if arr.ndim == 2:
            pass
        elif arr.ndim == 3:
            if zAxisOrder[-1] == "z":
                self.hdr.ImgSequence = 0
            elif zAxisOrder[-1] == "w":
                self.hdr.ImgSequence = 1
                self.hdr.NumWaves = arr.shape[-3]
            elif zAxisOrder[-1] == "t":
                self.hdr.ImgSequence = 2
                self.hdr.NumTimes = arr.shape[-3]
            else:
                raise ValueError("unsupported axis order")
        elif arr.ndim == 4:
            if zAxisOrder[-2:] == "zt":
                self.hdr.ImgSequence = 2
                self.hdr.NumTimes = arr.shape[-3]
            elif zAxisOrder[-2:] == "tz":
                self.hdr.ImgSequence = 0
                self.hdr.NumTimes = arr.shape[-4]
            elif zAxisOrder[-2:] == "wz":
                self.hdr.ImgSequence = 0
                self.hdr.NumWaves = arr.shape[-4]
            elif zAxisOrder[-2:] == "zw":
                self.hdr.ImgSequence = 1
                self.hdr.NumWaves = arr.shape[-3]
            else:
                raise ValueError("unsupported axis order")
        elif arr.ndim == 5:
            raise ValueError("FIXME TODO: 5D")
        else:
            raise ValueError("unsupported array ndim")
        self._initWhenHdrArraySet()

    def _initFromExistingFile(self):
        self.seekHeader()
        hdrArray = np.rec.fromfile(self._f, dtype=mrcHdr_dtype, shape=1)
        self.hdr = implement_hdr(hdrArray)
        self._nzBeforeByteOrder = self.hdr.Num[0]
        if self._nzBeforeByteOrder < 0 or self._nzBeforeByteOrder > 10000:
            self.hdr._array.dtype = self.hdr._array.dtype.newbyteorder()
            self._fileIsByteSwapped = True
        self._extHdrSize = self.hdr.next
        self._extHdrNumInts = self.hdr.NumIntegers
        self._extHdrNumFloats = self.hdr.NumFloats
        self._extHdrBytesPerSec = (self._extHdrNumInts + self._extHdrNumFloats) * 4
        self._dataOffset = self._hdrSize + self._extHdrSize
        if self._extHdrSize > 0 and (
            self._extHdrNumInts > 0 or self._extHdrNumFloats > 0
        ):
            nSecs = int(self._extHdrSize / self._extHdrBytesPerSec)
            self._extHdrArray = np.rec.fromfile(
                self._f,
                formats="%di4,%df4" % (self._extHdrNumInts, self._extHdrNumFloats),
                names="int,float",
                shape=nSecs,
            )  # ,
            # byteorder=byteorder)
            if self._fileIsByteSwapped:
                self._extHdrArray.newbyteorder()
            self.extInts = self._extHdrArray.field("int")
            self.extFloats = self._extHdrArray.field("float")
        self._initWhenHdrArraySet()

    def _initWhenHdrArraySet(self):
        nx, ny, nsecs = self.hdr.Num
        self._shape = (nsecs, ny, nx)  # todo: wavelenths , times
        self._shape2d = self._shape[-2:]
        self._dtype = MrcMode2dtype(self.hdr.PixelType)
        self._secByteSize = np.nbytes[self._dtype] * np.prod(self._shape2d)

    def setHdrForShapeType(self, shape, type):
        # not used by anything at the moment
        mrcmode = dtype2MrcMode(type)
        self.hdr.PixelType = mrcmode
        self.hdr.Num = shape[-1], shape[-2], np.prod(shape[:-2])
        self._initWhenHdrArraySet()

    def makeExtendedHdr(self, numInts, numFloats, nSecs=None):
        self._extHdrNumInts = self.hdr.NumIntegers = numInts
        self._extHdrNumFloats = self.hdr.NumFloats = numFloats
        self._extHdrBytesPerSec = (self._extHdrNumInts + self._extHdrNumFloats) * 4
        if nSecs is None:
            nSecs = self._shape[0]
        self._extHdrSize = self.hdr.next = minExtHdrSize(nSecs, self._extHdrBytesPerSec)
        self._dataOffset = self._hdrSize + self._extHdrSize
        if self._extHdrSize > 0 and (
            self._extHdrNumInts > 0 or self._extHdrNumFloats > 0
        ):
            nSecs = int(self._extHdrSize / self._extHdrBytesPerSec)
            self._extHdrArray = np.recarray(
                nSecs,  # None,#self._f,
                formats="%di4,%df4" % (self._extHdrNumInts, self._extHdrNumFloats),
                names="int,float",
            )
            # shape=nSecs)#  ,
            # byteorder=byteorder)
            self.extInts = self._extHdrArray.field("int")
            self.extFloats = self._extHdrArray.field("float")

    def info(self):
        """print useful information from header"""
        hdrInfo(self.hdr)

    def close(self):
        self._f.close()

    def flush(self):
        self._f.flush()

    def seekSec(self, i):
        if self._secByteSize == 0:  # type is None or self._shape2d is None:
            raise ValueError("not inited yet - unknown shape, type")
        self._f.seek(self._dataOffset + i * self._secByteSize)

    def seekHeader(self):
        self._f.seek(0)

    def seekExtHeader(self):
        self._f.seek(self._hdrSize)

    def readSec(self, i=None):
        """if i is None read "next" section at current position"""
        if i is not None:
            self.seekSec(i)
        a = np.fromfile(self._f, self._dtype, np.prod(self._shape2d))
        a.shape = self._shape2d
        return a

    def writeSec(self, a, i=None):
        """if i is None write "next" section at current position"""
        if i is not None:
            self.seekSec(i)
        # todo check type, shape
        return a.tofile(self._f)

    def readStack(self, nz, i=None):
        """if i is None read "next" section at current position"""
        if i is not None:
            self.seekSec(i)
        a = np.fromfile(self._f, self._dtype, nz * np.prod(self._shape2d))
        a.shape = (nz,) + self._shape2d
        return a

    def writeStack(self, a, i=None):
        """if i is None write "next" section at current position"""
        if i is not None:
            self.seekSec(i)
        # todo check type, shape
        return a.tofile(self._f)

    def writeHeader(self, seekTo0=False):
        self.seekHeader()
        self.hdr._array.tofile(self._f)
        if seekTo0:
            self.seekSec(0)

    def writeExtHeader(self, seekTo0=False):
        self.seekExtHeader()
        self._extHdrArray.tofile(self._f)
        if seekTo0:
            self.seekSec(0)


###########################################################################
def minExtHdrSize(nSecs, bytesPerSec):
    """return smallest multiple of 1024 to fit extHdr data"""
    return int(np.ceil(nSecs * bytesPerSec / 1024.0) * 1024)


def MrcMode2dtype(mode):
    PixelTypes = (
        np.uint8,
        np.int16,
        np.float32,
        np.float32,  # technically "complex32"... which does not exist in numpy
        np.complex64,
        np.int16,
        np.uint16,
        np.int32,
    )
    if mode < 0 or mode > 7:
        raise Exception("Priism file supports pixeltype 0 to 7 - %d given" % mode)
    return PixelTypes[int(mode)]


def dtype2MrcMode(dtype):
    if dtype == np.uint8:
        return 0
    if dtype == np.int16:
        return 1
    if dtype == np.float32:
        return 2
    #      if type == np.int8:
    #          return 3
    if dtype == np.complex64:
        return 4
    #      if type == np.In:
    #          return 5
    if dtype == np.uint16:
        return 6
    if dtype == np.int32:
        return 7
    raise TypeError("MRC does not support %s (%s)" % (dtype.__name__, dtype))


def shapeFromHdr(hdr, verbose=0):
    """
    return "smart" shape
    considering numTimes, numWavelenth and hdr.ImgSequence
    if verbose:
        print somthing like: w,t,z,y,x  ot z,y,x
    """
    zOrder = hdr.ImgSequence  # , 'Image sequence. 0=ZTW, 1=WZT, 2=ZWT. '),
    nt, nw = hdr.NumTimes, hdr.NumWaves
    nx, ny, nsecs = hdr.Num
    if nt == 0:
        # 20051213(ref."other's" MRC) print " ** NumTimes is zero - I assume 1."
        nt = 1
    if nw == 0:
        # 20051213(ref."other's" MRC) print " ** NumWaves is zero - I assume 1."
        nw = 1
    nz = int(nsecs / nt / nw)
    if nt == nw == 1:
        shape = (nz, ny, nx)
        orderLetters = "zyx"
    elif nz == 1 == nw:
        shape = (nt, ny, nx)
        orderLetters = "tyx"
    elif nt == 1 or nw == 1:
        if zOrder == 0 or zOrder == 2:
            nn = nt
            if nt == 1:
                nn = nw
                orderLetters = "wyx"
            else:
                orderLetters = "tyx"
            shape = (nn, nz, ny, nx)
        else:  # if zOrder == 1:
            if nt == 1:
                shape = (nz, nw, ny, nx)
                orderLetters = "zwyx"
            else:
                shape = (nt, nz, ny, nx)
                orderLetters = "tzyx"
    else:  # both nt and nw > 1
        if zOrder == 0:
            shape = (nw, nt, nz, ny, nx)
            orderLetters = "wtzyx"
        elif zOrder == 1:
            shape = (nt, nz, nw, ny, nx)
            orderLetters = "tzwyx"
        else:  # zOrder == 2:
            shape = (nt, nw, nz, ny, nx)
            orderLetters = "twzyx"
    if verbose:
        print(",".join(orderLetters))
    return shape


# my hack to allow thinks like a.Mrc.hdr.d = (1,2,3)
def implement_hdr(hdrArray):
    class hdr(object):
        __slots__ = mrcHdrNames[:] + ["_array"]

        def __init__(s):
            pass

        def __setattr__(s, n, v):
            # 20070131 hdrArray.field(n)[0] = v
            hdrArray[n][0] = v

        def __getattr__(s, n):
            if n == "_array":
                return hdrArray  # 20060818
            # 20070131 return hdrArray.field(n)[0]
            return hdrArray[n][0]

        def __str__(self):
            out = ""
            for field in mrcHdrNames:
                if field != "_array":
                    out += "{:12}{}\n".format(field, self.__getattr__(field))
            return out

        # depricated !!
        # def __call__(s, n):
        #    return hdrArray.field(n)[0]

    return hdr()


# class function
def makeHdrArray(buffer=None):
    if buffer is not None:
        # 20070131  h = buffer.view()
        # 20060131  h.__class__ = np.recarray
        h = buffer
        h.dtype = mrcHdr_dtype

        h = weakref.proxy(h)  # 20070131   CHECK if this works
    else:
        h = np.recarray(1, mrcHdr_dtype)
    # 20060818 return h
    return implement_hdr(h)


# class function
def hdrInfo(hdr):
    shape = hdr.Num[::-1]
    nz = shape[0]
    numInts = hdr.NumIntegers
    numFloats = hdr.NumFloats
    print("width:                      ", shape[2])
    print("height:                     ", shape[1])
    print("# total slices:             ", shape[0])
    nt, nw = hdr.NumTimes, hdr.NumWaves
    if nt == 0 or nw == 0:
        print(" ** ERROR ** : NumTimes or NumWaves is zero")
        print("NumTimes:", nt)
        print("NumWaves:", nw)
    else:
        if nt == 1 and nw == 1:
            print
        elif nw == 1:  # TODO: make comment about order
            print("  (%d times for %d zsecs)" % (nt, nz / nt))
        elif nt == 1:
            print("  (%d waves in %d zsecs)" % (nw, nz / nw))
        else:
            print("  (%d times for %d waves in %d zsecs)" % (nt, nw, nz / nw / nt))
    if nt != 1 or nw != 1:
        print("# slice order:        %d (0,1,2 = (ZTW or WZT or ZWT)" % hdr.ImgSequence)
    print("pixel width x    (um):      ", hdr.d[0])
    print("pixel width y    (um):      ", hdr.d[1])
    print("pixel height     (um):      ", hdr.d[2])
    print("# wavelengths:              ", nw)
    print("   wavelength 1  (nm):      ", hdr.wave[0])
    print("    intensity min/max/mean: ", hdr.mmm1[0], hdr.mmm1[1], hdr.mmm1[2])
    if nw > 1:
        print("   wavelength 2  (nm):      ", hdr.wave[1])
        print("    intensity min/max:      ", hdr.mm2[0], hdr.mm2[1])
    if nw > 2:
        print("   wavelength 3  (nm):      ", hdr.wave[2])
        print("    intensity min/max:      ", hdr.mm3[0], hdr.mm3[1])
    if nw > 3:
        print("   wavelength 4  (nm):      ", hdr.wave[3])
        print("    intensity min/max:      ", hdr.mm4[0], hdr.mm4[1])
    if nw > 4:
        print("   wavelength 5  (nm):      ", hdr.wave[4])
        print("    intensity min/max:      ", hdr.mm5[0], hdr.mm5[1])
    # /  ostr + "# times:              " + num_times + '\n';
    # /  ostr += "# slice order:        " + 0 or 1 or 2 (ZTW or WZT or ZWT) + '\n';
    # /  ostr +="filetype:              " += filetype ... 0=normal, ..., 2=stereo ...
    # /    ostr += "n1, n2, v1, v2:          " +=  depend on filetype ....
    print("lens type:                  ", hdr.LensNum)
    if hdr.LensNum == 12:
        print(" (60x)")
    elif hdr.LensNum == 13:
        print(" (100x)")
    else:
        print("(??)")
    print("origin   (um) x/y/z:        ", hdr.zxy0[1], hdr.zxy0[2], hdr.zxy0[0])
    print("# pixel data type:            ")
    if hdr.PixelType == 0:
        print("8 bit (unsigned)")
    elif hdr.PixelType == 1:
        print("16 bit (signed)")
    elif hdr.PixelType == 2:
        print("32 bit (signed real)")
    elif hdr.PixelType == 3:
        print("16 bit (signed complex integer)")
    elif hdr.PixelType == 4:
        print("32 bit (signed complex real)")
    elif hdr.PixelType == 5:
        print("16 bit (signed) IW_EMTOM")
    elif hdr.PixelType == 6:
        print("16 bit (unsigned short)")
    elif hdr.PixelType == 7:
        print("32 bit (signed long)")
    else:
        print(" ** undefined ** ")
    # //ostr += "bytes before image data:     " + 1024+inbsym + '\n';
    print("# extended header size:       ", hdr.next)
    if hdr.next > 0:
        n = numInts + numFloats
        if n > 0:
            print(" (%d secs)" % (hdr.next / (4.0 * n),))
        else:
            print(" (??? secs)")
        print("  (%d ints + %d reals per section)" % (numInts, numFloats))
    else:
        print
    if hdr.NumTitles < 0:
        print(
            " ** ERROR ** : NumTitles less than zero (NumTitles =", hdr.NumTitles, ")"
        )
    elif hdr.NumTitles > 0:
        n = hdr.NumTitles
        if n > 10:
            print(
                " ** ERROR ** : NumTitles larger than 10 (NumTitles =",
                hdr.NumTitles,
                ")",
            )
            n = 10
        for i in range(n):
            print("title %d: %s" % (i, hdr.title[i]))


def axisOrderStr(hdr, onlyLetters=True):
    """return string indicating meaning of shape dimensions
    ##
    ## ZTW   <- non-interleaved
    ## WZT   <- OM1 ( easy on stage)
    ## ZWT   <- added by API (used at all ??)
    ## ^
    ## |
    ## +--- first letter 'fastest'
    fixme: possibly wrong when doDataMap found bad file-size
    """
    zOrder = int(hdr.ImgSequence)  # , 'Image sequence. 0=ZTW, 1=WZT, 2=ZWT. '),
    nt, nw = hdr.NumTimes, hdr.NumWaves
    if nt == nw == 1:
        orderLetters = "zyx"
    elif nt == 1:
        orderLetters = ("wzyx", "zwyx", "wzyx")[zOrder]
    elif nw == 1:
        orderLetters = ("tzyx", "tzyx", "tzyx")[zOrder]
    else:
        orderLetters = ("wtzyx", "tzwyx", "twzyx")[zOrder]
    if onlyLetters:
        return orderLetters
    else:
        return "[" + ",".join(orderLetters) + "]"


def init_simple(hdr, mode, nxOrShape, ny=None, nz=None):
    """note: if  nxOrShape is tuple it is nz,ny,nx (note the order!!)"""
    if ny is nz is None:
        if len(nxOrShape) == 2:
            nz, (ny, nx) = 1, nxOrShape
        elif len(nxOrShape) == 1:
            nz, ny, nx = 1, 1, nxOrShape
        elif len(nxOrShape) == 3:
            nz, ny, nx = nxOrShape
        else:
            ny, nx = nxOrShape[-2:]
            nz = np.prod(nxOrShape[:-2])
    else:
        nx = nxOrShape
    hdr.Num = (nx, ny, nz)
    hdr.PixelType = mode
    hdr.mst = (0, 0, 0)  # 20060614: bugfixed was: (1,1,1))
    hdr.m = (1, 1, 1)  # CHECK : should be nx,ny,nz ??
    hdr.d = (1, 1, 1)
    hdr.angle = (90, 90, 90)  # 20060202: changed alpha,beta,gamma to 90 (was:0)
    hdr.axis = (1, 2, 3)
    hdr.mmm1 = (0, 100000, 5000)
    hdr.type = 0
    hdr.nspg = 0
    hdr.next = 0
    hdr.dvid = -16224
    hdr.blank = 0  # CHECK Hans: add ntst to record time domain offset
    hdr.NumIntegers = 0
    hdr.NumFloats = 0
    hdr.sub = 0
    hdr.zfac = 0
    hdr.mm2 = (0, 10000)
    hdr.mm3 = (0, 10000)
    hdr.mm4 = (0, 10000)
    hdr.ImageType = 0
    hdr.LensNum = 0
    hdr.n1 = 0
    hdr.n2 = 0
    hdr.v1 = 0
    hdr.v2 = 0
    hdr.mm5 = (0, 10000)
    hdr.NumTimes = 1
    hdr.ImgSequence = 0
    # 0 => not interleaved. That means z changes fastest, then time, then waves;
    # 1 => interleaved. That means wave changes fastest, then z, then time.
    hdr.tilt = (0, 0, 0)
    hdr.NumWaves = 1
    hdr.wave = (999, 0, 0, 0, 0)
    hdr.zxy0 = (0, 0, 0)
    hdr.NumTitles = 0
    hdr.title = "\0" * 80


def copyHdrInfo(hdrDest, hdrSrc):
    """copy all field of the header
    EXCEPT  shape AND PixelType AND all fields related to extended hdr
    """
    for field in mrcHdrNames:
        if field in ("Num", "PixelType", "next"):
            continue
        setattr(hdrDest, field, getattr(hdrSrc, field))


def setTitle(hdr, s, i=-1):
    """set title i (i==-1 means "append") to s"""
    n = hdr.NumTitles
    if i < 0:
        i = n
    if i > 9:
        raise ValueError("Mrc only support up to 10 titles (0<=i<10)")
    if len(s) > 80:
        raise ValueError("Mrc only support title up to 80 characters")
    if i >= n:
        hdr.NumTitles = i + 1
    if len(s) == 80:
        hdr.title[i] = s
    else:
        hdr.title[i] = s + "\0"


mrcHdrFields = [
    ("3i4", "Num", "Number of pixels in (x, y, z) dimensions"),
    (
        "i4",
        "PixelType",
        "Data type (0=uint8, 1=int16, 2=float32, 4=complex64, 6=uint16",
    ),
    (
        "3i4",
        "mst",
        "Index of the first (col/x, row/y, section/z).  (0,0,0) by default.",
    ),
    ("3i4", "m", "Pixel Sampling intervals in the (x,y,z) dimensions. usually (1,1,1)"),
    ("3f4", "d", "Pixel spacing times sampling interval in (x, y, z) dimensions"),
    ("3f4", "angle", "Cell angle (alpha, beta, gamma) in degress.  Default (90,90,90)"),
    ("3i4", "axis", "Axis (colum, row, section).  Defaults to (1, 2, 3)"),
    ("3f4", "mmm1", "(Min, Max, Mean) of the 1st wavelength image"),
    ("i2", "type", ""),  # seems to disagree with IVE header byte format/offset
    ("i2", "nspg", "Space group number (for crystallography)"),
    ("i4", "next", "Extended header size in bytes."),
    ("i2", "dvid", "ID value (-16224)"),
    ("30i1", "blank", "unused"),
    # seems to disagree with IVE header byte format/offset
    # or at least "blank" here includes "nblank", "ntst", and "blank"
    (
        "i2",
        "NumIntegers",
        "Number of 4 byte integers stored in the extended header per section.",
    ),
    (
        "i2",
        "NumFloats",
        "Number of 4 byte floating-point numbers stored "
        "in the extended header per section.",
    ),
    (
        "i2",
        "sub",
        "Number of sub-resolution data sets stored within "
        "the image. Typically, this equals 1.",
    ),
    ("i2", "zfac", "Reduction quotient for the z axis of the sub-resolution images."),
    ("2f4", "mm2", "(Min, Max) intensity of the 2nd wavelength image."),
    ("2f4", "mm3", "(Min, Max) intensity of the 3rd wavelength image."),
    ("2f4", "mm4", "(Min, Max) intensity of the 4th wavelength image."),
    (
        "i2",
        "ImageType",
        "Image type. (Type 0 used for normal imaging, 8000 used for pupil functions)",
    ),
    ("i2", "LensNum", "Lens identification number."),
    ("i2", "n1", "Depends on the image type."),
    ("i2", "n2", "Depends on the image type."),
    ("i2", "v1", "Depends on the image type."),
    ("i2", "v2", "Depends on the image type."),
    ("2f4", "mm5", "(Min, Max) intensity of the 5th wavelength image."),
    ("i2", "NumTimes", "Number of time points."),
    ("i2", "ImgSequence", "Image axis ordering. 0=XYZTW, 1=XYWZT, 2=XYZWT."),
    ("3f4", "tilt", "(x, y, z) axis tilt angle (degrees)."),
    ("i2", "NumWaves", "Number of wavelengths."),
    ("5i2", "wave", "Wavelengths (for channel [0, 1, 2, 3, 4]), in nm."),
    (
        "3f4",
        "zxy0",
        "(z,x,y) origin, in um.",
    ),  # 20050920  ## fixed: order is z,x,y NOT x,y,z
    ("i4", "NumTitles", "Number of titles. Valid numbers are between 0 and 10."),
    ("10a80", "title", "Title 1. 80 characters long."),
]
mrcHdrNames = []
mrcHdrFormats = []
mrcHdrDescriptions = {}
for ff in mrcHdrFields:
    mrcHdrFormats.append(ff[0])
    mrcHdrNames.append(ff[1])
    if len(ff) > 2:
        mrcHdrDescriptions[ff[1]] = ff[2]
del ff
del mrcHdrFields
mrcHdr_dtype = list(zip(mrcHdrNames, mrcHdrFormats))


# Tifffile API
def imsave(file, data, resolution=None, metadata={}, **kwargs):
    """Write numpy array to mrc file

    This is a wrapper on the mrc.save() function, meant to mimic a subset of
    the tifffile.imsave API
        resolution : (float, float, float), or (float, float)
            X, Y, (and Z. if ndim==3) resolutions in microns per pixel.
    """
    if resolution is not None:
        assert 2 <= len(resolution) <= 3, "resolution arg must be len 2 or 3"
        metadata["dx"] = resolution[0]
        metadata["dy"] = resolution[1]
        if len(resolution) == 3:
            metadata["dz"] = resolution[2]
    return save(data, file, metadata=metadata, **kwargs)


imwrite = imsave


def imread(file, writable=False):
    """Return image data from TIFF file(s) as numpy array.

    Args:
        file (str): File name

    Returns:
        np.ndarray: numpy array with data.  Mrc object is stored at arr.Mrc,
            and header information is at arr.Mrc.header.  For dv format,
            extended header info may be available at arr.Mrc.extHdr
    """
    return bindFile(file, writable=writable)
