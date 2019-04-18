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
template <class OutputIterator>
void alpha_edges( const Alpha_shape_2& A, OutputIterator out)
{
  Alpha_shape_edges_iterator it = A.alpha_shape_edges_begin(),
                             end = A.alpha_shape_edges_end();
  for( ; it!=end; ++it)
  {
    auto classType = A.classify(*it);
    if (classType == ClassType::REGULAR || classType == ClassType::SINGULAR)
      *out++ = A.segment(*it);
  }
}


bool write_edges(std::string out_file, std::vector<Segment> segments)
{
  std::ofstream edge_file;
  edge_file.open (out_file);
  for (auto & seg : segments)
  {
    edge_file << seg << std::endl;
  }
  edge_file.close();
}


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

  std::cout << "Reading " << n << " points from file" << std::endl;
  return true;
}
// Reads a list of points and returns a list of segments
// corresponding to the Alpha shape.

double calculate_alpha_shape(std::list<Point> &points, std::vector<Segment> &segments, double alpha=1.0)
{
  auto start = std::chrono::high_resolution_clock::now(); 
  Alpha_shape_2 A(points.begin(), points.end(),
                  FT(alpha),
                  Alpha_shape_2::GENERAL);
  alpha_edges(A, std::back_inserter(segments));
  auto end = std::chrono::high_resolution_clock::now();
  double time_taken = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

  // std::cout << "Alpha value is " << A.get_alpha() << std::endl;
  // time_taken *= 1e-6; 
  // std::cout << "Time taken by program is : " << std::fixed  << time_taken << std::setprecision(2) << " msec" << std::endl; 

  return time_taken;
}

int main(int argc, char* argv[])
{
  std::vector<std::string> argList(argv, argv + argc);
  if (argList.size() < 4) {
    std::cerr << "Incorrect number of arguments. Need input file, output file, and alpha" << std::endl;
    return -1;
  }
  auto point_file_name = argList[1];
  auto out_file_name = argList[2];
  double alpha = stod(argList[3]);

  

  std::list<Point> points;
  if(! file_input(points, point_file_name))
    return -1;
  std::vector<Segment> segments;
  double time_ms = calculate_alpha_shape(points, segments, alpha);
  write_edges(out_file_name, segments);

  
  return 0;
}