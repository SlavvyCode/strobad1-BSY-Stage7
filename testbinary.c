#include <stdio.h>
#include <time.h>
#include <stdlib.h>

int main() {
    time_t now = time(NULL);
    int random_val = rand();
    printf("--- Compiled Binary Output ---\n");
    printf("System Time: %s", ctime(&now));
    printf("Execution ID: %d\n", random_val);
    return 0;
}