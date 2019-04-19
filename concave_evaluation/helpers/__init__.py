import logging
import json
from os import path
from pathlib import Path

import click
import ast
from shapely.geometry import Polygon, shape
from descartes import PolygonPatch
import matplotlib.pyplot as plt
from shapely_geojson import dump, Feature

logger = logging.getLogger("Concave")

BLUE = '#6699cc'
GRAY = '#999999'

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

def get_point(pi, points, is_3D=False):
    if is_3D:
        return [points[pi, 0], points[pi, 1], points[pi, 2]]
    else:
        return [points[pi, 0], points[pi, 1]]

def get_poly_coords(outline, points, is_3D=False):
    return [get_point(pi, points, is_3D) for pi in outline]

def plot_line(ax, ob, index=-1):
    x, y = ob.xy
    ax.plot(x, y, color=GRAY, linewidth=3, solid_capstyle='round', zorder=1)
    if index > 0:
        ax.text(x[0], y[0], str(index))

def save_shapely(shape, fname, uid="", alg='polylidar'):
    feature = Feature(shape, properties={'uid': uid, 'alg': alg})
    with open(fname, "w") as f:
        dump(feature, f, indent=2)

def extract_shell(poly, allow_multiple=False):
    holes = list(poly.interiors)
    print(len(holes))
    shells = []
    if len(holes) == 1:
        shells.append(holes[0].coords)
    elif allow_multiple and len(holes) < 5:
        for hole in holes:
            shells.append(hole.coords)

    return shells
def lines_to_polygon(list_lines, buffer_amt=0.01):
    """Concerts a list of line strings into a polygon
    Its importnat to note that this is __one__ way to convert the edges
    returned by CGAL into a polygon. This method only works for a single connected region.
    It will fail on disconnected regions
    
    Arguments:
        list_lines {List[LineStrings]} -- A list of shapely line strings
    
    Keyword Arguments:
        buffer_amt {float} -- How much to buffer line strings, just need a little (default: {0.01})
    
    Returns:
        Polygon -- Returns a Polygon with holes
    """
    final_shape=list_lines[0]
    for line in list_lines:
        final_shape = final_shape.union(line)
    line_poly = final_shape.buffer(buffer_amt)
    final_poly = line_poly
    shell = None
    holes = []
    if line_poly.geom_type == 'MultiPolygon':
        geoms = list(line_poly.geoms)
        geoms.sort(key=lambda poly: poly.area, reverse=True)
        outer_hull = geoms[0]
        hull_list = extract_shell(outer_hull)
        if hull_list:
            shell = hull_list[0]
        else:
            logger.error("Could not convert line string (MultiPolygon, shell) to polygon")
            return final_poly
        
        for i in range(1, len(geoms)):
            geom = geoms[i]
            hole_list = extract_shell(geom, allow_multiple=True)
            if hole_list:
                holes.extend(hole_list)
            else:
                logger.error("Error extracting hole from line string (MultiPolygon, holes) to polygon")
                continue
    elif line_poly.geom_type == 'Polygon':
        hull_list = extract_shell(line_poly)
        if hull_list:
            shell = hull_list[0]
        else:
            logger.error("Could not convert line string (Polygon) to polygon")
            return final_poly
    else:
        logger.error("Could not convert line string (UK) to polygon")
        return final_poly

    final_poly =Polygon(shell=shell, holes=holes)
    return final_poly

def modified_fname(fname, base_dir=None, suffix='.geojson'):
    if base_dir is None:
        base_dir = path.dirname(fname)
    fname = Path(fname).stem
    save_fname = path.join(base_dir, fname + suffix)
    return save_fname