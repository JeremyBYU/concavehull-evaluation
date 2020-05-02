from os import path
import numpy as np
from pathlib import Path
import math
import logging
import pandas as pd

from concave_evaluation import REALSENSE_DIR

REALSENSE_POINTS_FPATH = path.join(REALSENSE_DIR, 'realsense_points.txt')
REALSENSE_GT_FPATH = path.join(REALSENSE_DIR, 'realsense.geojson')

from concave_evaluation.polylidar_evaluation import run_test as run_test_polylidar
from concave_evaluation.cgal_evaluation import run_test as run_test_cgal
from concave_evaluation.spatialite_evaluation import run_test as run_test_spatialite
from concave_evaluation.postgis_evaluation import run_test as run_test_postgis
from concave_evaluation.helpers import load_polygon
from concave_evaluation.helpers import measure_convexity_simple

logger = logging.getLogger("Concave")


def calc_mean_and_std(timings, l2, alg='polylidar'):
    mean = np.mean(timings)
    std = np.std(timings)
    max_ = np.max(timings)
    return dict(mean=mean, std=std, max=max_, l2=l2, alg=alg)


def run_realsense_tests():
    # Load the point data and the ground truth
    gt_shape, _ = load_polygon(REALSENSE_GT_FPATH)
    points = np.loadtxt(REALSENSE_POINTS_FPATH)
    num_points = int(points.shape[0])

    # Global algorithm parameters
    global_kwargs = dict(n=10, save_poly=True, gt_fpath=REALSENSE_GT_FPATH)
    polylidar_kwargs = dict(minTriangles=1)
    cgal_kwargs = dict()
    spatialite_kwargs = dict(factor=3)
    postgis_kwargs = dict()

    point_density = gt_shape.area / num_points
    alpha = math.sqrt(point_density) * 2
    cgal_kwargs['alpha'] = alpha ** 2
    polylidar_kwargs['alpha'] = alpha
    postgis_kwargs['target_percent'] = gt_shape.area / gt_shape.convex_hull.area

    print(postgis_kwargs['target_percent'] )
    return

    # Final params for this test
    polylidar_kwargs = dict(**global_kwargs, **polylidar_kwargs)
    cgal_kwargs = dict(**global_kwargs, **cgal_kwargs)
    spatialite_kwargs = dict(**global_kwargs, **spatialite_kwargs)
    postgis_kwargs = dict(**global_kwargs, **postgis_kwargs)

    logger.info("Running Polylidar")
    pl_data = run_test_polylidar(REALSENSE_POINTS_FPATH, **polylidar_kwargs)
    cgal_data = l2_norm_cgal = run_test_cgal(REALSENSE_POINTS_FPATH, **cgal_kwargs)
    sl_data = run_test_spatialite(REALSENSE_POINTS_FPATH, **spatialite_kwargs)
    post_data = run_test_postgis(REALSENSE_POINTS_FPATH, **spatialite_kwargs)

    # collapse polylidar subtimings
    timings_pl = np.sum(np.array(pl_data[1]), axis=1)
    pl_data = (None, timings_pl, pl_data[2])

    records = [calc_mean_and_std(timings, error, alg=alg) for (_, timings, error), alg in [
        (pl_data, 'polylidar'), (cgal_data, 'cgal'), (sl_data, 'spatialite'), (post_data, 'postgis')]]

    df = pd.DataFrame.from_records(records)
    print(df)

