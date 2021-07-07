from pathlib import Path

from mrc import imread

dv_file = Path(__file__).parent / "toxo.dv"


def test_reader():
    array = imread(str(dv_file))
    assert array.shape == (2, 17, 128, 128)
    assert array.Mrc.header.dvid == -16224
