import logging
import json
from os import path
from pathlib import Path
import math

import click
import numpy as np
import ast
from shapely.geometry import Polygon, shape, MultiPolygon, box, Point, LineString
from shapely.affinity import scale
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


def get360Angle(v1, v2):
    dot = np.dot(v1,v2)
    det = v1[0] * v2[1] - v1[1] * v2[0]
    ang = np.arctan2(det, dot)
    if ang < 0:
        ang += np.pi * 2
    
    return math.degrees(ang)

def measure_concavity(polygon):
    convex_hull = polygon.convex_hull
    convex_perimeter = convex_hull.length
    concave_perimeter = polygon.length

    concavity = (concave_perimeter - convex_perimeter) / convex_perimeter
    return concavity


def fake_building(x_dim=[0, 10, 1], y_dim=[0,10, 1], build_arm=True, holes=[]):
    box_base = box(x_dim[0], y_dim[0], x_dim[1], y_dim[1])
    if build_arm:
        box_arm = box(x_dim[1] * 0.5, y_dim[1], x_dim[1], y_dim[1] * 1.5)
        building = box_base.union(box_arm)
    else:
        building = box_base

    for hole_meta in holes:
        hole = Point(hole_meta[0], hole_meta[1]).buffer(hole_meta[2])
        building = building.difference(hole)
    all_points = []
    for y in range(0, int(y_dim[1] * 1.5), x_dim[2]):
        for x in range(0, x_dim[1], y_dim[2]):
            point = Point(x, y)
            if point.within(building) or point.intersects(building):
                all_points.append([x, y])
    return np.array(all_points), building

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

def plot_poly(polygon, ax, color='green', plot_holes=False, **kwargs):
    geoms = [polygon]
    if polygon.geom_type == 'MultiPolygon':
        geoms = list(polygon.geoms)
    for geom in geoms:
        plot_poly_(geom, ax, plot_holes=plot_holes, color=color, **kwargs)

def plot_poly_(polygon, ax, color='green', plot_holes=False, fill=False, **kwargs):
    poly_outline = Polygon(polygon.exterior.coords)
    outlinePatch = PolygonPatch(
        poly_outline, ec=color, fill=fill, fc=color, linewidth=2)
    ax.add_patch(outlinePatch)

    if plot_holes:
        for interior in polygon.interiors:
            poly_outline = Polygon(interior.coords)
            outlinePatch = PolygonPatch(
                poly_outline, ec='orange', fill=False, linewidth=2)
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
    geoms = [poly]
    if poly.geom_type == 'MultiPolygon':
        geoms = list(poly.geoms)
    for geom in geoms:
        plot_poly(geom, ax, plot_holes=True)
    scale_axes([map_bounds[0], map_bounds[2]], [
               map_bounds[1], map_bounds[3]], ax)
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


def plot_line(ax, ob, color=GRAY, linewidth=3, index=-1):
    x, y = ob.xy
    ax.plot(x, y, color=color, linewidth=linewidth, solid_capstyle='round', zorder=1)
    if index > 0:
        ax.text(x[0], y[0], str(index))

def plot_arrow(ax, ob, color=GRAY, scale_factor=1.0, offset=0.00, offset_side='right', index=None, center_text=True, fontsize=10, **kwargs):
    ls_ = scale(ob, xfact=scale_factor, yfact=scale_factor)
    ls_ = ls_.parallel_offset(offset, offset_side)
    if offset_side == 'right':
        ls_ = LineString(list(reversed(ls_.coords)))
    x, y = ls_.xy
    ax.arrow(x[0], y[0], x[1] - x[0], y[1]-y[0], color=color, zorder=1, **kwargs)

    if index is not None:
        # Get angle of this edge
        v0 = np.array([1, 0])
        v1 = np.array([x[1] - x[0], y[1] - y[0]])
        v0_ = v0 / np.linalg.norm(v0)
        v1_ = v1 / np.linalg.norm(v1)
        deg = get360Angle(v0_, v1_)
        deg_rot = deg
        # print("Degree: ", deg)
        offset_ = offset * 2
        x_shift = 0
        y_shift = 0
        if deg > 0 and deg < 90:
            offset_ = offset * 10
        elif deg >= 90 and deg < 180:
            deg_rot = deg - 180
            offset_ = offset * 6
        elif deg == 180:
            deg_rot = deg - 180
            offset_ = offset * 6
        elif deg > 180 and deg < 270:
            deg_rot = deg - 180
        elif deg >= 270 and deg < 360:
            deg_rot =  deg - 360

        
        if deg == 180 or deg == 0:
            x_shift = -0.25
        elif deg == 90 or deg == 270:
            y_shift = 0.1
            x_shift = -0.05
        elif deg > 90 and deg <= 315:
            x_shift = -.1
            y_shift = +.1
        # print(ls_.centroid)
  
        # print("Offset: " , offset_)
        ls_ = ls_.parallel_offset(offset_, 'left')
        center = ls_.centroid
        # print(center, index)
        ax.text(center.x + x_shift, center.y + y_shift, str(index), rotation=deg_rot, fontsize=fontsize)


def save_shapely(shape, fname, uid="", alg='polylidar'):
    feature = Feature(shape, properties={'uid': uid, 'alg': alg})
    with open(fname, "w") as f:
        dump(feature, f, indent=2)


def evaluate_l2(gt_shape, predicted_shape):
    left = gt_shape.difference(predicted_shape)
    right = predicted_shape.difference(gt_shape)
    numerator = left.union(right).area
    denominator = predicted_shape.area
    return numerator / denominator

def evaluate_l2(gt_shape, predicted_shape):
    left = gt_shape.difference(predicted_shape)
    right = predicted_shape.difference(gt_shape)
    numerator = left.union(right).area
    denominator = predicted_shape.area
    l2 = numerator / denominator
    return l2

def evaluate_iou(true_boundary, estimated):
    iou = estimated.intersection(true_boundary).area / estimated.union(true_boundary).area
    return iou

def extract_shell(poly, allow_multiple=False):
    holes = [Polygon(interior) for interior in poly.interiors]
    holes.sort(key=lambda poly: poly.area, reverse=True)
    shells = []
    if len(holes) == 0:
        # print("No holes")
        shells.append(Polygon(poly.exterior))
    elif len(holes) == 1:
        # print("only one hole")
        shells.append(holes[0])
    elif allow_multiple and len(holes) < 100:
        # print("More than one hole")
        for hole in holes:
            shells.append(hole)

    return shells

# need to handle first region better
# use exterior if we have multiple holes
# need to check if holes are in exterior
def is_inside_existing_shell(shells, poly):
    for index, shell in enumerate(shells):
        if shell.intersects(poly):
            return index
    return -1


def extract_and_assign(geoms, shells, holes):
    """Extracts shells and holes from from lines strings that have been buffered and unioned
    Sorts the polygons by area size first, the largest polygon is guaranteed to be an outer shell
    Then loop through all the other polygons and check if they are in inside the shell just extracted
    If it is add it as a hole to that shell. If not then its its own shell and add to the shell list. 
    Arguments:
        line_poly {Multipolygon} -- A multipolygon that is just lines strings unioned
        shells {List} -- List of outer shells of disconnected regions
        holes {List} -- List of Lists
    
    Raises:
        ValueError: If no shell could be found
    """
    # geoms = list(line_poly.geoms)
    geoms.sort(key=lambda poly: poly.area, reverse=True)
    # outer_hull = geoms[0]
    # hull_list = [Polygon(outer_hull.exterior)]
    # if hull_list:
    #     # Create the first outer shell of a polygon
    #     shells.append(hull_list[0])
    #     holes.append([])
    # else:
    #     logger.error(
    #         "Could not convert line string (MultiPolygon, shell) to polygon")
    #     raise ValueError(
    #         "Could not convert line string (MultiPolygon, shell) to polygon")

    for i in range(0, len(geoms)):
        # print(len(shells), len(holes))
        geom = geoms[i]
        # print(geom.is_valid)
        possible_holes = extract_shell(geom, allow_multiple=True)
        outer_shell = Polygon(geom.exterior)
        # print(i)
        if is_inside_existing_shell(shells, outer_shell) == -1:
            # print("New region to add, using outer exterior shell")
            shells.append(outer_shell)
            holes.append([])
            possible_holes.pop(0)
            # break


        for possible_hole in possible_holes:
            index = is_inside_existing_shell(shells, possible_hole)
            if index >= 0:
                # This is a hole and exists in the shell
                holes[index].append(possible_hole)
            else:
                # This is not a hole in any existing shell!
                # Create a new shell and an empty list of holes for it
                shells.append(possible_hole)
                holes.append([])
        # else:
        #     logger.error(
        #         "Error extracting hole from line string (MultiPolygon, holes) to polygon")
        #     continue

def convert_to_geometry(shells, holes):
    polygons = []
    for index, poly_shell in enumerate(shells):
        shell_lr = poly_shell.exterior # poly_shell is a polygon, get the linear_ring
        holes_lr = []
        holes_poly = holes[index]
        for hole_poly in holes_poly:
            holes_lr.append(hole_poly.exterior)
        polygons.append(Polygon(shell=shell_lr, holes=holes_lr))

    final_geometry = polygons[0]
    if len(polygons) > 1:
        # We have a multipolygon. Extracted disjoint regions
        final_geometry = MultiPolygon(polygons)

    return final_geometry


def lines_to_polygon(list_lines, buffer_amt=0.01):
    """Converts a list of line strings into a polygon
    Its importnat to note that this is __one__ way to convert the edges
    returned by CGAL into a polygon. This method only works for a single connected region.
    It will sometimes fail on disconnected regions

    Arguments:
        list_lines {List[LineStrings]} -- A list of shapely line strings

    Keyword Arguments:
        buffer_amt {float} -- How much to buffer line strings, just need a little (default: {0.01})

    Returns:
        (Multi)Polygon -- Returns a Polygon with holes
    """
    final_shape = list_lines[0]
    for line in list_lines:
        final_shape = final_shape.union(line)
    line_poly = final_shape.buffer(buffer_amt)
    final_poly = line_poly
    # return final_poly

    # This represents the outer shell of a polygon. Its a list
    # because there could be multiple polygons
    shells = []  
    # This represents the holes of a polygon, Its a list of lists
    # because there could be multiple holes for multiple polygons
    # The index of the outer list corresponds to the index in the shell list
    holes = []
    if line_poly.geom_type == 'MultiPolygon':
        # We have the possibility of multiple disconnected regions and multiple holes
        extract_and_assign(list(line_poly.geoms), shells, holes)

    elif line_poly.geom_type == 'Polygon':
        # Super simple, the lines created just a single connected region, no holes
        extract_and_assign([line_poly], shells, holes)
        # hull_list = extract_shell(line_poly)
        # if hull_list:
        #     shells.append(hull_list[0])
        #     holes.append([])
        # else:
        #     logger.error("Could not convert line string (Polygon) to polygon")
        #     return final_poly
    else:
        # This is a different geometry that this alg can handle
        # Just return whatever the shapely union produced
        logger.error("Could not convert line string (UK) to polygon")
        return final_poly

    final_poly = convert_to_geometry(shells, holes)
    return final_poly


def modified_fname(fname, base_dir=None, suffix='.geojson'):
    if base_dir is None:
        base_dir = path.dirname(fname)
    fname = Path(fname).stem
    save_fname = path.join(base_dir, fname + suffix)
    return save_fname, fname
