CXXFLAGS=-Wall -std=c++14 -O3
CXX=g++-7
DEFINES=
INCLUDES=-I${HOME}/miniconda3/envs/concave/include
LDFLAGS=-lpthread -L${HOME}/miniconda3/envs/concave/lib -lCGAL -lgmp
sub: cgal_subtimings.cpp
	$(CXX) $(CXXFLAGS) ${DEFINES} $(INCLUDES) ./cgal_subtimings.cpp -o ./bin/cgal_subtimings $(LDFLAGS)

all: cgal_alpha.cpp
	$(CXX) $(CXXFLAGS) ${DEFINES} $(INCLUDES) ./cgal_alpha.cpp -o ./bin/cgal_alpha $(LDFLAGS)
clean:
	$(RM) ./bin/cgal_alpha
