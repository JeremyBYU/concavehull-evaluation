import time
import numpy as np
from concave_evaluation.spatialite_evaluation import DBConn
from concave_evaluation.postgis_evaluation import DBConnPostGIS

spatialite_query = "SELECT ST_AsBinary(ST_ConcaveHull(ST_GeomFromText('MULTIPOINT ((10 40), (40 30), (20 20), (30 10))'), 3, 1)) as polygon"
postgis_query = "SELECT ST_AsBinary(ST_ConcaveHull(ST_GeomFromText('MULTIPOINT ((10 40), (40 30), (20 20), (30 10))'), .98, true)) as polygon"

def test_latency(db, n=1, spatialite=True):
    query = spatialite_query if spatialite else postgis_query
    diff = []
    for i in range(n):
        t0 = time.time()
        result = db.cursor.execute(query)
        t1 = time.time()
        a = db.cursor.fetchone()
        diff.append(t1-t0)
    return np.array(diff)

def main(n=10):

    db = DBConn(':memory:')
    diff = test_latency(db)
    print("Spatialite Latency {:.3f}".format(diff.mean() * 1000))

    db = DBConnPostGIS()
    diff = test_latency(db, spatialite=False)
    print("PostGIS Latency {:.3f}".format(diff.mean() * 1000))


if __name__ == "__main__":
    main()