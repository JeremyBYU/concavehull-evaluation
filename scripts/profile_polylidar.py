import math
import numpy as np
from polylidar import extractPlanesAndPolygons, extractPolygonsAndTimings
def gen_points(xmin=0, xmax=10, xstep=1, ymin=0, ymax=10, ystep=1):
    X, Y = np.mgrid[xmin:xmax:xstep, ymin:ymax:ystep]
    positions = np.vstack([X.ravel(), Y.ravel()])
    positions = positions.transpose().copy()
    return positions


def main(n=10_000_000):
    valmax = int(math.sqrt(n))
    polylidar_kwargs = dict(xyThresh=0.0, alpha=2.0)
    points = gen_points(xmax=valmax, ymax=valmax)
    polygons, times = extractPolygonsAndTimings(points, **polylidar_kwargs)
    print(times)


if __name__ == "__main__":
    main()