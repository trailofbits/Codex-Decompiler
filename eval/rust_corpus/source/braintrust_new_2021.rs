use std::env;
use std::io::Read;
use std::io::Write;
use std::collections::HashMap;

struct State {
  jt: HashMap<usize, usize>,
  tl: Vec<u8>,
  tr: Vec<u8>,
  tc: u8
}

impl State {
  fn new(code: &[u8]) -> State {
    let mut s: Vec<usize> = Vec::new();
    let mut m: HashMap<usize, usize> = HashMap::new();
    for (i, c) in code.iter().enumerate() {
      if *c == 91 {s.push(i);}
      if *c == 93 {
        let j = s.pop().unwrap();
        m.insert(i, j);
        m.insert(j, i);
      }
    }

    assert!(s.len() == 0);
    State {
      jt: m,
      tl: Vec::new(),
      tr: Vec::new(),
      tc: 0
    }
  }
}