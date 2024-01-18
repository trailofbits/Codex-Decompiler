# This ghidra headless script allows you to export the ghidra pseudocode of a function
from ghidra.program.model.symbol import SymbolType
from ghidra.app.decompiler import DecompInterface
import os

name = os.environ['FUNC_NAME']
filename = name.replace(":","_")

output_path = os.environ['PSEUDOCODE_OUTPUT_PATH']
program_name = currentProgram.getName()
full_path = os.path.join(output_path, program_name + "_" + filename + ".txt")

symbolTable = currentProgram.getSymbolTable()

symbols = symbolTable.getSymbolIterator()

for symbol in symbols:
    if symbol.getSymbolType() == SymbolType.FUNCTION:
        print(symbol.getName(True))
        if symbol.getName(True) == name:
            print("Found function!")
            function = getFunctionAt(symbol.getAddress())
            decompInterface = DecompInterface()
            decompInterface.openProgram(currentProgram)
            results = decompInterface.decompileFunction(function, 0, None)
            functionCode = results.getDecompiledFunction().getC()
            f = open(full_path, "w")
            f.write(functionCode)
            f.close()
