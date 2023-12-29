#include <fcntl.h>
#include <getopt.h>
#include <unistd.h>

int reed(int argc, char** argv) {
  struct option options[] = {
    {"encrypt",       no_argument, NULL, 'e'},
    {"decrypt",       no_argument, NULL, 'd'},
    {"key",     required_argument, NULL, 'k'},
    { NULL,                     0, NULL,  0 }
  };

  int index;
  int mode = 0;
  int key  = 0;

  while(1) {
    int opt = getopt_long(argc, argv, "edk:", options, &index);
    if(opt < 0) break;

    switch(opt) {
    case 'e':
      mode = 0;
      break;
    case 'd':
      mode = 1;
      break;
    case 'k':
      key = slurp(optarg);
      if(key < 1 || key > 25) {
        domp("Invalid key: ", optarg);
      }
      else {
        break;
      }
    case '?':
    default:
      _exit(1);
    }
  }

  if(key == 0) {
    write(STDERR_FILENO, "Key required.\n", 14);
    _exit(1);
  }

  if(mode != 0) {
    key = 26 - key;
  }

  return key;
}