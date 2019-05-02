from os import path, listdir
from concave_evaluation.helpers import load_polygon
from concave_evaluation import DEFAULT_GT_DIR

import pandas as pd


def main():
    gt_files = listdir(DEFAULT_GT_DIR)
    records = []
    for gt_file in gt_files:
        gt_fpath = path.join(DEFAULT_GT_DIR, gt_file)
        gt_poly, _ = load_polygon(gt_fpath)
        gt_area_convex = gt_poly.convex_hull.area
        gt_area = gt_poly.area
        target_percent = gt_area / gt_area_convex
        records.append(dict(shape=gt_file, target_percent=target_percent))
    df = pd.DataFrame.from_records(records)
    print(df)
if __name__ == "__main__":
    main()