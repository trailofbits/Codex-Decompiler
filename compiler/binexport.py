from com.google.security.binexport import BinExportExporter
from java.io import File
import os

addr_set = currentProgram.getMemory()
program_name = currentProgram.getName()
output_path = os.environ['BINEXPORT_OUTPUT_PATH']
full_path = os.path.join(output_path, program_name + ".BinExport")
name = File(full_path)
exporter = BinExportExporter()
exporter.export(name, currentProgram, addr_set, monitor)