from os import path
import subprocess
import logging
import ast

import numpy as np
from shapely.geometry import LineString
import matplotlib.pyplot as plt
logger = logging.getLogger("Concave")

from concave_evaluation.helpers import plot_line, lines_to_polygon, plot_poly_make_fig, save_shapely, modified_fname, load_polygon, evaluate_l2
from concave_evaluation import DEFAULT_CGAL_SAVE_DIR, CGAL_BIN


def create_line_strings(result):
    num_lines = result.shape[0]
    all_lines = []
    for i in range(num_lines):
        np_line = result[i,:]
        line = LineString([(np_line[0], np_line[1]),(np_line[2], np_line[3])])
        all_lines.append(line)

    return all_lines


def launch_cgal(point_fpath, edge_fpath, alpha=10, n=1):
    args = [CGAL_BIN, point_fpath, edge_fpath, str(alpha), str(n)]
    # print(args)
    timings = []
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, encoding='utf-8')
        if result.returncode == 0:
            # Success! Stdout will be an array of the timings, parse it with python AST
            timings = ast.literal_eval(result.stdout)
        else:
            raise ValueError("CGAL binary returned error")
    except Exception:
        logger.exception("Error launching cgal with args %r", args)
    return timings

def run_test(point_fpath, save_dir=DEFAULT_CGAL_SAVE_DIR, n=1, alpha=10, save_poly=True, gt_fpath=None, **kwargs):
    # If we already passed in a numpy array, no need to load from file
    if isinstance(point_fpath, np.ndarray):
        points = point_fpath
        # create a temporary file and write points to it, CGAL runner needs a file to operate
        point_fpath = path.join(save_dir, 'temp_points.csv')
        np.savetxt(point_fpath, points)
    else:
        points = np.loadtxt(point_fpath)

    save_fname, test_name = modified_fname(point_fpath, save_dir)
    edge_fpath = path.join(save_dir, 'output.csv')
    # This launches the CGAL alpha shape C++ binary with appropriate parameters
    timings = launch_cgal(point_fpath, edge_fpath, alpha=alpha, n=n)

    # Load the edges file that CGAL created of the polygon
    edges = np.loadtxt(edge_fpath)

    # convert these edges to line strings and eventually to a polygon and save
    # Note that this process is not timed! Nor does this process have anything to do
    # with Polylidar and its polygon creation algorithm.
    all_lines = create_line_strings(edges)
    union_lines_poly = lines_to_polygon(all_lines)
    if save_poly:
        if (not union_lines_poly.is_valid):
            logger.error("CGAL polygon not valid %r", point_fpath)
        save_shapely(union_lines_poly, save_fname, alg='cgal')

    l2_norm = np.NaN
    # Evaluate L2 Norm if we have the ground truth data
    # if the path is a string (nominal) then load the polygon
    if isinstance(gt_fpath, str):
        gt_shape, _ = load_polygon(gt_fpath)
        l2_norm = evaluate_l2(gt_shape, union_lines_poly)
    elif gt_fpath is not None:
        gt_shape = gt_fpath
        l2_norm = evaluate_l2(gt_shape, union_lines_poly)

    # fig = plt.figure(1, figsize=(5,5), dpi=180)
    # ax = fig.add_subplot(111)
    # ax.scatter(points[:, 0], points[:, 1])
    # for index, line in enumerate(all_lines):
    #     plot_line(ax, line, index=None)
    # plt.show()

    return union_lines_poly, timings, l2_norm

    




    