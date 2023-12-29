#include <cmath>
#include <iostream>

int main(int argc, char** argv) {
  if(argc != 2) {
    std::cerr << "USAGE: ./grade n" << std::endl;
    std::exit(2);
  }

  int num = std::atoi(argv[1]);
  int sum = 1;

  if(num <= 0) {
    std::cerr << "Don't be so negative." << std::endl;
    std::exit(2);
  }

  for(int i = std::sqrt(num); i > 1; --i) {
    if(num % i == 0) {
      sum += num / i;
      sum += i;
    }
  }

  if(sum == num) {
    std::cout << "Perfect!" << std::endl;
    return 0;
  }
  else {
    std::cout << "Needs improvement." << std::endl;
    return 1;
  }
}