from pathlib import Path

import numpy as np
import psutil
import pytest

from mrc._new import DVFile

DATA = Path(__file__).parent / "data"


@pytest.fixture(autouse=True)
def no_files_left_open():
    files_before = {p for p in psutil.Process().open_files() if p.path.endswith("dv")}
    yield
    files_after = {p for p in psutil.Process().open_files() if p.path.endswith("dv")}
    assert files_before == files_after == set()


@pytest.mark.parametrize("fname", DATA.glob("*.dv"), ids=lambda x: x.name)
def test_read_dv(fname):
    assert DVFile.is_supported_file(fname)
    with DVFile(fname) as f:
        assert f.to_xarray(squeeze=False).shape == f.shape
        assert f.ndim == len(f.shape)
        assert isinstance(f.lens, str)
        assert f.hdr.image_type
        assert np.asarray(f).shape == tuple(x for x in f.shape if x > 1)
