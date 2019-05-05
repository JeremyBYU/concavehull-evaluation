import time
import numpy as np
from concave_evaluation.spatialite_evaluation import DBConn
from concave_evaluation.postgis_evaluation import DBConnPostGIS

spatialite_query = "SELECT ST_AsBinary(ST_ConcaveHull(ST_GeomFromText('MULTIPOINT ((10 40), (40 30), (20 20), (30 10))'), 3, 1)) as polygon"
postgis_query = "SELECT ST_AsBinary(ST_ConcaveHull(ST_GeomFromText('MULTIPOINT ((10 40), (40 30), (20 20), (30 10))'), .98, true)) as polygon"

base_query = "SELECT 1"

def test_latency(db, n=1, query=base_query):
    diff = []
    for i in range(n):
        t0 = time.time()
        result = db.cursor.execute(query)
        t1 = time.time()
        a = db.cursor.fetchone()
        diff.append(t1-t0)
    diff = np.array(diff)
    mean = np.mean(diff) * 1000
    std = np.std(diff) * 1000
    return mean, std

def main(n=10):

    db_sp = DBConn(':memory:')
    mean, std = test_latency(db_sp, query=base_query)
    print("Spatialite Basic Latency (ms) - Mean:{:.3f}, Std: {:.3f}".format(mean, std))

    db_post = DBConnPostGIS()
    mean, std = test_latency(db_post, query=base_query)
    print("PostGIS Basic Latency (ms) - Mean: {:.3f}, Std: {:.3f}".format(mean, std))

    mean, std = test_latency(db_sp, query=spatialite_query)
    print("Spatialite Concave Hull Latency (ms) - Mean:{:.3f}, Std: {:.3f}".format(mean, std))

    mean, std = test_latency(db_post, query=postgis_query)
    print("PostGIS Concave Hull Latency (ms) - Mean: {:.3f}, Std: {:.3f}".format(mean, std))


if __name__ == "__main__":
    main()