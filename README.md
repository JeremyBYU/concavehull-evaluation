# Concave Hull Evaluation

This repository will contain all code for evaluating several concave hull algorithms. The following algorithms and implementations will be benchmarked:

* UMICH - Polylidar
* CGAL - Alpha Shapes
* Matlab - Alpha Shapes
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
7. Matlab - No idea how anyone can afford it without a university license. Obtain at your own peril.

Finally install all other dependencies used for analysis: `pip install -e .`



## Usage

### Generate Data

First you need to generate the data (or download it optionally) using the following script.

`concave generate-fixtures`




