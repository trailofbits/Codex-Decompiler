#include <iostream>

int main(int argc, char** argv) {
  int64_t a =  0;
  int64_t z = -1;

  if(argc == 3) {
    a = atoll(argv[1]);
    z = atoll(argv[2]);
  }
  else if(argc == 2) {
    z = atoll(argv[1]);
  }

  if(a < 0 || z < 0 || a > z) {
    std::cerr << "USAGE: ./blaise (range)" << std::endl;
    std::exit(1);
  }

  for(int64_t row = a; row <= z; ++row) {
    int64_t val = 1;
    int64_t mul = row;
    int64_t div = 1;

    while(mul != 0) {
      std::cout << val << '\t';

      val *= mul;
      val /= div;
      mul -= 1;
      div += 1;
    }

    std::cout << 1 << std::endl;
  }
}