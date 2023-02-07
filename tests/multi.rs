use std::sync::{Mutex, Arc};
use std::thread;

fn main() {
    let numbers = Arc::new(Mutex::new(vec![1, 2, 3, 4, 5]));
    let mut threads = vec![];

    for i in 0..5 {
        let numbers = numbers.clone();
        threads.push(thread::spawn(move || {
            let mut numbers = numbers.lock().unwrap();
            println!("Thread {}: {}", i, numbers[i]);
        }));
    }

    for thread in threads {
        thread.join().unwrap();
    }
}
