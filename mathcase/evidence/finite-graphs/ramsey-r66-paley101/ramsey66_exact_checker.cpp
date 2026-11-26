#include <array>
#include <bitset>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>

#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
using Matrix = std::array<std::bitset<101>, 101>;
struct Search { bool found=false; bool timed_out=false; std::vector<int> witness; std::uint64_t nodes=0; };
static bool find_clique(const Matrix& adjacency, std::bitset<101> candidates, int need,
                        std::vector<int>& path, Search& result,
                        std::chrono::steady_clock::time_point start, int seconds) {
  if ((result.nodes % 100000)==0 && result.nodes>0) std::cerr << "search_progress nodes=" << result.nodes << "\\n";
  if (need==0) { result.found=true; result.witness=path; return true; }
  if (candidates.count()<static_cast<std::size_t>(need)) return false;
  if ((result.nodes & 0x3fffULL)==0 && std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()>=seconds) {
    result.timed_out=true; return false;
  }
  for (int v=0; v<101; ++v) {
    if (!candidates.test(v)) continue;
    auto later=candidates;
    for (int u=0; u<=v; ++u) later.reset(u);
    if (later.count()+1<static_cast<std::size_t>(need)) break;
    ++result.nodes;
    path.push_back(v);
    auto next=later & adjacency[v];
    if (find_clique(adjacency,next,need-1,path,result,start,seconds)) return true;
    path.pop_back();
    if (result.timed_out) return false;
  }
  return false;
}
static Search search_homogeneous(const Matrix& graph, bool independent, int n, int seconds) {
  Matrix adjacency{};
  for (int i=0;i<n;++i) for (int j=0;j<n;++j) {
    if (i!=j) adjacency[i].set(j, independent ? !graph[i][j] : graph[i][j]);
  }
  std::bitset<101> candidates; for(int i=0;i<n;++i)candidates.set(i);
  Search result; std::vector<int> path;
  find_clique(adjacency,candidates,6,path,result,std::chrono::steady_clock::now(),seconds);
  return result;
}
struct ParsedEdges { Matrix graph{}; std::size_t count=0; };
static void skip_ws(const std::string& text, std::size_t& pos) {
  while(pos<text.size() && std::isspace(static_cast<unsigned char>(text[pos]))) ++pos;
}
static void expect_char(const std::string& text, std::size_t& pos, char expected) {
  skip_ws(text,pos); if(pos>=text.size() || text[pos]!=expected) throw std::runtime_error(std::string("expected '")+expected+"' at offset "+std::to_string(pos)); ++pos;
}
static int parse_uint(const std::string& text, std::size_t& pos) {
  skip_ws(text,pos); if(pos>=text.size() || !std::isdigit(static_cast<unsigned char>(text[pos]))) throw std::runtime_error("expected unsigned integer at offset "+std::to_string(pos));
  int value=0; while(pos<text.size() && std::isdigit(static_cast<unsigned char>(text[pos]))) {int digit=text[pos++]-'0'; if(value>(1000000-digit)/10)throw std::runtime_error("integer overflow"); value=value*10+digit;} return value;
}
static ParsedEdges parse_edges(const std::string& text) {
  auto key=text.find("\"edges\""); if(key==std::string::npos)throw std::runtime_error("edges missing");
  auto colon=text.find(':',key+7); if(colon==std::string::npos)throw std::runtime_error("edges colon missing");
  std::size_t pos=colon+1; expect_char(text,pos,'['); ParsedEdges parsed; std::pair<int,int> previous{-1,-1};
  for(;;) {
    skip_ws(text,pos); if(pos>=text.size())throw std::runtime_error("unterminated edges array"); if(text[pos]==']'){++pos;break;}
    expect_char(text,pos,'['); int u=parse_uint(text,pos); expect_char(text,pos,','); int v=parse_uint(text,pos); expect_char(text,pos,']');
    if(u<0||v<0||u>=101||v>=101||u>=v)throw std::runtime_error("invalid edge pair");
    std::pair<int,int> current{u,v}; if(parsed.count>0 && previous>=current)throw std::runtime_error("edges not unique/sorted");
    parsed.graph[u].set(v);parsed.graph[v].set(u);previous=current;++parsed.count;
    skip_ws(text,pos); if(pos<text.size()&&text[pos]==','){++pos;continue;} if(pos<text.size()&&text[pos]==']'){++pos;break;} throw std::runtime_error("expected edge separator at offset "+std::to_string(pos));
  }
  return parsed;
}
static Matrix read_graph(const std::string& path) {
  std::ifstream in(path,std::ios::binary);if(!in)throw std::runtime_error("cannot open certificate");
  std::string text((std::istreambuf_iterator<char>(in)),{});
  if(text.find("\"schema\": \"mathcase-simple-graph-certificate-v1\"")==std::string::npos || text.find("\"vertices\": 101")==std::string::npos)throw std::runtime_error("schema/vertices mismatch");
  auto parsed=parse_edges(text); if(parsed.count!=2525)throw std::runtime_error("expected 2525 edges");
  for(int i=0;i<101;++i){if(parsed.graph[i][i])throw std::runtime_error("loop");if(parsed.graph[i].count()!=50)throw std::runtime_error("degree != 50");}
  return parsed.graph;
}
static bool self_test() {
  const std::string pretty="{\"edges\": [\n [0, 1], [0, 2]\n]}";
  auto parsed=parse_edges(pretty);
  if(parsed.count!=2||!parsed.graph[0][1]||!parsed.graph[0][2]||parsed.graph[1][2])return false;
  bool duplicate_rejected=false;try{(void)parse_edges("{\"edges\": [[0,1],[0,1]]}");}catch(const std::exception&){duplicate_rejected=true;}
  bool range_rejected=false;try{(void)parse_edges("{\"edges\": [[0,101]]}");}catch(const std::exception&){range_rejected=true;}
  Matrix k6{},empty{},mixed{};
  for(int i=0;i<6;++i)for(int j=i+1;j<6;++j){k6[i].set(j);k6[j].set(i);}
  mixed[0].set(1);mixed[1].set(0);
  auto a=search_homogeneous(k6,false,6,2),b=search_homogeneous(empty,true,6,2);
  auto c=search_homogeneous(mixed,false,6,2),d=search_homogeneous(mixed,true,6,2);
  auto e=search_homogeneous(k6,true,6,2),f=search_homogeneous(empty,false,6,2);
  if(!duplicate_rejected||!range_rejected||!a.found||a.witness.size()!=6||!b.found||b.witness.size()!=6||c.found||d.found||e.found||f.found)return false;
  std::cout<<"PASS parses pretty JSON edge arrays\nPASS rejects duplicate and out-of-range edges\nPASS finds K6 and independent 6-set\nPASS rejects mixed six-set for both searches\n";return true;
}int main(int argc,char**argv) {
  if(argc==2&&std::string(argv[1])=="--self-test")return self_test()?0:2;
  if(argc<2||argc>3){std::cerr<<"usage: checker CERTIFICATE.json [SECONDS<=900]\n";return 64;}
  int seconds=argc==3?std::stoi(argv[2]):900;
  if(seconds<1||seconds>900){std::cerr<<"seconds must be in 1..900\n";return 64;}
  try {
    Matrix g=read_graph(argv[1]);
    auto clique=search_homogeneous(g,false,101,seconds);
    if(clique.timed_out){std::cerr<<"FAIL deadline_during_clique_search nodes="<<clique.nodes<<"\n";return 3;}
    if(clique.found){std::cerr<<"FAIL clique_of_six witness=";for(auto v:clique.witness)std::cerr<<v<<",";std::cerr<<"\n";return 2;}
    auto independent=search_homogeneous(g,true,101,seconds);
    if(independent.timed_out){std::cerr<<"FAIL deadline_during_independent_search nodes="<<independent.nodes<<"\n";return 3;}
    if(independent.found){std::cerr<<"FAIL independent_set_of_six witness=";for(auto v:independent.witness)std::cerr<<v<<",";std::cerr<<"\n";return 2;}
    std::cout<<"PASS_EXACT_R66_CERTIFICATE vertices=101 edges=2525 clique_search_nodes="<<clique.nodes<<" independent_search_nodes="<<independent.nodes<<" no_K6=yes no_independent6=yes\n";return 0;
  } catch(const std::exception&e) {std::cerr<<"FAILED_PRESERVED "<<e.what()<<"\n";return 2;}
}