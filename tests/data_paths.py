import os
from pathlib import Path

pwd = Path(os.path.abspath(__file__))
data_dir = Path(pwd.parent, "data_files")

# test nexus data file
FILE = str(data_dir / "HIFI00195790.nxs")

# test filter file generated from `data_files/filters.py`
FILTER = str(data_dir / "load_filter.json")
