# Compiler Augmented Generation Tool
This folder contains all the code for the Compiler Augmented Generation tool which leverages different feedback mechanisms to guide an LLM in decompilation tasks. 
The tool supports five different modes to for feedback: bindiff (Bindiff output), disdiff (Disassembly Diff from Decompetition), objdump (Disassembly Diff from Objdump), ghidra (Ghidra Pseudocode Diff), ghidra_eval (Ghidra Pseuodocode Scoring)
## compiler-star.py
This file contains the main tool. An example command for this tool is as follows:
```bash
python3 compiler-star.py -p ./baby_cpp_main_2021.txt -b ../cpp.out -c clang++ -m ghidra -k ./ghidra_10.4_PUBLIC/support/analyzeHeadless -s ./ghidra_proj/ -o ./trailofbits/output -f '-g -O0' -u main -l cpp
```
This example command is running the tool on the baby_cpp_main_2021 prompt and binary from the eval folder. It is also using the ghidra feedback mode.
The full list and description of all the command line arguments of this tool is given below:
```bash
usage: Compiler Augmented LLM Decompilation [-h] -p PROMPT -b BINARY -o OUTPUT -c COMPILER [-f FLAGS] -m MODE [-i ITERATIONS] [-k HEADLESS]
                                            [-s PROJ] [-q STUB] -u FUNC -l LANGUAGE [-z ACCURACY_MODE] [-a SOURCE_FILE]

This program uses chain of thought reasoning with LLMs and feedback from the compiler to improve decompilation results.

options:
  -h, --help            show this help message and exit
  -p PROMPT, --prompt PROMPT
                        Path to initial disassembly prompt.
  -b BINARY, --binary BINARY
                        Path to initial binary file.
  -o OUTPUT, --output OUTPUT
                        Path to output directory.
  -c COMPILER, --compiler COMPILER
                        Compiler binary to compile the files.
  -f FLAGS, --flags FLAGS
                        Compiler flags.
  -m MODE, --mode MODE  Feedback mode: (bindiff/disdiff/objdump/ghidra/ghidra-eval)
  -i ITERATIONS, --iterations ITERATIONS
                        Number of iterations in chain of thought.
  -k HEADLESS, --headless HEADLESS
                        Path to Ghidra headless binary (analyzeHeadless).
  -s PROJ, --proj PROJ  Path to Ghidra project directory.
  -q STUB, --stub STUB  Path to stub source file used in compiling.
  -u FUNC, --func FUNC  Name of the function to be decompiled.
  -l LANGUAGE, --language LANGUAGE
                        Language of initial binary file (C, CPP, Go, Rust).
  -z ACCURACY_MODE, --accuracy_mode ACCURACY_MODE
                        Mode of Accuracy Measurement (0: AST parsing) (1: Code Similarity)
  -a SOURCE_FILE, --source_file SOURCE_FILE
                        Path to source file used for accuracy measurements.
```
This file also has a function named generate_llm_response which can be easily modified to work with any LLM. Currently, it uses GPT-4.
## binexport.py
This file is a ghidra headless script that allows you to export the BinExport file for any given binary. It is used in bindiff mode in the main tool.
## pseudoexport.py
This file is a ghidra headless script that allows you to export the Ghidra pseudocode of a function from a binary. It is used in ghidra and ghidra_eval modes in the main tool.
## decompetition_disassembler
This folder is a clone of the [Disassembler Differ](https://github.com/decompetition/disassembler/tree/master) from the Decompetition team. It is used in the disdiff mode in the main tool.

## Demos
Here are the links to couple demos showing the tool in action.  
[Demo Showing LLM Fixing Compiler Errors](https://drive.google.com/file/d/1nqabvyky-_deZMT28ArDqjxYYw1U2d4Q/view?usp=sharing)  
[Demo Showing LLM Improving Decompilation](https://drive.google.com/file/d/1OhZh4RzZXkRNrxouDxtXqqe_EIHjfwYz/view?usp=sharing)  
