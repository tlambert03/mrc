import os
from pathlib import Path

import pytest

README = Path(__file__).parent.parent / "README.md"
SAMPLE = Path(__file__).parent / "data" / "example5dOMX.dv"


@pytest.mark.skipif(os.name == "nt", reason="paths annoying on windows")
def test_readme():
    code = README.read_text().split("```python")[1].split("```")[0]
    code = code.replace("some_file.dv", str(SAMPLE.absolute()))
    exec(code)
