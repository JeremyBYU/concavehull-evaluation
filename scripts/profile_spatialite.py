"""

Run with Google pprof. You can use the python library pprof

python -m yep -v ./scripts/profile_polylidar.py
Profiling shows that 93% of the time is spent in the CascadedUnion. (Unioning hundreds of thousands of triangles)
A small but other significant amount of time is spent in triangulation.

Spatialite is running as an in-memory database.
"""
import math
import numpy as np
from concave_evaluation.spatialite_evaluation import run_test
from concave_evaluation import DEFAULT_TEST_FILE_HARD


def main(fpath=DEFAULT_TEST_FILE_HARD):
    polygon, timings, l2 = run_test(fpath, save_poly=False, n=1, factor=3.0)


if __name__ == "__main__":
    main()