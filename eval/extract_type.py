# This script extracts all the unique type names of an AST from a json file (node-types.json) of the tree-sitter library.
import json

def extract_unique_types(filename):
    with open(filename, 'r') as f:
        data = json.load(f)

    unique_types = set()
    extract_types(data, unique_types)

    return list(unique_types)

def extract_types(item, unique_types):
    if isinstance(item, dict):
        for key, value in item.items():
            if key == 'type':
                if isinstance(value, str):
                    unique_types.add(value)
            extract_types(value, unique_types)
    elif isinstance(item, list):
        for i in item:
            extract_types(i, unique_types)

filename = 'cpp-types.json'
unique_types = extract_unique_types(filename)
for typ in unique_types:
    print(typ)
