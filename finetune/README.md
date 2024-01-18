# Decompilation Dataset Extraction/Finetuning Tools
This folder contains all the code to create the decompilation dataset and finetune a large language model using that data.
## Dataset
The current version of the dataset can be found here: [Decomp Dataset](https://huggingface.co/datasets/ap0009/decomp_dataset).
## Finetuning
You can finetune a model using this dataset with the following commands:
```bash
wget https://huggingface.co/datasets/ap0009/decomp_dataset/resolve/main/decomp_dataset.json
pip3 install axolotl
accelerate launch -m axolotl.cli.train deepseek.yml
```
After couple hours of training, you should get a ./qlora.out folder with the finetuned model.
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
## data subfolder
This data subfolder contains the README information on how to collect all the data for the original dataset. All the data sources should be put into this folder for the extraction tools to work properly.
## deepseek.yml
This file contains the configuration used to finetune deepseek-coder-6.7b-instruct with the decompilation data. This configuration can be modified to customize finetuning.
