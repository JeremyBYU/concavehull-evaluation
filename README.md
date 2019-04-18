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
3. PostGIS 2.5.2 - Get it [here](https://postgis.net/).
4. CGAL 4.12 - `conda install -c conda-forge cgal`
5. Spatialite - `conda install -c conda-forge libspatialite`
6. Polyidar - `pip install polylidar.whl` - Install from here

Finally install all other dependencies used for analysis: `pip install -e .`

Make instruction for cpp code.

1. `export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/jeremy/miniconda/envs/concave/lib`
2. `cd cpp/cgal && make`


## Usage

### Generate Data

First you need to generate the data (or download it optionally) using the following script.

`concave generate-fixtures`




