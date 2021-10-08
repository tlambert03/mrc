import struct
from pathlib import Path
from typing import NamedTuple, Optional, Union

import numpy as np


class DVFile:
    ext_hdr: Optional["ExtHeader"]
    hdr: "Header"

    def __init__(self, path: Union[str, Path]) -> None:
        with open(path, "rb") as fh:
            *r, self._title = _HDR.unpack(fh.read(_HDR.size))
            self.hdr = Header(*r)
            if self.hdr.ext_hdr_len:
                self.ext_hdr = ExtHeader(fh.read(self.hdr.ext_hdr_len), self.hdr)
            else:
                self.ext_hdr = None

        self.data: np.memmap = np.memmap(
            fh.name,
            self.dtype,
            offset=_HDR.size + self.hdr.ext_hdr_len,
            shape=self.shape,
        )

    def __array__(self):
        return self.asarray()

    def asarray(self, squeeze=True):
        return self.data.squeeze() if squeeze else self.data

    def to_xarray(self, squeeze=True):
        import xarray as xr

        attrs = {"header": self.hdr._asdict()}
        attrs["header"].pop("blank")
        if self.ext_hdr:
            attrs["extended_header"] = self.ext_hdr._asdict()
        arr = xr.DataArray(
            np.asarray(self.data),
            dims=list(self.sizes),
            coords=self._expand_coords(),
            attrs=attrs,
        )
        return arr.squeeze() if squeeze else arr

    def _expand_coords(self):
        ord = self.hdr.sequence_order[::-1]
        _map = {
            "C": "exWavelen",
            "T": "timeStampSeconds",
            "Z": "stageZCoord",
        }
        coords = {}
        for key, val in self.sizes.items():
            if key in ("XY"):
                coords[key] = np.arange(val) * getattr(self.voxel_size, key.lower())
            elif self.ext_hdr:
                stride = np.prod([self.sizes[ord[i]] for i in range(ord.index(key))])
                f = [self.ext_hdr.frame(i * int(stride)) for i in range(val)]
                coords[key] = [getattr(x, _map[key]) for x in f]
        return coords

    @property
    def shape(self):
        return tuple(self.sizes.values())

    @property
    def ndim(self):
        return len(self.shape)

    def __getitem__(self, key):
        return self.data[key]

    @property
    def axes(self):
        return self.hdr.sequence_order + "YX"

    @property
    def dtype(self):
        return [
            np.uint8,
            np.int16,
            np.float32,
            None,
            np.complex64,
            np.int16,
            np.uint16,
            np.int32,
        ][self.hdr.pixel_type]

    @property
    def sizes(self):
        d = {
            "T": self.hdr.nt,
            "C": self.hdr.nc,
            "Z": self.hdr.nz,
            "Y": self.hdr.height,
            "X": self.hdr.width,
        }
        return {k: d[k] for k in self.axes}

    @property
    def voxel_size(self) -> "Voxel":
        return Voxel(self.hdr.dx, self.hdr.dy, self.hdr.dz)

    @property
    def lens(self) -> str:
        return self.hdr.lens


class Voxel(NamedTuple):
    x: float
    y: float
    z: float


_HDR = struct.Struct("10i6f3i3f2i2hi24s4h6f6h2f2h3f6h3fi800s")


class Header(NamedTuple):
    width: int
    height: int
    n_sections: int
    pixel_type: int
    x_start: int
    y_start: int
    z_start: int
    mx: int
    my: int
    mz: int
    dx: float
    dy: float
    dz: float
    alpha: float
    beta: float
    gamma: float
    col_ax: int
    row_ax: int
    section_ax: int
    min: float
    max: float
    mean: float
    space_group_num: int
    ext_hdr_len: int
    dvid: int
    nblank: int
    t_start: int
    blank: str
    n_ints: int
    n_floats: int
    n_subres: int
    zfac: int
    min2: float
    max2: float
    min3: float
    max3: float
    min4: float
    max4: float
    img_type: int
    lens_num: int
    n1: int
    n2: int
    v1: int
    v2: int
    min5: float
    max5: float
    nt: int
    img_seq: int
    x_tilt: float
    y_tilt: float
    z_tilt: float
    nc: int
    wave1: int
    wave2: int
    wave3: int
    wave4: int
    wave5: int
    z0: float
    x0: float
    y0: float
    ntiles: int
    # title: str

    @property
    def sequence_order(self):
        # note, these are reversed from the header readme,
        # to reflect how numpy parses the memmap
        return ["CTZ", "TZC", "TCZ"][self.img_seq]

    @property
    def nz(self):
        return self.n_sections // (self.nc or 1) // (self.nt or 1)

    @property
    def image_type(self):
        return {
            0: "NORMAL",
            100: "NORMAL",
            1: "TILT_SERIES",
            2: "STEREO_TILT_SERIES",
            3: "AVERAGED_IMAGES",
            4: "AVERAGED_STEREO_PAIRS",
            5: "EM_TILT_SERIES",
            20: "MULTIPOSITION",
            8000: "PUPIL_FUNCTION",
        }[self.img_type]

    @property
    def lens(self) -> str:
        from .lenses import D

        try:
            return D[self.lens_num]["name"]
        except KeyError:
            return ""


class ExtHeaderFrame(NamedTuple):
    photosensorReading: float
    timeStampSeconds: float
    stageXCoord: float
    stageYCoord: float
    stageZCoord: float
    minInten: float
    maxInten: float
    meanInten: float
    expTime: float
    ndFilter: float
    exWavelen: float
    emWavelen: float
    intenScaling: float
    energyConvFactor: float


class ExtHeader:
    def __init__(self, buf, hdr: Header) -> None:
        self.buffer = buf
        self._hdr = hdr
        self.n_frames = hdr.n_sections
        self.n_floats = hdr.n_floats
        self._section_length = (hdr.n_floats + hdr.n_ints) * 4
        self._shape = [getattr(hdr, f"n{i.lower()}") for i in hdr.sequence_order]
        self._struct = struct.Struct(f"{hdr.n_ints}i{len(ExtHeaderFrame._fields)}f")

    def frame(self, idx: int) -> ExtHeaderFrame:
        if idx >= self.n_frames:
            raise IndexError(f"index {idx} out of range for {self.n_frames} frames")
        f = self._struct.unpack_from(self.buffer, self._section_length * idx)
        return ExtHeaderFrame(*f[8:])

    def _asdict(self):
        return {
            np.unravel_index(i, self._shape): self.frame(i)._asdict()
            for i in range(self.n_frames)
        }
