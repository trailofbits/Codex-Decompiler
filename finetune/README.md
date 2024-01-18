# Decompilation Dataset Extraction/Finetuning Tools
This folder contains all the code to create the decompilation dataset and finetune a large language model using that data.
## Dataset
The current version of the dataset can be found here: [Decomp Dataset](https://huggingface.co/datasets/ap0009/decomp_dataset).
## extract_*.py
The extract_c.py, extract_cpp.py, extract_go.py, and extract_rust.py are all standalone scripts that use the files from the data folder to extract disassembly and source pairings which will be then stored in an output folder.  
The scripts can be ran as follows:
```bash
python3 extract_*.py
```
Please make sure to have the compilers for each language installed (C: clang, CPP: clang++, Go: go, Rust: rustc) and all the data cloned in the right location in the data subfolder.
To create your own custom dataset, you can modify the compiler flags used or the data in the data subfolder.
## merge.py
This file is a utility script that allows you to combine all the json output files from the extraction tools into one singular json. The tool can be simply invoked by just calling the filename with python.
