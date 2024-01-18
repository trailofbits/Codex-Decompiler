# Decompilation Evaluation/Scoring Tool
This folder contains all the code for the decompilation scoring tool which calculates for any given decompilation output how accurate it is compared to the original source.
The scoring of decompilation is done by parsing the decompilation and determining the number of function calls and branches.
# eval.py
This file contains the main code for the tool. The tool can be used as follows:
```bash
python3 eval.py -d PATH_TO_DISASSEMBLY_FILES -s PATH_TO_SOURCE_FILES -l LANGUAGE
```
Here is the full help description of the tool:
```bash
usage: Pseudocode Evaluator [-h] -d DISASM -s SOURCE -l LANGUAGE

This program evaluates the accuracy of decompiled code compared to its disassembly.

options:
  -h, --help            show this help message and exit
  -d DISASM, --disasm DISASM
                        Specify the directory to disassembly files.
  -s SOURCE, --source SOURCE
                        Specify the directory to decompilation source files.
  -l LANGUAGE, --language LANGUAGE
                        Specify the language (C, CPP, Rust, Go) of decompilation files.
```
The eval functions from the eval.py are used in the benchmark tool as a scoring method.
## extract_type.py
This file is a script such that given a JSON file (Ex: [cpp_types.json](https://github.com/tree-sitter/tree-sitter-cpp/blob/master/src/node-types.json)) from the tree-sitter library of the types in AST, it can determine the unique types of the AST.
## *_corpus folders
The c_corpus, cpp_corpus, rust_corpus, and go_corpus subfolders themselves have subfolders named prompts, disasm, and source which contain the prompts, disassembly, and source of binaries from the Decompetition challenges.
The data from these folders can be used with the benchmarking and compiler augmented generation tool as well.
Here are links to the code from the challenges:  
[Challenges 2020](https://github.com/decompetition/challenges-2020)  
[Challenges 2021](https://github.com/decompetition/challenges-2021)
