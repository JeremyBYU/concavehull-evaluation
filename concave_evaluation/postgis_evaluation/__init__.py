
import time
from os import path
import sqlite3

import numpy as np
from shapely.geometry import asMultiPoint, asPoint
from shapely.wkb import dumps, loads
import psycopg2
import psycopg2.extras

from concave_evaluation.helpers import save_shapely, modified_fname

DEFAULT_PG_CONN = "dbname=concave user=concave password=concave host=localhost"

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
    final_geometry = loads(result['polygon'], hex=True)
    # This may not be a polygon, filter out
    if final_geometry.geom_type == 'GeometryCollection':
        # PostGIS returned points as well as Polygons! Just get the polygons
        polygons = [geom for geom in final_geometry.geoms if geom.geom_type in ['Polygon', 'MultiPolygon']]
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


def run_test(point_fpath, save_dir="./test_fixtures/results/postgis", db_path=DEFAULT_PG_CONN, n=1, target_percent=0.99, **kwargs):
    points = np.loadtxt(point_fpath)
    db = DBConnPostGIS(db_path)

    save_fname, test_name = modified_fname(point_fpath, save_dir)
    insert_multipoint(db.conn, points, test_name=test_name)

    polygon, timings = extract_concave_hull(db.conn, test_name, target_percent=target_percent, n=n)

    save_shapely(polygon, save_fname, alg='postgis')
    print(timings)
    return polygon, timings




    
