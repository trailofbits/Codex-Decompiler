This project was built by Akshat Parikh during the Trail of Bits 2022 Winter Internship. The project is provided as is. Contact opensource@trailofbits.com if you'd like to use this project.

# Codex Decompiler
Codex Decompiler is a Ghidra plugin that utilizes OpenAI's models to improve the decompilation and reverse engineering experience. It currently has the ability to take the disassembly from Ghidra and then feed it to OpenAI's codex model to decompile the code. The plugin also offers several other features to perform on the decompiled code such as finding vulnerabilities using OpenAI, generating a description using OpenAI, or decompiling the Ghidra pseudocode. Down below, you can see an example of the plugin being run in Ghidra and the available features.

![pluginDisplay](https://user-images.githubusercontent.com/68412398/212231570-7047ab53-92d1-49d0-a773-720e94d0fb48.png)

## Setup
1. Download this repository and change the apiKey variable in the plugin python file.
2. Move the plugin to the ghidra_scripts directory which by default is at ```$USER_HOME/ghidra_scripts```.
3. Boot up Ghidra and import the binary you want to analyze.
4. Run autoanalysis on the binary.
5. Click "Script Manager" in the Window tab and a new window should appear.
6. Find the script named ghidraRevAI and click the checkmark button to include the script and then the green arrow button to run the script.
## Usage
1. Each time, you boot up Ghidra you will need to run the script again.
2. To use the plugin, go to any function inside of the Listing window and press Ctrl+J.
3. A new window should pop up where you can see different operations that can be performed on the pseudocode in the taskbar.
Here is an example of the taskbar.

![taskbar](https://user-images.githubusercontent.com/68412398/212239760-677c0483-386a-4de6-9ab2-ea7747a34a6a.png)

Note: all of the output from OpenAI (pseudocode) is cached to ghidra_scripts directory under the subfolder output. This is done to avoid unnecessary calls to the API which can be costly.
### List of Operations:
- ![context](https://user-images.githubusercontent.com/68412398/212240054-dcad8e91-48bc-4555-9602-01c4708ed69e.png) Generate a description for the pseudocode displayed
- ![edit](https://user-images.githubusercontent.com/68412398/212240118-23597a8e-1d83-445b-a948-f38cd802476b.png) View, edit, and resubmit the last prompt sent to OpenAI
- ![save](https://user-images.githubusercontent.com/68412398/212240172-fb3261ef-4745-4945-9d6f-e214f5fd04bb.png) Save the changes in the pseudocode editor to the file output
- ![refresh](https://user-images.githubusercontent.com/68412398/212240232-2d527eb3-0ab8-4601-8ac4-82c3eb5a22a6.png) Decompile the disassembly again
- ![find](https://user-images.githubusercontent.com/68412398/212240274-cf901029-3fe3-4d0d-9fd0-888e67b7eb5f.png) Find vulnerabilities in the pseudocode
- ![gear](https://user-images.githubusercontent.com/68412398/212240354-078b2676-e701-47c8-afb2-f5a6ecda6140.png) Decompile the pseudocode that Ghidra generated

## Limitations
For any of the aforementioned features, the output from OpenAI can be faulty and inconsistent. Thus, before doing anything with the generated pseudocode or other data, make sure that it is correct.
## References
1. https://ghidra.re/ghidra_docs/api/
2. https://www.javaprogrammingforums.com/java-swing-tutorials/915-how-add-line-numbers-your-jtextarea.html
## Acknowledgments/Contributions
I would like to acknowledge everyone at Trail of Bits for helping me through this project and providing feedback. I thoroughly enjoyed my experience with the company and creating this tool.
