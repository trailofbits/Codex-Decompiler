from capstone import *
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
import os
import argparse

def eval_asm(disasm_file):
    md = Cs(CS_ARCH_X86, CS_MODE_64)

    f = open(disasm_file, "r")
    text = f.read()
    f.close()
    asm = bytes(eval(text))

    branch_count = 0
    call_count = 0

    for insn in md.disasm(asm, 0x1000):
        if insn.mnemonic.startswith('j') and insn.mnemonic != "jmp":
            branch_count += 1
            
        if insn.mnemonic == 'call':
            #print(f"Assembly function call: {insn.op_str.split()[-1]}")
            call_count += 1

    print(f"Assembly branches: {branch_count}")
    print(f"Assembly calls: {call_count}")

def eval_c(decomp_file):
    language = get_language('c')
    parser = get_parser('c')

    f = open(decomp_file, "r")
    source_code = f.read()
    f.close()

    tree = parser.parse(bytes(source_code, "utf8"))

    function_calls = 0
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
                        print(f"C function call: {name}")
                        function_calls += 1
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
            elif cursor.node.type == "initializer_list":
                function_calls += 1

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

    print(f"C branches: {branches}")
    print(f"C function calls: {function_calls}")

def eval_cpp(decomp_file):
    language = get_language('cpp')
    parser = get_parser('cpp')

    f = open(decomp_file, "r")
    source_code = f.read()
    f.close()

    tree = parser.parse(bytes(source_code, "utf8"))

    function_calls = 0
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
                        print(f"CPP function call: {name}")
                        function_calls += 1
            elif cursor.node.type in {"new_expression", "delete_expression", "lambda_expression"}:
                function_calls += 1
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
            elif cursor.node.type == "initializer_list":
                function_calls += 1

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

    print(f"C++ branches: {branches}")
    print(f"C++ function calls: {function_calls}")

def eval_rust(decomp_file):
    language = get_language('rust')
    parser = get_parser('rust')

    f = open(decomp_file, "r")
    source_code = f.read()
    f.close()

    tree = parser.parse(bytes(source_code, "utf8"))

    function_calls = 0
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
                    print(f"Rust function call: {function_node.text.decode('utf8')}")
                    function_calls += 1
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

    print(f"Rust branches: {branches}")
    print(f"Rust function calls: {function_calls}")

def eval_go(decomp_file):
    language = get_language('go')
    parser = get_parser('go')

    f = open(decomp_file, "r")
    source_code = f.read()
    f.close()

    tree = parser.parse(bytes(source_code, "utf8"))

    function_calls = 0
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
                    print(f"Go function call: {function_node.text.decode('utf8')}")
                    function_calls += 1
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

    print(f"Go branches: {branches}")
    print(f"Go function calls: {function_calls}")

eval_funcs = {"c": eval_c, "cpp": eval_cpp, "rust": eval_rust, "go": eval_go}

def main():
    parser = argparse.ArgumentParser(
                    prog='Pseudocode Evaluator',
                    description='This program evaluates the accuracy of decompiled code compared to its disassembly.')
    parser.add_argument('-d', '--disasm', type=str, required=True, help="Specify the directory to disassembly files.")
    parser.add_argument('-s', '--source', type=str, required=True, help='Specify the directory to decompilation source files.')
    parser.add_argument('-l', '--language', type=str, required=True, help='Specify the language (C, CPP, Rust, Go) of decompilation files.')
    args = parser.parse_args()

    disasm_path = args.disasm
    decomp_path = args.source
    language = args.language.lower()

    if language in eval_funcs:
        if os.path.exists(disasm_path) and os.path.exists(decomp_path):
            disasm_arr = os.listdir(disasm_path)
            decomp_arr = os.listdir(decomp_path)
            for file in disasm_arr:
                name = os.path.splitext(file)[0]
                decomp_file = None
                for element in decomp_arr:
                    if element.startswith(name):
                        decomp_file = element
                        break
                if decomp_file:
                    print(os.path.splitext(file)[0])
                    eval_asm(os.path.join(disasm_path, file))
                    eval_funcs.get(language)(os.path.join(decomp_path, decomp_file))
                    print("\n")
                else:
                    print("Skipping current disassembly file as corresponding decompilation could not be found.")
        else:
            print("Invalid paths to files.")
    else:
        print("Invalid language specified.")

if __name__ == "__main__":
    main()