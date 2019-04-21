"""Click commands to launch test runners for the concave algorithms
"""
import click

# All the algorithmic implementations for generating a concave shape from a point set
from concave_evaluation.polylidar_evaluation import run_test as run_test_polylidar
from concave_evaluation.cgal_evaluation import run_test as run_test_cgal
from concave_evaluation.spatialite_evaluation import run_test as run_test_spatialite
from concave_evaluation.postgis_evaluation import run_test as run_test_postgis, DEFAULT_PG_CONN



@click.group()
def evaluate():
    """Evaluates conave hull implementations"""
    pass


@evaluate.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/points/mi_glove_2000.csv')
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default='test_fixtures/results/polylidar')
@click.option('-xy', '--xy-thresh', default=10.0)
@click.option('-a', '--alpha', default=0.0)
@click.option('-n', '--number-iter', default=1)
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def polylidar(input_file, save_directory, alpha, xy_thresh, number_iter, plot):
    """Runs polylidar on input point file"""
    run_test_polylidar(input_file, save_dir=save_directory, alpha=alpha, xyThresh=xy_thresh, n=number_iter)


@evaluate.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/points/mi_glove_2000.csv')
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default='test_fixtures/results/cgal')
@click.option('-a', '--alpha', default=100.0)
@click.option('-n', '--number-iter', default=1)
@click.option('-p', '--plot', default=False, is_flag=True, required=False,
              help="Plot polygons")
def cgal(input_file, save_directory, alpha, number_iter, plot):
    """Runs cgal on input point file"""
    run_test_cgal(input_file, save_directory, alpha=alpha, n=number_iter)

@evaluate.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/points/mi_glove_2000.csv')
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default='test_fixtures/results/spatialite')
@click.option('-db', '--database', type=click.Path(exists=False), default=':memory:')
@click.option('-f', '--factor', default=3.0)
@click.option('-n', '--number-iter', default=1)
def spatialite(input_file, save_directory, database, factor, number_iter):
    """Runs spatialite on input point file"""
    run_test_spatialite(input_file, save_directory, database, factor=factor, n=number_iter)


@evaluate.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/points/mi_glove_2000.csv')
@click.option('-sd', '--save-directory', type=click.Path(exists=True), default='test_fixtures/results/postgis')
@click.option('-db', '--database', default=DEFAULT_PG_CONN)
@click.option('-tp', '--target-percent', default=0.90)
@click.option('-n', '--number-iter', default=1)
def postgis(input_file, save_directory, database, target_percent, number_iter):
    """Runs postgis on input point file"""
    run_test_postgis(input_file, save_directory, database, target_percent=target_percent, n=number_iter)

@evaluate.command()
@click.option('-i', '--input-file', type=click.Path(exists=True), default='test_fixtures/points/mi_glove_2000.csv')
@click.option('-n', '--number-iter', default=1)
@click.pass_context
def all(ctx, input_file, number_iter):
    """Evaluates all conave hull implementation algorithms"""
    ctx.forward(polylidar)
    ctx.forward(cgal)
    ctx.forward(spatialite)
    ctx.forward(postgis)