import re
import os
from bs4 import BeautifulSoup
import subprocess
import json
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
from tqdm import tqdm

language = get_language('go')
parser = get_parser('go')

GENERATE = True

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    exit_code = process.wait()

    output, error = output.decode("utf-8"), error.decode("utf-8")
    return exit_code, output, error

def traverse_tree(tree):
    func_sources = {}
    def find_functions(node):
        node_type = node.type
        children = node.children
        
        if node_type in {'function_declaration', 'method_declaration'}:
            if node.child_by_field_name('name'):
                name = node.child_by_field_name('name').text.decode('utf8')
                func_sources[name] = node.text.decode('utf8')
        else:
            for child in children:
                find_functions(child)

    find_functions(tree.root_node)
    return func_sources

if GENERATE:
    go_blocks = []
    for root, dirs, files in os.walk("./data/go_corpus/"):
        for filename in files:
            if filename.endswith(".go"):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath) as f:
                        contents = f.read()
                        f.close()
                        go_blocks.append(contents)
                except:
                    continue

    go_blocks = list(set(go_blocks))
    print(len(go_blocks))

    if not os.path.exists("./output"):
        os.mkdir("./output")

    if not os.path.exists("./output/go_binaries"):
        os.mkdir("./output/go_binaries")

    if not os.path.exists("./output/go_prompts"):
        os.mkdir("./output/go_prompts")

    count = 0

    for i in tqdm(range(len(go_blocks))):
        tree = parser.parse(bytes(go_blocks[i], "utf8"))
        func_sources = traverse_tree(tree)

        if len(func_sources) > 0:
            f = open(os.path.join("./output", f"temp.go"), "w")
            f.write(go_blocks[i])
            f.close()

            commands = [(f'go build -o ./output/go_binaries/go_{i}.out ./output/temp.go', f'objdump -d -C --no-show-raw-insn ./output/go_binaries/go_{i}.out')]

            for command, objdump_command in commands:
                exit_code, output, error = run_command(command)
                if exit_code != 0:
                    continue
                else:
                    exit_code, output, error = run_command(objdump_command)
                    if exit_code == 0:
                        for func in func_sources:
                            pattern = re.compile(rf"<main.{func}\(\S*\)>:\n(([^\n]+\n)*)")
                            match = re.search(pattern, output)
                            if match:
                                filename = objdump_command.split(' ')[-1].split('/')[-1]
                                disasm = re.sub(r'\s[0-9abcdef]+:\s', '', match.group(2))
                                f = open(os.path.join('./output/go_prompts', filename + "_" + str(count) + ".json"), "w")
                                if count % 2 == 0:
                                    json_payload = {
                                        "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nGenerate just the Go code for the function that produced the above x86 64-bit assembly. The Go code is idiomatic and uses standard libraries and channels.",
                                        "output": func_sources.get(func)
                                    }
                                else:
                                    json_payload = {
                                        "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nDecompile the above x86 64-bit assembly into Go code. The Go code is idiomatic and uses standard libraries and channels.",
                                        "output": func_sources.get(func)
                                    }
                                json.dump(json_payload, f)
                                f.close()
                            else:
                                try:
                                    pattern = re.compile(rf"<main.{func}>:\n(([^\n]+\n)*)")
                                    match = re.search(pattern, output)
                                except:
                                    continue
                                if match:
                                    filename = objdump_command.split(' ')[-1].split('/')[-1]
                                    disasm = re.sub(r'\s[0-9abcdef]+:\s', '', match.group(1))
                                    f = open(os.path.join('./output/go_prompts', filename + "_" + str(count) + ".json"), "w")
                                    if count % 2 == 0:
                                        json_payload = {
                                            "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nGenerate just the Go code for the function that produced the above x86 64-bit assembly. The Go code is idiomatic and uses standard libraries and channels.",
                                            "output": func_sources.get(func)
                                        }
                                    else:
                                        json_payload = {
                                            "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nDecompile the above x86 64-bit assembly into Go code. The Go code is idiomatic and uses standard libraries and channels.",
                                            "output": func_sources.get(func)
                                        }
                                    json.dump(json_payload, f)
                                    f.close()
                            count += 1
                    else:
                        print(f"Error in objdump: {error}")
