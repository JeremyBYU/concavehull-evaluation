import logging
import json

import click
import ast
from shapely.geometry import Polygon, shape
from descartes import PolygonPatch
import matplotlib.pyplot as plt

logger = logging.getLogger("ConcaveEval")


class PythonLiteralOption(click.Option):

    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except:
            raise click.BadParameter(value)

def measure_concavity(polygon):
    convex_hull = polygon.convex_hull
    convex_perimeter = convex_hull.length
    concave_perimeter = polygon.length

    concavity = (concave_perimeter - convex_perimeter) / convex_perimeter
    return concavity

def round_dict(dict_value):
    for k, v in dict_value.items():
        dict_value[k] = round(v, 2)
    return dict_value

def get_max_bounds_polys(polygons):
    max_bounds = polygons[0].bounds
    for poly in polygons:
        max_bounds = get_max_bound(max_bounds, poly.bounds)

    return max_bounds

def get_max_bound(bound1, bound2):
    minx = min(bound1[0], bound2[0])
    miny = min(bound1[1], bound2[1])
    maxx = max(bound1[2], bound2[2])
    maxy = max(bound1[3], bound2[3])

    return (minx, miny, maxx, maxy)


def plot_poly(polygon, ax, color='green', plot_holes=False):
    poly_outline = Polygon(polygon.exterior.coords)
    outlinePatch = PolygonPatch(poly_outline, ec=color, fill=False, linewidth=2)
    ax.add_patch(outlinePatch)

    if plot_holes:
        for interior in polygon.interiors:
            poly_outline = Polygon(interior.coords)
            outlinePatch = PolygonPatch(poly_outline, ec='orange', fill=False, linewidth=2)
            ax.add_patch(outlinePatch)

def plot_polygons(polygons, points_2D, ax, color='green'):
    for poly in polygons:
        shell_coords = points_2D[poly.shell]
        hole_coords = [points_2D[hole] for hole in poly.holes]
        outline = Polygon(shell=shell_coords)
        outlinePatch = PolygonPatch(outline, ec=color, fill=False, linewidth=2)
        ax.add_patch(outlinePatch)
        # for hole in hole_coords:
        #     outline = Polygon(shell=hole)
        #     outlinePatch = PolygonPatch(outline, ec='orange', fill=False, linewidth=2)
        #     ax.add_patch(outlinePatch)

def scale_axes(xlim, ylim, *args):
    for ax in args:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

def plot_poly_make_fig(poly):
    fig = plt.figure(figsize=(5, 5))
    ax = plt.subplot(1, 1, 1)
    map_bounds = poly.bounds
    plot_poly(poly, ax)
    scale_axes([map_bounds[0], map_bounds[2]], [map_bounds[1], map_bounds[3]], ax)
    plt.show()

def load_polygon(poly_fpath):
    """Attempts to load a polygon geojson file"""
    try:
        with open(poly_fpath) as f:
            poly_geojson = json.load(f)
        # print(poly_geojson)
        poly = shape(poly_geojson['geometry'])
        # print(poly)
        return poly, poly_geojson
    except Exception as e:
        logger.exception("Error loading %r", poly_fpath)
        return None, None
            

