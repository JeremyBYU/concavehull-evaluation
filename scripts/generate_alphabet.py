import os

from shapely.geometry import Polygon, LinearRing, asLinearRing
import pandas as pd
import numpy as np
import pickle

DIR_PATH = os.path.dirname(os.path.realpath(
    __file__))  # directory path of this file

ALPH_DIR = os.path.join(DIR_PATH, '..', 'test_fixtures', 'alphabet')
ALPH_CSV = os.path.join(ALPH_DIR, 'alphabet.csv')

R_SCRIPT = """
library(gglogo)

# check that all letters and digits are nicely shaped:
new_alphabet <- createPolygons(c("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"), font="Garamond")

print(new_alphabet)
write.csv(new_alphabet, "/home/jeremy/Documents/UMICH/concavehull-evaluation/test_fixtures/alphabet/alphabet.csv")
"""

def main(scale=200, points=4000):
    df = pd.read_csv(ALPH_CSV, index_col=0)
    letters = df['group'].unique()
    poly_letters = []
    poly_params = []
    for letter in letters:
        shell = None
        holes = []
        df_ = df[df['group'] == letter]
        p_groups = df_['pathGroup'].unique()
        for index, p_group in enumerate(p_groups):
            dfp_ = df_[df_['pathGroup'] == p_group]
            lr = dfp_[['x', 'y']].values * scale
            if index == 0:
                shell = asLinearRing(lr)
            else:
                holes.append(asLinearRing(lr))
        poly = Polygon(shell=shell, holes=holes)
        if not poly.is_valid:
            print("Invalid Polygon!")
        poly_letters.append(poly)
        poly_params.append(dict(name=letter))
        # print(poly.geometryType())
    print(len(poly_letters))
    pickle.dump((poly_letters, poly_params), open(os.path.join(ALPH_DIR, 'polygons.pkl'), "wb"))
    


if __name__ == "__main__":
    main()