import re
import os
from bs4 import BeautifulSoup
import subprocess
import json
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
import faulthandler
import signal
from tqdm import tqdm

language = get_language('rust')
parser = get_parser('rust')

GENERATE = True

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    exit_code = process.wait()

    output, error = output.decode("utf-8"), error.decode("utf-8")
    return exit_code, output, error

def traverse_tree(tree):
    func_sources = {}
    def find_functions(node, namespace_stack=[]):
        node_type = node.type
        children = node.children
        
        if node_type in {'struct_item', 'trait_item'}:
            if node.child_by_field_name('name'):
                name = node.child_by_field_name('name').text.decode('utf8')
                namespace_stack.append(name)
            if len(children) > 2:
                for i in range(2, len(children)):
                    find_functions(children[i], namespace_stack)
            if len(namespace_stack) > 0:
                namespace_stack.pop()
        elif node_type == "impl_item":
            if node.child_by_field_name('trait'):
                namespace_stack.append(node.child_by_field_name('trait').text.decode('utf8'))
            elif node.child_by_field_name('type'):
                namespace_stack.append(node.child_by_field_name('type').text.decode('utf8'))
            if len(children) > 2:
                for i in range(2, len(children)):
                    find_functions(children[i], namespace_stack)
            if len(namespace_stack) > 0:
                namespace_stack.pop()
        elif node_type == "function_item":
            full_function_name = '::'.join(namespace_stack + [node.child_by_field_name("name").text.decode('utf8')])
            func_sources[full_function_name] = node.text.decode('utf8')
        else:
            for child in children:
                find_functions(child, namespace_stack)

    find_functions(tree.root_node)
    return func_sources

if GENERATE:
    rust_blocks = []
    for root, dirs, files in os.walk("./data/rust-by-example"):
        for filename in files:
            if filename.endswith(".md"):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath) as f:
                        contents = f.read()
                        f.close()
                        blocks = re.findall(r'(\'\'\'|```)rust\S*\s([\s\S]*?)(\'\'\'|```)', contents, re.S)
                        for block in blocks:
                            rust_blocks.append(block[1])
                except:
                    continue

    for root, dirs, files in os.walk("./data/rust_corpus"):
        for filename in files:
            if filename.endswith(".rs"):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath) as f:
                        contents = f.read()
                        f.close()
                        rust_blocks.append(contents)
                except:
                    continue

    rust_blocks = list(set(rust_blocks))
    print(len(rust_blocks))

    if not os.path.exists("./output"):
        os.mkdir("./output")

    if not os.path.exists("./output/rust_binaries"):
        os.mkdir("./output/rust_binaries")

    if not os.path.exists("./output/rust_prompts"):
        os.mkdir("./output/rust_prompts")

    count = 0

    for i in tqdm(range(len(rust_blocks))):
        tree = parser.parse(bytes(rust_blocks[i], "utf8"))
        func_sources = traverse_tree(tree)

        if len(func_sources) > 0:
            f = open(os.path.join("./output", f"temp.rs"), "w")
            f.write(rust_blocks[i])
            f.close()

            commands = [(f'rustc --edition 2015 -g ./output/temp.rs -o ./output/rust_binaries/rust_{i}_debug_no_2015.out', f'objdump -d -C -s --no-show-raw-insn ./output/rust_binaries/rust_{i}_debug_no_2015.out'), 
                    (f'rustc --edition 2015 -g -O ./output/temp.rs -o ./output/rust_binaries/rust_{i}_debug_two_2015.out', f'objdump -d -C -s --no-show-raw-insn ./output/rust_binaries/rust_{i}_debug_two_2015.out'),
                    (f'rustc --edition 2015 ./output/temp.rs -o ./output/rust_binaries/rust_{i}_no_debug_no_2015.out', f'objdump -d -C -s --no-show-raw-insn ./output/rust_binaries/rust_{i}_no_debug_no_2015.out'),
                    (f'rustc --edition 2018 -g ./output/temp.rs -o ./output/rust_binaries/rust_{i}_debug_no_2018.out', f'objdump -d -C -s --no-show-raw-insn ./output/rust_binaries/rust_{i}_debug_no_2018.out'), 
                    (f'rustc --edition 2018 -g -O ./output/temp.rs -o ./output/rust_binaries/rust_{i}_debug_two_2018.out', f'objdump -d -C -s --no-show-raw-insn ./output/rust_binaries/rust_{i}_debug_two_2018.out'),
                    (f'rustc --edition 2018 ./output/temp.rs -o ./output/rust_binaries/rust_{i}_no_debug_no_2018.out', f'objdump -d -C -s --no-show-raw-insn ./output/rust_binaries/rust_{i}_no_debug_no_2018.out'),
                    (f'rustc --edition 2021 -g ./output/temp.rs -o ./output/rust_binaries/rust_{i}_debug_no_2021.out', f'objdump -d -C -s --no-show-raw-insn ./output/rust_binaries/rust_{i}_debug_no_2021.out'), 
                    (f'rustc --edition 2021 -g -O ./output/temp.rs -o ./output/rust_binaries/rust_{i}_debug_two_2021.out', f'objdump -d -C -s --no-show-raw-insn ./output/rust_binaries/rust_{i}_debug_two_2021.out'),
                    (f'rustc --edition 2021 ./output/temp.rs -o ./output/rust_binaries/rust_{i}_no_debug_no_2021.out', f'objdump -d -C -s --no-show-raw-insn ./output/rust_binaries/rust_{i}_no_debug_no_2021.out'),
                    ]

            for command, objdump_command in commands:
                exit_code, output, error = run_command(command)
                if exit_code != 0:
                    continue
                else:
                    exit_code, output, error = run_command(objdump_command)
                    if exit_code == 0:
                        for func in func_sources:
                            try:
                                pattern = re.compile(rf"<temp::{func}\(\S*\)>:\n(([^\n]+\n)*)")
                                match = re.search(pattern, output)
                            except:
                                continue
                            if match:
                                filename = objdump_command.split(' ')[-1].split('/')[-1]
                                disasm = re.sub(r'\s[0-9abcdef]+:\s', '', match.group(2))
                                f = open(os.path.join('./output/rust_prompts', filename + "_" + str(count) + ".json"), "w")
                                if count % 2 == 0:
                                    json_payload = {
                                        "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nGenerate just the Rust code for the function that produced the above x86 64-bit assembly. The Rust code is idiomatic and uses macros, channels, and functions or data types from standard libraries.",
                                        "output": func_sources.get(func)
                                    }
                                else:
                                    json_payload = {
                                        "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nDecompile the above x86 64-bit assembly into Rust code. The Rust code is idiomatic and uses macros, channels, and functions or data types from standard libraries.",
                                        "output": func_sources.get(func)
                                    }
                                json.dump(json_payload, f)
                                f.close()
                            else:
                                try:
                                    pattern = re.compile(rf"<temp::{func}>:\n(([^\n]+\n)*)")
                                    match = re.search(pattern, output)
                                except:
                                    continue
                                if match:
                                    filename = objdump_command.split(' ')[-1].split('/')[-1]
                                    disasm = re.sub(r'\s[0-9abcdef]+:\s', '', match.group(1))
                                    f = open(os.path.join('./output/rust_prompts', filename + "_" + str(count) + ".json"), "w")
                                    if count % 2 == 0:
                                        json_payload = {
                                            "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nGenerate just the Rust code for the function that produced the above x86 64-bit assembly. The Rust code is idiomatic and uses macros, channels, and functions or data types from standard libraries.",
                                            "output": func_sources.get(func)
                                        }
                                    else:
                                        json_payload = {
                                            "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nDecompile the above x86 64-bit assembly into Rust code. The Rust code is idiomatic and uses macros, channels, and functions or data types from standard libraries.",
                                            "output": func_sources.get(func)
                                        }
                                    json.dump(json_payload, f)
                                    f.close()
                            count += 1
                    else:
                        print(f"Error in objdump: {error}")
