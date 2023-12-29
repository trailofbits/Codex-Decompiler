#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

int main(int argc, char** argv) {
    if(argc < 2){
        printf("Please provide a seed.\n");
        return -1;
    }

    int seed = strtol(argv[1], NULL, 0);
    char domain[32] = {0};

    for(int i = 0; i < 16; i++){
        memset(domain, 0, 32);
        int r = seed ^ i;
        int k = rrrand(&r);
        int l = 5 + k % 5;
        for(int c = 0; c<l; c++){
            int n = rrrand(&r);
            domain[c] = n % 26 + 'a';
        }
        strcat(domain, ".biz");
        printf("%s\n", domain);
    }
    return 0;
}