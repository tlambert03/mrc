# -*- coding: utf-8 -*-

"""Top-level package for mrc.py."""

__author__ = """Sebastian Haase"""
__maintainer__ = "Talley Lambert"
__email__ = "talley@hms.harvard.edu"
__license__ = "BSD license - see LICENSE file"
__version__ = "__version__ = '0.1.5'"

from .mrc import (
    bindFile,
    Mrc,
    open,
    load,
    save,
    Mrc2,
    shapeFromHdr,
    makeHdrArray,
    hdrInfo,
    copyHdrInfo,
    imsave,
    imwrite,
    imread,
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
