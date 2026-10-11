// SPDX-License-Identifier: MIT
// Read-only inspection of the actual stripped Go ELF's runtime pclntab.
// It verifies Go function-name metadata, not an independent legal conclusion.
package main

import (
  "debug/elf"
  "debug/gosym"
  "encoding/json"
  "errors"
  "fmt"
  "os"
  "sort"
  "strings"
)

type Result struct {
  Input string `json:"input"`
  Functions []string `json:"go_lzo_functions"`
  Count int `json:"function_count"`
  Evidence string `json:"evidence_scope"`
}

func inspect(path string) (Result,error) {
  f,err:=elf.Open(path)
  if err!=nil { return Result{},err }
  defer f.Close()
  pcln:=f.Section(".gopclntab")
  code:=f.Section(".text")
  if pcln==nil || code==nil { return Result{},errors.New("ELF lacks Go pclntab or text section") }
  data,err:=pcln.Data()
  if err!=nil {return Result{},err}
  t:=gosym.NewLineTable(data,code.Addr)
  tab,err:=gosym.NewTable(nil,t)
  if err!=nil {return Result{},err}
  var names []string
  for _,fn:=range tab.Funcs {
    if strings.HasPrefix(fn.Name,"github.com/rasky/go-lzo.") ||
       strings.HasPrefix(fn.Name,"github.com/rasky/go-lzo/") {
      names=append(names,fn.Name)
    }
  }
  sort.Strings(names)
  return Result{Input:path,Functions:names,Count:len(names),
    Evidence:"Functions recorded in .gopclntab of the actual GitHub Release ELF; not a complete determination of GPL compatibility."},nil
}

func main() {
  if len(os.Args)!=2 {
    fmt.Fprintln(os.Stderr,"usage: go run audit_published_elf.go /path/to/verified-ELF")
    os.Exit(2)
  }
  v,err:=inspect(os.Args[1])
  if err!=nil {fmt.Fprintln(os.Stderr,err);os.Exit(2)}
  out,err:=json.MarshalIndent(v,"","  ")
  if err!=nil {fmt.Fprintln(os.Stderr,err);os.Exit(2)}
  fmt.Println(string(out))
}
