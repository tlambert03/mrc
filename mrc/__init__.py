"""Top-level package for mrc.py."""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"
__author__ = "Talley Lambert"
__email__ = "talley.lambert@gmail.com"
__author__ = "Sebastian Haase"
__maintainer__ = "Talley Lambert"
__email__ = "talley.lambert@gmail.com"

from .mrc import (
    Mrc,
    Mrc2,
    bindFile,
    copyHdrInfo,
    hdrInfo,
    imread,
    imsave,
    imwrite,
    load,
    makeHdrArray,
    open,
    save,
    shapeFromHdr,
)

__all__ = [
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
