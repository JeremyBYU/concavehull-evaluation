import random
from shapely.affinity import scale, translate
from shapely.geometry import Point
import numpy as np

def random_points_within(poly, num_points):
    min_x, min_y, max_x, max_y = poly.bounds
    points = []
    while len(points) < num_points:
        random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
        if (random_point.within(poly)):
            points.append([random_point.x, random_point.y])
    return np.array(points)

def scale_poly(poly, max_size=200):
    bounds = poly.bounds
    x_range = bounds[2] - bounds[0]
    y_range = bounds[3] - bounds[1]
    ratio = min(max_size / x_range, max_size / y_range)
    poly_scaled = scale(poly, xfact=ratio, yfact=ratio)
    bounds = poly_scaled.bounds
    poly_shifted = translate(poly_scaled, -bounds[0], -bounds[1])

    return poly_shifted

    

