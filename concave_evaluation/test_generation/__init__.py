import random
from multiprocessing import Pool
from shapely.affinity import scale, translate
from shapely.geometry import Point
import numpy as np

import logging

def distance_to(point, geom):
    all_rings = []
    if geom.geom_type == 'Polygon':
        all_rings = list(geom.interiors)
        all_rings.insert(0, geom.exterior)
    elif geom.geom_type == 'MultiPolygon':
        all_rings =[]
        for geom_ in geom.geoms:
            all_rings.extend(list(geom_.interiors))
            all_rings.insert(0, geom_.exterior)
    else:
        raise NotImplementedError("distance_to not implemented for this geometry type {}".format(geom.geom_type))
    
    distances = [point.distance(ring) for ring in all_rings]
    return min(distances)

def random_points_within_mp(poly, num_points, min_distance=0.0, processes=4):
    points_per_processor = num_points / processes
    num_points_list = [points_per_processor] * 4
    args = [[poly, num_points_, min_distance, i]for i, num_points_ in enumerate(num_points_list)]

    with Pool(processes=processes) as pool:
        points = pool.starmap(random_points_within, args)
    
    return np.vstack(points)

def random_points_map(args):
    return random_points_within(args[0], args[1], 0.0, None)

def random_points_within(poly, num_points=2000, min_distance=0.0, seed=1):
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    min_x, min_y, max_x, max_y = poly.bounds
    points = []
    count = 0
    while len(points) < num_points:
        if count > 100:
            pass
            # logging.warn("Could not find a point after 100 iterations!")
            # break
        random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
        if (random_point.within(poly) and (min_distance == 0.0 or distance_to(random_point, poly) >= min_distance)):
            points.append([random_point.x, random_point.y])
        count += 1
    return np.array(points)

import random
from shapely.affinity import affine_transform
from shapely.geometry import Point, Polygon
from shapely.ops import triangulate

# def random_points_in_polygon_smarter(poly, num_points=2000, min_distance=0.0, seed=1):
#     "Return list of num_points points chosen uniformly at random inside the polygon."
#     areas = []
#     transforms = []
#     for t in triangulate(poly):
#         areas.append(t.area)
#         (x0, y0), (x1, y1), (x2, y2), _ = t.exterior.coords
#         transforms.append([x1 - x0, x2 - x0, y2 - y0, y1 - y0, x0, y0])
#     points = []
#     for transform in random.choices(transforms, weights=areas, k=num_points):
#         x, y = [random.random() for _ in range(2)]
#         if x + y > 1:
#             p = Point(1 - x, 1 - y)
#         else:
#             p = Point(x, y)
#         point = affine_transform(p, transform)
#         points.append([point.x, point.y])
#     return np.array(points)

def scale_poly(poly, max_size=200):
    bounds = poly.bounds
    x_range = bounds[2] - bounds[0]
    y_range = bounds[3] - bounds[1]
    ratio = min(max_size / x_range, max_size / y_range)
    poly_scaled = scale(poly, xfact=ratio, yfact=ratio)
    bounds = poly_scaled.bounds
    poly_shifted = translate(poly_scaled, -bounds[0], -bounds[1])

    return poly_shifted

def holes_poly(poly, num_holes=10, hole_radius=5.0):
    # print()
    working_poly = poly
    for i in range(num_holes):
        # print('Hole ', i)
        point = random_points_within(working_poly, 1, hole_radius * 2)[0]
        hole = Point(point[0], point[1]).buffer(hole_radius)
        working_poly = working_poly.difference(hole)

    assert working_poly.is_valid

    return working_poly

    

