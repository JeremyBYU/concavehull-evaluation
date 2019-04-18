CXXFLAGS=-Wall -std=c++14 -O3
CXX=g++-7
DEFINES=
INCLUDES=-I/home/jeremy/miniconda3/envs/concave/include
LDFLAGS=-lpthread -L/home/jeremy/miniconda3/envs/concave/lib -lCGAL -lgmp 
all: cgal_alpha.cpp
	$(CXX) $(CXXFLAGS) ${DEFINES} $(INCLUDES) ./cgal_alpha.cpp -o ./bin/cgal_alpha $(LDFLAGS)
clean:
	$(RM) ./bin/cgal_alpha
