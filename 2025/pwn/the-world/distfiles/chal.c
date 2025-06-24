//  gcc chal.c -o chal -lpthread -lcrypto -lssl

#define _GNU_SOURCE
#include <pthread.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <errno.h>
#include <stdint.h>
#include <sys/param.h>
#include <openssl/sha.h>

#define NUM_MINERS 3

struct mining {
  union {
    unsigned char *result;
    long long int hash;
  } data;
  int hash_len;
  char *prefix;
  int prefix_len;
};

enum Status {
  NEVER_STARTED = 0,
  RUNNING,
  RESULT_READY,
  BUFFER_READY,
  FINISHED,
};

pthread_mutex_t mutex;
atomic_char status[NUM_MINERS];
struct mining miners[NUM_MINERS];
int notify_fd[NUM_MINERS][2];

void handler(int) {
  for (int i=0; i<NUM_MINERS; i++) {
    close(notify_fd[i][0]);
    close(notify_fd[i][1]);
  }

  puts("Timed out");
  exit(0);
}

void* miner_thread(void* arg) {
  char alloced[7] = "";
  int idx = (int)arg;

  while (1) {
    while (1) {
      pthread_mutex_lock(&mutex);
      int stat = atomic_load(&status[idx]);
      pthread_mutex_unlock(&mutex);

      if (stat == RUNNING) break;
      usleep(1000);
    }

    int prefix_len = miners[idx].prefix_len;
    int result_len = prefix_len + 8;
    char *candidate = malloc(result_len);
    if (!candidate) {
      puts("End");
      exit(1);
    }

    memcpy(candidate, miners[idx].prefix, prefix_len);

    uint64_t suffix=0;
    while (1) {
      unsigned char hash[64] = "";

      for (int i=0; i<8; i++) {
        candidate[prefix_len+i] = (suffix >> (i*8)) & 0xff;
      }

      SHA256_CTX sha256;
      SHA256_Init(&sha256);
      SHA256_Update(&sha256, candidate, result_len);
      SHA256_Final(hash, &sha256);

      if (memcmp(hash, &miners[idx].data.hash, miners[idx].hash_len) == 0) {
        break;
      }

      if (suffix+1 < suffix) break;
      ++suffix;
    }

    pthread_mutex_lock(&mutex);
    atomic_store(&status[idx], RESULT_READY);
    pthread_mutex_unlock(&mutex);

    read(notify_fd[idx][0], alloced, 7);
    assert(memcmp(alloced, "ALLOCED", 7) == 0);

    sleep(1);

    pthread_mutex_lock(&mutex);
    atomic_store(&status[idx], FINISHED);
    memcpy(miners[idx].data.result, candidate, result_len);
    pthread_mutex_unlock(&mutex);

    free(candidate);
  }

  return NULL;
}

void start_mining(void) {
  int idx = -1;
  int hash_len = -1;
  int prefix_len = -1;
  char *prefix;

  printf("Miner idx: ");
  scanf("%d", &idx);
  if (idx < 0 || NUM_MINERS <= idx) {
    puts("Invalid index");
    return;
  }

  pthread_mutex_lock(&mutex);
  char stat = atomic_load(&status[idx]);
  pthread_mutex_unlock(&mutex);
  if (stat == RUNNING || stat == RESULT_READY || stat == BUFFER_READY) {
    puts("It's used");
    return;
  }

  printf("Length of hash: ");
  scanf("%d", &hash_len);

  if (hash_len < 0 || 8 < hash_len) {
    puts("Invalid length");
    return;
  }

  long long int hash;
  printf("Hash: ");
  scanf("%lld", &hash);

  printf("Length of prefix: ");
  scanf("%d", &prefix_len);
  if (prefix_len < 0 || 0x1000000 < prefix_len) {
    puts("Too large");
    return;
  }

  prefix = malloc(prefix_len+1);
  if (!prefix) {
    puts("End");
    exit(1);
  }

  for (int i=0; i<prefix_len+1; i++) {
    prefix[i] = 0;
  }

  printf("Prefix: ");
  getchar(); // consume newline
  fgets(prefix, prefix_len+1, stdin);

  pthread_mutex_lock(&mutex);
  stat = atomic_load(&status[idx]);
  pthread_mutex_unlock(&mutex);

  if (stat == FINISHED && miners[idx].data.result) {
    free(miners[idx].data.result);
    miners[idx].data.result = NULL;
  }

  miners[idx].hash_len = hash_len;
  miners[idx].data.hash = hash;

  miners[idx].prefix_len = prefix_len;

  if (miners[idx].prefix) free(miners[idx].prefix);
  miners[idx].prefix = prefix;

  pthread_mutex_lock(&mutex);
  atomic_store(&status[idx], RUNNING);
  pthread_mutex_unlock(&mutex);
}

void show_results(void) {
  for (int idx=0; idx<NUM_MINERS; idx++) {
    pthread_mutex_lock(&mutex);
    char stat = atomic_load(&status[idx]);
    pthread_mutex_unlock(&mutex);

    if (stat != RESULT_READY) continue;

    pthread_mutex_lock(&mutex);
    miners[idx].data.result = malloc(miners[idx].prefix_len + 8);
    if (!miners[idx].data.result) {
      puts("End");
      exit(1);
    }
    atomic_store(&status[idx], BUFFER_READY);
    pthread_mutex_unlock(&mutex);

    write(notify_fd[idx][1], "ALLOCED", 7);
  }

  for (int idx=0; idx<NUM_MINERS; idx++) {
    pthread_mutex_lock(&mutex);
    int stat = atomic_load(&status[idx]);
    pthread_mutex_unlock(&mutex);

    if (stat == RUNNING) {
      printf("\n#%d - RUNNING\n", idx);
      printf("Hash: %llx\n", miners[idx].data.hash);
    } else if (stat == RESULT_READY) {
      printf("\n#%d - RESULT READY\n", idx);
    } else if (stat == BUFFER_READY) {
      printf("\n#%d - BUFFER READY\n", idx);
    } else if (stat == FINISHED) {
      printf("\n#%d - FINISHED\n", idx);
      printf("Result: ");
      int result_len = miners[idx].prefix_len + 8;
      for (int i=0; i<result_len; i++) {
        printf("%02X", miners[idx].data.result[i]);
      }
      puts("");
    } else if (stat == NEVER_STARTED) {
      printf("\n#%d - UNUSED\n", idx);
    } else {
      puts("End");
      exit(1);
    }
  }
  puts("");
}

int main() {
  pthread_t miner_threads[NUM_MINERS];

  setbuf(stdout, NULL);
  pthread_mutex_init(&mutex, NULL);

  for (int i = 0; i < NUM_MINERS; i++) {
    if (pipe(notify_fd[i]) == -1) {
      puts("End");
      return 0;
    }
    pthread_create(&miner_threads[i], NULL, miner_thread, (void*)i);
  }

  signal(SIGALRM, handler);
  alarm(60);

  while (1) {
    puts("1. Start new mining");
    puts("2. Show results");
    puts("3. Exit");
    printf("Enter command: ");

    int cmd;
    scanf("%d", &cmd);
    if (cmd == 3) break;

    switch (cmd) {
    case 1:
      start_mining();
      break;
    case 2:
      show_results();
      break;
    }
  }

  return 0;
}
