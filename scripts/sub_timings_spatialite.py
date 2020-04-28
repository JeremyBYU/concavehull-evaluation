"""This module captrues subtiming for algorithmic steps inside of spatialite ST_ConcaveHull
In order to capture these subtiming you must modify the source code of spatialite (minimal).
Twos file must be changed which calculate the execution timings for 3 "main" steps in the concave hull algorithm.

1. Triangulation (GEOS Delaunay triangulation)
2. Shape Extraction (Edge length statistics and filtering triangles)
3. Polygon Extraction (GEOS UNION)

Spatialite commpiles into a compiled extension module which sqlite3 can then load and call the C functions directly (concave hull functions in this case)
To build spatialite first download 4.3a from the website here: https://www.gaia-gis.it/fossil/libspatialite/index / http://www.gaia-gis.it/gaia-sins/libspatialite-4.3.0a.tar.gz

Build with following steps (expect to be in extracted directory of spatialite):

1. `sudo apt-get install libsqlite3-dev libproj-dev libxml2-dev zlib1g-dev libgeos-dev`
2. `mkdir build`
3. `./configure --enable-freexl=no --prefix=$(pwd)/build`
4. `make install`

After successfully bulding there should be a `build/lib` folder with `mod_spatialite.so`. 
Now try and modify the source code of the two files below in comments below.
The git diffs are at the end of this file below. Note that Spatilialite doesn't use git (it uses Fossil)
so I believe you will have to manually make these changes. Honestly you should only be doing this if you are 
quite adamanet about reproducing.


Results:  Every execution of ST_ConcaveHull will now print out an array of [x, y, z] where
x = milliseconds it took for triangulation
y = milliseconds it took for shape extraction
z = milliseconds it took for polygon extration

Note these timings summed do not indicate the *exact total* execution timing of ST_ConcaveHull.
However it does include about 98-99%. You can verify because the total timing is captured on the calling
function side.


"""
from os import path
import numpy as np    
from concave_evaluation.spatialite_evaluation import extract_concave_hull, insert_multipoint, DBConn
from concave_evaluation import POINTS_DIR


# NOTE: for subtimings to be executed you need a modified version of spatialite that prints out subtimings
# NOTE: Once you have manually built the modified version you must put the path to FULL PATH to mod_spatialite.so below
PATH_TO_MODIFIED_SPATIALITE_EXTENSION = "/home/jeremy/Software/libspatialite-4.3.0a/build/lib/mod_spatialite.so"

def main():
    # create in memory database
    db = DBConn(":memory:", use_row=True, extension_path=PATH_TO_MODIFIED_SPATIALITE_EXTENSION)      
    fpath = path.join(POINTS_DIR, "caholes_64000.csv")
    points = np.loadtxt(fpath) 
    # Load points into database
    insert_multipoint(db.conn, points, 'point_test')

    # subtimings will be printed to stdout
    result = extract_concave_hull(db.conn, 'point_test', n=30)  
    print(result)



if __name__ == "__main__":
    main()


################################################
####### GIT DIFF for gg_relations_ext.c ########
# Please modify the source file as described below

# diff --git a/src/gaiageo/gg_relations_ext.c b/src/gaiageo/gg_relations_ext.c
# index 5303c9b..0e9baf7 100644
# --- a/src/gaiageo/gg_relations_ext.c
# +++ b/src/gaiageo/gg_relations_ext.c
# @@ -48,6 +48,7 @@ the terms of any one of the MPL, the GPL or the LGPL.
#  #include <stdio.h>
#  #include <string.h>
#  #include <float.h>
# +#include <sys/time.h>
 
#  #if defined(_WIN32) && !defined(__MINGW32__)
#  #include "config-msvc.h"
# @@ -4334,11 +4335,27 @@ gaiaConcaveHull (gaiaGeomCollPtr geom, double factor, double tolerance,
#      return result;
#  }
 
# +// call this function to start a nanosecond-resolution timer
# +struct timespec timer_start_relations(){
# +    struct timespec start_time;
# +    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &start_time);
# +    return start_time;
# +}
# +
# +// call this function to end a timer, returning nanoseconds elapsed as a long
# +double timer_end_relations(struct timespec start_time){
# +    struct timespec end_time;
# +    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &end_time);
# +    double diffInNanos = (end_time.tv_sec - start_time.tv_sec) * (double)1e3 + (end_time.tv_nsec - start_time.tv_nsec) * 1e-6;
# +    return diffInNanos;
# +}
# +
#  GAIAGEO_DECLARE gaiaGeomCollPtr
#  gaiaConcaveHull_r (const void *p_cache, gaiaGeomCollPtr geom, double factor,
#  		   double tolerance, int allow_holes)
#  {
#  /* Concave Hull */
# +	// printf("Active Module Extension \n");
#      GEOSGeometry *g1;
#      GEOSGeometry *g2;
#      gaiaGeomCollPtr result;
# @@ -4360,8 +4377,14 @@ gaiaConcaveHull_r (const void *p_cache, gaiaGeomCollPtr geom, double factor,
#      gaiaResetGeosMsg_r (cache);
#      if (!geom)
#  	return NULL;
# +
#      g1 = gaiaToGeos_r (cache, geom);
# +	struct timespec vartime = timer_start_relations();  // begin a timer called 'vartime'
#      g2 = GEOSDelaunayTriangulation_r (handle, g1, tolerance, 0);
# +	double elapsed_milliseconds = timer_end_relations(vartime);
# +	printf("[%.4f", elapsed_milliseconds);
# +	fflush(stdout);
# +
#      GEOSGeom_destroy_r (handle, g1);
#      if (!g2)
#  	return NULL;


##########################################
####### git diff for gg_voronoj.c ########
# Please modify the source file as described below

# diff --git a/src/gaiageo/gg_voronoj.c b/src/gaiageo/gg_voronoj.c
# index f39c7ce..cfa26b5 100644
# --- a/src/gaiageo/gg_voronoj.c
# +++ b/src/gaiageo/gg_voronoj.c
# @@ -49,6 +49,7 @@ the terms of any one of the MPL, the GPL or the LGPL.
#  #include <string.h>
#  #include <float.h>
#  #include <math.h>
# +#include <sys/time.h>
 
#  #if defined(_WIN32) && !defined(__MINGW32__)
#  #include "config-msvc.h"
# @@ -1618,6 +1619,21 @@ concave_hull_no_holes (gaiaGeomCollPtr in)
#      return out;
#  }
 
# +struct timespec timer_start_concave(){
# +    struct timespec start_time;
# +    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &start_time);
# +    return start_time;
# +}
# +
# +// call this function to end a timer, returning nanoseconds elapsed as a long
# +double timer_end_concave(struct timespec start_time){
# +    struct timespec end_time;
# +    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &end_time);
# +    double diffInNanos = (end_time.tv_sec - start_time.tv_sec) * (double)1e3 + (end_time.tv_nsec - start_time.tv_nsec) * 1e-6;
# +    return diffInNanos;
# +}
# +
# +
#  static void *
#  concave_hull_build_common (const void *p_cache, void *p_first,
#  			   int dimension_model, double factor, int allow_holes)
# @@ -1651,6 +1667,9 @@ concave_hull_build_common (const void *p_cache, void *p_first,
#      concave.quot = 0.0;
#      concave.count = 0.0;
 
# +	struct timespec vartime = timer_start_concave();  // begin a timer called 'vartime'
# +
# +
#      pg = first;
#      while (pg)
#        {
# @@ -1870,6 +1889,13 @@ concave_hull_build_common (const void *p_cache, void *p_first,
#  	  return NULL;
#        }
 
# +	// print timings of triangle filtering and triangle (polygon) set creation
# +	double elapsed_milliseconds = timer_end_concave(vartime);
# +	printf(",%.4f", elapsed_milliseconds);
# +	fflush(stdout);
# +
# +	vartime = timer_start_concave();
# +
#  /* merging all triangles into the Concave Hull */
#      segm = result;
#      if (p_cache != NULL)
# @@ -1877,6 +1903,11 @@ concave_hull_build_common (const void *p_cache, void *p_first,
#      else
#  	result = gaiaUnaryUnion (segm);
#      gaiaFreeGeomColl (segm);
# +	// print timing of polygon creation which using UnaryUnon
# +	elapsed_milliseconds = timer_end_concave(vartime);
# +	printf(",%.4f],", elapsed_milliseconds);
# +	fflush(stdout);
# +
#      if (!result)
#  	return NULL;
#      if (result->FirstPolygon == NULL)

