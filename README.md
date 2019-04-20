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

### Generate Data

First you need to generate the data (or download it optionally) using the following script.

`concave generate-fixtures`




