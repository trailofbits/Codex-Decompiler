package main

import "os"
import "fmt"
import "bufio"
import "strings"
import "unicode"

func main() {
    reader := bufio.NewReader(os.Stdin)
    fmt.Print("Enter string: ")
    text, _ := reader.ReadString('\n')

    for _, c := range text {
        var s string = string(c)
        var x string = ""
        if c & 1 == 0 {
            if unicode.IsUpper(c){
                x = strings.ToLower(s)
            } else {
                x = strings.ToUpper(s)
            }
        } else {
            x = s
        }
        fmt.Print(x)
    }
}