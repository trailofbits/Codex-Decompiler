import os
import json

# This script allows you to merge many json files into one singular json file.
def merge_json_files(dirs, output_file):
    json_objects = []

    for input_dir in dirs:
        for filename in os.listdir(input_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(input_dir, filename)

                with open(file_path, 'r') as file:
                    json_object = json.load(file)

                json_objects.append(json_object)

    with open(output_file, 'w') as output_file:
        json.dump(json_objects, output_file, indent=2)

if __name__ == "__main__":
    input_directory = ["./output/c_prompts", "./output/cpp_prompts", './output/go_prompts', './output/rust_prompts']

    output_file = "./merged.json"

    merge_json_files(input_directory, output_file)

    print(f"Merged JSON file saved to: {output_file}")
