package main

import "fmt"

// https://en.wikipedia.org/wiki/Cartesian_tree
// Builds using the first linear-time method.

type Node struct {
	P *Node
	L *Node
	R *Node
	D  int
}

func main() {
	var root *Node = nil
	var curr *Node = nil
	var data int

	for {
		n, err := fmt.Scan(&data)
		if n != 1 || err != nil {
			break
		}

		for curr != nil && curr.D > data {
			curr = curr.P
		}

		if curr == nil {
			curr = Cons(data, root, nil)
			root = curr
		} else {
			tmp := Cons(data, curr.R, nil)
			curr.SetR(tmp)
			curr = tmp
		}
	}

	root.Dump()
	fmt.Println()
}