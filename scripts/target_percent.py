from os import path, listdir
from concave_evaluation.helpers import load_polygon
from concave_evaluation import DEFAULT_GT_DIR, DEFAULT_PG_SAVE_DIR
from pprint import pprint

import pandas as pd


def main():
    gt_files = listdir(DEFAULT_GT_DIR)
    gt_files = sorted(gt_files)
    cs_files = listdir(DEFAULT_PG_SAVE_DIR)
    cs_files = sorted(cs_files)
    records = []
    gt_ch_map = dict()
    for gt_file in gt_files:
        
        gt_fpath = path.join(DEFAULT_GT_DIR, gt_file)
        gt_poly, _ = load_polygon(gt_fpath)
        gt_area_convex = gt_poly.convex_hull.area
        gt_area = gt_poly.area
        target_percent = gt_area / gt_area_convex
        records.append(dict(shape=gt_file, target_percent=target_percent))
        gt_key = gt_file.split('.')[0]
        gt_ch_map[gt_key] = gt_area_convex
    df = pd.DataFrame.from_records(records)
    # What we should be targeting
    print("Target Percent")
    print(df)
    print()
    # What we actually got
    # Results show that PostGIS does not obtain the target percent requested
    # Documentation online indicates that means it has "given" up and can no longer reduce area
    records = []
    for cs_file in cs_files:
        cs_fpath = path.join(DEFAULT_PG_SAVE_DIR, cs_file)
        cs_poly, _ = load_polygon(cs_fpath)
        cs_poly_area = cs_poly.area
        gt_key = cs_file.split('_')[0]
        gt_area_convex = gt_ch_map.get(gt_key)
        if gt_area_convex:
            actual_percent_reduction = cs_poly_area / gt_area_convex
            records.append(dict(shape=cs_file, percent_reduction=actual_percent_reduction))
    df = pd.DataFrame.from_records(records)
    print("Actual Percent Reduction")
    print(df)
if __name__ == "__main__":
    main()