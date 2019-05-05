
import time
from os import path
import sqlite3
import sys

import numpy as np
from shapely.geometry import asMultiPoint, asPoint
from shapely.wkb import dumps, loads
import psycopg2
import psycopg2.extras

from concave_evaluation.helpers import save_shapely, modified_fname, load_polygon, evaluate_l2
from concave_evaluation import (DEFAULT_TEST_FILE, DEFAULT_PG_SAVE_DIR, DEFAULT_PG_CONN)

INIT_TABLE = """
SELECT DropGeometryTable ('public','concave');

CREATE TABLE concave (
    ID SERIAL PRIMARY KEY, 
    test_name TEXT, Geometry geometry(MultiPoint, 0) );

"""


def insert_multipoint(connection, points, test_name='test'):
    multipoint = asMultiPoint(points)

    wkb = multipoint.wkb
    # print(wkb)
    query = """
    INSERT INTO concave
    (test_name, Geometry)
    VALUES (%s, ST_GeomFromWKB(%s, -1))
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (test_name, wkb))

    # print("Size of WKB:", sys.getsizeof(wkb))

    connection.commit()


def extract_concave_hull(connection, test_name, n=1, target_percent=1.0):
    query = """
    SELECT ST_ConcaveHull(Geometry, %s, true) as polygon
    FROM concave
    WHERE test_name = %s
    """
    # Start Timing here
    timings = []
    with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        for i in range(n):
            t0 = time.time()
            cursor.execute(query, (target_percent, test_name))
            result = cursor.fetchone()
            t1 = time.time()
            time_ms = (t1 - t0) * 1000
            timings.append(time_ms)
    # load the actual polygon into a shapely geometry, not timed
    # print("Size of Polygon:", sys.getsizeof(result['polygon']))
    final_geometry = loads(result['polygon'], hex=True)
    # This may not be a polygon, filter out
    if final_geometry.geom_type == 'GeometryCollection':
        # PostGIS returned points as well as Polygons! Just get the polygons
        polygons = [geom for geom in final_geometry.geoms if geom.geom_type in [
            'Polygon', 'MultiPolygon']]
        final_geometry = polygons[0]
        if len(polygons) > 1:
            final_geometry = MultiPolygon(polygons)

    return final_geometry, timings


class DBConnPostGIS(object):
    def __init__(self, db_path=DEFAULT_PG_CONN):
        """ Sets up Database connection to postgis"""
        self.conn = psycopg2.connect(db_path)

        self.cursor = self.conn.cursor()
        self.cursor.execute(INIT_TABLE)


def run_test(point_fpath, save_dir=DEFAULT_PG_SAVE_DIR, db_path=DEFAULT_PG_CONN, n=1,
             target_percent=0.90, save_poly=True, gt_fpath=None, **kwargs):
    points = np.loadtxt(point_fpath)
    db = DBConnPostGIS(db_path)

    save_fname, test_name = modified_fname(point_fpath, save_dir)
    insert_multipoint(db.conn, points, test_name=test_name)

    polygon, timings = extract_concave_hull(
        db.conn, test_name, target_percent=target_percent, n=n)
    if save_poly:
        save_shapely(polygon, save_fname, alg='postgis')

    l2_norm = np.NaN
    if gt_fpath:
        gt_shape, _ = load_polygon(gt_fpath)
        l2_norm = evaluate_l2(gt_shape, polygon)

    return polygon, timings, l2_norm
