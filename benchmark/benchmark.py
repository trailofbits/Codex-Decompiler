from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
import os
import re
import argparse
import torch
from unixcoder import UniXcoder

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = UniXcoder("microsoft/unixcoder-base-nine")
model.to(device)

accuracy_results = []
verbose = False

def clean_output(text):
    pattern = re.compile(r"(''')|(```)")

    lines = text.split('\n')

    filtered_lines = [line for line in lines if not re.search(pattern, line)]

    result_string = '\n'.join(filtered_lines)

    return result_string

def eval_c(code):
    language = get_language('c')
    parser = get_parser('c')

    tree = parser.parse(bytes(code, "utf8"))

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
                        if verbose:
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

    if verbose:
        print(f"C branches: {branches}")
        print(f"C function calls: {function_calls}")

    return (branches, function_calls)

def eval_cpp(code):
    language = get_language('cpp')
    parser = get_parser('cpp')

    tree = parser.parse(bytes(code, "utf8"))

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
                        if verbose:
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

    if verbose:
        print(f"C++ branches: {branches}")
        print(f"C++ function calls: {function_calls}")

    return (branches, function_calls)

def eval_rust(code):
    language = get_language('rust')
    parser = get_parser('rust')

    tree = parser.parse(bytes(code, "utf8"))

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
                    if verbose:
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

    if verbose:
        print(f"Rust branches: {branches}")
        print(f"Rust function calls: {function_calls}")

    return (branches, function_calls)

def eval_go(code):
    language = get_language('go')
    parser = get_parser('go')

    tree = parser.parse(bytes(code, "utf8"))

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
                    if verbose:
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

    if verbose:
        print(f"Go branches: {branches}")
        print(f"Go function calls: {function_calls}")

    return (branches, function_calls)

def generate_llm_response(prompt):
    llm = AzureChatOpenAI(deployment_name="gpt-4-32k")

    message = [SystemMessage(content="You are a helpful AI coding assistant. You are to only generate code to accomplish the user given task. Do not provide any explanation or description. Just provide code."), HumanMessage(content=prompt)]

    output = clean_output(llm(message).content)

    return output

def run_eval(prompt_file, source_file, language, mode):
    eval_func = eval_funcs.get(language)

    f = open(prompt_file, "r")
    prompt = f.read()
    f.close()

    f = open(source_file, "r")
    source = f.read()
    f.close()
    
    global accuracy_results
    response = generate_llm_response(prompt)
    if verbose:
        print(response)

    if mode == 0:
        (original_branches, original_calls) = eval_func(source)
        (new_branches, new_calls) = eval_func(response)
        total = original_branches + original_calls
        branches_diff = abs(new_branches - original_branches)
        calls_diff = abs(new_calls - original_calls)
        weighted_error = (branches_diff / original_branches) * (original_branches / total) + (calls_diff / original_calls) * (original_calls / total)
        
        if verbose:
            print(f"Error between decompilation and source: {weighted_error}")
        
        accuracy_results.append(1 - weighted_error)
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
        
        if verbose:
            print(f"Code similarity between decompilation and source: {similarity}")
        
        accuracy_results.append(similarity)


eval_funcs = {"c": eval_c, "cpp": eval_cpp, "rust": eval_rust, "go": eval_go}

def main():
    parser = argparse.ArgumentParser(
                    prog='LLM Decompliation Benchmark',
                    description='This program benchmarks how well an LLM can decompile assembly code back to the source language.')
    parser.add_argument('-p', '--prompts', type=str, required=True, help="Specify the directory to benchmark prompts.")
    parser.add_argument('-s', '--source', type=str, required=True, help='Specify the directory to source files.')
    parser.add_argument('-l', '--language', type=str, required=True, help='Specify the language (C, CPP, Rust, Go) of source files.')
    parser.add_argument('-m','--mode',type=int, required=True, help="Specify mode for determining accuracy (0: AST parsing) and (1: Code Similarity)") 
    parser.add_argument('-v', '--verbose', default=False, action='store_true')
    args = parser.parse_args()

    if args.mode == 0 or (args.mode == 1 and args.language.lower() != "rust"):
        prompt_path = args.prompts
        source_path = args.source
        global verbose
        verbose = args.verbose
        language = args.language.lower()

        if language in eval_funcs:
            if os.path.exists(prompt_path) and os.path.exists(source_path):
                prompt_arr = os.listdir(prompt_path)
                source_arr = os.listdir(source_path)
                for file in prompt_arr:
                    name = os.path.splitext(file)[0]
                    source_file = None
                    for element in source_arr:
                        if element.startswith(name):
                            source_file = element
                            break
                    if source_file:
                        run_eval(os.path.join(prompt_path, file), os.path.join(source_path, source_file), language, args.mode)
                        if verbose:
                            print("\n")
                    else:
                        print("Skipping prompt because source file could not be found!")
                print(f"Total accuracy for llm: {sum(accuracy_results) / len(accuracy_results)}")
            else:
                print("Invalid paths to files.")
        else:
            print("Invalid specified language.")
    else:
        print("Invalid mode entered.")

if __name__ == "__main__":
    main()
