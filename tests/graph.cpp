#include <iostream>
#include <map>
#include <vector>

class Node {
 public:
  int data;
  std::vector<Node*> neighbors;
  bool visited = false;

  Node(int data) {
    this->data = data;
  }
};

std::map<int, Node*> graph;

// Function to add an edge to the graph
void addEdge(int source, int destination) {
  Node* src = graph[source];
  Node* dest = graph[destination];
  src->neighbors.push_back(dest);
}

// Recursive function to perform depth-first traversal
void DFS(Node* node) {
  std::cout << node->data << " ";
  node->visited = true;

  for (auto neighbor : node->neighbors) {
    if (!neighbor->visited) {
      DFS(neighbor);
    }
  }
}

int main() {
  // Create nodes
  for (int i = 1; i <= 7; i++) {
    graph[i] = new Node(i);
  }

  // Add edges
  addEdge(1, 2);
  addEdge(1, 3);
  addEdge(2, 4);
  addEdge(2, 5);
  addEdge(3, 6);
  addEdge(3, 7);

  // Perform depth-first traversal
  std::cout << "DFS Traversal: ";
  DFS(graph[1]);
  std::cout << std::endl;

  return 0;
}
