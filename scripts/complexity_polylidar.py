import math
import numpy as np
import pandas as pd
from polylidar import extractPlanesAndPolygons, extractPolygonsAndTimings

def gen_points(xmin=0, xmax=10, xstep=1, ymin=0, ymax=10, ystep=1):
    X, Y = np.mgrid[xmin:xmax:xstep, ymin:ymax:ystep]
    positions = np.vstack([X.ravel(), Y.ravel()])
    positions = positions.transpose().copy()
    return positions


n_val_bad=[25_000, 50_000, 100_000, 200_000, 400_000, 500_000, 650_000, 800_000, 1_000_000, 1_200_000, 1_600_000, 2_000_000, 2_500_000, 3_200_000, 6_400_000]
n_val_good=[25_000, 50_000, 100_000, 200_000, 400_000, 800_000, 1_600_000, 3_200_000, 6_400_000, 12_800_000, 25_600_000]
n_val_test=[25_000, 50_000, 100_000]
def polylidar_timings(reps=3, n_val=n_val_good):
    records = []
    polylidar_kwargs = dict(xyThresh=0.0, alpha=2.0)
    for n in n_val:
        valmax = int(math.sqrt(n))
        points = gen_points(xmax=valmax, ymax=valmax)
        true_n = points.shape[0]
        for j in range(reps):
            polygons, times = extractPolygonsAndTimings(points, **polylidar_kwargs)
            records.append(dict( n=true_n, delaunay=times[0], region=times[1], polygon=times[2]))
    return records


def main():
    records = polylidar_timings(reps=3, n_val=n_val_test)
    df = pd.DataFrame.from_records(records)
    df = df[['n', 'delaunay', 'region', 'polygon']]
    df.to_csv("./analysis/polylidar_complexity.csv", index=False)


if __name__ == "__main__":
    main()

# records = union_timings()