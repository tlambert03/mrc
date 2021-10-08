"""DV (deltavision) file reader."""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"


from ._new import DVFile, imread
from .mrc import (
    Mrc,
    Mrc2,
    bindFile,
    copyHdrInfo,
    hdrInfo,
    imsave,
    imwrite,
    load,
    makeHdrArray,
    open,
    save,
    shapeFromHdr,
)

__all__ = [
    "DVFile",
    "bindFile",
    "Mrc",
    "open",
    "load",
    "save",
    "Mrc2",
    "shapeFromHdr",
    "makeHdrArray",
    "hdrInfo",
    "copyHdrInfo",
    "imsave",
    "imwrite",
    "imread",
]
