#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Alpha_shape_2.h>
#include <CGAL/Alpha_shape_vertex_base_2.h>
#include <CGAL/Alpha_shape_face_base_2.h>
#include <CGAL/Delaunay_triangulation_2.h>
#include <CGAL/algorithm.h>
#include <CGAL/assertions.h>
#include <fstream>
#include <iostream>
#include <list>
#include <vector>
#include <chrono> 
typedef CGAL::Exact_predicates_inexact_constructions_kernel  K;
typedef K::FT                                                FT;
typedef K::Point_2                                           Point;
typedef K::Segment_2                                         Segment;
typedef CGAL::Alpha_shape_vertex_base_2<K>                   Vb;
typedef CGAL::Alpha_shape_face_base_2<K>                     Fb;
typedef CGAL::Triangulation_data_structure_2<Vb,Fb>          Tds;
typedef CGAL::Delaunay_triangulation_2<K,Tds>                Triangulation_2;
typedef CGAL::Alpha_shape_2<Triangulation_2>                 Alpha_shape_2;
typedef Alpha_shape_2::Alpha_shape_edges_iterator            Alpha_shape_edges_iterator;
typedef Alpha_shape_2::Classification_type                   ClassType;


template <typename TElem>
std::ostream& operator<<(std::ostream& os, const std::vector<TElem>& vec) {
    // typedef std::vector<TElem>::const_iterator iter_t;
    auto iter_begin = vec.begin();
    auto iter_end   = vec.end();
    os << "[";
    for (auto iter = iter_begin; iter != iter_end; ++iter) {
        std::cout << ((iter != iter_begin) ? "," : "") << *iter;
    }
    os << "]";
    return os;
}

template <class OutputIterator>
void alpha_edges( const Alpha_shape_2& A, OutputIterator out)
{
  Alpha_shape_edges_iterator it = A.alpha_shape_edges_begin(),
                             end = A.alpha_shape_edges_end();
  for( ; it!=end; ++it)
  {
    auto classType = A.classify(*it);
    if (classType == ClassType::REGULAR)
      *out++ = A.segment(*it);
  }
}


// Write all the alpha edges to a file
void write_edges(std::string out_file, std::vector<Segment> segments)
{
  std::ofstream edge_file;
  edge_file.open (out_file);
  for (auto & seg : segments)
  {
    edge_file << seg << std::endl;
  }
  edge_file.close();
}

// Read in an input file of the point cloud
bool file_input(std::list<Point> &points, std::string file_path)
{
  int n = 0;
  std::ifstream is(file_path, std::ios::in);
  if(is.fail())
  {
    std::cerr << "unable to open file for input" << std::endl;
    return false;
  }

  std::string line;
  while (std::getline(is, line))
  {
      std::istringstream iss(line);
      double a, b;
      if (!(iss >> a >> b)) { break; } // error
      points.emplace_back(a, b);
      n++;
      // process pair (a,b)
  }

  // std::cout << "Reading " << n << " points from file" << std::endl;
  return true;
}
// Reads a list of points and returns a list of segments
// corresponding to the Alpha shape.

std::vector<double> calculate_alpha_shape(std::list<Point> &points, std::vector<Segment> &segments, double alpha=1.0, int n=1)
{
  std::vector<double> time_list;
  // This loop repetitively calls alpha shape to time it
  // Note that CGAL returns only an unordered set of edges (we filter so its only the boundary edges)
  // It does not return a polygon, which is what we desire.
  for (int i = 0; i< n; i++)
  {
    std::vector<Segment> segments_temp;
    auto start = std::chrono::high_resolution_clock::now(); 
    Alpha_shape_2 A(points.begin(), points.end(),
                    FT(alpha),
                    Alpha_shape_2::GENERAL);
    alpha_edges(A, std::back_inserter(segments_temp));
    auto end = std::chrono::high_resolution_clock::now();
    double time_taken = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();

    time_taken *= 1e-3; 
    time_list.push_back(time_taken);
  }
  // Here we actually push back the alpha shape to segments vector
  Alpha_shape_2 A(points.begin(), points.end(),
                  FT(alpha),
                  Alpha_shape_2::GENERAL);
  alpha_edges(A, std::back_inserter(segments));

  return time_list;
}

int main(int argc, char* argv[])
{
  std::vector<std::string> argList(argv, argv + argc);
  if (argList.size() < 4) {
    std::cerr << "Incorrect number of arguments. Need input file, output file, alpha, n (optional)" << std::endl;
    return -1;
  }
  auto point_file_name = argList[1];
  auto out_file_name = argList[2];
  double alpha = stod(argList[3]);
  int n = argList.size() == 5 ? stoi(argList[4]) : 1;

  // Read input file
  std::list<Point> points;
  if(! file_input(points, point_file_name))
    return -1;

  // Get alpha shape, record unordered line segments; record time for n iterations
  std::vector<Segment> segments;
  auto time_list = calculate_alpha_shape(points, segments, alpha, n);
  // Write the alpha shape to a file
  write_edges(out_file_name, segments);
  std::cout << time_list << std::endl;

  return 0;
}