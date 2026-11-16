"""Add synthetic selog blocks B and I to a NeXus event file.

Both new blocks share the time axis of raw_data_1/selog/Temp/value_log, with
B taking cos(0.2 * t) and I taking exp(-0.2 * t).
"""

import sys

import h5py
import numpy as np

DEFAULT_FILE = "HIFI00195790.nxs"


def add_groups(filename: str) -> None:
    with h5py.File(filename, "r+") as file:
        selog = file["raw_data_1/selog"]
        time = selog["Temp/value_log/time"][...]

        for name, value in (
            ("B", np.cos(0.2 * time)),
            ("I", np.exp(-0.2 * time)),
        ):
            value_log = selog.create_group(name).create_group("value_log")
            value_log.create_dataset("time", data=time)
            value_log.create_dataset("value", data=value.astype(time.dtype))


if __name__ == "__main__":
    add_groups(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE)
