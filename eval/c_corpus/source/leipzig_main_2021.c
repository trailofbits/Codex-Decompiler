#include <setjmp.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

long int   COUNTER;
long int   CURRENT;
sigjmp_buf RESTART;

int main(int ARGC, char** ARGV) {
  if(ARGC != 2) {
    fprintf(stderr, "Nein!\n");
    raise(SIGABRT);
  }

  COUNTER = 0;
  CURRENT = atoi(ARGV[1]);
  if(CURRENT < 1) {
    fprintf(stderr, "Nein...\n");
    raise(SIGABRT);
  }

  signal(SIGUSR1, dec);
  signal(SIGUSR2, inc);
  signal(SIGTTIN, chk);
  signal(SIGTTOU, pty);

  volatile int PID = getpid();
  int SIG = sigsetjmp(RESTART, 1);
  if(!SIG) SIG = SIGTTIN;
  kill(PID, SIG);
}