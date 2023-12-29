#include <iostream>
#include <random>

using RNG = std::mt19937_64;

void mutate(RNG& rng, unsigned char state[3]) {
  std::uniform_int_distribution<int> index(0, 2);
  std::uniform_int_distribution<int> delta(0, 1);

  unsigned char& c = state[index(rng)];
  c += 2 * delta(rng) - 1;

  if(c > 9) c = 1;
  if(c > 5) c = 4;
}