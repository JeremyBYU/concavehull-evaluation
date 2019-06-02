import random
import logging
import pickle
from functools import partial
import json
from os import path
from pathlib import Path
import multiprocessing as mp

import click
# Monkey patch Click to show default values for all commands
orig_init = click.core.Option.__init__

def new_init(self, *args, **kwargs):
    orig_init(self, *args, **kwargs)
    self.show_default = True
click.core.Option.__init__ = new_init


import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
import hvplot
import hvplot.pandas

from concave_evaluation import DEFAULT_SHAPE_FILE, DEFAULT_SAVED_RANDOM_POLYS
from concave_evaluation.helpers import (round_dict, measure_concavity, PythonLiteralOption, plot_poly_make_fig,
                                        get_max_bounds_polys, plot_poly, scale_axes, load_polygon, measure_convexity_simple)
from concave_evaluation.test_generation.polygen import generatePolygon
from concave_evaluation.test_generation import random_points_within_mp, scale_poly, holes_poly, random_points_within
from concave_evaluation.scripts.testrunner import evaluate

logger = logging.getLogger("Concave")


# Set the random seeds for determinism
random.seed(0)
np.random.seed(0)

@click.group()
def cli():
    """Generates data and run benchmarks for concave algorithms"""
    pass

# Add test runner commands for each concave hull implementation
cli.add_command(evaluate)


@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/unprocessed/mi_glove_mercator.geojson')
@click.option('-o', '--output-file', type=click.Path(exists=False), default=DEFAULT_SHAPE_FILE)
@click.option('-m', '--max-size', type=float, default=200, required=False,
              show_default=True, help="Max Size of any dimension")
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def scale(input_file, output_file, max_size, plot):
    """Scales a polygon be within the max_size provided. Keeps aspect ratio"""
    poly, poly_geojson = load_polygon(input_file)
    poly = scale_poly(poly)
    assert poly.is_valid
    poly_geojson['geometry'] = poly.__geo_interface__
    with open(output_file, 'w') as outfile:  
        json.dump(poly_geojson, outfile, indent=2)

    if plot:
        plot_poly_make_fig(poly)

@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default=DEFAULT_SHAPE_FILE)
@click.option('-o', '--output-file', type=click.Path(exists=False), default='test_fixtures/gt_shapes/migloveholes.geojson')
@click.option('-nh', '--number-holes', type=int, default=10, required=False,
              show_default=True, help="Number of holes")
@click.option('-hr', '--hole-radius', type=float, default=10.0, required=False,
              show_default=True, help="Hole Radius")
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def holes(input_file, output_file, number_holes, hole_radius, plot):
    """Generates holes inside the polygon provided    
    """
    poly, poly_geojson = load_polygon(input_file)
    poly = holes_poly(poly, num_holes=number_holes, hole_radius=hole_radius)
    assert poly.is_valid
    poly_geojson['geometry'] = poly.__geo_interface__
    with open(output_file, 'w') as outfile:  
        json.dump(poly_geojson, outfile, indent=2)

    if plot:
        plot_poly_make_fig(poly)

    
@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default=DEFAULT_SHAPE_FILE)
# @click.option('-pd', '--point-densities', cls=PythonLiteralOption, default="[0.1, 0.5, 1.0, 1.5, 2.0]", required=False,
#               show_default=True, help="Point Density to Generate of Polygon.")
@click.option('-np', '--number-points', cls=PythonLiteralOption, default="[2000, 4000, 8000, 16000, 32000, 64000]", required=False,
              show_default=True, help="Number of points in polygon")           
@click.option('-d', '--distribution', type=click.Choice(['uniform']), default='uniform')
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default='test_fixtures/points')
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def points(input_file, number_points, distribution, save_directory, plot):
    """Generates random points within the polygon provided    
    """
    fname = Path(input_file).stem
    poly, poly_geojson = load_polygon(input_file)
    poly_area = poly.area
    records = []
    for num_points in number_points:
        # num_points = int(poly_area * point_density)
        points = random_points_within_mp(poly, num_points, processes=4)
        record = dict(points=points, np=num_points)
        records.append(record)
        fname_record = "{}_{}.csv".format(fname, num_points)
        fpath_record = path.join(save_directory, fname_record)
        np.savetxt(fpath_record, points)
    if plot:
        for record in records:
            points = record['points']
            df = pd.DataFrame(points, columns=["x", "y"])
            scatter_plot = df.hvplot.scatter("x", "y", hover=False, width=500, height=500, title="NP={}".format(record['np']))
            hvplot.show(scatter_plot)
            input("Enter to Continue")


@click.option('-nv', '--number-vertices', cls=PythonLiteralOption, default="[100, 101, 1]", required=False,
              help="Number of Vertices to generate for polygon")
@click.option('-pr', '--polygon-radius', cls=PythonLiteralOption, default="[100, 101, 1]", required=False,
              help="Polygon Radius")
@click.option('-pi', '--polygon-irregularity', cls=PythonLiteralOption, default="[0.1, 0.8, 0.1]", required=False,
              help="Jumps in angle")
@click.option('-ps', '--polygon-spikeness', cls=PythonLiteralOption, default="[0.1, 0.8, 0.1]", required=False,
              help="Jump in radius")
@click.option('-r', '--repeat', default=1, required=False,
              help="How many times to repeatedly geneate a polygon of the same parameters")
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
@click.option('-pp', '--plot-pickle', type=click.Path(exists=True), required=False)
@click.option('-o', '--output', type=click.Path(exists=False), default='test_fixtures/generated/polygons.pkl')
@cli.command()
def polygon(
        number_vertices, polygon_radius, polygon_irregularity, polygon_spikeness, repeat, plot, plot_pickle, output):
    """Generates random polygons 
    """
    print("Arguments: ", number_vertices, polygon_radius, polygon_irregularity, polygon_spikeness)

    START_X = 100
    START_Y = 100
    starting_poly_list = []
    poly_params = []
    # Either generate the polygons or load them from a serialized pickle file
    if plot_pickle:
        starting_poly_list, poly_params = pickle.load(open(plot_pickle, 'rb'))
        plot = True
    else:
        for nv in range(*number_vertices):
            for pr in np.arange(*polygon_radius):
                for pi in np.arange(*polygon_irregularity):
                    for ps in np.arange(*polygon_spikeness):
                        for r in np.arange(repeat):
                            poly_param = round_dict(dict(nv=nv, pr=pr, pi=pi, ps=ps, r=r))
                            try:
                                poly = generatePolygon(START_X, START_Y, pr, pi, ps, nv)
                                convexity = measure_convexity_simple(poly)
                                starting_poly_list.append(poly)
                                poly_param['convexity'] = convexity
                                poly_params.append(poly_param)
                            except Exception:
                                logger.exception("Could not generate polygon with these params: %r", poly_param)
                        
        pickle.dump((starting_poly_list, poly_params), open(output, "wb"))
    print("Generated/Loaded {} polygons".format(len(poly_params)))
    if plot:
        map_bounds = get_max_bounds_polys(starting_poly_list)
        fig = plt.figure(figsize=(5, 5))
        ax = plt.subplot(1, 1, 1)

        def update(frame):
            poly = starting_poly_list[frame]
            params = poly_params[frame]
            ax.clear()
            plot_poly(poly, ax)
            ax.set_title("Params {}".format(params))
            scale_axes([map_bounds[0], map_bounds[2]], [map_bounds[1], map_bounds[3]], ax)
            return fig,
        anim = FuncAnimation(fig, update, frames=len(poly_params), interval=500, repeat=False)
        anim.save("random_polygons.mp4")
        plt.show()


def seed_np():
    seed = mp.current_process()._identity[0]
    return np.random.seed(seed)

@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default=DEFAULT_SAVED_RANDOM_POLYS)
# @click.option('-pd', '--point-densities', cls=PythonLiteralOption, default="[0.1, 0.5, 1.0, 1.5, 2.0]", required=False,
#               show_default=True, help="Point Density to Generate of Polygon.")
@click.option('-np', '--number-points', cls=PythonLiteralOption, default="[2000]", required=False,
              show_default=True, help="Number of points in polygon")           
@click.option('-d', '--distribution', type=click.Choice(['uniform']), default='uniform')
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default='test_fixtures/points')
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def points_pkl(input_file, number_points, distribution, save_directory, plot):
    """Generates random points in polygons provided by a pickle file
    """
    polys, poly_params = pickle.load(open(input_file, 'rb'))
    fname = Path(input_file).stem
    records = []
    # polys = polys[:2]
    num_polys = len(polys)

    for num_points in number_points:
        with mp.Pool(processes=6, initializer=seed_np, initargs=()) as pool:
            for i, poly_points in enumerate(tqdm(pool.imap(partial(random_points_within, num_points=num_points, seed=None), polys), total=num_polys)):
                records.append(dict(points=poly_points, poly_param=poly_params[i], np=num_points))
        output = path.join(save_directory, "{}_{}.pkl".format(fname,num_points))
        pickle.dump(records, open(output, "wb"))


    if plot:
        for record in records:
            points = record['points']
            df = pd.DataFrame(points, columns=["x", "y"])
            scatter_plot = df.hvplot.scatter("x", "y", hover=False, width=500, height=500, title="NP={}".format(record['np']))
            hvplot.show(scatter_plot)
            input("Enter to Continue")


@cli.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default=DEFAULT_SAVED_RANDOM_POLYS)
# @click.option('-pd', '--point-densities', cls=PythonLiteralOption, default="[0.1, 0.5, 1.0, 1.5, 2.0]", required=False,
#               show_default=True, help="Point Density to Generate of Polygon.")
@click.option('-o', '--output-file', type=click.Path(exists=False), default='test_fixtures/generated/polygons_holes.pkl')
@click.option('-nh', '--number-holes', type=int, default=5, required=False,
              show_default=True, help="Number of holes")
@click.option('-hr', '--hole-radius', type=float, default=7.5, required=False,
              show_default=True, help="Hole Radius")
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def polygon_holes(input_file, output_file, number_holes, hole_radius, plot):
    """Generates holes inside polygons given by a list of polygons from a pickle file
    """
    polys, poly_params = pickle.load(open(input_file, 'rb'))
    polys_hole = []
    # polys = polys[:100]
    num_polys = len(polys)
    poly_params = [dict(item, **{'holes': True}) for item in poly_params]

    with mp.Pool(processes=6, initializer=seed_np, initargs=()) as pool:
        for i, poly_hole in enumerate(tqdm(pool.imap(partial(holes_poly, num_holes=number_holes, hole_radius=hole_radius), polys), total=num_polys)):
            polys_hole.append(poly_hole)

    pickle.dump((polys_hole, poly_params), open(output_file, "wb"))


    if plot:
        map_bounds = get_max_bounds_polys(polys_hole)
        fig = plt.figure(figsize=(5, 5))
        ax = plt.subplot(1, 1, 1)

        def update(frame):
            poly = polys_hole[frame]
            params = poly_params[frame]
            ax.clear()
            plot_poly(poly, ax, plot_holes=True)
            ax.set_title("Params {}".format(params))
            scale_axes([map_bounds[0], map_bounds[2]], [map_bounds[1], map_bounds[3]], ax)
            return fig,
        anim = FuncAnimation(fig, update, frames=len(polys), interval=500, repeat=False)
        anim.save("random_polygons.mp4")
        plt.show()

if __name__ == "__main__":
    cli()
