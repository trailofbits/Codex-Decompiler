from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from unixcoder import UniXcoder
import re
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = UniXcoder("microsoft/unixcoder-base-nine")
model.to(device)

disassembly = """
PUSH RBP
MOV RBP,RSP
SUB RSP,0x120
MOV dword ptr [RBP + -0x4],0x0
MOV dword ptr [RBP + -0x8],EDI
MOV qword ptr [RBP + -0x10],RSI
MOV dword ptr [RBP + -0x18],0x4
MOV dword ptr [RBP + -0x1c],0x0
LEA RDI,[RBP + -0x48]
MOV qword ptr [RBP + -0xc8],RDI
CALL std::allocator<char>::allocator
MOV RDX,qword ptr [RBP + -0xc8]
LAB_00402b2e:
MOV ESI,0x406004
LEA RDI,[RBP + -0x40]
CALL std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::basic_string
JMP LAB_00402b41
LAB_00402b41:
LEA RDI,[RBP + -0x48]
CALL std::allocator<char>::~allocator
LAB_00402b4a:
MOV EDI,dword ptr [RBP + -0x8]
MOV RSI,qword ptr [RBP + -0x10]
MOV RDX,0x40601f
CALL getopt
MOV dword ptr [RBP + -0x14],EAX
CMP EAX,-0x1
JZ LAB_00402d96
MOV EAX,dword ptr [RBP + -0x14]
MOV dword ptr [RBP + -0xcc],EAX
SUB EAX,0x3a
JZ LAB_00402d26
JMP LAB_00402b83
LAB_00402b83:
MOV EAX,dword ptr [RBP + -0xcc]
SUB EAX,0x63
JZ LAB_00402bd9
JMP LAB_00402b97
LAB_00402b97:
MOV EAX,dword ptr [RBP + -0xcc]
SUB EAX,0x68
JZ LAB_00402c66
JMP LAB_00402bab
LAB_00402bab:
MOV EAX,dword ptr [RBP + -0xcc]
SUB EAX,0x6c
JZ LAB_00402c51
JMP LAB_00402d91
LAB_00402bd9:
MOV RCX,qword ptr [optarg]
MOV qword ptr [RBP + -0xe0],RCX
LEA RDI,[RBP + -0x80]
MOV qword ptr [RBP + -0xd8],RDI
CALL std::allocator<char>::allocator
MOV RSI,qword ptr [RBP + -0xe0]
MOV RDX,qword ptr [RBP + -0xd8]
LAB_00402c05:
LEA RDI,[RBP + -0x78]
CALL std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::basic_string
JMP LAB_00402c13
LAB_00402c13:
LEA RDI,[RBP + -0x40]
LEA RSI,[RBP + -0x78]
CALL std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::operator=
LEA RDI,[RBP + -0x78]
CALL std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string
LEA RDI,[RBP + -0x80]
CALL std::allocator<char>::~allocator
JMP LAB_00402d91
LAB_00402c51:
MOV RDI,qword ptr [optarg]
CALL atoi
MOV dword ptr [RBP + -0x18],EAX
JMP LAB_00402d91
LAB_00402c66:
MOV RCX,qword ptr [optarg]
MOV qword ptr [RBP + -0xf0],RCX
LEA RDI,[RBP + -0xa8]
MOV qword ptr [RBP + -0xe8],RDI
CALL std::allocator<char>::allocator
MOV RSI,qword ptr [RBP + -0xf0]
MOV RDX,qword ptr [RBP + -0xe8]
LAB_00402c95:
LEA RDI,[RBP + -0xa0]
CALL std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::basic_string
JMP LAB_00402ca6
LAB_00402ca6:
XOR EDX,EDX
MOV ESI,EDX
LEA RDI,[RBP + -0xa0]
CALL std::__cxx11::stoul
MOV RCX,RAX
MOV qword ptr [RBP + -0xf8],RCX
JMP LAB_00402cc5
LAB_00402cc5:
MOV RAX,qword ptr [RBP + -0xf8]
MOV dword ptr [RBP + -0x1c],EAX
LEA RDI,[RBP + -0xa0]
CALL std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string
LEA RDI,[RBP + -0xa8]
CALL std::allocator<char>::~allocator
JMP LAB_00402d91
LAB_00402d26:
MOV EDI,0x40a200
MOV ESI,0x406026
CALL std::operator<<
MOV RCX,RAX
MOV qword ptr [RBP + -0x100],RCX
JMP LAB_00402d44
LAB_00402d44:
MOV RDI,qword ptr [RBP + -0x100]
MOV ESI,dword ptr [optopt]
CALL std::basic_ostream<char,std::char_traits<char>>::operator<<
MOV RCX,RAX
MOV qword ptr [RBP + -0x108],RCX
JMP LAB_00402d65
LAB_00402d65:
MOV RDI,qword ptr [RBP + -0x108]
MOV ESI,0x406071
CALL std::operator<<
JMP LAB_00402d7b
LAB_00402d7b:
JMP LAB_00402d91
LAB_00402d91:
JMP LAB_00402b4a
LAB_00402d96:
CMP dword ptr [RBP + -0x1c],0x0
JNZ LAB_00402dca
MOV EDI,0x40a200
MOV ESI,0x40603e
CALL std::operator<<
JMP LAB_00402db4
LAB_00402db4:
MOV dword ptr [RBP + -0x4],0xffffffff
MOV dword ptr [RBP + -0xac],0x1
JMP LAB_00402e9a
LAB_00402dca:
MOV ESI,0x402770
LEA RDI,[RBP + -0xb8]
LEA RDX,[RBP + -0x40]
LEA RCX,[RBP + -0x18]
CALL std::thread::thread<void_(&)(std::basic_string<char>,_int),_std::basic_string<char>_&,_int_&,_void>
JMP LAB_00402de8
LAB_00402de8:
MOV ESI,0x402930
LEA RDI,[RBP + -0xc0]
LEA RDX,[RBP + -0x1c]
CALL std::thread::thread<void_(&)(unsigned_int),_unsigned_int_&,_void>
JMP LAB_00402e02
LAB_00402e02:
LEA RDI,[RBP + -0xb8]
CALL std::thread::join
JMP LAB_00402e13
LAB_00402e13:
LEA RDI,[RBP + -0xc0]
CALL std::thread::join
JMP LAB_00402e24
LAB_00402e24:
MOV EDI,0x40a200
MOV ESI,0x406073
CALL std::operator<<
MOV RCX,RAX
MOV qword ptr [RBP + -0x110],RCX
JMP LAB_00402e42
LAB_00402e42:
MOV RDI,qword ptr [RBP + -0x110]
MOV ESI,0x40a3c0
CALL std::operator<<
MOV RCX,RAX
MOV qword ptr [RBP + -0x118],RCX
JMP LAB_00402e62
LAB_00402e62:
MOV RDI,qword ptr [RBP + -0x118]
MOV ESI,0x406071
CALL std::operator<<
LAB_00402e73:
JMP LAB_00402e78
LAB_00402e78:
LEA RDI,[RBP + -0xc0]
CALL std::thread::~thread
LEA RDI,[RBP + -0xb8]
CALL std::thread::~thread
MOV dword ptr [RBP + -0xac],0x0
LAB_00402e9a:
LEA RDI,[RBP + -0x40]
CALL std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string
MOV EAX,dword ptr [RBP + -0x4]
ADD RSP,0x120
POP RBP
RET
"""

reference_table = """
Reference Table:
Address Data
00406004 ds "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
0040601f ds "c:l:h:"
0040a1c0 undefined8 0000000000000000h
0040a1c0 undefined8 0000000000000000h
0040a1c0 undefined8 0000000000000000h
0040a200 undefined1[272] 
00406026 ds "Missing argument for %c"
0040a1c8 undefined4 00000000h
0040a200 undefined1[272] 
0040603e ds "Usage: ./cracker -h 0xhash [-c charset] [-l length]\n"
0040a200 undefined1[272] 
00406073 ds "[*] Cracked: "
0040a3c0 undefined1[32] 
"""

source = """
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>
#include <getopt.h> /* getopt */

#define BUFSIZE 128

std::condition_variable not_full;
std::condition_variable not_empty;
std::mutex mutex;
std::vector<std::string> buffer;
std::string FOUND = "";

int main(int argc, char **argv) {
    int opt;
    int length = 4;
    uint32_t hash = 0;
    std::string charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    while ((opt = getopt(argc, argv, "c:l:h:")) != -1){
        switch (opt)
            {
            case 'c':
                charset = std::string(optarg);
                break;
            case 'l':
                length = std::atoi(optarg);
                break;
            case 'h':
                hash = std::stoul(optarg, nullptr, 0);
                break;
            case ':':
                std::cout << "Missing argument for %c" << optopt << "\n";
                break;
            }
    }

    if(hash == 0){
        std::cout << "Usage: ./cracker -h 0xhash [-c charset] [-l length]\n";
        return -1;
    }

    std::thread producer = std::thread(produce, charset, length);
    std::thread consumer = std::thread(consume, hash);

    producer.join();
    consumer.join();

    std::cout << "[*] Cracked: " << FOUND << "\n";

}
"""

func_header = "default funcC(int argc, char * * argv):"

initial_prompt = """
I am trying to decompile a large function from x86 64-bit assembly code. I will give you sections of the assembly code. The assembly code has been divided into sections based on each label in the assembly code. The sections of assembly code will be given sequentially. The final section of the assembly code will end with the word END_OF_FUNCTION.
There will also be a reference table given which provides information about memory addresses. You will also be given all the decompiled code from the past sections. Generate the CPP code for the x86 64-bit assembly code so far using the assembly code and past decompilation. Do not provide any explanation or description. Just write the code.
"""

def clean_output(text):
    pattern = re.compile("(\'\'\'|```)\S*\s([\s\S]*?)(\'\'\'|```)")
    match = re.match(pattern, text)
    if match:
        return match.group(2)
    else:
        return text

def generate_llm_response(system_prompt, prompt):
    llm = AzureChatOpenAI(deployment_name="gpt-4-32k")

    message = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]

    output = clean_output(llm(message).content)

    return output

def calculate_similarity(response):
    tokens_ids = model.tokenize([source],max_length=1023,mode="<encoder-only>")
    source_ids = torch.tensor(tokens_ids).to(device)
    tokens_embeddings,source_embedding = model(source_ids)

    tokens_ids = model.tokenize([response],max_length=1023,mode="<encoder-only>")
    source_ids = torch.tensor(tokens_ids).to(device)
    tokens_embeddings,response_embedding = model(source_ids)

    norm_source_embedding = torch.nn.functional.normalize(source_embedding, p=2, dim=1)
    norm_response_embedding = torch.nn.functional.normalize(response_embedding, p=2, dim=1)

    similarity = torch.einsum("ac,bc->ab",norm_source_embedding,norm_response_embedding).item()
    return similarity

def initial_decomp():
    prompt = f'x86 64-bit Assembly:\n\n{func_header}\n{disassembly}\n\n{reference_table}\nGenerate just the C++ code for the function that produced the above x86 64-bit assembly. The C++ code should only represent the funcC function. The C++ code is idiomatic and uses standard libraries and range based loops.'
    response = generate_llm_response("You are a helpful AI assistant. Do not provide any explanations or description. Just write code.", prompt)
    output = clean_output(response)
    print(f'Initial Decompilation:\n{output}')
    return calculate_similarity(output)

def split_disasm_label(disasm):
    pattern = r'(LAB_[0-9a-fA-F]+:)\s(.*?)\s(?=LAB_[0-9a-fA-F]+:|$)'
    label_sections = re.findall(pattern, disasm, re.DOTALL)
    print(f'{len(label_sections)} label sections extracted from disassembly.')
    pattern2 = r'^(.*?)(?=LAB_[0-9a-fA-F]+:)'
    header = re.search(pattern2, disasm, re.DOTALL)
    sections = [(func_header, header.group(1))] + label_sections
    return sections

def chain_of_thought_prompts(sections):
    final_code = []
    for i in range(len(sections)):
        label, disasm = sections[i]
        newline = '\n'
        if i == len(sections) - 1:
            prompt = f"x86 64-bit Assembly:\n\n{label}:\n{disasm}\n//END_OF_FUNCTION\n\n{reference_table}\nPast Decompilation:\n{newline.join(final_code)}"
        else:
            prompt = f"x86 64-bit Assembly:\n\n{label}:\n{disasm}\n\n{reference_table}\nPast Decompilation:\n{newline.join(final_code)}"
        response = generate_llm_response(initial_prompt, prompt)
        output = clean_output(response)
        final_code.append(output)
    return final_code[-1]

def summarize_decomp(decomp_code):
    prompt = f'Code:\n{decomp_code}'
    response = generate_llm_response("You are given the C++ pseudocode of a program. Rewrite the C++ code to be more concise, use better variable names, remove labels, etc. Preserve the main logic of the program. Do not provide any explanations or description. Just write code.", prompt)
    output = clean_output(response)
    return output

def main():
    initial_accuracy = initial_decomp()
    print(f"Initial code similarity between decompilation and source: {initial_accuracy}")
    
    disasm_sections = split_disasm_label(disassembly)
    if len(disasm_sections) > 1:
        final_response = chain_of_thought_prompts(disasm_sections)
        final_output = clean_output(final_response)
        print(f'Final Decompilation:\n{final_output}')

        final_accuracy = calculate_similarity(final_response)
        print(f"Final code similarity between decompilation and source: {final_accuracy}")

        summary = summarize_decomp(final_response)
        print(f'Summarized Decompilation:\n{summary}')

        summary_accuracy = calculate_similarity(summary)
        print(f"Final code similarity between summarized decompilation and source: {summary_accuracy}")

    else:
        print("No sections detected in disassembly code!")

if __name__ == "__main__":
    main()
