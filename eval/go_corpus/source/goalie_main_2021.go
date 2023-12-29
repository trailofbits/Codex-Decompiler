package main

import (
    "flag"
    "fmt"
    "math/rand"
    "os"
    "os/signal"
    "syscall"
    "time"
)

var OFFSETS = [][]int {
    []int {-1, -1},
    []int {-1,  0},
    []int {-1, +1},
    []int { 0, +1},
    []int {+1, +1},
    []int {+1,  0},
    []int {+1, -1},
    []int { 0, -1}}

type Field struct {
    W uint
    H uint

    data [][]bool
    temp [][]bool
}

func main() {
    os.Args[0] = "goalie"
    f := flag.Duration("f", 314 * time.Millisecond, "frame delay")
    w := flag.Uint(    "w",                     40, "width")
    h := flag.Uint(    "h",                     20, "height")
    n := flag.Uint(    "n",                      0, "frames")
    q := flag.Bool(    "q",                  false, "quiet")
    s := flag.Int64(   "s",                      0, "seed")
    flag.Parse()

    if *s == 0 {
        rand.Seed(time.Now().UnixNano())
    } else {
        rand.Seed(*s)
    }

    go func() {
        sigchan := make(chan os.Signal, 1)
        signal.Notify(sigchan, syscall.SIGTERM, syscall.SIGINT)
        <-sigchan
        *n = 1
    }()

    board := NewField(*w, *h)
    board.Seed()

    for i := uint(0); *n == 0 || i < *n; i++ {
        board.Step()

        if !*q {
            if i != 0 {
                fmt.Printf("\033[%dF", board.H - 1)
            }

            board.Draw()
            time.Sleep(*f)
        }
    }

    if *q {
        board.Draw()
    }
}