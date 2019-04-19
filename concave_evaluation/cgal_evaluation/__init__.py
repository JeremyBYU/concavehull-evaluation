from os import path

import numpy as np
from shapely.geometry import LineString
import matplotlib.pyplot as plt

from concave_evaluation.helpers import plot_line, lines_to_polygon, plot_poly_make_fig, save_shapely, modified_fname

THIS_DIR = path.dirname(__file__)
CGAL_BIN = path.join(THIS_DIR, '..', '..', 'cpp', 'cgal', 'bin', 'cgal_alpha')


def create_line_strings(result):
    num_lines = result.shape[0]
    all_lines = []
    for i in range(num_lines):
        np_line = result[i,:]
        line = LineString([(np_line[0], np_line[1]),(np_line[2], np_line[3])])
        all_lines.append(line)

    return all_lines


def run_test(point_fpath, save_dir="./test_fixtures/results/cgal", n=1, alpha=10, **kwargs):
    result_file = "./test_fixtures/results/cgal/output.csv"
    result = np.loadtxt(result_file)

    all_lines = create_line_strings(result)
    union_lines_poly = lines_to_polygon(all_lines)

    save_fname, _ = modified_fname(point_fpath, save_dir)
    save_shapely(union_lines_poly, save_fname, alg='cgal')

    # plot_poly_make_fig(union_lines_poly)
    # fig = plt.figure(1, figsize=(5,5), dpi=180)
    # ax = fig.add_subplot(111)
    # for index, line in enumerate(all_lines):
    #     plot_line(ax, line, index)
    # plt.show()

    




    