import time
import logging
from os import path
from pathlib import Path
from shapely.geometry import Polygon, MultiPolygon
from polylidar import extractPolygons
import numpy as np
from concave_evaluation.helpers import get_poly_coords, save_shapely, modified_fname


logger = logging.getLogger("Concave")


def convert_to_shapely_polygons(polygons, points, return_first=False):
    """Converts a list of C++ polygon to shapely polygon
    If more than one polygon is returned from polylidar, selects the one with the largest shell if return_first is True
    """
    polygons.sort(key=lambda poly: len(poly.shell), reverse=True)
    if not polygons:
        logger.warn("No polygons returned")
        return None
    if len(polygons) > 1:
        logger.info("More than one polygon returned")
    shapely_polygons = []
    for poly in polygons:
        shell_coords = get_poly_coords(poly.shell, points)
        hole_coords = [get_poly_coords(hole, points) for hole in poly.holes]
        poly_shape = Polygon(shell=shell_coords, holes=hole_coords)
        if hole_coords:
            logger.info("Holes inside the polygon")
        if not poly_shape.is_valid:
            logger.warn("Invalid Polygon Generated by polylidar")
            continue
        shapely_polygons.append(poly_shape)

    # Return only the largest polygon (the "best")
    if shapely_polygons and return_first:
        return shapely_polygons[0]

    # Check if a multipolygon
    if len(shapely_polygons) == 1:
        return shapely_polygons[0]
    elif len(shapely_polygons) > 1:
        return MultiPolygon(shapely_polygons)
    else:
        # Whoa nothing inside!
        logger.error("No polygons returned for polylidar")
        raise ValueError("No polygons returned for polylidar")

    return shapely_polygons


def get_polygon(points, noise=2.0, alpha=0.0, xyThresh=0.0, add_noise=False, **kwargs):
    if add_noise:
        points = points + np.random.randn(points.shape[0], 2) * noise

    polylidar_kwargs = {"alpha": alpha, 'xyThresh': xyThresh}
    # Timing should start here
    t0 = time.time()
    polygons = extractPolygons(points, **polylidar_kwargs)
    end = (time.time() - t0) * 1000
    # Timing should end here

    polygons = convert_to_shapely_polygons(
        polygons, points, return_first=False)
    return polygons, end


def run_test(point_fpath, save_dir="./test_fixtures/results/polylidar", n=1, alpha=0.0, xyThresh=10, **kwargs):
    # Choose alpha parameter or xyThresh
    if alpha > 0:
        xyThresh = 0.0
    points = np.loadtxt(point_fpath)
    time_ms = []
    for i in range(n):
        polygons, ms = get_polygon(
            points, alpha=alpha, xyThresh=xyThresh, **kwargs)
        time_ms.append(ms)

    save_fname, _ = modified_fname(point_fpath, save_dir)
    save_shapely(polygons, save_fname, alg='polylidar')

    print(time_ms)

    return polygons, time_ms
