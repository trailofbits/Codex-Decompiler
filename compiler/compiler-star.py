import os 
import argparse
import subprocess
import re
import difflib
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from decompetition_disassembler.bindings import get_disasm, diff_all
from dotenv import load_dotenv

load_dotenv()
differ = difflib.Differ()

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

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    exit_code = process.wait()

    output, error = output.decode("utf-8"), error.decode("utf-8")
    return exit_code, output, error

def clean_output(text):
    pattern = re.compile(r"(''')|(```)")

    lines = text.split('\n')

    filtered_lines = [line for line in lines if not re.search(pattern, line)]

    result_string = '\n'.join(filtered_lines)

    return result_string

def generate_decomp(prompt):
    llm = AzureChatOpenAI(deployment_name="gpt-4-32k")

    message = [SystemMessage(content="You are a helpful AI coding assistant. You are to only generate code to accomplish the user given task. Do not provide any explanation or description. Just provide only code."), HumanMessage(content=prompt)]

    output = clean_output(llm(message).content)

    return output

def write_source(output_dir, language, decomp, stub):
    if language == "go":
        filename = os.path.join(output_dir, "temp.go")
    elif language == "rust":
        filename = os.path.join(output_dir, "temp.rs")
    elif language == "cpp":
        filename = os.path.join(output_dir, "temp.cpp")
    else:
        filename = os.path.join(output_dir, "temp.c")
    
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

def compile_error_prompt(initial_prompt, decomp, error):
    return f"The previous decompilation resulted in a compiler error. Fix the errors and re-generate the pseudocode.\nCompiler Error:\n{error}\nPrevious Decompilation:\n{decomp}"

def bindiff_prompt(bindiff_out, language, func_name):
    bindiff_out = "\n".join(bindiff_out.split("\n")[1:-1])
    return f"The previous decompilation was able to be compiled. Here is the bindiff output between the original binary and the decompiled code binary.\n{bindiff_out}\nUsing this bindiff output, re-generate {language} pseudocode for the {func_name} function so that there is no difference. The {language} is idiomatic and uses functions, structures, and more from the standard libraries."

def diff_prompt(diff, language, func_name):
    return f"The previous decompilation was able to be compiled. Here is a diff between the disassembly of the original binary and the decompiled code binary:\n{diff}\nUsing this diff of the disassembly, re-generate {language} pseudocode for the {func_name} function so that there is no difference in the disassembly. The {language} is idiomatic and uses functions, structures, and more from the standard libraries."

def main():
    parser = argparse.ArgumentParser(
                prog='Compiler Augmented LLM Decompilation',
                description='This program uses chain of thought reasoning with LLMs and feedback from the compiler to improve decompilation results.')
    parser.add_argument('-p', '--prompt', type=str, required=True, help="Path to initial disassembly prompt.")
    parser.add_argument('-b', '--binary', type=str, required=True, help='Path to initial binary file.')
    parser.add_argument('-o', '--output', type=str, required=True, help="Path to output directory.")
    parser.add_argument('-c', '--compiler', type=str, required=True, help='Compiler binary to compile the files.')
    parser.add_argument("-f", "--flags", required=False, help="Compiler flags.")
    parser.add_argument("-m", "--mode", type=str, required=True, help="Feedback mode: (bindiff/disdiff/objdump)")
    parser.add_argument("-i", "--iterations", type=int, default=5, required=False, help="Number of iterations in chain of thought.")
    parser.add_argument('-k', '--headless', type=str, required=False, help="Path to Ghidra headless binary (analyzeHeadless).")
    parser.add_argument('-s', '--proj', type=str, required=False, help="Path to Ghidra project directory.")
    parser.add_argument('-q', '--stub', type=str, required=False, help="Path to stub source file used in compiling.")
    parser.add_argument('-u', '--func', type=str, required=True, help="Name of the function to be decompiled.")
    parser.add_argument('-l', '--language', type=str, required=True, help='Language of initial binary file (C, CPP, Go, Rust).')
    args = parser.parse_args()

    mode = args.mode.lower()
    language = args.language.lower()

    if os.path.exists(args.prompt) and os.path.exists(args.binary) and os.path.exists(args.output):
        if mode == "bindiff" and not (os.path.exists(args.headless) and os.path.exists(args.proj)):
            print("Invalid path to Ghidra headless, project folder, or bindiff.")
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
        else:
            print("Invalid mode!")
            quit()
        
        f = open(args.prompt, "r")
        initial_prompt = f.read()
        f.close()

        prompt = initial_prompt

        for iter_count in range(args.iterations):
            print(f'{iter_count}\n{prompt}\n')
            decomp_code = generate_decomp(prompt)
            print(decomp_code)
            print("\n")
            source_file = write_source(args.output, language, decomp_code, args.stub)
            exit_code, output, error = compile(args.compiler, os.path.join(args.output, filename + "_" + str(iter_count) + ".out"), source_file, args.flags)
            
            if exit_code != 0:
                prompt = compile_error_prompt(initial_prompt, decomp_code, error)
            else:
                if mode == "bindiff":
                    binexport(args.headless, args.proj, os.path.join(args.output, filename + "_" + str(iter_count) + ".out"), args.output)
                    bindiff_out = bindiff(initial_diff_path, os.path.join(args.output, filename + "_" + str(iter_count) + ".out.BinExport"), args.output)
                    prompt = bindiff_prompt(bindiff_out, language, args.func)
                elif mode == "objdump":
                    curr_objdump = objdump(os.path.join(args.output, filename + "_" + str(iter_count) + ".out"), args.func)
                    diff = list(differ.compare(initial_objdump.splitlines(), curr_objdump.splitlines()))
                    
                    if not any(line.startswith(('+', '-', '?')) for line in diff):
                        print("No difference in disassembly detected!")
                        print(f"Final decompilation:\n{decomp_code}")
                        quit()
                    else:
                        prompt = diff_prompt('\n'.join(diff), language, args.func)
                elif mode == "disdiff":
                    curr_disasm = get_disasm(os.path.join(args.output, filename + "_" + str(iter_count) + ".out"), language, args.func)
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
                        prompt = diff_prompt(diff_disasm, language, args.func)
                else:
                    print("Invalid mode!")
    else:
        print("Invalid source, prompt, or output path.")

if __name__ == "__main__":
    main()
