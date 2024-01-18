import re
import os
from bs4 import BeautifulSoup
import subprocess
import json
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser

language = get_language('c')
parser = get_parser('c')

GENERATE = True

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    exit_code = process.wait()

    output, error = output.decode("utf-8"), error.decode("utf-8")
    return exit_code, output, error

def traverse_tree(tree):
    func_sources = {}
    cursor = tree.walk()

    reached_root = False
    while reached_root == False:
        if cursor.node.type == "function_definition":
            queue = [cursor.node.child_by_field_name("declarator")]
            while queue:
                node = queue.pop(0)
                if node.type == 'function_declarator':
                    func_sources[node.child_by_field_name("declarator").text.decode('utf8')] = cursor.node.text.decode('utf8')
                    break
                else:
                    queue.extend(node.children)

        if cursor.goto_first_child():
            continue

        if cursor.goto_next_sibling():
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True

            if cursor.goto_next_sibling():
                retracing = False
    return func_sources

if GENERATE:
    f = open('./data/c-by-example.md')
    text = f.read()
    f.close()

    c_blocks = []
    blocks = re.findall(r'(\'\'\'|```)c\S*\s([\s\S]*?)(\'\'\'|```)', text, re.S)
    for block in blocks:
        c_blocks.append(block[1])

    for root, dirs, files in os.walk("./data/cppreference"):
        for filename in files:
            if filename.endswith(".html"):
                filepath = os.path.join(root, filename)
                with open(filepath) as f:
                    contents = f.read()
                    f.close()
                    soup = BeautifulSoup(contents, 'html.parser')
                    source_c_div = soup.find_all('div', class_='source-c')
                    for div in source_c_div:
                        extracted_text = div.get_text()
                        c_blocks.append(extracted_text)

    for root, dirs, files in os.walk("./data/c_corpus/"):
        for filename in files:
            if filename.endswith(".c"):
                filepath = os.path.join(root, filename)
                with open(filepath) as f:
                    contents = f.read()
                    f.close()
                    c_blocks.append(contents)

    c_blocks = list(set(c_blocks))
    print(len(c_blocks))

    if not os.path.exists("./output"):
        os.mkdir("./output")

    if not os.path.exists("./output/c_binaries"):
        os.mkdir("./output/c_binaries")

    if not os.path.exists("./output/c_prompts"):
        os.mkdir("./output/c_prompts")

    count = 0

    for i in range(len(c_blocks)):
        tree = parser.parse(bytes(c_blocks[i], "utf8"))
        func_sources = traverse_tree(tree)

        if len(func_sources) > 0:
            f = open(os.path.join("./output", f"temp.c"), "w")
            f.write(c_blocks[i])
            f.close()

            commands = [(f'clang -g -O0 ./output/temp.c -o ./output/c_binaries/c_{i}_debug_no.out', f'objdump -d -C -s --no-show-raw-insn ./output/c_binaries/c_{i}_debug_no.out'), 
                    (f'clang -g -O1 ./output/temp.c -o ./output/c_binaries/c_{i}_debug_one.out', f'objdump -d -C -s --no-show-raw-insn ./output/c_binaries/c_{i}_debug_one.out'),
                    (f'clang -g -O2 ./output/temp.c -o ./output/c_binaries/c_{i}_debug_two.out', f'objdump -d -C -s --no-show-raw-insn ./output/c_binaries/c_{i}_debug_two.out'),
                    (f'clang -g -O3 ./output/temp.c -o ./output/c_binaries/c_{i}_debug_three.out', f'objdump -d -C -s --no-show-raw-insn ./output/c_binaries/c_{i}_debug_three.out'),
                    (f'clang -O0 ./output/temp.c -o ./output/c_binaries/c_{i}_no_debug_no.out', f'objdump -d -C -s --no-show-raw-insn ./output/c_binaries/c_{i}_no_debug_no.out'), 
                    (f'clang -O1 ./output/temp.c -o ./output/c_binaries/c_{i}_no_debug_one.out', f'objdump -d -C -s --no-show-raw-insn ./output/c_binaries/c_{i}_no_debug_one.out'),
                    (f'clang -O2 ./output/temp.c -o ./output/c_binaries/c_{i}_no_debug_two.out', f'objdump -d -C -s --no-show-raw-insn ./output/c_binaries/c_{i}_no_debug_two.out'),
                    (f'clang -O3 ./output/temp.c -o ./output/c_binaries/c_{i}_no_debug_three.out', f'objdump -d -C -s --no-show-raw-insn ./output/c_binaries/c_{i}_no_debug_three.out')
                    ]

            for command, objdump_command in commands: 
                exit_code, output, error = run_command(command)
                if exit_code != 0:
                    continue
                else:
                    exit_code, output, error = run_command(objdump_command)
                    if exit_code == 0:
                        for func in func_sources:
                            pattern = re.compile(rf"<{func}>:\n(([^\n]+\n)*)")
                            match = re.search(pattern, output)
                            if match:
                                filename = objdump_command.split(' ')[-1].split('/')[-1]
                                disasm = re.sub(r'\s[0-9abcdef]+:\s', '', match.group(1))
                                f = open(os.path.join('./output/c_prompts', filename + "_" + str(count) + ".json"), "w")
                                if count % 2 == 0:
                                    json_payload = {
                                        "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nGenerate just the C code for the function that produced the above x86 64-bit assembly. The C code is idiomatic and uses functions, types, and structures from standard libraries.",
                                        "output": func_sources.get(func)
                                    }
                                else:
                                    json_payload = {
                                        "instruction": f"x86 64-bit Assembly:\n{func}:\n{disasm}\n//end of function {func}\nDecompile the above x86 64-bit assembly into C code. The C code is idiomatic and uses functions, types, and structures from standard libraries.",
                                        "output": func_sources.get(func)
                                    }
                                json.dump(json_payload, f)
                                f.close()
                            count += 1
                    else:
                        print(f"Error in objdump: {error}")
