# Concave Hull Evaluation

This repository will contain all code for evaluating several concave hull algorithms. The following algorithms and implementations will be benchmarked:

* UMICH - Polylidar
* CGAL - Alpha Shapes
* Spatialite - ST_ConcaveHull
* PostGIS - ST_ConcaveHull


## Install Instructions

Only linux is officially supported for simplicity. However the code should mostly be portable. The following main dependencies are required to install.

1. Miniconda/Conda Python 3.6 - Get it [here](https://docs.conda.io/en/latest/miniconda.html). 
2. C++ Compiler that can compile C++ 14.
3. PostGIS 2.5.2 - Read PostGIS instruction below
4. CGAL 4.12 - `conda install -c conda-forge cgal`
5. Spatialite - `conda install -c conda-forge libspatialite`
6. Polyidar - `pip install polylidar.whl` - Install from here

Finally install all other dependencies used for analysis: `pip install -e .`

Make instruction for cpp code.

1. `export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/jeremy/miniconda/envs/concave/lib`
2. `cd cpp/cgal && make`

### PostGIS instructions

There are two options to install PostGIS:

1. Install locally on your machine following instructions [here](https://postgis.net/)
2. Use the docker container included (sets up database and configures for you)

Instructions for option 2 are the following:

1. Install docker
2. Build Image - `cd docker; & docker build . -t jeremybyu/postgis-concave:latest; & cd .. ;`
3. Launch Container - `docker run --name concave -p 5050:5050 -p 5432:5432 -v ${PWD}:/home/concave jeremybyu/postgis-concave:latest`
4. View PGAdmin (Optional) - `docker exec -i -t concave bash -c 'python $PGADMIN/pgAdmin4.py'`


## Usage

You have a nice CLI that you can use to launch the benchmarking and test dataset creation process.  See commands here:

```
concave --help
concave evaluate --help
```

### Generate Data

First you need to generate the data (or download it optionally) using the following script.

#### Scale and normalize a projected polygon

```bash
concave scale --help
# Example
concave scale -i test_fixtures/unprocessed/ca_mercator.geojson -o test_fixtures/gt_shapes/ca.geojson
```

#### Generate holes inside a polygon

```bash
concave holes --help
# Example
concave holes -i test_fixtures/gt_shapes/ca.geojson -o test_fixtures/gt_shapes/caholes.geojson
```


#### Generate Points inside a polygon

```bash
concave points --help
# Example
concave points -i test_fixtures/gt_shapes/ca.geojson -o test_fixtures/gt_shapes/caholes.geojson
```

1. Generate points for a shape - `concave `


### Note on Timings

**PostGIS**

We upload the data to the database server before we begin timing. Once data is uploaded we execute the ST_ConcaveHull query through a python `psycopg` client. The timing technically includes the following:
1. Time to transmit SQL text command to server (measured to be less than 1 ms (local))
2. Time to parse text command and execute algorithm.
3. Time to send back raw binary polygon data (WKB) to client. Note the polygon is much smaller than the point clouds (1-10).
    * Point Size 128000, Size of WKB: 2688042, Size of Polygon: 13451 (Bytes)

We can also time using `psql` using this command - `psql --host=localhost -U concave -c '\timing' -c 'SELECT ST_ConcaveHull(Geometry, .90, false) as polygon FROM concave'`.
This timing was found to be roughly equivalent to the python command (actually a little slower for some reason..)

**Spatialite**

We use an in memory SQLite database and load the C spatialite module. We do not time the uploading of the point cloud data.  We only time the execution of the 
ST_ConcaveHull algorithm.  SQLite is actually a library that is part of the program being executed, there is no client/sever transfer costs like PostGIS experiences (though minimal).

**CGAL**

Timing begins when then alpha shape is constructed and all UNORDERED boundary edges are extracted. Note that CGAL does not output a proper polygon as the other implementations provide.
Therefore CGAL has an advantage in the sense it still has not "finished" the problem yet. 

However do note that CGAL actually does some work that Polylidar and all the others don't. Fore every edge it makes a note of the alpha shape interval for the edge. This allows a **family** of alpha shapes
to be rapidly constructed.  This is a really neat feature if you want to rapidly see a suite of different levels of concavity of a point cloud. However if you just want one answer for one alpha value, this is excess work.


## Notes


### Profile

1. `python -m yep -v -- ./scripts/profile_polylidar.py`






