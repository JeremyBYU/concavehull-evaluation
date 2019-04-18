import numpy as np
from shapely.geometry import LineString
import matplotlib.pyplot as plt

from concave_evaluation.helpers import plot_line


def create_line_strings(result):
    num_lines = result.shape[0]
    all_lines = []
    for i in range(num_lines):
        np_line = result[i,:]
        line = LineString([(np_line[0], np_line[1]),(np_line[2], np_line[3])])
        all_lines.append(line)

    return all_lines


def run_test(point_fpath, n=1, **kwargs):
    result_file = "./test_fixtures/results/cgal/output.csv"
    result = np.loadtxt(result_file)
    all_lines = create_line_strings(result)

    fig = plt.figure(1, figsize=(5,5), dpi=180)
    ax = fig.add_subplot(111)
    for line in all_lines:
        plot_line(ax, line)
    plt.show()




    