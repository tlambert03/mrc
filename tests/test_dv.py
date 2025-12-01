from pathlib import Path

import numpy as np
import psutil
import pytest

from mrc import DVFile, imread

DATA = Path(__file__).parent / "data"
IMAGES = [f for f in DATA.iterdir() if f.suffix in {".dv", ".r3d", ".otf"}]


@pytest.fixture(autouse=True)
def no_files_left_open():
    files_before = {p for p in psutil.Process().open_files() if p.path.endswith("dv")}
    yield
    files_after = {p for p in psutil.Process().open_files() if p.path.endswith("dv")}
    assert files_before == files_after == set()


@pytest.mark.parametrize("fname", IMAGES, ids=lambda x: x.name)
def test_read_dv(fname):
    assert DVFile.is_supported_file(fname)
    arr = imread(fname)

    with DVFile(fname) as f:
        assert f.to_xarray(squeeze=False).shape == f.shape
        assert f.ndim == len(f.shape)
        assert isinstance(f.lens, str)
        assert f.hdr.image_type

        np.testing.assert_array_equal(f.to_xarray(delayed=True, squeeze=True), arr)
        assert arr.shape == tuple(x for x in f.shape if x > 1)

        if f.path.endswith("otf"):
            assert np.iscomplexobj(arr)


@pytest.mark.parametrize("fname", IMAGES[:4], ids=lambda x: x.name)
def test_dual_read(fname):
    with DVFile(fname) as f:
        arr = imread(fname)
        a1 = f.asarray()
    assert np.all(a1 == arr)
