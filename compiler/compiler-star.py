import os 
import argparse
import subprocess
import re
import difflib
import torch
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from decompetition_disassembler.bindings import get_disasm, diff_all
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
from collections import Counter
from unixcoder import UniXcoder

differ = difflib.Differ()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = UniXcoder("microsoft/unixcoder-base-nine")
model.to(device)

def compile(compiler, output_name, source_file, flags):
    if flags:
        if compiler == "go":
            command = f"{compiler} build {flags} -o {output_name} {source_file}"
        else:
            command = f"{compiler} {flags} {source_file} -o {output_name}"
    else:
        if compiler == "go":
            command = f"{compiler} build -o {output_name} {source_file}"
        else:
            command = f"{compiler} {source_file} -o {output_name}"
    return run_command(command)

def binexport(headless_path, proj_folder, binary_path, output_path):
    os.environ["BINEXPORT_OUTPUT_PATH"] = output_path
    command = f"{headless_path} {proj_folder} test -deleteProject -overwrite -import {binary_path} -postscript {os.path.join(os.getcwd(), 'binexport.py')}"
    exit_code, output, error = run_command(command)
    
    if exit_code != 0:
        print(f"Error in binexporting {binary_path}!")
        if not output.isspace():
            print(f"Stdout:\n{output}\n")
        if not error.isspace():
            print(f"Stderr:\n{error}\n")
        quit()

def bindiff(initial_diff_path, diff_path, output_dir):
    command = f"bindiff --primary {initial_diff_path} --secondary {diff_path} --output_dir {output_dir}"
    exit_code, output, error = run_command(command)

    if exit_code != 0:
        print(f"Error in bindiff!")
        if not output.isspace():
            print(f"Stdout:\n{output}\n")
        if not error.isspace():
            print(f"Stderr:\n{error}\n")
        quit()
    else:
        return output

def objdump(binary_path, func_name):
    command = f"objdump -d -C -s --no-show-raw-insn --no-addresses {binary_path}"
    exit_code, output, error = run_command(command)

    if exit_code != 0:
        print(f"Error in objdump!")
        if not output.isspace():
            print(f"Stdout:\n{output}\n")
        if not error.isspace():
            print(f"Stderr:\n{error}\n")
        quit()
    else:
        pattern = re.compile(rf"<{func_name}>:\n([^\n]+\n)*")
        match = re.search(pattern, output)
        if match:
            return re.sub(r'((-?(0x)?)[\dabcdef]+\(.*?\))|(\<(.+)[^\n]?(\+|\-)[^\n]?((0x)?[\dabcdef]+)\>)', '<offset(?)>', match.group())
        else:
            print("Function not found in objdump output.")
            quit()

def get_ghidra_pseudo(headless_path, proj_folder, binary_path, output_path, func_name):
    os.environ["PSEUDOCODE_OUTPUT_PATH"] = output_path
    os.environ['FUNC_NAME'] = func_name
    command = f"{headless_path} {proj_folder} test -deleteProject -overwrite -import {binary_path} -postscript {os.path.join(os.getcwd(), 'pseudoexport.py')}"
    exit_code, output, error = run_command(command)

    output_file = os.path.join(output_path, os.path.basename(binary_path) + "_" + func_name.replace(":","_") + ".txt")
    if exit_code != 0 or not os.path.exists(output_file):
        print(f"Error in exporting pseudocode {binary_path}!")
        if not output.isspace():
            print(f"Stdout:\n{output}\n")
        if not error.isspace():
            print(f"Stderr:\n{error}\n")
        quit()
    else:
        f = open(output_file, "r")
        output = f.read()
        f.close()
        return output

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    exit_code = process.wait()

    output, error = output.decode("utf-8"), error.decode("utf-8")
    return exit_code, output, error

def clean_output(text):
    pattern = re.compile(r"('''|```)\S+\n([\s\S]*?)('''|```)")

    match = re.search(pattern, text)
    if match:
        return match.group(2)
    else:
        return text

def generate_decomp(prompt):
    llm = AzureChatOpenAI(deployment_name="gpt-4-32k")

    message = [SystemMessage(content="You are a helpful AI coding assistant. You are to only generate code to accomplish the user given task. Do not provide any explanation or description. Just provide only code."), HumanMessage(content=prompt)]

    output = clean_output(llm(message).content)

    return output

def write_source(output_dir, language, decomp, stub):
    if language == "go":
        filename = os.path.join(output_dir, "source.go")
    elif language == "rust":
        filename = os.path.join(output_dir, "source.rs")
    elif language == "cpp":
        filename = os.path.join(output_dir, "source.cpp")
    else:
        filename = os.path.join(output_dir, "source.c")
    
    if stub and os.path.exists(stub):
        f = open(stub, "r")
        stub = f.read()
        f.close()
        full_source = stub + "\n" + decomp
    else:
        full_source = decomp

    f = open(filename, "w")
    f.write(full_source)
    f.close()

    return filename

def eval_c(code):
    language = get_language('c')
    parser = get_parser('c')

    tree = parser.parse(bytes(code, "utf8"))

    function_calls = []
    branches = 0

    macros = set()

    def eval_exp(node):
        if node.type == "binary_expression":
           left_node = node.child_by_field_name("left")
           operator = node.child_by_field_name("operator")
           right_node = node.child_by_field_name("right")
           (count, output) = eval_exp(left_node)
           (count2, output2) = eval_exp(right_node)
           if operator.type == "||" or operator.type == "&&":
               return (1 + count + count2, True)
           else:
               return (count + count2, True)
        elif node.type == "parenthesized_expression":
            return eval_exp(node.child(1))
        elif node.type == "comma_expression":
            left_node = node.child_by_field_name("left")
            right_node = node.child_by_field_name("right")
            (count, output) = eval_exp(left_node)
            (count2, output2) = eval_exp(right_node)
            return (count + count2, output or output2)
        elif node.type == "conditional_expression":
            (count, output) = eval_exp(node.child(0))
            (count2, output2) = eval_exp(node.child(1))
            (count3, output3) = eval_exp(node.child(2))
            return (count + count2 + count3, output or output2 or output3)
        else:
            return (0, False)


    def traverse_tree(tree):
        cursor = tree.walk()

        reached_root = False
        while reached_root == False:
            nonlocal branches
            nonlocal function_calls
            if cursor.node.type == "call_expression":
                function_node = cursor.node.child_by_field_name('function')
                if function_node is not None:
                    name = function_node.text.decode('utf8')
                    if name not in macros:
                        function_calls.append(name)
            elif cursor.node.type in {"for_statement", "do_statement", "while_statement", "if_statement", "conditional_expression"}:
                condition_node = cursor.node.child_by_field_name('condition')
                (eval_count, binary_bool) = eval_exp(condition_node)
                if eval_count == 0:
                    if binary_bool:
                        branches += 1
                    else:
                        if condition_node.type == "parenthesized_expression":
                            if condition_node.child(1).type != "number_literal" and condition_node.child(1).type != "preproc_defined":
                                branches += 1
                        elif cursor.node.type == "conditional_expression" and condition_node.type != "number_literal" and condition_node.type != "preproc_defined":
                            branches +=1
                else:
                    branches += (eval_count + 1)
            elif cursor.node.type == "case_statement":
                if cursor.node.child(0).text.decode('utf8') != "default":
                    branches += 1
            elif cursor.node.type == "preproc_function_def":
                macros.add(cursor.node.child_by_field_name("name").text.decode('utf8'))

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

    traverse_tree(tree)

    return (branches, function_calls)

def eval_cpp(code):
    language = get_language('cpp')
    parser = get_parser('cpp')

    tree = parser.parse(bytes(code, "utf8"))

    function_calls = []
    branches = 0

    macros = set()

    def eval_exp(node):
        if node.type == "binary_expression":
           left_node = node.child_by_field_name("left")
           operator = node.child_by_field_name("operator")
           right_node = node.child_by_field_name("right")
           (count, output) = eval_exp(left_node)
           (count2, output2) = eval_exp(right_node)
           if operator.type == "||" or operator.type == "&&":
               return (1 + count + count2, True)
           else:
               return (count + count2, True)
        elif node.type == "parenthesized_expression":
            return eval_exp(node.child(1))
        elif node.type == "comma_expression":
            left_node = node.child_by_field_name("left")
            right_node = node.child_by_field_name("right")
            (count, output) = eval_exp(left_node)
            (count2, output2) = eval_exp(right_node)
            return (count + count2, output or output2)
        elif node.type == "conditional_expression":
            (count, output) = eval_exp(node.child(0))
            (count2, output2) = eval_exp(node.child(1))
            (count3, output3) = eval_exp(node.child(2))
            return (count + count2 + count3, output or output2 or output3)
        else:
            return (0, False)


    def traverse_tree(tree):
        cursor = tree.walk()

        reached_root = False
        while reached_root == False:
            nonlocal branches
            nonlocal function_calls
            if cursor.node.type == "call_expression":
                function_node = cursor.node.child_by_field_name('function')
                if function_node is not None:
                    name = function_node.text.decode('utf8')
                    if name not in macros:
                        function_calls.append(name)
            elif cursor.node.type in {"for_statement", "do_statement", "while_statement", "if_statement", "conditional_expression", "static_assert_declaration"}:
                condition_node = cursor.node.child_by_field_name('condition')
                if cursor.node.type in {"if_statement", "while_statement"}:
                    condition_node = condition_node.child_by_field_name("value")
                (eval_count, binary_bool) = eval_exp(condition_node)
                if eval_count == 0:
                    if binary_bool:
                        branches += 1
                    else:
                        if condition_node.type == "parenthesized_expression":
                            if condition_node.child(1).type != "number_literal" and condition_node.child(1).type != "preproc_defined":
                                branches += 1
                        elif cursor.node.type == "conditional_expression" and condition_node.type != "number_literal" and condition_node.type != "preproc_defined":
                            branches +=1
                else:
                    branches += (eval_count + 1)
            elif cursor.node.type == "case_statement":
                if cursor.node.child(0).text.decode('utf8') != "default":
                    branches += 1
            elif cursor.node.type == "preproc_function_def":
                macros.add(cursor.node.child_by_field_name("name").text.decode('utf8'))

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

    traverse_tree(tree)

    return (branches, function_calls)

def eval_rust(code):
    language = get_language('rust')
    parser = get_parser('rust')

    tree = parser.parse(bytes(code, "utf8"))

    function_calls = []
    branches = 0

    def eval_exp(node):
        if node.type == "binary_expression":
           left_node = node.child_by_field_name("left")
           operator = node.child_by_field_name("operator")
           right_node = node.child_by_field_name("right")
           (count, output) = eval_exp(left_node)
           (count2, output2) = eval_exp(right_node)
           if operator.type == "||" or operator.type == "&&":
               return (1 + count + count2, True)
           else:
               return (count + count2, True)
        elif node.type == "parenthesized_expression" or node.type == "let_chain":
            return eval_exp(node.child(0))
        elif node.type == "let_condition" or node.type == "for_expression":
            return eval_exp(node.child_by_field_name("value"))
        elif node.type == "if_expresion" or node.type == "while_expression" or node.type == "match_pattern":
            return eval_exp(node.child_by_field_name("condition"))
        else:
            return (0, False)


    def traverse_tree(tree):
        cursor = tree.walk()

        reached_root = False
        while reached_root == False:
            nonlocal branches
            nonlocal function_calls
            if cursor.node.type == "call_expression":
                function_node = cursor.node.child_by_field_name('function')
                if function_node is not None:
                    function_calls.append(function_node.text.decode('utf8'))
            elif cursor.node.type in {"for_expression", "if_expression", "while_expression", "match_pattern"}:
                if cursor.node.type == "match_pattern":
                    condition_node = cursor.node.child_by_field_name('condition')
                    if condition_node:
                        (eval_count, binary_bool) = eval_exp(condition_node)
                        if eval_count == 0:
                            if binary_bool or "literal" not in condition_node.type:
                                branches += 1
                        else:
                            branches += (eval_count + 1)
                    else:
                        branches += 1
                else:
                    if cursor.node.type == "for_expression":
                        condition_node = cursor.node.child_by_field_name("value")
                    else:
                        condition_node = cursor.node.child_by_field_name('condition')
                    
                    (eval_count, binary_bool) = eval_exp(condition_node)
                    if eval_count == 0:
                        if binary_bool or "literal" not in condition_node.type:
                            branches += 1
                    else:
                        branches += (eval_count + 1)

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

    traverse_tree(tree)

    return (branches, function_calls)

def eval_go(code):
    language = get_language('go')
    parser = get_parser('go')

    tree = parser.parse(bytes(code, "utf8"))

    function_calls = []
    branches = 0

    def eval_exp(node):
        if node.type == "binary_expression":
           left_node = node.child_by_field_name("left")
           operator = node.child_by_field_name("operator")
           right_node = node.child_by_field_name("right")
           (count, output) = eval_exp(left_node)
           (count2, output2) = eval_exp(right_node)
           if operator.type == "||" or operator.type == "&&":
               return (1 + count + count2, True)
           else:
               return (count + count2, True)
        elif node.type == "parenthesized_expression":
            return eval_exp(node.child(0))
        else:
            return (0, False)


    def traverse_tree(tree):
        cursor = tree.walk()

        reached_root = False
        while reached_root == False:
            nonlocal branches
            nonlocal function_calls
            if cursor.node.type == "call_expression":
                function_node = cursor.node.child_by_field_name('function')
                if function_node is not None:
                    function_calls.append(function_node.text.decode('utf8'))
            elif cursor.node.type == "for_statement":
                condition_node = None
                for child in cursor.node.children:
                    if child.type == "for_clause":
                        condition_node = child.child_by_field_name("condition")
                        break
                    elif child.type == "range_clause":
                        branches += 1
                        break
                    elif "expression" in child.type:
                        condition_node = child
                        break
                if condition_node:
                    (eval_count, binary_bool) = eval_exp(condition_node)
                    if eval_count == 0:
                        if binary_bool or "literal" not in child.type:
                            branches += 1
                    else:
                        branches += (eval_count + 1)
            elif cursor.node.type == "if_statement":
                condition_node = cursor.node.child_by_field_name("condition")
                (eval_count, binary_bool) = eval_exp(condition_node)
                if eval_count == 0:
                    if binary_bool or "literal" not in condition_node.type:
                        branches += 1
                else:
                    branches += (eval_count + 1)
            elif cursor.node.type == "expression_case":
                branches += 1

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

    traverse_tree(tree)

    return (branches, function_calls)

eval_funcs = {"c": eval_c, "cpp": eval_cpp, "rust": eval_rust, "go": eval_go}

def compile_error_prompt(initial_prompt, decomp, error):
    return f"The previous decompilation resulted in a compiler error. Fix the errors and re-generate the pseudocode.\nCompiler Error:\n{error}\nPrevious Decompilation:\n{decomp}"

def bindiff_prompt(bindiff_out, language, func_name, decomp):
    bindiff_out = "\n".join(bindiff_out.split("\n")[1:-1])
    return f"The previous decompilation was able to be compiled.\nPrevious Decompilation:\n{decomp}\nHere is the bindiff output between the original binary and the decompiled code binary.\n{bindiff_out}\nUsing this bindiff output, re-generate {language} code for the {func_name} function so that there is no difference. The {language} code is idiomatic and uses functions, structures, and more from the standard libraries."

def diff_prompt(diff, language, func_name, decomp):
    return f"The previous decompilation was able to be compiled.\nPrevious Decompilation:\n{decomp}\nHere is a diff between the disassembly of the original binary and the decompiled code binary:\n{diff}\nUsing this diff of the disassembly, re-generate {language} code for the {func_name} function so that there is no difference in the disassembly. The {language} code is idiomatic and uses functions, structures, and more from the standard libraries."

def pseudo_diff_prompt(diff, language, func_name, decomp):
    return f"The previous decompilation was able to be compiled.\nPrevious Decompilation:\n{decomp}\nHere is a diff between the pseudocode of the function in the original binary and the decompiled code binary:\n{diff}\nUsing this diff, re-generate {language} code for the {func_name} function so that there is no difference in the pseudocode. The {language} code is idiomatic and uses functions, structures, and more from the standard libraries."

def eval_diff_prompt(language, func_name, decomp, initial_pseudo, diff_branches, shared_calls, missing_calls, extra_calls):
    output = f"The previous decompilation was able to be compiled.\nPrevious Decompilation:\n{decomp}\Here is the pseudocode for the original binary:\n{initial_pseudo}\n"
    if diff_branches > 0:
        output += f"The decompilation of the original binary has {diff_branches} extra branches in the code.\n"
    elif diff_branches < 0:
        output += f"The decompilation of the original binary is missing {diff_branches} branches in the code.\n"
    if len(shared_calls) > 0:
        output += f"Here are the shared function calls between the decompilation and the pseudocode of the original binary: {','.join(shared_calls)}\n"
    if len(missing_calls) > 0:
        output += f"Here are the function calls that are missing in the decompilation from the pseudocode of the original binary: {','.join(missing_calls)}\n"
    if len(extra_calls) > 0:
        output += f"Here are the extra function calls in the decompilation and not in the pseudocode of the original binary: {','.join(extra_calls)}\n"
    output += f"Using this information, re-generate {language} code for the {func_name} function so that there is no difference. The {language} code is idiomatic and uses functions, structures, and more from the standard libraries."

    return output

def run_eval(source, response, language, mode):
    if mode == 0:
        eval_func = eval_funcs.get(language)
        (original_branches, original_calls) = eval_func(source)
        (new_branches, new_calls) = eval_func(response)
        total = original_branches + original_calls
        branches_diff = abs(new_branches - original_branches)
        calls_diff = abs(new_calls - original_calls)
        weighted_error = (branches_diff / original_branches) * (original_branches / total) + (calls_diff / original_calls) * (original_calls / total)

        print(f"Error between decompilation and source: {weighted_error}")
        
        return weighted_error
    else:
        tokens_ids = model.tokenize([source],max_length=1023,mode="<encoder-only>")
        source_ids = torch.tensor(tokens_ids).to(device)
        tokens_embeddings,source_embedding = model(source_ids)

        tokens_ids = model.tokenize([response],max_length=1023,mode="<encoder-only>")
        source_ids = torch.tensor(tokens_ids).to(device)
        tokens_embeddings,response_embedding = model(source_ids)

        norm_source_embedding = torch.nn.functional.normalize(source_embedding, p=2, dim=1)
        norm_response_embedding = torch.nn.functional.normalize(response_embedding, p=2, dim=1)

        similarity = torch.einsum("ac,bc->ab",norm_source_embedding,norm_response_embedding).item()
        
        print(f"Code similarity between decompilation and source: {similarity}")
        
        return similarity

def main():
    parser = argparse.ArgumentParser(
                prog='Compiler Augmented LLM Decompilation',
                description='This program uses chain of thought reasoning with LLMs and feedback from the compiler to improve decompilation results.')
    parser.add_argument('-p', '--prompt', type=str, required=True, help="Path to initial disassembly prompt.")
    parser.add_argument('-b', '--binary', type=str, required=True, help='Path to initial binary file.')
    parser.add_argument('-o', '--output', type=str, required=True, help="Path to output directory.")
    parser.add_argument('-c', '--compiler', type=str, required=True, help='Compiler binary to compile the files.')
    parser.add_argument("-f", "--flags", required=False, help="Compiler flags.")
    parser.add_argument("-m", "--mode", type=str, required=True, help="Feedback mode: (bindiff/disdiff/objdump/ghidra/ghidra-eval)")
    parser.add_argument("-i", "--iterations", type=int, default=5, required=False, help="Number of iterations in chain of thought.")
    parser.add_argument('-k', '--headless', type=str, required=False, help="Path to Ghidra headless binary (analyzeHeadless).")
    parser.add_argument('-s', '--proj', type=str, required=False, help="Path to Ghidra project directory.")
    parser.add_argument('-q', '--stub', type=str, required=False, help="Path to stub source file used in compiling.")
    parser.add_argument('-u', '--func', type=str, required=True, help="Name of the function to be decompiled.")
    parser.add_argument('-l', '--language', type=str, required=True, help='Language of initial binary file (C, CPP, Go, Rust).')
    parser.add_argument('-z', '--accuracy_mode', type=int, default=None, required=False, help='Mode of Accuracy Measurement (0: AST parsing) (1: Code Similarity)')
    parser.add_argument('-a', '--source_file', type=str, required=False, help='Path to source file used for accuracy measurements.')
    args = parser.parse_args()

    mode = args.mode.lower()
    language = args.language.lower()

    if os.path.exists(args.prompt) and os.path.exists(args.binary) and os.path.exists(args.output):
        if (mode == "bindiff" or mode == "ghidra") and not (os.path.exists(args.headless) and os.path.exists(args.proj)):
            print("Invalid path to Ghidra headless, project folder, or bindiff.")
            quit()

        if args.accuracy_mode:
            print(args.accuracy_mode)
            if args.accuracy_mode == 1 and args.language == "rust":
                print("Rust language cannot be used with code similarity measurement.")
                quit()
            elif args.accuracy_mode not in {0, 1}:
                print("Invalid accuracy mode!")
                quit()
            elif not os.path.exists(args.source_file):
                print("Invalid path to source file for accuracy measurements!")
                quit() 

        filename = os.path.splitext(os.path.split(args.binary)[1])[0]
        if mode == "bindiff":
            binexport(args.headless, args.proj, args.binary, args.output)
            initial_diff_path = os.path.join(args.output, filename, ".BinExport")
        elif mode == "objdump":
            initial_objdump = objdump(args.binary, args.func)
        elif mode == "disdiff":
            initial_disasm = get_disasm(args.binary, language, args.func)
            if args.func not in initial_disasm:
                print(f"Function {args.func} was not identfied in initial binary.")
                quit()
        elif mode == "ghidra" or mode == "ghidra_eval":
            initial_pseudo = get_ghidra_pseudo(args.headless, args.proj, args.binary, args.output, args.func)
        else:
            print("Invalid mode!")
            quit()
        
        f = open(args.prompt, "r")
        initial_prompt = f.read()
        f.close()

        f = open(args.source_file, "r")
        source = f.read()
        f.close()

        prompt = initial_prompt
        accuracy = 0
        best_decomp = None

        for iter_count in range(args.iterations):
            print(f'{iter_count}\n{prompt}\n')
            decomp_code = generate_decomp(prompt)
            print(decomp_code)
            print("\n")
            curr_accuracy = run_eval(source, decomp_code, language, args.accuracy_mode)
            if curr_accuracy > accuracy:
                accuracy = curr_accuracy
                best_decomp = decomp_code

            source_file = write_source(args.output, language, decomp_code, args.stub)
            new_binary_path = os.path.join(args.output, filename + "_" + str(iter_count) + ".out")
            exit_code, output, error = compile(args.compiler, new_binary_path, source_file, args.flags)
            
            if exit_code != 0:
                prompt = compile_error_prompt(initial_prompt, decomp_code, error)
            else:
                if mode == "bindiff":
                    binexport(args.headless, args.proj, new_binary_path, args.output)
                    bindiff_out = bindiff(initial_diff_path, os.path.join(args.output, filename + "_" + str(iter_count) + ".out.BinExport"), args.output)
                    prompt = bindiff_prompt(bindiff_out, language, args.func, decomp_code)
                elif mode == "objdump":
                    curr_objdump = objdump(new_binary_path, args.func)
                    diff = list(differ.compare(curr_objdump.splitlines(), initial_objdump.splitlines()))
                    
                    if not any(line.startswith(('+', '-', '?')) for line in diff):
                        print("No difference in disassembly detected!")
                        print(f"Final decompilation:\n{decomp_code}")
                        quit()
                    else:
                        prompt = diff_prompt('\n'.join(diff), language, args.func, decomp_code)
                elif mode == "disdiff":
                    curr_disasm = get_disasm(new_binary_path, language, args.func)
                    functions, _ = diff_all(curr_disasm, initial_disasm)
                    diff_disasm = ""
                    diff = False
                    
                    for diff in functions[args.func]['hunks']:
                        line = diff[1].lstrip()
                        if diff[0] == -1:
                            diff_disasm += f"- {line}\n"
                        elif diff[0] == 0:
                            diff_disasm += f"  {line}\n"
                        else:
                            diff_disasm += f"+ {line}\n"

                    if not diff:
                        print("No difference in disassembly detected!")
                        print(f"Final decompilation:\n{decomp_code}")
                        quit()
                    else:
                        prompt = diff_prompt(diff_disasm, language, args.func, decomp_code)
                elif mode == "ghidra":
                    curr_pseudo = get_ghidra_pseudo(args.headless, args.proj, new_binary_path, args.output, args.func)
                    diff = list(differ.compare(curr_pseudo.splitlines(), initial_pseudo.splitlines()))
                    
                    if not any(line.startswith(('+', '-', '?')) for line in diff):
                        print("No difference in pseudocode detected!")
                        print(f"Final decompilation:\n{decomp_code}")
                        quit()
                    else:
                        prompt = pseudo_diff_prompt('\n'.join(diff), language, args.func, decomp_code)
                elif mode == "ghidra_eval":
                    curr_pseudo = get_ghidra_pseudo(args.headless, args.proj, new_binary_path, args.output, args.func)
                    if language == "go" or language == "rust":
                        # Ghidra pseudocode is C/C++ style so eval using C++
                        initial_branches, initial_calls = eval_funcs['cpp'](initial_pseudo)
                        curr_branches, curr_calls = eval_funcs['cpp'](curr_pseudo)
                    else:
                        initial_branches, initial_calls = eval_funcs[language](initial_pseudo)
                        curr_branches, curr_calls = eval_funcs[language](curr_pseudo)
                    initial_calls, curr_calls = Counter(initial_calls), Counter(curr_calls)
                    if curr_branches == initial_branches and initial_calls == curr_calls:
                        print("No difference in pseudocode detected!")
                        print(f"Final decompilation:\n{decomp_code}")
                        quit()
                    else:
                        shared_calls, missing_calls, extra_calls = [], [], []
                        for func in initial_calls.elements():
                            if initial_calls[func] == curr_calls[func]:
                                for i in range(initial_calls[func]):
                                    shared_calls.append(func)
                            elif initial_calls[func] < curr_calls[func]:
                                for i in range(curr_calls[func] - initial_calls[func]):
                                    extra_calls.append(func)
                            else:
                                for i in range(initial_calls[func] - curr_calls[func]):
                                    missing_calls.append(func)
                        prompt = eval_diff_prompt(language, args.func, decomp_code, initial_pseudo, curr_branches - initial_branches, shared_calls, missing_calls, extra_calls)
                else:
                    print("Invalid mode!")
                    quit()
        print(f"Best Decompilation:\n{best_decomp}")
        print(f"Accuracy of Best Decompilation:\n{accuracy}")
    else:
        print("Invalid source, prompt, or output path.")

if __name__ == "__main__":
    main()
