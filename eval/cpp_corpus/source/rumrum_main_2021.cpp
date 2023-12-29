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

int main(int argc, char **argv) {
    int opt;
    int length = 4;
    uint32_t hash = 0;
    std::string charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    while ((opt = getopt(argc, argv, "c:l:h:")) != -1){
        switch (opt)
            {
            case 'c':
                charset = std::string(optarg);
                break;
            case 'l':
                length = std::atoi(optarg);
                break;
            case 'h':
                hash = std::stoul(optarg, nullptr, 0);
                break;
            case ':':
                std::cout << "Missing argument for %c" << optopt << "\n";
                break;
            }
    }

    if(hash == 0){
        std::cout << "Usage: ./cracker -h 0xhash [-c charset] [-l length]\n";
        return -1;
    }

    std::thread producer = std::thread(produce, charset, length);
    std::thread consumer = std::thread(consume, hash);

    producer.join();
    consumer.join();

    std::cout << "[*] Cracked: " << FOUND << "\n";

}