
import time
from os import path
import sqlite3
import numpy as np
from shapely.geometry import asMultiPoint, asPoint
from shapely.wkb import dumps, loads

from concave_evaluation.helpers import save_shapely, modified_fname
from concave_evaluation import (DEFAULT_SPATIALITE_DB, DEFAULT_TEST_FILE)
INIT_TABLE = """
SELECT DropGeoTable('concave');

CREATE TABLE concave (
id INTEGER NOT NULL PRIMARY KEY,
test_name TEXT);

SELECT AddGeometryColumn('concave', 'Geometry', -1, 'MultiPoint', 'XY');

SELECT CreateSpatialIndex('concave', 'Geometry');
"""


def insert_multipoint(conn, points, test_name='test'):
    multipoint = asMultiPoint(points)

    wkb = multipoint.wkb
    # print(wkb)
    query = """
    INSERT INTO concave
    (test_name, Geometry)
    VALUES (?, MPointFromWKB(?, -1))
    """
    conn.execute(query, (test_name, wkb))
    conn.commit()


def extract_concave_hull(conn, test_name, n=1, factor=1.0):
    query = """
    SELECT ST_AsBinary(ST_ConcaveHull(Geometry, ?, 1)) as polygon
    FROM concave
    WHERE test_name == ?
    """
    # Start Timing here
    timings = []
    for i in range(n):
        t0 = time.time()
        cursor = conn.execute(query, (factor, test_name))
        result = cursor.fetchone()
        t1 = time.time()
        time_ms = (t1 - t0) * 1000
        timings.append(time_ms)
    polygon = loads(result['polygon'])

    return polygon, timings


class DBConn(object):
    def __init__(self, db_path, use_row=True):
        """ Sets up Database connection and loads in the spatialite extension """
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.enable_load_extension(True)
        self.conn.execute('SELECT load_extension("mod_spatialite");')
        # Initialize if this is a new database
        if db_path == ':memory:' or not path.exists(db_path):
            self.conn.execute("SELECT InitSpatialMetaData(1);")
        self.conn.executescript(INIT_TABLE)
        self.conn.row_factory = sqlite3.Row if use_row else dict_factory
        self.cursor = self.conn.cursor()


def run_test(point_fpath, save_dir=DEFAULT_TEST_FILE, db_path=DEFAULT_SPATIALITE_DB, n=1,
             factor=3.0, save_poly=True, **kwargs):
    points = np.loadtxt(point_fpath)
    db = DBConn(db_path, use_row=True)

    save_fname, test_name = modified_fname(point_fpath, save_dir)
    insert_multipoint(db.conn, points, test_name=test_name)
    polygon, timings = extract_concave_hull(
        db.conn, test_name, factor=factor, n=n)

    if save_poly:
        save_shapely(polygon, save_fname, alg='spatialite')
    print(timings)
    return polygon, timings
