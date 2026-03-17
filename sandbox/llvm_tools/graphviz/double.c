#include <stdlib.h>

//int double_1(int *);

void init(int *p) {
  *p=1;
}

int double_1(int *p){
  int tmp = *p;
  *p = 2*tmp;
  return (*p); 
}

int main() {
  int r = 0;
  int *p = (int *) malloc(sizeof(int));
  init(p);
  while (*p < 100) {
    r = double_1(p);
  }
  return r;
}
