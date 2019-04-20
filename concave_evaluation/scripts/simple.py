import random

import logging
import pickle
import json
from os import path
from pathlib import Path
logger = logging.getLogger("Concave")


import click
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from concave_evaluation.helpers import (round_dict, measure_concavity, PythonLiteralOption, plot_poly_make_fig,
                                        get_max_bounds_polys, plot_poly, scale_axes, load_polygon)
from concave_evaluation.test_generation.polygen import generatePolygon
from concave_evaluation.test_generation import random_points_within, scale_poly, holes_poly


# All the algorithmic implementations for generating a concave shape from a point set
from concave_evaluation.polylidar_evaluation import run_test as run_test_polylidar
from concave_evaluation.cgal_evaluation import run_test as run_test_cgal
from concave_evaluation.spatialite_evaluation import run_test as run_test_spatialite
from concave_evaluation.postgis_evaluation import run_test as run_test_postgis, DEFAULT_PG_CONN

import pandas as pd
import hvplot
import hvplot.pandas


random.seed(0)
np.random.seed(0)

@click.group()
def cli():
    """Generates data and run benchmarks for concave algorithms"""

@cli.command()
def generate_fixtures():
    print("Hello")


@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/points/mi_glove_np_2000.csv')
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default='test_fixtures/results/polylidar')
@click.option('-xy', '--xy-thresh', default=10.0)
@click.option('-a', '--alpha', default=0.0)
@click.option('-n', '--number-iter', default=1)
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def polylidar(input_file, save_directory, alpha, xy_thresh, number_iter, plot):
    polygons, time_ms = run_test_polylidar(input_file, save_dir=save_directory, alpha=alpha, xyThresh=xy_thresh, n=number_iter)
    print(time_ms)
    if plot:
        pass


@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/points/mi_glove_np_2000.csv')
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default='test_fixtures/results/cgal')
@click.option('-a', '--alpha', default=100.0)
@click.option('-n', '--number-iter', default=1)
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def cgal(input_file, save_directory, alpha, number_iter, plot):
    run_test_cgal(input_file, save_directory, alpha=alpha, n=number_iter)

@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/points/mi_glove_np_2000.csv')
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default='test_fixtures/results/spatialite')
@click.option('-db', '--database', type=click.Path(exists=True), default='test_fixtures/db/spatialite.db')
@click.option('-f', '--factor', default=3.0)
@click.option('-n', '--number-iter', default=1)
def spatialite(input_file, save_directory, database, factor, number_iter):
    run_test_spatialite(input_file, save_directory, database, factor=factor, n=number_iter)


@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/points/mi_glove_np_2000.csv')
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default='test_fixtures/results/postgis')
@click.option('-db', '--database', default=DEFAULT_PG_CONN)
@click.option('-tp', '--target-percent', default=0.99)
@click.option('-n', '--number-iter', default=1)
def postgis(input_file, save_directory, database, target_percent, number_iter):
    run_test_postgis(input_file, save_directory, database, target_percent=target_percent, n=number_iter)


@click.option('-nv', '--number-vertices', cls=PythonLiteralOption, default="[100, 101, 1]", required=False,
              help="Number of Vertices to generate for polygon")
@click.option('-pr', '--polygon-radius', cls=PythonLiteralOption, default="[1000, 1001, 1]", required=False,
              help="Number of Vertices to generate for polygon")
@click.option('-pi', '--polygon-irregularity', cls=PythonLiteralOption, default="[0.1, 0.5, 0.1]", required=False,
              help="Number of Vertices to generate for polygon")
@click.option('-ps', '--polygon-spikeness', cls=PythonLiteralOption, default="[0.1, 0.5, 0.1]", required=False,
              help="Number of Vertices to generate for polygon")
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
@click.option('-pp', '--plot-pickle', type=click.Path(exists=True), required=False)
@click.option('-o', '--output', type=click.Path(exists=False), default='test_fixtures/generated/polygons.pkl')
@cli.command()
def polygon(
        number_vertices, polygon_radius, polygon_irregularity, polygon_spikeness, plot, plot_pickle, output):
    print("Arguments: ", number_vertices, polygon_radius, polygon_irregularity, polygon_spikeness)

    START_X = 3000
    START_Y = 3000
    starting_poly_list = []
    poly_params = []
    concavity_list = []
    # Either generate the polygons or load them from a serialized pickle file
    if plot_pickle:
        starting_poly_list, poly_params, concavity_list = pickle.load(open(plot_pickle, 'rb'))
        plot = True
    else:
        for nv in range(*number_vertices):
            for pr in np.arange(*polygon_radius):
                for pi in np.arange(*polygon_irregularity):
                    for ps in np.arange(*polygon_spikeness):
                        poly_param = round_dict(dict(nv=nv, pr=pr, pi=pi, ps=ps))
                        try:
                            poly = generatePolygon(START_X, START_Y, pr, pi, ps, nv)
                            poly_params.append(poly_param)
                            concavity_list.append(measure_concavity(poly))
                            starting_poly_list.append(poly)
                        except Exception:
                            logger.exception("Could not generate polygon with these params: %r", poly_param)
                        
        pickle.dump((starting_poly_list, poly_params, concavity_list), open(output, "wb"))
    print("Generated/Loaded {} polygons".format(len(poly_params)))
    if plot:
        map_bounds = get_max_bounds_polys(starting_poly_list)
        fig = plt.figure(figsize=(5, 5))
        ax = plt.subplot(1, 1, 1)

        def update(frame):
            poly = starting_poly_list[frame]
            params = poly_params[frame]
            concavity = concavity_list[frame]
            ax.clear()
            plot_poly(poly, ax)
            ax.set_title("Params {} \n Concavity: {:.2f}".format(params,concavity))
            scale_axes([map_bounds[0], map_bounds[2]], [map_bounds[1], map_bounds[3]], ax)
            return fig,
        anim = FuncAnimation(fig, update, frames=len(poly_params), interval=500, repeat=False)
        anim.save("random_polygons.mp4")
        plt.show()


@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/unprocessed/mi_glove_mercator.geojson')
@click.option('-o', '--output-file', type=click.Path(exists=False), default='test_fixtures/gt_shapes/mi_glove.geojson')
@click.option('-m', '--max-size', type=float, default=200, required=False,
              show_default=True, help="Max Size of any dimension")
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def scale(input_file, output_file, max_size, plot):
    poly, poly_geojson = load_polygon(input_file)
    poly = scale_poly(poly)
    assert poly.is_valid
    poly_geojson['geometry'] = poly.__geo_interface__
    with open(output_file, 'w') as outfile:  
        json.dump(poly_geojson, outfile, indent=2)

    if plot:
        plot_poly_make_fig(poly)

@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/gt_shapes/mi_glove.geojson')
@click.option('-o', '--output-file', type=click.Path(exists=False), default='test_fixtures/gt_shapes/mi_glove_holes.geojson')
@click.option('-nh', '--number-holes', type=int, default=10, required=False,
              show_default=True, help="Number of holes")
@click.option('-hr', '--hole-radius', type=float, default=5.0, required=False,
              show_default=True, help="Hole Radius")
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def holes(input_file, output_file, number_holes, hole_radius, plot):
    poly, poly_geojson = load_polygon(input_file)
    poly = holes_poly(poly, num_holes=number_holes, hole_radius=hole_radius)
    assert poly.is_valid
    poly_geojson['geometry'] = poly.__geo_interface__
    with open(output_file, 'w') as outfile:  
        json.dump(poly_geojson, outfile, indent=2)

    if plot:
        plot_poly_make_fig(poly)

    
@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/mi_glove.geojson')
# @click.option('-pd', '--point-densities', cls=PythonLiteralOption, default="[0.1, 0.5, 1.0, 1.5, 2.0]", required=False,
#               show_default=True, help="Point Density to Generate of Polygon.")
@click.option('-np', '--number-points', cls=PythonLiteralOption, default="[2000, 10000, 20000, 30000, 40000]", required=False,
              show_default=True, help="Number of points in polygon")           
@click.option('-d', '--distribution', type=click.Choice(['uniform']), default='uniform')
@click.option('-od', '--output-directory', type=click.Path(exists=True), default='test_fixtures/points')
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def points(input_file, number_points, distribution, save_directory, plot):

    fname = Path(input_file).stem
    poly, poly_geojson = load_polygon(input_file)
    poly_area = poly.area
    records = []
    for num_points in number_points:
        # num_points = int(poly_area * point_density)
        points = random_points_within(poly, num_points)
        record = dict(points=points, np=num_points)
        records.append(record)
        fname_record = "{}_np_{}.csv".format(fname, num_points)
        fpath_record = path.join(save_directory, fname_record)
        np.savetxt(fpath_record, points)
    if plot:
        for record in records:
            points = record['points']
            df = pd.DataFrame(points, columns=["x", "y"])
            scatter_plot = df.hvplot.scatter("x", "y", hover=False, width=500, height=500, title="NP={}".format(record['np']))
            hvplot.show(scatter_plot)
            input("Enter to Continue")


if __name__ == "__main__":
    cli()
