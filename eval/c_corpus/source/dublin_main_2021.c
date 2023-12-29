#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#define XOR(a, b) ((uintptr_t) (a) ^ (uintptr_t) (b))

typedef struct {
  uintptr_t ptr;
  int       val;
} Node;

int main(int argc, char** argv) {
  Node* head = NULL;
  Node* tail = NULL;

  Node* l = NULL;
  Node* c = NULL;
  Node* r = NULL;

  while(1) {
    int val = 0;
    if(scanf("%d", &val) != 1) {
      break;
    }

    while(c && c->val > val) {
      r = c;
      c = l;
      if(l) l = (Node*) XOR(l->ptr, r);

      // printf("Moved L:  %18p %18p %18p\n", l, c, r);
    }

    while(c && c->val < val) {
      l = c;
      c = r;
      if(r) r = (Node*) XOR(r->ptr, l);

      // printf("Moved R:  %18p %18p %18p\n", l, c, r);
    }

    if(c) {
      if(c->val <= val) l = c;
      if(c->val >  val) r = c;
    }

    c = insert(val, l, r);
    if(!l) head = c;
    if(!r) tail = c;
  }

  if(head && tail) {
    printf("Forward:\n");
    walk(head, "smallest");

    printf("Reverse:\n");
    walk(tail, "largest");
  }

  return 0;
}