#include <ctype.h>
#include <stdio.h>

int main() {
  char cap = 1;

  while(1) {
    int c = getc(stdin);
    if(c == EOF) break;

    if(isspace(c)) {
      putc(c, stdout);
      cap = 1;
    }
    else if(cap) {
      putc(toupper(c), stdout);
      cap = 0;
    }
    else {
      putc(tolower(c), stdout);
    }
  }

  return 0;
}