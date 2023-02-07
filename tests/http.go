package main

import (
        "fmt"
        "net/http"
)

func main() {
        http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
                http.ServeFile(w, r, "./files"+r.URL.Path)
        })

        fmt.Println("Server is listening...")
        http.ListenAndServe(":8000", nil)
}
