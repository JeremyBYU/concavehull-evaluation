# Concave Hull Evaluation

This repository will contain all code for evaluating several concave hull algorithms. The following algorithms and implementations will be benchmarked:

* UMICH - Polylidar
* CGAL - Alpha Shapes
* Spatialite - ST_ConcaveHull
* PostGIS - ST_ConcaveHull

Two main benchmarks are provided which assess computation time and accuracy of shape reproduction:

1. Varying size point clouds of U.S. State Shapes. See how algorithms scale with increasing number of points.
2. Point clouds of the English Alphabet.
3. Plane Segmented RGBD Point clouds (must be downloaded)

Below is a sample of timing results on the State Shape of California (CA). Point clouds of varying size are sampled inside the CA Polygon (green is exterior hull and orange are holes). The chart shows execution time (in ms) for each algorithm as the point set size increases. Solid lines denotes no holes in polygon while dashed lines represents holes were inserted (as seen in the first picture).

<p align="middle">
  <img src="https://raw.githubusercontent.com/JeremyBYU/concavehull-evaluation/master/assets/repo/ca_image.png" height="100%" /> 
  <img src="https://raw.githubusercontent.com/JeremyBYU/concavehull-evaluation/master/assets/repo/ca_time.png" height="100%" /> 
</p>

## Install Instructions

Only linux is officially supported for simplicity. However the code should mostly be portable. The following main dependencies are required to install.

0. Clone this Repository - `git clone https://github.com/JeremyBYU/concavehull-evaluation.git && cd concavehull-evaluation`
1. Miniconda/Conda Python 3.6 - Get it [here](https://docs.conda.io/en/latest/miniconda.html). `conda create --name concave python=3.6`
2. Install a C++ Compiler that can compile C++ 14.
3. PostGIS 2.5.2 - Read PostGIS instruction below
4. CGAL 4.12 - `conda install -c conda-forge cgal=4.12 shapely`
5. Spatialite - `conda install -c conda-forge libspatialite`
6. Polyidar - `cd thirdparty/polylidar && export PL_USE_ROBUST_PREDICATES=1 && pip install -e ".[dev]" && cd ../..`

Finally install all other dependencies used for analysis: `pip install -e .`

Make instruction for CGAL cpp code.

1. `export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:PATH_TO_YOUR_CONDA_ENV/concave/lib`. For example `export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/miniconda3/envs/concave/lib`
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
5. Also need to install this package for python package `psycopg2`: `sudo apt-get install libpq-dev`


## Usage

You have a CLI that you can use to launch the benchmarking and test dataset creation process.  See commands here:

```
concave --help
concave evaluate --help
```

### Generate Data

First you need to generate the data (or download it optionally) using the following script. I recommend downloading all the data from this public link here: [test_fixtures](https://drive.google.com/open?id=1ItDcc1l2I4ONbqR2NavCSLncYnYRRTW1). Download and unzip the test_fixtures folder into this repository. Realsense data can be downloaded here and must be extracted into test_fixtures: [realsense](https://drive.google.com/open?id=1x60jidIChes0CQNn7_9M2-AfulPIg3PP)

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
concave points -i test_fixtures/gt_shapes/ca.geojson
```

### Run Benchmarks

You can run ``concave evaluate --help`` to view available commands:

```
(concave) ➜  concavehull-evaluation git:(subalgorithm_timings) ✗ concave evaluate --help        
Usage: concave evaluate [OPTIONS] COMMAND [ARGS]...

  Evaluates conave hull implementations

Options:
  --help  Show this message and exit.  [default: False]

Commands:
  all                   Evaluates all concave hull algorithms on state...
  alphabet              Evaluates all algorithms on an alphabet set.
  cgal                  Runs cgal on input point file
  polylidar             Runs polylidar on input point file
  polylidar-montecarlo  Runs montecarlo sims on polylidar.
  postgis               Runs postgis on input point file
  realsense             Evaluates concave hull implementations on realsense...
  spatialite            Runs spatialite on input point file

```

1. State benchmarks - `concave evaluate all -cf test_fixtures/config.json`. This will take a while.
2. Alphabet benchmarks - `concave evaluate alphabet`
3. Monte Carlo Testing for polylidar - `concave evaluate polylidar-montecarlo`


### Note on Timings

**Polylidar**

We use robust geometric predicates when bulding polylidar. This makes comparision on par with these other alorithms which also include the ability (Spatialite[GEOS], CGAL). Note that *if* robust predicates is disabled a 30% speedup is achieved.

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


## Extras


### Subtimings

Some individuals have shown interest in seeing the execution times of the algorithmic steps in  polylidar in comparison to the other algorithms.
Polylidar already has the ability to extract execution timing for the substeps in its algorithm (this is used by me often to profile my algorithm and find weak spots to improve it). However I did not design this benchmark
to extract subtimings for the other algorithms (and neither did they design the interfaces for their algorithms to do so!). This section describes how to extract these sub steps timings for polylidar, cgal, and spatialite.

All examples here will gather subtimings for `caholes_64000.csv` (64,000 points of CA state shape with holes). For analysis please see `analysis/SubTimings.ipynb`.

CGAL -

1. Build - Same directions as above except `make sub`.
2. Run - `./cpp/cgal/bin/cgal_subtimings test_fixtures/points/caholes_64000.csv test_fixtures/results/cgal/output.csv 0.8695942337343202 30`
3. This will output 30 examples runs of alpha shapes producing timings for triangulation then alpha shape construction.

Output:

```txt
[[46.862,160.001],[44.394,158.039],[44.468,152.339],[44.405,152.891],[44.374,152.626],[44.388,154.035],[44.466,153.964],[44.466,153.671],[44.389,153.933],[44.36,152.299],[44.444,153.398],[44.37,153.527],[44.357,153.021],[44.384,154.086],[44.462,153.508],[44.59,153.483],[44.444,153.228],[44.539,154.614],[44.462,152.466],[44.363,153.76],[44.449,154.291],[44.472,154.772],[44.573,152.665],[44.726,154.413],[44.477,154.577],[44.494,155.103],[44.508,155.043],[44.474,153.003],[44.53,153.702],[44.4,154.183]]

```

Polylidar

1. `concave evaluate polylidar -i test_fixtures/points/caholes_64000.csv -a 0.9325203663911691 -n 30`

```txt
[[36.12799835205078, 4.36299991607666, 0.9810000061988831], [35.928001403808594, 4.394000053405762, 1.027999997138977], [36.665000915527344, 4.3470001220703125, 1.059000015258789], [35.79399871826172, 4.316999912261963, 0.9760000109672546], [35.8390007019043, 4.35699987411499, 1.1080000400543213], [36.36899948120117, 4.396999835968018, 0.9990000128746033], [35.97100067138672, 4.35699987411499, 0.9700000286102295], [35.84700012207031, 4.359000205993652, 0.9929999709129333], [35.72999954223633, 4.355000019073486, 0.9779999852180481], [35.779998779296875, 4.335999965667725, 0.9580000042915344], [36.327999114990234, 4.354000091552734, 0.9649999737739563], [35.77000045776367, 4.429999828338623, 0.9819999933242798], [36.29100036621094, 4.381999969482422, 0.972000002861023], [36.444000244140625, 4.3470001220703125, 0.9639999866485596], [35.87900161743164, 4.372000217437744, 0.9879999756813049], [35.93000030517578, 4.382999897003174, 0.9760000109672546], [35.95600128173828, 4.414999961853027, 0.9729999899864197], [36.525001525878906, 4.375999927520752, 0.9789999723434448], [35.819000244140625, 4.373000144958496, 0.9829999804496765], [36.13800048828125, 4.375999927520752, 0.9769999980926514], [36.43600082397461, 4.366000175476074, 0.9679999947547913], [35.79999923706055, 4.392000198364258, 0.9700000286102295], [35.6879997253418, 4.366000175476074, 0.9860000014305115], [35.70100021362305, 4.372000217437744, 0.9879999756813049], [36.05099868774414, 4.34499979019165, 0.9679999947547913], [35.75400161743164, 4.3379998207092285, 0.972000002861023], [36.01100158691406, 4.3470001220703125, 0.9679999947547913], [35.724998474121094, 4.35099983215332, 0.9810000061988831], [36.13600158691406, 4.339000225067139, 0.9700000286102295], [36.02899932861328, 4.368000030517578, 0.9879999756813049]]

```

Spatialite

1. `python scripts/sub_timings_spatialite.py` - Please note you need a modified version of spatialite to retrieve subtimings! Please read the documentation in `sub_timings_spatialite.py` to learn how to generate it.

```txt
[[243.2134,128.8915,10360.2976],[227.9394,130.3733,10390.0784],[227.4224,134.5224,10378.9729],[224.1232,129.1779,10553.6631],[238.2201,137.2343,10890.5426],[229.3539,135.3008,10517.0301],[228.7435,130.1042,10465.4918],[231.9369,130.8360,10482.0692],[227.3919,132.8230,10459.4602],[227.2898,133.1695,10500.2744],[226.9457,131.7726,10611.0244],[237.7284,134.2110,10911.7942],[234.5558,138.6091,10921.2371],[236.4156,137.5632,10925.5706],[239.3039,138.8017,10912.7750],[230.0623,137.1160,10923.9332],[237.9716,140.4151,10932.0248],[237.7439,137.0150,10913.0082],[238.0106,135.7160,11105.2319],[240.1162,137.9742,11188.3114],[238.8588,137.1617,11084.2021],[236.3043,135.8150,10873.0050],[235.1310,135.2349,10900.7403],[234.9856,137.3502,10921.8185],[236.2775,135.5974,10916.4996],[234.9958,132.2554,10902.1786],[235.7370,136.4068,10923.0945],[238.3606,138.1947,10927.9517],[232.7049,141.2146,10924.7551],[236.9476,137.6959,10942.4811]]
```

### Profile

If you are interested in profiling polylidar (I am!) then run this. You need to have `yep` installed.

1. `python -m yep -v -- ./scripts/profile_polylidar.py`
