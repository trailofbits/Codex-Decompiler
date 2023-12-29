#include <stdio.h>
#include <string.h>

#define KEYLEN 23

#define A 5
#define O 3
#define B 7
#define C 5

int check(char *key)
{
	unsigned char a[A+1] = {0};
	unsigned char o[O+1] = {0};
	unsigned char b[B+1] = {0};
	unsigned char c[C+1] = {0};

    sscanf(key, "%5c-%3c-%7c-%5c", a, o, b, c);

    if(strlen(a) != A || strlen(o) != O || strlen(b) != B || strlen(c) != C)
        return -1;

    int dummy;
    int year;
    sscanf(a, "%3d%2d", &dummy, &year);

    if(dummy < 1 || dummy > 366)
        return -1;

    if(year > 03 && year < 95)
        return -1;

    if(strcmp(o, "OEM") != 0)
        return -1;

    if(ctoi(b[0]) != 0 || ctoi(b[7]) == 0 || ctoi(b[7]) > 8)
        return -1;

    int sum = ctoi(b[1]) + ctoi(b[2]) + ctoi(b[3]) + ctoi(b[4]) + ctoi(b[5]) + ctoi(b[6]);

    if(sum % 7 != 0){
        return -1;
    }

    return 0;
}