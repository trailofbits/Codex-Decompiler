#include <condition_variable>
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>
#include <getopt.h> /* getopt */

#define BUFSIZE 128

std::condition_variable not_full;
std::condition_variable not_empty;
std::mutex mutex;
std::vector<std::string> buffer;
std::string FOUND = "";

void produce(std::string charset, const int length) {
    while(true){
        std::unique_lock<std::mutex> lock(mutex);

        not_full.wait(lock, [](){
            return buffer.size() != BUFSIZE || FOUND == "";
        });

        if(FOUND != "") return;

        buffer.push_back(gen_random(charset, length));
        lock.unlock();
        not_empty.notify_one();
    }
}