"""Plots how the number of points influences - triangles, edges, and boundary edges
Key takeaway, boundary edges are very very small
Returns:
    [type] -- [description]
"""

import math
import numpy as np
from polylidar import extractPlanesAndPolygons
import pandas as pd
import matplotlib.pyplot as plt 
import seaborn as sns
def gen_points(xmin=0, xmax=10, xstep=1, ymin=0, ymax=10, ystep=1):
    X, Y = np.mgrid[xmin:xmax:xstep, ymin:ymax:ystep]
    positions = np.vstack([X.ravel(), Y.ravel()])
    positions = positions.transpose().copy()
    return positions

n_val_good_giant=[25_000, 50_000, 100_000, 200_000, 400_000, 800_000, 1_600_000, 3_200_000]
n_val_test=[25_000, 50_000, 100_000]
def polylidar_edgegrowth(reps=3, n_val=n_val_test):
    records = []
    polylidar_kwargs = dict(xyThresh=0.0, alpha=2.0)
    for n in n_val:
        valmax = int(math.sqrt(n))
        points = gen_points(xmax=valmax, ymax=valmax)
        true_n = points.shape[0]
        delaunay, planes, polygons = extractPlanesAndPolygons(points, **polylidar_kwargs)
        hull_size = len(delaunay.hull_tri)
        triangles = len(delaunay.triangles) / 3
        edges = len(delaunay.triangles)
        borderedges = len(polygons[0].shell)
        records.append(dict( n=true_n, n_copy=true_n, triangles=triangles, edges=edges, borderedges=borderedges, hullsize=hull_size))
    return records


def main():
    records = polylidar_edgegrowth(reps=3, n_val=n_val_good_giant)
    df = pd.DataFrame.from_records(records)
    df = df[['n', 'n_copy', 'triangles', 'edges', 'borderedges', 'hullsize']]
    df_m = pd.melt(df, id_vars=['n'], value_vars=['triangles', 'edges', 'borderedges', 'hullsize','n_copy'])
    print(df_m)
    sns.lineplot(x="n", y="value",
                hue="variable",
                data=df_m)

    # print(df)
    plt.show()
    result = df['edges'] / df['borderedges']
    print(result)
    # df.to_csv("./analysis/polylidar_complexity.csv", index=False)


if __name__ == "__main__":
    main()
