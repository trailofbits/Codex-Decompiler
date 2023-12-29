package main

import (
	"fmt"
	"os"
	"strings"
	"bufio"
	"math/rand"
)

var predictions []string = []string{
	"42",
	"Look east!",
	"You got the gift, but it looks like you're waiting for something.",
	"In one hand you'll have your enemies' life and in the other hand you'll have your own.",
	"You just have to make up your own damn mind!",
	"Everything that has a beginning has an end.",
	"What do all men with power want?",
	"Change is inevitable.",
	"Know thyself!",
	"Love of money and nothing else will ruin you.",
	"Care for these things fall on me!",
	"Make your own nature, not the advice of others, your guide in life.",
	"The number 73 marks the hour of your downfall!"}
	
func predict(data []string) {
	var index int = 0xFEEDBEEF
	for _, s := range data {
		for _, c := range s {
			index += int(c)
		}
	}
	rand.Seed(int64(index))
	index += rand.Int()
	index = index % len(predictions)
	fmt.Println("Your prediction:")
	fmt.Println(predictions[index])
}
