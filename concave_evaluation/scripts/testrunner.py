"""Click commands to launch test runners for the concave algorithms
"""
import json
from pathlib import Path
from os import listdir, path
import math
import pickle
import click
import pandas as pd
import numpy as np
import logging
from tqdm import tqdm

# All the algorithmic implementations for generating a concave shape from a point set
from concave_evaluation import (DEFAULT_PG_CONN, DEFAULT_SPATIALITE_DB, DEFAULT_TEST_FILE, DEFAULT_RESULTS_SAVE_DIR,
                                DEFAULT_PG_SAVE_DIR, DEFAULT_PL_SAVE_DIR, DEFAULT_SL_SAVE_DIR, DEFAULT_CGAL_SAVE_DIR,
                                GENERATED_DIR, POINTS_DIR, ALPHABET_DIR)
from concave_evaluation.polylidar_evaluation import run_test as run_test_polylidar
from concave_evaluation.cgal_evaluation import run_test as run_test_cgal
from concave_evaluation.spatialite_evaluation import run_test as run_test_spatialite
from concave_evaluation.postgis_evaluation import run_test as run_test_postgis
from concave_evaluation.helpers import load_polygon
from concave_evaluation.helpers import measure_convexity_simple

logger = logging.getLogger("Concave")


@click.group()
def evaluate():
    """Evaluates conave hull implementations"""
    pass
  

@evaluate.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default=DEFAULT_TEST_FILE)
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default=DEFAULT_PL_SAVE_DIR)
@click.option('-xy', '--xy-thresh', default=10.0)
@click.option('-a', '--alpha', default=0.0)
@click.option('-n', '--number-iter', default=1)
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def polylidar(input_file, save_directory, alpha, xy_thresh, number_iter, plot):
    """Runs polylidar on input point file"""
    run_test_polylidar(input_file, save_dir=save_directory,
                       alpha=alpha, xyThresh=xy_thresh, n=number_iter)


@evaluate.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default=DEFAULT_TEST_FILE)
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default=DEFAULT_CGAL_SAVE_DIR)
@click.option('-a', '--alpha', default=100.0)
@click.option('-n', '--number-iter', default=1)
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def cgal(input_file, save_directory, alpha, number_iter, plot):
    """Runs cgal on input point file"""
    run_test_cgal(input_file, save_directory, alpha=alpha, n=number_iter)


@evaluate.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default=DEFAULT_TEST_FILE)
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default=DEFAULT_SL_SAVE_DIR)
@click.option('-db', '--database', type=click.Path(exists=False), default=DEFAULT_SPATIALITE_DB)
@click.option('-f', '--factor', default=3.0)
@click.option('-n', '--number-iter', default=1)
def spatialite(input_file, save_directory, database, factor, number_iter):
    """Runs spatialite on input point file"""
    run_test_spatialite(input_file, save_directory,
                        database, factor=factor, n=number_iter)


@evaluate.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default=DEFAULT_TEST_FILE)
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default=DEFAULT_PG_SAVE_DIR)
@click.option('-db', '--database', default=DEFAULT_PG_CONN)
@click.option('-tp', '--target-percent', default=0.90)
@click.option('-n', '--number-iter', default=1)
def postgis(input_file, save_directory, database, target_percent, number_iter):
    """Runs postgis on input point file"""
    run_test_postgis(input_file, save_directory, database,
                     target_percent=target_percent, n=number_iter)


@evaluate.command()
@click.option('-cf', '--config-file', type=click.Path(exists=True))
@click.option('-i', '--input-file', type=click.Path(exists=True), default=DEFAULT_TEST_FILE)
@click.option('-n', '--number-iter', default=1)
@click.pass_context
def all(ctx, config_file, input_file, number_iter):
    """Evaluates all concave hull algorithms on state shapes"""
    if config_file is not None:
        run_as_config(config_file)

    else:
        ctx.forward(polylidar)
        ctx.forward(cgal)
        ctx.forward(spatialite)
        ctx.forward(postgis)


def create_records(timings, shape_name, num_points, l2_norm, alg='polylidar', section='all', has_hole=False, **kwargs):
    records = []
    # backwards compatability to previous function, if only 1 timing for this poly, integrate timing and accuracy into one record
    if len(timings) ==1:
        records.append(dict(alg=alg, shape=shape_name, points=num_points,
                        l2_norm=l2_norm, time=timings[0], holes=has_hole, section=section, **kwargs))
        return records
    
    for time in timings:
        records.append(dict(alg=alg, shape=shape_name, points=num_points,
                            l2_norm=np.NaN, time=time, holes=has_hole, section=section, **kwargs))

    if section == 'all':
        records.append(dict(alg=alg, shape=shape_name, points=num_points,
                            l2_norm=l2_norm, time=np.NaN, holes=has_hole, section=section, **kwargs))


    return records


def run_tests(point_fpath, config):
    records = []
    file_name = Path(point_fpath).stem
    shape_name, num_points = file_name.split('_')
    gt_fpath = config['common_alg_params']['gt_fpath']
    num_points = int(num_points)

    # Global algorithm parameters
    alg_params = dict(config['alg_params'])


    # Check if there are individual alg parameters for this test params, if so then update
    if config['tests'].get(shape_name):
        test_alg_params = config['tests'].get(shape_name)
        alg_params.update(**test_alg_params)

    # Skip if number of points not requested for a test
    if not num_points in config['n_points'] or not shape_name in config['shapes']:
        logger.info("Skipping file %r", file_name)
        return records

    global_kwargs = config['common_alg_params']
    # Final params for this test
    polylidar_kwargs = dict(**global_kwargs, **alg_params['polylidar'])
    cgal_kwargs = dict(**global_kwargs, **alg_params['cgal'])
    spatialite_kwargs = dict(**global_kwargs, **alg_params['spatialite'])
    postgis_kwargs = dict(**global_kwargs, **alg_params['postgis'])

    # alpha can be smaller for cgal and polylidar when the point density is higher
    # spatialite and postgis parameters are already normalized with point density
    # The magic parameters are not what concern us. Only if we can get reasonable results.
    gt_shape, _ = load_polygon(gt_fpath)
    point_density = gt_shape.area / num_points
    alpha = math.sqrt(point_density) * 2
    cgal_kwargs['alpha'] = alpha ** 2
    polylidar_kwargs['alpha'] = alpha

    has_hole = 'holes' in point_fpath

    # Polylidar Timings, has more fine grain timings provided
    if 'polylidar' in config['algs']:
        _, timings, l2_norm = run_test_polylidar(
            point_fpath, **polylidar_kwargs)
        logger.info("Running Polylidar")
        timings = np.array(timings)
        for i, section in enumerate(['delaunay', 'mesh', 'polygon', 'all']):
            if section == 'all':
                timings_section = np.sum(timings, axis=1)
            else:
                timings_section = timings[:, i]
            records.extend(create_records(timings_section, shape_name,
                                          num_points, l2_norm, alg='polylidar', section=section, has_hole=has_hole))
    # CGAL Timings
    if 'cgal' in config['algs']:
        logger.info("Running CGAL")
        _, timings, l2_norm = run_test_cgal(point_fpath, **cgal_kwargs)
        records.extend(create_records(timings, shape_name,
                                      num_points, l2_norm, alg='cgal', has_hole=has_hole))
    # PostGIS Timings
    if 'postgis' in config['algs']:
        logger.info("Running PostGIS")
        _, timings, l2_norm = run_test_postgis(point_fpath, **postgis_kwargs)
        records.extend(create_records(timings, shape_name,
                                      num_points, l2_norm, alg='postgis', has_hole=has_hole))
    # Spatialite Timings
    if 'spatialite' in config['algs']:
        logger.info("Running Spatialite")
        _, timings, l2_norm = run_test_spatialite(
            point_fpath, **spatialite_kwargs)
        records.extend(create_records(timings, shape_name,
                                      num_points, l2_norm, alg='spatialite', has_hole=has_hole))
    return records


@evaluate.command()
def polylidar_montecarlo():
    """Runs montecarlo sims on polylidar.  All options are hardcoded"""
    polys_fpath = path.join(GENERATED_DIR, "polygons.pkl")
    polys_holes_fpath = path.join(GENERATED_DIR, "polygons_holes.pkl")

    points_list = [path.join(POINTS_DIR, "polygons_2000.pkl"), path.join(POINTS_DIR, "polygons_8000.pkl"),
                    path.join(POINTS_DIR, "polygons_holes_2000.pkl"), path.join(POINTS_DIR, "polygons_holes_8000.pkl") ]
    poly_list = [polys_fpath, polys_fpath, polys_holes_fpath, polys_holes_fpath]

    save_path = path.join(DEFAULT_RESULTS_SAVE_DIR, "polylidar_montecarlo.csv")

    total_execs = int(9800 * 4)
    all_records = []

    with tqdm(total=total_execs) as pbar:
        for points, polys in zip(points_list, poly_list):
            # print(points, polys)
            records_ = run_montecarlo(points, polys, algs=['polylidar'], pbar=pbar)
            all_records.extend(records_)

    df = pd.DataFrame.from_records(all_records)
    df.to_csv(save_path, index=False)

@evaluate.command()
@click.option('-po', '--polylidar-only', default=False, is_flag=True, required=False, help="Only Polylidar")
def alphabet(polylidar_only):
    """Evaluates all algorithms on an alphabet set.  Saves results in results/alphabets_results.csv"""
    points_list = [path.join(ALPHABET_DIR, "polygons_2000.pkl") ]
    poly_list = [path.join(ALPHABET_DIR, "polygons.pkl")]

    fname = "alphabet_results.csv" if not polylidar_only else "alphabet_results_robust.csv"
    save_path = path.join(DEFAULT_RESULTS_SAVE_DIR, fname)

    total_execs = int(26)
    all_records = []
    algs = ['polylidar', 'cgal', 'spatialite', 'postgis'] if not polylidar_only else ['polylidar']
    with tqdm(total=total_execs) as pbar:
        for points, polys in zip(points_list, poly_list):
            # print(points, polys)
            records_ = run_montecarlo(points, polys, algs=algs, pbar=pbar)
            all_records.extend(records_)

    df = pd.DataFrame.from_records(all_records)
    df.to_csv(save_path, index=False)
    print(df)


def setup_run_polylidar(poly, shape_name, has_hole, convexity, points, num_points, run_kwargs):
    polylidar_kwargs = dict(**run_kwargs)
    point_density = poly.area / num_points
    alpha = math.sqrt(point_density) * 2
    polylidar_kwargs.update(dict(alpha=alpha, gt_fpath=poly))

    # logger.info("Running Polylidar")
    concave_poly, timings, l2_norm = run_test_polylidar(points, **polylidar_kwargs)
    is_valid = concave_poly.is_valid
    convexity = measure_convexity_simple(poly)
    timings = np.array(timings)
    timings_section = np.sum(timings, axis=1)

    return create_records(timings_section, shape_name, num_points, l2_norm, 'polylidar', 'all', has_hole=has_hole, convexity=convexity)


def setup_run_cgal(poly, shape_name, has_hole, convexity, points, num_points, run_kwargs):
    kwargs = dict(**run_kwargs)
    point_density = poly.area / num_points
    alpha = math.sqrt(point_density) * 2
    alpha = alpha ** 2
    kwargs.update(dict(alpha=alpha, gt_fpath=poly))

    # logger.info("Running Polylidar")
    concave_poly, timings, l2_norm = run_test_cgal(points, **kwargs)
    is_valid = concave_poly.is_valid

    return create_records(timings, shape_name, num_points, l2_norm, 'cgal', 'all', has_hole=has_hole, convexity=convexity)

def setup_run_spatialite(poly, shape_name, has_hole, convexity, points, num_points, run_kwargs):
    kwargs = dict(**run_kwargs)
    kwargs.update(dict(factor=3.0, gt_fpath=poly))

    # logger.info("Running Polylidar")
    concave_poly, timings, l2_norm = run_test_spatialite(points, **kwargs)
    is_valid = concave_poly.is_valid

    return create_records(timings, shape_name, num_points, l2_norm, 'spatialite', 'all', has_hole=has_hole, convexity=convexity)

def setup_run_postgis(poly, shape_name, has_hole, convexity, points, num_points, run_kwargs):
    kwargs = dict(**run_kwargs)
    target_percent = poly.area / poly.convex_hull.area
    kwargs.update(dict(target_percent=target_percent, gt_fpath=poly))

    # logger.info("Running Polylidar")
    concave_poly, timings, l2_norm = run_test_postgis(points, **kwargs)
    is_valid = concave_poly.is_valid if concave_poly is not None else False

    return create_records(timings, shape_name, num_points, l2_norm, 'postgis', 'all', has_hole=has_hole, convexity=convexity)



def run_montecarlo(points_dict_fpath, polygon_fpath, algs=['polylidar', 'cgal', 'spatialite', 'postgis'], pbar=None):
    poly_list, poly_params = pickle.load(open(polygon_fpath, 'rb'))
    points_dict = pickle.load(open(points_dict_fpath, 'rb'))

    records = []

    run_kwargs = dict(n=1, save_poly=False)
    for i, (poly, point_dict) in enumerate(zip(poly_list, points_dict)):
        points = point_dict['points']
        num_points = points.shape[0]
        poly_name = point_dict.get('poly_param').get('name') if point_dict.get('poly_param').get('name') else str(i)
        has_hole = len(poly.interiors) > 0
        convexity = measure_convexity_simple(poly)
        if 'polylidar' in algs:
            record = setup_run_polylidar(poly, poly_name, has_hole, convexity, points, num_points, run_kwargs)
            records.extend(record)
        if 'cgal' in algs:
            record = setup_run_cgal(poly, poly_name, has_hole, convexity, points, num_points, run_kwargs)
            records.extend(record)
        if 'spatialite' in algs:
            record = setup_run_spatialite(poly, poly_name, has_hole, convexity, points, num_points, run_kwargs)
            records.extend(record)
        if 'postgis' in algs:
            record = setup_run_postgis(poly, poly_name, has_hole, convexity, points, num_points, run_kwargs)
            records.extend(record)

        if pbar:
            pbar.update(1)

        # if i > 1:
        #     break;

    return records

def run_as_config(config_file):
    with open(config_file) as f:
        config = json.load(f)

    directory_name = config['points_dir']
    gt_dir = config['gt_dir']
    filenames = listdir(directory_name)
    point_files = [
        filename for filename in filenames if filename.endswith('.csv')]
    all_records = []
    for point_file in point_files:
        logger.info("Processing file %r", point_file)
        point_fpath = path.join(directory_name, point_file)
        gt_fpath = path.join(gt_dir, point_file.split('_')[0] + '.geojson')
        config['common_alg_params']['gt_fpath'] = gt_fpath
        all_records.extend(run_tests(point_fpath, config))

    df = pd.DataFrame.from_records(all_records)
    df.to_csv(config['save_csv'], index=False)
