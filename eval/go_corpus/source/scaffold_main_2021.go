package main

import (
    "bufio"
    "flag"
    "fmt"
    "log"
    "math/rand"
    "os"
    "strings"
    "time"
)

var BODYPARTS = []string {
    "liver",
    "right kidney",
    "spleen",
    "pancreas",
    "rumen",
    "esophagus",
    "head",
}

func main() {
    os.Args[0] = "scaffold"
    path := flag.String("w", "/usr/share/dict/words", "words file")
    seed := flag.Int64( "s", time.Now().UnixNano(),  "random seed")
    flag.Parse()

    rand.Seed(*seed)
    read := bufio.NewReader(os.Stdin)
    word := []byte(selec(*path))
    ltrs := len(word)
    know := []byte(strings.Repeat("_", ltrs))
    pick := make(map[byte]bool)
    fail := 0

    for true {
        fmt.Print("(" + string(know) + "): ")
        s, err := read.ReadString('\n')
        if err != nil {break}

        if len(s) < 2 {
            continue
        }

        c := s[0]
        if pick[c] {
            fmt.Println("You already tried that.")
            continue
        }

        count  := 0
        pick[c] = true
        for i := 0; i < len(word); i++ {
            if word[i] == c {
                know[i] = c
                count++
            }
        }

        if count == 0 {
            fmt.Println("You lost your " + BODYPARTS[fail] + "!")
            fail++
            if fail == len(BODYPARTS) {
                fmt.Println("It was fatal.")
                return
            }
        } else {
            ltrs -= count
            if ltrs == 0 {
                fmt.Println("Yay.")
                return
            }
        }
    }
}