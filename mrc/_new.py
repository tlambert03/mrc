import struct
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Callable,
    Dict,
    NamedTuple,
    Optional,
    Tuple,
    Union,
)

import numpy as np

if TYPE_CHECKING:
    import dask.array as da
    import xarray as xr

__author__ = "Talley Lambert"
__email__ = "talley.lambert@gmail.com"


class DVFile:
    ext_hdr: Optional["ExtHeader"]
    hdr: "Header"
    _data: Optional[np.memmap] = None

    def __init__(self, path: Union[str, Path]) -> None:
        self._path = str(path)
        with open(path, "rb") as fh:
            head_struct = _pick_struct(fh)
            if head_struct is None:
                raise ValueError(f"{path} is not a recognized DV file.")
            fh.seek(0)
            *r, self._title = head_struct.unpack(fh.read(head_struct.size))
            self.hdr = Header(*r)
            if self.hdr.ext_hdr_len:
                self.ext_hdr = ExtHeader(fh.read(self.hdr.ext_hdr_len), self.hdr)
            else:
                self.ext_hdr = None
        self.open()

    def __enter__(self) -> "DVFile":
        return self

    def __exit__(self, *a) -> None:
        self.close()

    def open(self) -> None:
        if self.closed:
            self._data = np.memmap(
                str(self._path),
                self.dtype,
                offset=LE_HDR.size + self.hdr.ext_hdr_len,
                shape=self.shape,
            )

    def close(self) -> None:
        if not self.closed:
            self.data._mmap.close()
            self._data = None

    @property
    def path(self) -> str:
        return self._path

    @property
    def closed(self) -> bool:
        return self._data is None

    @property
    def data(self) -> np.memmap:
        if self._data is None:
            raise RuntimeError(
                "Cannot read from closed file.  Please reopen with .open()"
            )
        return self._data

    def __array__(self) -> np.ndarray:
        return self.asarray()

    def asarray(self, squeeze=True) -> np.ndarray:
        return self.data.squeeze() if squeeze else self.data

    def to_dask(self) -> "da.Array":
        from dask.array import map_blocks

        chunks = [(1,) * v if k in "TZC" else (v,) for k, v in self.sizes.items()]
        return map_blocks(self._dask_block, chunks=chunks, dtype=self.dtype)

    def _dask_block(self, block_id: Tuple[int]) -> np.ndarray:
        ncoords = 3
        return self[block_id[:ncoords]][(np.newaxis,) * ncoords]

    def to_xarray(self, delayed=False, squeeze=True) -> "xr.DataArray":
        import xarray as xr

        attrs = {"header": self.hdr._asdict()}
        attrs["header"].pop("blank")
        if self.ext_hdr:
            attrs["extended_header"] = self.ext_hdr._asdict()
        arr = xr.DataArray(
            self.to_dask() if delayed else np.asarray(self.data),
            dims=list(self.sizes),
            coords=self._expand_coords(),
            attrs={"metadata": attrs},
        )
        return arr.squeeze() if squeeze else arr

    def _expand_coords(self) -> Dict[str, Any]:
        ord = self.hdr.sequence_order[::-1]
        _map: Dict[str, Callable[[ExtHeaderFrame], str]] = {
            "C": lambda x: f"{x.exWavelen}/{x.emWavelen}",
            "T": lambda x: f"{x.timeStampSeconds}",
            "Z": lambda x: f"{x.stageZCoord}",
        }
        coords = {}
        for key, val in self.sizes.items():
            if key in ("XY"):
                coords[key] = np.arange(val) * getattr(self.voxel_size, key.lower())
            elif self.ext_hdr:
                stride = np.prod([self.sizes[ord[i]] for i in range(ord.index(key))])
                f = [self.ext_hdr.frame(i * int(stride)) for i in range(val)]
                coords[key] = [_map[key](x) for x in f]
        return coords

    @property
    def shape(self) -> Tuple[int, ...]:
        return tuple(self.sizes.values())

    @property
    def ndim(self) -> int:
        return len(self.shape)

    def __getitem__(self, key) -> np.ndarray:
        return self.data[key]

    @property
    def axes(self) -> str:
        return self.hdr.sequence_order + "YX"

    @property
    def dtype(self) -> type:
        return [
            np.uint8,
            np.int16,
            np.float32,
            np.complex64,
            np.complex64,
            np.int16,
            np.uint16,
            np.int32,
        ][self.hdr.pixel_type]

    @property
    def sizes(self) -> Dict[str, int]:
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

    def __repr__(self) -> str:
        try:
            details = " (closed)" if self.closed else f" {self.dtype}: {self.sizes!r}"
            extra = f": {Path(self._path).name!r}{details}"
        except Exception:
            extra = ""
        return f"<ND2File at {hex(id(self))}{extra}>"

    @staticmethod
    def is_supported_file(path):
        with open(path, "rb") as fh:
            return _pick_struct(fh) is not None


HDR_FORMAT = "10i6f3i3f2i2hi24s4h6f6h2f2h3f6h3fi800s"
LE_HDR = struct.Struct("<" + HDR_FORMAT)
BE_HDR = struct.Struct(">" + HDR_FORMAT)


def _pick_struct(fh: BinaryIO) -> Optional[struct.Struct]:
    fh.seek(24 * 4)
    dvid = fh.read(2)
    if dvid == b"\xa0\xc0":
        return LE_HDR
    if dvid == b"\xc0\xa0":
        return BE_HDR
    return None


class Voxel(NamedTuple):
    x: float
    y: float
    z: float


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
    dvid: int  # 2
    nblank: int  # 2
    t_start: int
    blank: str  # 24
    n_ints: int  # 2
    n_floats: int  # 2
    n_subres: int  # 2
    zfac: int  # 2
    min2: float
    max2: float
    min3: float
    max3: float
    min4: float
    max4: float
    img_type: int  # 2
    lens_num: int  # 2
    n1: int  # 2
    n2: int  # 2
    v1: int  # 2
    v2: int  # 2
    min5: float
    max5: float
    nt: int  # 2
    img_seq: int  # 2
    x_tilt: float
    y_tilt: float
    z_tilt: float
    nc: int  # 2
    wave1: int  # 2
    wave2: int  # 2
    wave3: int  # 2
    wave4: int  # 2
    wave5: int  # 2
    z0: float
    x0: float
    y0: float
    ntiles: int
    # title: str

    @property
    def sequence_order(self) -> str:
        # note, these are reversed from the header readme,
        # to reflect how numpy parses the memmap
        return {
            0: "CTZ",
            1: "TZC",
            2: "TCZ",
        }[self.img_seq]

    @property
    def nz(self) -> int:
        return self.n_sections // (self.nc or 1) // (self.nt or 1)

    @property
    def image_type(self) -> str:
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
    def __init__(self, buf: bytes, hdr: Header) -> None:
        self.buffer = buf
        self._hdr = hdr
        self.n_frames = hdr.n_sections
        self._section_length = (hdr.n_floats + hdr.n_ints) * 4
        self._shape = [getattr(hdr, f"n{i.lower()}") for i in hdr.sequence_order]
        self._struct = struct.Struct(f"{hdr.n_ints}i{len(ExtHeaderFrame._fields)}f")

    def frame(self, idx: int) -> ExtHeaderFrame:
        if idx >= self.n_frames:
            raise IndexError(f"index {idx} out of range for {self.n_frames} frames")
        f = self._struct.unpack_from(self.buffer, self._section_length * idx)
        return ExtHeaderFrame(*f[8:])

    def _asdict(self) -> dict:
        return {
            np.unravel_index(i, self._shape): self.frame(i)._asdict()
            for i in range(self.n_frames)
        }
