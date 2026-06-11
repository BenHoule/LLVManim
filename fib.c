#include <stdlib.h>

void init(int *p) {
  *p = 1;
}

int fib(int *p){
  if (*p > 2) {
    int *tmp = (int *) malloc(sizeof(int) * 2);
    tmp[0] = *p - 1;
    tmp[1] = *p - 2;
    *p = fib(tmp) + fib(&tmp[1]);
    free(tmp);
    return (*p);
  }

  return *p > 0 ? 1 : 0;
}

int main() {
  int r = 0;
  int *p = (int *) malloc(sizeof(int));
  init(p);
  r = fib(p);
  free(p);
  return r;
}
