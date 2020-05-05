from os import path
import numpy as np
from pathlib import Path
import math
import json
import logging
import pandas as pd
import click
from PIL import Image

from concave_evaluation import REALSENSE_DIR, REALSENSE_CONFIG

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


@click.group()
def realsense():
    """Evaluates concave hull implementations on realsense data"""
    pass


def segment_points(points, z_thresh=.035):
    half_rows = int(points.shape[0] / 2)
    z_med = np.median(points[half_rows:, 2])
    mask = points[:, 2] < z_med + z_thresh
    points_2d = np.ascontiguousarray(points[mask][:, :3])
    return points_2d


def get_data_from_scene(scene: dict):
    scene_data = dict()
    scene_data['points3d'] = np.loadtxt(scene['point_fpath'])
    scene_data['points3d_segmented'] = segment_points(scene_data['points3d'])
    scene_data['points2d'] = np.ascontiguousarray(scene_data['points3d_segmented'][:, :2])
    scene_data['gt_shape'] = load_polygon(scene['gt_fpath'])
    scene_data['color'] = Image.open(scene['color_fpath'])
    scene_data['depth'] = Image.open(scene['depth_fpath'])
    with open(scene['meta_fpath']) as f:
        scene_data['meta'] = json.load(f)
    scene_data['depth_raw'] = np.loadtxt(scene['depth_raw_fpath'])
    scene_data['scene_name'] = scene['scene_name']
    scene_data['scene_idx'] = scene['scene_idx']
    scene_data['scene_dir'] = scene['scene_dir']

    return scene_data


def get_realsense_scenes(realsense_dir):
    rs_dir = Path(realsense_dir)
    scenes = []
    paths = []
    # Sort the scenes
    for subdir in rs_dir.iterdir():
        paths.append(subdir)
    paths.sort()
    # Create scene dictionaries
    for subdir in paths:
        scene = dict(point_fpath=subdir / 'points.txt', gt_fpath=subdir / 'gt.geojson',
                     color_fpath=subdir / 'color_nopoly.jpg', depth_fpath=subdir / 'depth.jpg',
                     depth_raw_fpath=subdir / 'depth_raw.txt', meta_fpath=subdir / 'meta.json',
                     scene_name=subdir.stem, scene_idx=int(subdir.stem.split('_')[1]) - 1,
                     scene_dir=subdir)
        scenes.append(scene)

    return scenes


@realsense.command()
@click.option('-cf', '--config-file', type=click.Path(exists=True), default=REALSENSE_CONFIG)
def view(config_file):
    """Visualize the 3D and 2D point from the Realsense Camera"""
    import open3d as o3d
    with open(config_file) as f:
        config = json.load(f)
    scenes = get_realsense_scenes(config['realsense_dir'])
    for scene in scenes:
        # if scene['scene_name'] != "Scene_004":
        #     continue
        scene_data = get_data_from_scene(scene)
        logger.info("Visualizing - %s", scene['scene_name'])
        pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(scene_data['points3d']))
        o3d.visualization.draw_geometries_with_editing([pcd])
        pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(scene_data['points3d_segmented']))
        o3d.visualization.draw_geometries([pcd])


@realsense.command()
@click.option('-cf', '--config-file', type=click.Path(exists=True), default=REALSENSE_CONFIG)
def all(config_file):
    """Runs all Realsense Benchmarks"""
    with open(config_file) as f:
        config = json.load(f)
    scenes = get_realsense_scenes(config['realsense_dir'])
    all_dfs = []
    for scene in scenes:
        scene_data = get_data_from_scene(scene)
        logger.info("Evaluating - %s", scene['scene_name'])
        df = run_test_on_scene(scene_data, config)
        all_dfs.append(df)

    df = pd.concat(all_dfs, axis=0)
    df = df.reset_index()
    print(df)
    df.to_csv(config['save_csv'])


def run_test_on_scene(scene_data: dict, config: dict):
    gt_shape, _ = scene_data['gt_shape']
    points = scene_data['points2d']

    num_points = int(points.shape[0])

    # Global algorithm parameters
    global_kwargs = config['common_alg_params']
    global_kwargs['gt_fpath'] = gt_shape
    global_kwargs['save_poly'] = scene_data['scene_name']

    polylidar_kwargs = dict(minTriangles=1)
    cgal_kwargs = dict()
    spatialite_kwargs = dict(factor=3)
    postgis_kwargs = dict()

    point_density = gt_shape.area / num_points
    alpha = math.sqrt(point_density) * 2
    cgal_kwargs['alpha'] = alpha ** 2
    polylidar_kwargs['alpha'] = alpha
    postgis_kwargs['target_percent'] = gt_shape.area / gt_shape.convex_hull.area

    # Final params for this test
    polylidar_kwargs = dict(**global_kwargs, **polylidar_kwargs)
    cgal_kwargs = dict(**global_kwargs, **cgal_kwargs)
    spatialite_kwargs = dict(**global_kwargs, **spatialite_kwargs)
    postgis_kwargs = dict(**global_kwargs, **postgis_kwargs)

    logger.info("Running Polylidar")
    pl_data = run_test_polylidar(points, **polylidar_kwargs)
    logger.info("Running CGAL")
    cgal_data = run_test_cgal(points, **cgal_kwargs)
    logger.info("Running Spatialite")
    sl_data = run_test_spatialite(points, **spatialite_kwargs)
    logger.info("Running Postgis")
    post_data = run_test_postgis(points, **spatialite_kwargs)

    # collapse polylidar subtimings
    timings_pl = np.sum(np.array(pl_data[1]), axis=1)
    pl_data = (None, timings_pl, pl_data[2])

    records = [calc_mean_and_std(timings, error, alg=alg) for (_, timings, error), alg in [
        (pl_data, 'polylidar'), (cgal_data, 'cgal'), (sl_data, 'spatialite'), (post_data, 'postgis')]]

    df = pd.DataFrame.from_records(records)
    df['scene_name'] = scene_data['scene_name']
    df['num_points'] = num_points
    return df
