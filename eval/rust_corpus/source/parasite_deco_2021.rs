use std::char;
use std::io;

use std::collections::HashMap;
use std::iter::Peekable;

// Encodes and decodes SKATS Hangul.
// https://en.wikipedia.org/wiki/SKATS
// https://en.wikipedia.org/wiki/Korean_language_and_computers#Hangul_Syllables_block

// Codes for Initial, Medial, and Final jamo.
const I: &'static str = "L?LL?F?B?BB?V?M?W?WW?G?GG?K?P?PP?C?X?Z?O?J";
const M: &'static str = "E?EU?I?IU?T?TU?S?SU?A?AE?AEU?AU?N?H?HT?HTU?HU?R?D?DU?U";
const F: &'static str = "?L?LL?LG?F?FP?FJ?B?V?VL?VM?VW?VG?VZ?VO?VJ?M?W?WG?G?GG?K?P?C?X?Z?O?J";

fn deco(input: &str) -> String {
    let imap: HashMap<&str, usize> = I.split("?").enumerate().map(|(i, v)| (v, i)).collect();
    let mmap: HashMap<&str, usize> = M.split("?").enumerate().map(|(i, v)| (v, i)).collect();
    let fmap: HashMap<&str, usize> = F.split("?").enumerate().map(|(i, v)| (v, i)).collect();
  
    let mut result = String::new();
    let uppercase  = input.to_ascii_uppercase();
    let mut iter   = uppercase.chars().peekable();
  
    while iter.peek().is_some() {
      let ti = read(&imap, iter.by_ref());
      let tm = read(&mmap, iter.by_ref());
      let tf = read(&fmap, iter.by_ref());
  
      match (ti, tm) {
        (Some(xi), Some(xm)) => {
          let n = 588 * xi + 28 * xm + tf.unwrap_or(0) + 44032;
          let c = std::char::from_u32(n as u32);
          result.push(c.unwrap());
        }
        _ => {}
      }
  
      let _ = iter.by_ref().take_while(|c| *c != ' ');
      iter.next();
  
      if iter.peek() == Some(&' ') {
        result.push(' ');
        iter.next();
      }
    }
  
    return result;
  }