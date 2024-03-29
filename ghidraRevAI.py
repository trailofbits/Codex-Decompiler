# This script uses the OpenAI model to generate pseudocode for a function. It also provides other functionalities on the pseudocode such as searching for vulnerabilities.
# @author Akshat Parikh (Trail of Bits)
# @category Analysis
# @keybinding
# @menupath
# @toolbar

import java
import json
import os
import re
from java.net import HttpURLConnection
from java.net import URL
from java.io import InputStreamReader
from java.io import BufferedReader
from java.lang import String
from java.lang import StringBuffer
from java.lang import StringBuilder
from javax.swing import JTextArea
from javax.swing import JScrollPane
from javax.swing import ScrollPaneConstants
from javax.swing.event import DocumentListener
from java.awt.event import KeyEvent
from java.awt.event import InputEvent
from java.awt import Color
from ghidra.framework.plugintool import ComponentProviderAdapter
from ghidra.app.decompiler import DecompInterface
from ghidra.util import HelpLocation
from ghidra.framework.options import OptionType
from docking import WindowPosition
from docking.action import DockingAction
from docking.action import KeyBindingData
from resources import ResourceManager
from docking.action import ToolBarData
from docking.widgets.dialogs import MultiLineInputDialog
from ghidra.util.task import Task
from ghidra.util.task import TaskLauncher

API_TYPES = ["openai", "azure"]
DEFAULT_API_TYPE = "openai"
DEFAULT_AZURE_API_BASE = "https://{{azure-resource}}.openai.azure.com"
DEFAULT_AZURE_CODE_MODEL_NAME = "codex"
DEFAULT_AZURE_TEXT_MODEL_NAME = "gpt35"
DEFAULT_OPENAI_API_BASE = "https://api.openai.com"
DEFAULT_OPENAI_CODE_MODEL_NAME = "gpt-3.5-turbo"
DEFAULT_OPENAI_TEXT_MODEL_NAME = "gpt-3.5-turbo"

OPTION_API_TYPE = "openai.api_type"
OPTION_API_BASE = "openai.api_base"
OPTION_API_VERSION = "openai.api_version"
OPTION_CODE_MODEL = "openai.code_model_name"
OPTION_TEXT_MODEL = "openai.text_model_name"
OPTION_API_KEY = "openai.api_key"

tool = state.getTool()
options = tool.getOptions("Codex-Decompiler")
api_key = None

def init_options():
    help_location = HelpLocation("Codex-Decompiler", "codexdecompiler")
    options.registerOption(OPTION_API_TYPE, DEFAULT_API_TYPE, help_location, "OpenAI API Type (openai/azure)")
    options.registerOption(OPTION_API_BASE, DEFAULT_OPENAI_API_BASE, help_location, "OpenAI Base URL")
    options.registerOption(OPTION_API_VERSION, "", help_location, "Azure OpenAI API Version")
    options.registerOption(OPTION_CODE_MODEL, DEFAULT_OPENAI_CODE_MODEL_NAME, help_location, "Model name for code tasks")
    options.registerOption(OPTION_TEXT_MODEL, DEFAULT_OPENAI_TEXT_MODEL_NAME, help_location, "Model name for text tasks")
    options.registerOption(OPTION_API_KEY, "", None, "OpenAI API Key (set it to change the environment value)")

def get_tool_option(name):
    return options.getString(name, None)

def get_code_model():
    return get_tool_option(OPTION_CODE_MODEL)

def get_text_model():
    return get_tool_option(OPTION_TEXT_MODEL)

def get_api_key():
    api_key_option = get_tool_option(OPTION_API_KEY)
    if api_key_option:
        return api_key_option

    if os.environ.get("OPENAI_API_KEY") is not None:
        return os.environ["OPENAI_API_KEY"]
    else:
        api_key_option = askString("OpenAI API Key", "OpenAI API Key")
        options.setString(OPTION_API_KEY, api_key_option)
        return api_key_option

pluginPath = sourceFile.getAbsolutePath().replace(sourceFile.getName(), "")
guiAdapter = None
currentFunction = None
currentAddress = None
currentQuery = None

class PluginComponentProviderAdapter(ComponentProviderAdapter):
    def __init__(self, tool, name):
        ComponentProviderAdapter.__init__(self, tool, name, name)
        self.textArea = JTextArea(10, 80)
        self.textArea.setEditable(True)
        self.textArea.setLineWrap(True)
        self.lineTextArea = LineNumberedTextArea(self.textArea)
        self.scrollPane = JScrollPane(self.textArea)
        self.scrollPane.setVerticalScrollBarPolicy(
            ScrollPaneConstants.VERTICAL_SCROLLBAR_ALWAYS
        )
        self.scrollPane.setWheelScrollingEnabled(True)
        self.scrollPane.setRowHeaderView(self.lineTextArea)
        self.setDefaultWindowPosition(WindowPosition.RIGHT)
        self.setTitle("OpenAI Pseudocode")
        self.textArea.getDocument().addDocumentListener(ScrollDocumentListener(self.lineTextArea))
        self.setVisible(True)
        self.createActions()

    def getComponent(self):
        return self.scrollPane

    def update(self, text):
        self.textArea.setText(text)

    def getText(self):
        return self.textArea.getText()

    def createActions(self):
        generateContextAction = ContextDockingAction(self.getName())
        editQueryAction = EditQueryDockingAction(self.getName(), self.getComponent())
        saveAction = SaveAction(self.getName())
        refreshAction = RefreshAction(self.getName())
        findVulnAction = FindVulnAction(self.getName())
        altDecompAction = AltDecompAction(self.getName())
        
        self.addLocalAction(generateContextAction)
        self.addLocalAction(editQueryAction)
        self.addLocalAction(saveAction)
        self.addLocalAction(refreshAction)
        self.addLocalAction(findVulnAction)
        self.addLocalAction(altDecompAction)

class LineNumberedTextArea(JTextArea):
    def __init__(self, textArea):
        self.textArea = textArea
        self.setBackground(Color.LIGHT_GRAY)
        self.setEditable(False)
    
    def updateLineNumbers(self):
        lineNumbersText = self.getLineNumbersText()
        self.setText(lineNumbersText)
    
    def getLineNumbersText(self):
        caretPosition = self.textArea.getDocument().getLength()
        root = self.textArea.getDocument().getDefaultRootElement()
        lineNumbersTextBuilder = StringBuilder()
        lineNumbersTextBuilder.append("1").append(os.linesep)

        for index in range(2, root.getElementIndex(caretPosition) + 2):
            lineNumbersTextBuilder.append(index).append(os.linesep)

        return lineNumbersTextBuilder.toString()

class ScrollDocumentListener(DocumentListener):
    def __init__(self, lineTextArea):
        DocumentListener.__init__(self)
        self.lineTextArea = lineTextArea
        
    def insertUpdate(self, documentEvent):
        self.lineTextArea.updateLineNumbers()
        
    def removeUpdate(self, documentEvent):
        self.lineTextArea.updateLineNumbers()
        
    def changedUpdate(self, documentEvent):
        self.lineTextArea.updateLineNumbers()

class DecompileTask(Task):
    def __init__(self, address, temp):
        Task.__init__(self, "Decompiling function", False, False, False, False)
        self.address = address
        self.temp = temp

    def run(self, monitor):
        disassembleFunction(self.address, self.temp)
        
class PluginDockingAction(DockingAction):
    def __init__(self):
        DockingAction.__init__(
            self, "Generate OpenAI Pseudocode", "OpenAI Plugin", True
        )
        self.setAddToAllWindows(True)
        self.setDescription(
            "Takes the disassembly of a function and uses the OpenAI api to generate pseudocode."
        )
        self.setKeyBindingData(KeyBindingData(KeyEvent.VK_J, InputEvent.CTRL_DOWN_MASK))

    def actionPerformed(self, actionContext):
        if actionContext.getComponentProvider().getName() == "Listing":
            global currentAddress
            currentAddress = actionContext.getLocation().getAddress()
            TaskLauncher.launch(DecompileTask(currentAddress, 0))


class ContextDockingAction(DockingAction):
    class ContextDockingTask(Task):
        def __init__(self):
            Task.__init__(self, "Generating context for pseudocode", False, False, False, False)

        def run(self, monitor):
            generateContextApi(guiAdapter.getText())

    def __init__(self, owner):
        DockingAction.__init__(self, "Generate Context", owner, False)
        self.markHelpUnnecessary()
        self.setEnabled(True)
        icon = ResourceManager.loadImage("images/locationIn.gif")
        self.setToolBarData(ToolBarData(icon))

    def actionPerformed(self, actionContext):
        TaskLauncher.launch(self.ContextDockingTask())


class EditQueryDockingAction(DockingAction):
    def __init__(self, owner, component):
        DockingAction.__init__(self, "Edit OpenAI Query", owner, False)
        self.markHelpUnnecessary()
        self.component = component
        self.setEnabled(True)
        icon = ResourceManager.loadImage("images/edit-cut.png")
        self.setToolBarData(ToolBarData(icon))

    def actionPerformed(self, actionContext):
        state.getTool().showDialog(
            CustomMultiLineInputDialog("Query Editor", None, currentQuery, None),
            self.component,
        )

class CustomMultiLineInputDialog(MultiLineInputDialog):
    def __init__(self, name, message, text, icon):
        MultiLineInputDialog.__init__(self, name, message, text, icon)

    def okCallback(self):
        global currentQuery
        currentQuery = self.getValue()
        data = {"prompt": self.getValue(), "max_tokens": 512, "n": 1, "temperature": 0}
        output = checkCacheOrSend(get_code_model(), data)
        if output is not None:
            global guiAdapter
            if guiAdapter is None:
                guiAdapter = PluginComponentProviderAdapter(
                    state.getTool(), "OpenAI Pseudocode"
                )
            guiAdapter.update(str(output))
        else:
            print("Invalid output from api")
        self.close()
        self.dispose()

class SaveAction(DockingAction):
    class SaveActionTask(Task):
        def __init__(self):
            Task.__init__(self, "Saving decompilation to cache", False, False, False, False)

        def run(self, monitor):
            api_type = get_tool_option("openai.api_type")
            model_name = get_code_model()
            filename = re.sub(
                r"\W+",
                "",
                os.path.basename(currentProgram.getExecutablePath()) + "-"
                + currentFunction.getName(),
            ) + "-" + api_type + "-" + model_name + ".txt"
            filepath = os.path.join(pluginPath, "output", filename)
            if os.path.isfile(filepath):
                file = open(filepath, "r")
                jsonData = json.load(file)
                file.close()
                file = open(filepath, "w")
                jsonData[currentQuery] = str(guiAdapter.getText())
                json.dump(jsonData, file)
                file.close()
            else:
                file = open(filepath, "w")
                jsonData = {currentQuery:str(guiAdapter.getText())}
                json.dump(jsonData, file)
                file.close()

    def __init__(self, owner):
        DockingAction.__init__(self, "Save Edits", owner, False)
        self.markHelpUnnecessary()
        self.setEnabled(True)
        icon = ResourceManager.loadImage("images/disk.png")
        self.setToolBarData(ToolBarData(icon))
    
    def actionPerformed(self, actionContext):
        TaskLauncher.launch(self.SaveActionTask())
        
        
class RefreshAction(DockingAction):        
    def __init__(self, owner):
        DockingAction.__init__(self, "Re-generate Pseudocode", owner, False)
        self.markHelpUnnecessary()
        self.setEnabled(True)
        icon = ResourceManager.loadImage("images/reload3.png")
        self.setToolBarData(ToolBarData(icon))
    
    def actionPerformed(self, actionContext):
        TaskLauncher.launch(DecompileTask(currentAddress, 0.25))
        
class FindVulnAction(DockingAction):
    class FindVulnTask(Task):
        def __init__(self):
            Task.__init__(self, "Finding vulnerabilities in pseudocode", False, False, False, False)

        def run(self, monitor):
            global guiAdapter
            decompiledCode = guiAdapter.getText()
            prompt = "Find any possible vulnerabilities in the following code. Describe the cause of the bug and possible ways to trigger it in a code comment. Be concise and only provide relevant information.\nCode:\n\n" + decompiledCode
            global currentQuery
            currentQuery = prompt
            data = {"prompt": prompt, "max_tokens": 512, "n": 1, "temperature": 0, "stream": False}
            output = checkCacheOrSend(get_code_model(), data, decompiledCode)
            if output is not None:
                if guiAdapter is None:
                    guiAdapter = PluginComponentProviderAdapter(
                        state.getTool(), "OpenAI Pseudocode"
                    )
                guiAdapter.update(str(output))
            else:
                print("Invalid output from api")

    def __init__(self, owner):
        DockingAction.__init__(self, "Find vulns", owner, False)
        self.markHelpUnnecessary()
        self.setEnabled(True)
        icon = ResourceManager.loadImage("images/video-x-generic16.png")
        self.setToolBarData(ToolBarData(icon))
        
    def actionPerformed(self, actionContext):
        TaskLauncher.launch(self.FindVulnTask())
            
class AltDecompAction(DockingAction):
    class AltDecompTask(Task):
        def __init__(self):
            Task.__init__(self, "Decompiling function using Ghidra's pseudocode", False, False, False, False)

        def run(self, monitor):
            decompInterface = DecompInterface()
            decompInterface.openProgram(currentProgram)
            results = decompInterface.decompileFunction(currentFunction, 0, None)
            functionCode = results.getDecompiledFunction().getC()
            prompt = "Understand this code and rewrite it in a better manner with more descriptive function/variable names, better logic, and more.\nCode:\n" + functionCode + "New Code:\n"
            global currentQuery
            currentQuery = prompt
            data = {"prompt": prompt, "max_tokens": 512, "n": 1, "temperature": 0}
            output = checkCacheOrSend(get_code_model(), data)
            global guiAdapter
            if output is not None:
                if guiAdapter is None:
                    guiAdapter = PluginComponentProviderAdapter(
                        state.getTool(), "OpenAI Pseudocode"
                    )
                guiAdapter.update(str(output))
            else:
                print("Invalid output from api")

    def __init__(self, owner):
        DockingAction.__init__(self, "Decompile using Ghidra's decomp", owner, False)
        self.markHelpUnnecessary()
        self.setEnabled(True)
        icon = ResourceManager.loadImage("images/exec.png")
        self.setToolBarData(ToolBarData(icon))
        
    def actionPerformed(self, actionContext):
        TaskLauncher.launch(self.AltDecompTask())

            
class LanguageTemplate:
    def __init__(self, inputString):
        if inputString == "swift":
            self.name = "Swift"
            self.template = "This Swift code is idiomatic and uses functions and types from standard libraries.\n"
        elif inputString == "cpp":
            self.name = "C++"
            self.template = "The C++ code is idiomatic and uses standard libraries and range based loops.\n"
        elif inputString == "rust":
            self.name = "Rust"
            self.template = "The RUST code is idiomatic and uses macros, channels, and functions or data types from standard libraries.\n"
        elif inputString == "go":
            self.name = "Go"
            self.template = (
                "The GO code is idiomatic and uses standard libraries and channels.\n"
            )
        else:
            self.name = "C"
            self.template = "The C code is idiomatic and uses functions, types, and structures from standard libraries.\n"

    def getName(self):
        return self.name

    def getTemplate(self):
        return self.template


def string_in_list(s, l):
    return any(map(lambda x: s in x, l))


def getArch():
    return currentProgram.getLanguage().getProcessor().toString()


def getSize():
    return str(currentProgram.getAddressFactory().getDefaultAddressSpace().getSize())


def getLanguage():
    symbolIterator = currentProgram.getSymbolTable().getAllSymbols(True)
    symbols = []
    
    for symbol in symbolIterator:
        symbols.append(symbol.getName(True))

    have_swift = string_in_list("swift_", symbols)
    have_arclite = string_in_list("arclite_", symbols)

    if have_swift and have_arclite:
        return LanguageTemplate("swift")
        
    have_rustc = string_in_list("rust", symbols)
    have_corec = string_in_list("_ZN4core", symbols)

    if have_rustc and have_corec:
        return LanguageTemplate("rust")

    have_runtime = string_in_list("runtime_", symbols)
    have_cgo = string_in_list("goargs", symbols)

    if have_runtime and have_cgo:
        return LanguageTemplate("go")

    have_cxa = string_in_list("cxa_", symbols)
    have_std = string_in_list("_ZN", symbols)

    if have_cxa and have_std:
        return LanguageTemplate("cpp")
        
    return LanguageTemplate("c")


def disassembleFunction(address, temp):
    print("Collecting data about function.")
    global currentFunction
    currentFunction = getFunctionContaining(address)
    if currentFunction is not None:
        addr_set = currentFunction.getBody()
        insts = currentProgram.getListing().getInstructions(addr_set, True)
        arch = getArch()
        size = getSize()
        language = getLanguage()
        full_func = arch + " " + size + "-bit Assembly:\n"
        instructions = ""
        symbols = currentProgram.getSymbolTable()
        refs = "Reference Table:\nAddress Data\n"
        for inst in insts:
            inst_string = inst.toString()
            for i in range(inst.getNumOperands()):
                addr = inst.getAddress(i)
                if addr is not None:
                    data = currentProgram.getListing().getDataAt(addr)
                    if data is not None:
                        refs += addr.toString() + " " + data.toString() + "\n"
                    symbol = symbols.getPrimarySymbol(addr)
                    if symbol is not None:
                        value = symbol.getName(True)
                        if value.find("EXTERNAL") != -1:
                            value = value.replace("<EXTERNAL>::", "")
                        inst_string = inst_string.replace("0x" + addr.toString(), value)
            label = inst.getLabel()
            if label is not None and label != currentFunction.getName():
                final = label + ":\n" + inst_string + "\n"
            else:
                final = inst_string + "\n"
            instructions += final
        calling_conv = currentFunction.DEFAULT_CALLING_CONVENTION_STRING
        params = currentFunction.getParameters()
        func_header = "\n{calling_conv} {func_name}({params}):\n".format(
            calling_conv=calling_conv,
            func_name=currentFunction.getName(),
            params=", ".join(
                [
                    str(param).replace("[", "").replace("]", "").split("@")[0]
                    for param in params
                ]
            ),
        )
        full_func += (
            func_header
            + instructions
            + "//end of function "
            + currentFunction.getName()
            + "\n\n"
            + refs
            + "\nGenerate the "
            + language.getName()
            + " code that produced the above "
            + arch
            + " "
            + size
            + "-bit assembly."
            + language.getTemplate()
        )
        decompileApi(full_func, temp)
    else:
        print("Select a different location.")


def decompileApi(functionData, temp):
    global currentQuery
    currentQuery = functionData
    data = {"prompt": functionData, "max_tokens": 512, "n": 1, "temperature": temp}
    kwargs = {}
    if temp > 0:
        kwargs['noCache'] = True

    output = checkCacheOrSend(get_code_model(), data, **kwargs)
    if output is not None:
        global guiAdapter
        if guiAdapter is None:
            guiAdapter = PluginComponentProviderAdapter(
                state.getTool(), "OpenAI Pseudocode"
            )
        guiAdapter.update(str(output))
    else:
        print("Invalid output from api")


def generateContextApi(pseudocode):
    prompt = (
        "Understand the following code and generate a description for it as a code comment. Be concise and only provide relevant information.\n\nCode:\n"
        + pseudocode
    )
    global currentQuery
    currentQuery = prompt
    data = {"prompt": prompt, "max_tokens": 512, "n": 1, "temperature": 0}
    output = checkCacheOrSend(get_code_model(), data)
    if output is not None:
        global guiAdapter
        if guiAdapter is None:
            guiAdapter = PluginComponentProviderAdapter(
                state.getTool(), "OpenAI Pseudocode"
            )
        guiAdapter.update(str(output) + "\n" + pseudocode)
    else:
        print("Invalid output from api")

def checkCacheOrSend(model_name, data, appendString = None, noCache = False):
    api_type = get_tool_option("openai.api_type")
    filename = re.sub(
        r"\W+",
        "",
        os.path.basename(currentProgram.getExecutablePath()) + "-"
        + currentFunction.getName(),
    ) + "-" + api_type + "-" + model_name + ".txt"
    jsonData = {}
    filepath = os.path.join(pluginPath, "output", filename)
    if os.path.isfile(filepath) and noCache is False:
        f = open(filepath, "r")
        if os.path.getsize(filepath) > 0:
            jsonData = json.load(f)
        f.close()
        if data.get("prompt") in jsonData:
            print("Loading cached response.")
            return jsonData.get(data.get("prompt"))

    output = sendToApi(model_name, data)
    # Do not cache empty results or errors so we try again next time
    if not output:
        return output

    if appendString is not None:
        output += appendString

    jsonData[data.get("prompt")] = str(output)
    if noCache is False:
        f2 = open(filepath, "w+")
        json.dump(jsonData, f2)
        f2.close()
    return output

def sendToApi(model_name, data):
    print("Sending data to OpenAI api.")
    api_type = get_tool_option("openai.api_type")
    api_base = get_tool_option("openai.api_base")
    api_version = get_tool_option("openai.api_version")
    api_key = get_api_key()

    is_chat_api = model_name in ["gpt35", "gpt-3.5-turbo", "gpt-4"]
    type_path = '/chat' if is_chat_api else ''

    if api_type == "azure":
        path = "/openai/deployments/%s%s/completions?api-version=%s" % (model_name, type_path, api_version)
        authorization_header = "Api-Key"
        authorization_value = api_key
    elif api_type == "openai":
        path = "/v1%s/completions" % (type_path,)
        data['model'] = model_name
        authorization_header = "Authorization"
        authorization_value = "Bearer " + api_key
    else:
        return None

    # If this is a Chat API model, convert the prompt into a message, according
    # to the Chat API.
    if is_chat_api:
        prompt = data.pop('prompt')
        data['messages'] = [{'role': 'user', 'content': prompt}]

    try:
        url = URL(api_base + path)
        con = url.openConnection()
        con.setRequestMethod("POST")
        con.setRequestProperty("Content-Type", "application/json")
        con.setRequestProperty("Accept", "application/json")
        con.setRequestProperty(authorization_header, authorization_value)
        con.setDoOutput(True)
        outputStream = con.getOutputStream()
        input_data = String(json.dumps(data)).getBytes("utf-8")
        outputStream.write(input_data, 0, len(input_data))
        outputStream.flush()
        outputStream.close()
        responseCode = con.getResponseCode()
        if responseCode == HttpURLConnection.HTTP_OK:
            inpt = BufferedReader(InputStreamReader(con.getInputStream()))
            response = StringBuffer()
            inputLine = inpt.readLine()
            while inputLine is not None:
                response.append(inputLine)
                inputLine = inpt.readLine()
            inpt.close()
            response_string = response.toString()
            if response_string is not None:
                response_json = json.loads(response_string)
                choice = response_json["choices"][0]
                if is_chat_api:
                    output = choice["message"]['content']
                else:
                    output = choice["text"]
                return output
        else:
            print("Error in accessing api: " + con.getResponseMessage())
            return None
    except java.lang.Exception as err:
        print("Error in sending request: " + err.toString())


def main():
    init_options()
    print("Press Ctrl+J/Cmd+J in any function to decompile it using OpenAI.")
    print("Modify Codex-Decompiler options through Edit > Tool Options > Codex-Decompiler.")
    if not os.path.exists(pluginPath + "output"):
        os.mkdir(pluginPath + "output")
    state.getTool().addAction(PluginDockingAction())


if __name__ == "__main__":
    main()
