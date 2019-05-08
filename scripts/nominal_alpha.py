from os import path, listdir
import math
from concave_evaluation.helpers import load_polygon
from concave_evaluation import DEFAULT_GT_DIR

import pandas as pd

num_points = [2000, 4000, 8000, 16000, 32000, 64000]

def main():
    gt_files = listdir(DEFAULT_GT_DIR)
    records = []
    for gt_file in gt_files:
        gt_fpath = path.join(DEFAULT_GT_DIR, gt_file)
        gt_poly, _ = load_polygon(gt_fpath)
        gt_area = gt_poly.area
        for n_points in num_points:
            point_density = gt_area / n_points
            alpha = math.sqrt(point_density) * 2
            records.append(dict(shape=gt_file, n=n_points, point_density=point_density, alpha=alpha))
    df = pd.DataFrame.from_records(records)
    print(df)
if __name__ == "__main__":
    main()