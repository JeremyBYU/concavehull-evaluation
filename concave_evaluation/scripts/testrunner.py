"""Click commands to launch test runners for the concave algorithms
"""
import json
from pathlib import Path
from os import listdir, path
import click
import pandas as pd
import numpy as np
import logging

# All the algorithmic implementations for generating a concave shape from a point set
from concave_evaluation import (DEFAULT_PG_CONN, DEFAULT_SPATIALITE_DB, DEFAULT_TEST_FILE,
                                DEFAULT_PG_SAVE_DIR, DEFAULT_PL_SAVE_DIR, DEFAULT_SL_SAVE_DIR, DEFAULT_CGAL_SAVE_DIR)
from concave_evaluation.polylidar_evaluation import run_test as run_test_polylidar
from concave_evaluation.cgal_evaluation import run_test as run_test_cgal
from concave_evaluation.spatialite_evaluation import run_test as run_test_spatialite
from concave_evaluation.postgis_evaluation import run_test as run_test_postgis


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
    """Evaluates all conave hull implementation algorithms"""
    if config_file is not None:
        run_as_config(config_file)

    else:
        ctx.forward(polylidar)
        ctx.forward(cgal)
        ctx.forward(spatialite)
        ctx.forward(postgis)

def create_records(timings, shape_name, num_points, l2_norm, alg='polylidar', section='all'):
    records = []
    for time in timings:
        records.append(dict(alg=alg, shape=shape_name, points=num_points, l2_norm=np.NaN, time=time, section=section))

    if section == 'all':
        records.append(dict(alg=alg, shape=shape_name, points=num_points, l2_norm=l2_norm, time=np.NaN, section=section))

    return records

def run_tests(point_fpath, config):
    records = []
    file_name = Path(point_fpath).stem
    shape_name, num_points = file_name.split('_')
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
    if num_points >= 16000:
        alpha = 2
        cgal_kwargs['alpha'] = alpha ** 2
        polylidar_kwargs['alpha'] = alpha


    # Polylidar Timings, has more fine grain timings provided
    if 'polylidar' in config['algs']:
        _, timings, l2_norm = run_test_polylidar(point_fpath, **polylidar_kwargs)
        logger.info("Running Polylidar")
        timings = np.array(timings)
        for i, section in enumerate(['delaunay', 'mesh', 'polygon', 'all']):
            if section == 'all':
                timings_section = np.sum(timings, axis=1)
            else:
                timings_section = timings[:, i]
            records.extend(create_records(timings_section, shape_name, num_points, l2_norm, alg='polylidar', section=section))
    # CGAL Timings
    if 'cgal' in config['algs']:
        logger.info("Running CGAL")
        _, timings, l2_norm = run_test_cgal(point_fpath, **cgal_kwargs)
        records.extend(create_records(timings, shape_name, num_points, l2_norm, alg='cgal'))
    # PostGIS Timings
    if 'postgis' in config['algs']:
        logger.info("Running PostGIS")
        _, timings, l2_norm = run_test_postgis(point_fpath, **postgis_kwargs)
        records.extend(create_records(timings, shape_name, num_points, l2_norm, alg='postgis'))
    # Spatialite Timings
    if 'spatialite' in config['algs']:
        logger.info("Running Spatialite")
        _, timings, l2_norm = run_test_spatialite(point_fpath, **spatialite_kwargs)
        records.extend(create_records(timings, shape_name, num_points, l2_norm, alg='spatialite'))
    return records

def run_as_config(config_file):
    with open(config_file) as f:
        config = json.load(f)
    
    directory_name = config['points_dir']
    gt_dir = config['gt_dir']
    filenames = listdir(directory_name)
    point_files = [ filename for filename in filenames if filename.endswith('.csv')]
    all_records = []
    for point_file in point_files:
        logger.info("Processing file %r", point_file)
        point_fpath = path.join(directory_name, point_file)
        gt_fpath = path.join(gt_dir, point_file.split('_')[0] + '.geojson')
        config['common_alg_params']['gt_fpath'] = gt_fpath
        all_records.extend(run_tests(point_fpath, config))
    
    df = pd.DataFrame.from_records(all_records)
    df.to_csv(config['save_csv'], index=False)

    
