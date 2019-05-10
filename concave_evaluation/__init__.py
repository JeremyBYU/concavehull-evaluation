from os.path import join, abspath, dirname
import os

THIS_DIR = dirname(__file__)
MAIN_DIR = join(THIS_DIR, '../')
TEST_FIXTURES_DIR = join(MAIN_DIR, 'test_fixtures')

CGAL_BIN = abspath(join(MAIN_DIR, 'cpp', 'cgal', 'bin', 'cgal_alpha'))

DEFAULT_GT_DIR = join(TEST_FIXTURES_DIR, 'gt_shapes')
DEFAULT_SHAPE_FILE = join(TEST_FIXTURES_DIR, 'gt_shapes/miglove.geojson')
DEFAULT_TEST_FILE = join(TEST_FIXTURES_DIR, 'points/miglove_2000.csv')
DEFAULT_TEST_FILE_HARD = join(TEST_FIXTURES_DIR, 'points/miglove_64000.csv')

DEFAULT_RESULTS_SAVE_DIR = join(TEST_FIXTURES_DIR, 'results')

DEFAULT_PL_SAVE_DIR = join(DEFAULT_RESULTS_SAVE_DIR, 'polylidar')
DEFAULT_CGAL_SAVE_DIR = join(DEFAULT_RESULTS_SAVE_DIR, 'cgal')
DEFAULT_PG_SAVE_DIR = join(DEFAULT_RESULTS_SAVE_DIR, 'postgis')
DEFAULT_SL_SAVE_DIR = join(DEFAULT_RESULTS_SAVE_DIR, 'spatialite')


DEFAULT_PG_CONN = "dbname=concave user=concave password=concave host=localhost"
DEFAULT_SPATIALITE_DB = ":memory:"
