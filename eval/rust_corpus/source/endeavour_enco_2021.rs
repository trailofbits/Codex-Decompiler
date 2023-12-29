use std::env;
use std::io;

// Encoder and decoder for the Morse alphabet.
// https://en.wikipedia.org/wiki/Morse_code

const SHRDLU: &'static str = "?ETIANMSURWDKGOHVF?L?PJBXCYZQ??";

fn enco(key: &Vec<char>, input: &str) -> String {
  let mut result = String::new();
  let mut broken = false;

  for c in input.to_ascii_uppercase().chars() {
    if c == ' ' {
      result.push('/');
      broken = false;
      continue;
    }

    if broken {
      result.push(' ');
      broken = false;
    }

    if c == '?' {
      result.push('?');
      continue;
    }

    match key.iter().position(|&x| x == c) {
      None    => result.push('?'),
      Some(x) => {
        let mut i = x;
        let mut v: Vec<char> = vec!();
        broken = true;

        while i > 0 {
          if i & 1 == 1 {
            v.push('.');
          }
          else {
            v.push('-');
          }

          i = (i - 1) / 2;
        }

        for c in v.iter().rev() {
          result.push(*c);
        }
      }
    }
  }

  return result;
}