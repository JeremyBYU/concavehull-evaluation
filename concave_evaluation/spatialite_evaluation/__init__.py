
import time
from os import path
import sqlite3
import numpy as np
from shapely.geometry import asMultiPoint, asPoint
from shapely.wkb import dumps, loads

from concave_evaluation.helpers import save_shapely, modified_fname

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


def extract_concave_hull(conn, test_name, factor=1.0):
    query = """
    SELECT ST_AsBinary(ST_ConcaveHull(Geometry, ?, 1)) as polygon
    FROM concave
    WHERE test_name == ?
    """
    # Start Timing here
    t0 = time.time()
    cursor = conn.execute(query, (factor, test_name))
    result = cursor.fetchone()
    t1 = time.time()

    time_ms = (t1 - t0) * 1000
    polygon = loads(result['polygon'])

    return polygon, time_ms

class DBConn(object):
    def __init__(self, db_path, use_row=True):
        """ Sets up Database connection and loads in the spatialite extension """
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.enable_load_extension(True)
        # Initialize if this is a new database
        if not path.exists(db_path):
            self.conn.execute("SELECT InitSpatialMetaData(1);")
        self.conn.execute('SELECT load_extension("mod_spatialite");')
        self.conn.executescript(INIT_TABLE)
        self.conn.row_factory = sqlite3.Row if use_row else dict_factory
        self.cursor = self.conn.cursor()


def run_test(point_fpath, save_dir="./test_fixtures/results/spatialite", db_path="./test_fixtures/db/spatialite.db", n=1, factor=1.0, **kwargs):
    points = np.loadtxt(point_fpath)
    db = DBConn(db_path, use_row=True)

    save_fname, test_name = modified_fname(point_fpath, save_dir)
    insert_multipoint(db.conn, points, test_name=test_name)
    polygon, time_ms = extract_concave_hull(db.conn, test_name, factor=factor)

    save_shapely(polygon, save_fname, alg='spatialite')

    return polygon, time_ms




    
