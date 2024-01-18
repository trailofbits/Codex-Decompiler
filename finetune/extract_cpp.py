import re
import os
from bs4 import BeautifulSoup
import subprocess
import json
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
from tqdm import tqdm

language = get_language('cpp')
parser = get_parser('cpp')

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
        
        if node_type in {'class_specifier', 'struct_specifier', 'namespace_definition', 'namespace_alias_definition'}:
            if node.child_by_field_name('name'):
                name = node.child_by_field_name('name').text.decode('utf8')
                namespace_stack.append(name)
            if len(children) > 2:
                for i in range(2, len(children)):
                    find_functions(children[i], namespace_stack)
            if len(namespace_stack) > 0:
                namespace_stack.pop()
        
        elif node_type == "function_definition":
            queue = [node.child_by_field_name("declarator")]
            while queue:
                node2 = queue.pop(0)
                if node2.type == 'function_declarator':
                    full_function_name = '::'.join(namespace_stack + [node2.child_by_field_name("declarator").text.decode('utf8')])
                    func_sources[full_function_name] = node.text.decode('utf8')
                    break
                else:
                    queue.extend(node2.children)

        else:
            for child in children:
                find_functions(child, namespace_stack)

    find_functions(tree.root_node)
    return func_sources

if GENERATE:
    f = open('./data/c-by-example.md')
    text = f.read()
    f.close()

    cpp_blocks = []
    blocks = re.findall(r'(\'\'\'|```)cpp\S*\s([\s\S]*?)(\'\'\'|```)', text, re.S)
    for block in blocks:
        cpp_blocks.append(block[1])

    for root, dirs, files in os.walk("./data/cppreference"):
        for filename in files:
            if filename.endswith(".html"):
                filepath = os.path.join(root, filename)
                with open(filepath) as f:
                    contents = f.read()
                    f.close()
                    soup = BeautifulSoup(contents, 'html.parser')
                    source_cpp_div = soup.find_all('div', class_='source-cpp')
                    for div in source_cpp_div:
                        extracted_text = div.get_text()
                        cpp_blocks.append(extracted_text)

    for root, dirs, files in os.walk("./data/cpp_corpus"):
        for filename in files:
            if filename.endswith(".cpp") or filename.endswith(".cxx"):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath) as f:
                        contents = f.read()
                        f.close()
                        cpp_blocks.append(contents)
                except:
                    continue

    cpp_blocks = list(set(cpp_blocks))
    print(len(cpp_blocks))

    if not os.path.exists("./output"):
        os.mkdir("./output")

    if not os.path.exists("./output/cpp_binaries"):
        os.mkdir("./output/cpp_binaries")

    if not os.path.exists("./output/cpp_prompts"):
        os.mkdir("./output/cpp_prompts")

    count = 0

    for i in tqdm(range(len(cpp_blocks))):
        tree = parser.parse(bytes(cpp_blocks[i], "utf8"))
        func_sources = traverse_tree(tree)

        if len(func_sources) > 0:
            f = open(os.path.join("./output", f"temp.cpp"), "w")
            f.write(cpp_blocks[i])
            f.close()

            commands = [(f'clang++ -g -O0 ./output/temp.cpp -o ./output/cpp_binaries/cpp_{i}_debug_no.out', f'objdump -d -C -s --no-show-raw-insn ./output/cpp_binaries/cpp_{i}_debug_no.out'), 
                    (f'clang++ -g -O1 ./output/temp.cpp -o ./output/cpp_binaries/cpp_{i}_debug_one.out', f'objdump -d -C -s --no-show-raw-insn ./output/cpp_binaries/cpp_{i}_debug_one.out'),
                    (f'clang++ -g -O2 ./output/temp.cpp -o ./output/cpp_binaries/cpp_{i}_debug_two.out', f'objdump -d -C -s --no-show-raw-insn ./output/cpp_binaries/cpp_{i}_debug_two.out'),
                    (f'clang++ -g -O3 ./output/temp.cpp -o ./output/cpp_binaries/cpp_{i}_debug_three.out', f'objdump -d -C -s --no-show-raw-insn ./output/cpp_binaries/cpp_{i}_debug_three.out'),
                    (f'clang++ -O0 ./output/temp.cpp -o ./output/cpp_binaries/cpp_{i}_no_debug_no.out', f'objdump -d -C -s --no-show-raw-insn ./output/cpp_binaries/cpp_{i}_no_debug_no.out'), 
                    (f'clang++ -O1 ./output/temp.cpp -o ./output/cpp_binaries/cpp_{i}_no_debug_one.out', f'objdump -d -C -s --no-show-raw-insn ./output/cpp_binaries/cpp_{i}_no_debug_one.out'),
                    (f'clang++ -O2 ./output/temp.cpp -o ./output/cpp_binaries/cpp_{i}_no_debug_two.out', f'objdump -d -C -s --no-show-raw-insn ./output/cpp_binaries/cpp_{i}_no_debug_two.out'),
                    (f'clang++ -O3 ./output/temp.cpp -o ./output/cpp_binaries/cpp_{i}_no_debug_three.out', f'objdump -d -C -s --no-show-raw-insn ./output/cpp_binaries/cpp_{i}_no_debug_three.out')
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
                                pattern = re.compile(rf"<{func}\(\S*\)>:\n(([^\n]+\n)*)")
                                match = re.search(pattern, output)
                            except:
                                continue
                            if match:
                                filename = objdump_command.split(' ')[-1].split('/')[-1]
                                disasm = re.sub(r'\s[0-9abcdef]+:\s', '', match.group(2))
                                f = open(os.path.join('./output/cpp_prompts', filename + "_" + str(count) + ".json"), "w")
                                if count % 2 == 0:
                                    json_payload = {
                                        "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nGenerate just the C++ code for the function that produced the above x86 64-bit assembly. The C++ code is idiomatic and uses functions, types, and structures from standard libraries.",
                                        "output": func_sources.get(func)
                                    }
                                else:
                                    json_payload = {
                                        "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nDecompile the above x86 64-bit assembly into C++ code. The C++ code is idiomatic and uses functions, types, and structures from standard libraries.",
                                        "output": func_sources.get(func)
                                    }
                                json.dump(json_payload, f)
                                f.close()
                            else:
                                try:
                                    pattern = re.compile(rf"<{func}>:\n(([^\n]+\n)*)")
                                    match = re.search(pattern, output)
                                except:
                                    continue
                                if match:
                                    filename = objdump_command.split(' ')[-1].split('/')[-1]
                                    disasm = re.sub(r'\s[0-9abcdef]+:\s', '', match.group(1))
                                    f = open(os.path.join('./output/cpp_prompts', filename + "_" + str(count) + ".json"), "w")
                                    if count % 2 == 0:
                                        json_payload = {
                                            "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nGenerate just the C++ code for the function that produced the above x86 64-bit assembly. The C++ code is idiomatic and uses functions, types, and structures from standard libraries.",
                                            "output": func_sources.get(func)
                                        }
                                    else:
                                        json_payload = {
                                            "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nDecompile the above x86 64-bit assembly into C++ code. The C++ code is idiomatic and uses functions, types, and structures from standard libraries.",
                                            "output": func_sources.get(func)
                                        }
                                    json.dump(json_payload, f)
                                    f.close()
                            count += 1
                    else:
                        print(f"Error in objdump: {error}")
