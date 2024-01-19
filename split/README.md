# Decompilation Splitting Demo
This repo contains all the code for the demo of splitting the disassembly of a large function into chunks and then decompiling each chunk.
The technique used to split the disassembly in this demo is label splitting where the disassembly is divided into sections based on the different branch labels that exist.
## function_split.py
This file contains the main code for the demo. It can be run using the following command:
```bash
python3 function_split.py
```
The demo will then run.  
Note that this might take a lot of time depending on the number of sections that exist.  
There is a generate_llm_response function in this file which can be easily modified to work with any LLM.  
For this demo, the data used is from the rumrum binary from the 2021 Decompetition challenge. There are some variables in the file that can be easily changed to work with any program.
# Video of Demo
Here is a link to a video demonstrating the decompilation splitting technique:  
[Video #1](https://drive.google.com/file/d/1tNZp2ygdOU-gBVgfqtBYXy7GI8m5hld2/view?usp=sharing)
