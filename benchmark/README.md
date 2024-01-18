# Decompilation Benchmarking Tool
This folder contains all the code for the decompilation benchmarking tool which can test the accuracy of a given LLM in decompilation tasks. 
This tool can be used with the dataset provided in the eval folder.
For measuring the accuracy of the measurement, there are two modes where one mode scores the output by parsing the AST of the decompilation and the other mode determines the cosine similarity of the output.
## Usage
The tool can be used as follows:
```bash
python3 benchmark.py -p PATH_TO_PROMPTS -s PATH_TO_SOURCE_FILES -l LANGUAGE -m MODE
```
For the mode command line argument there are two values: (0: AST parsing) and (1: Code Similarity). In the benchmark.py file, there is a function named generate_llm_response which can be modified to work with any LLM.
