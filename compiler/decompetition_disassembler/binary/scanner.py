import capstone

from intervaltree            import IntervalTree
from elftools.elf.relocation import RelocationSection

# The Scanner class handles finding named entries in an ELF binary,
# specifically: sections, symbols, and functions.

def address(instruction, operand):
    """Calculate the absolute address referred to by an instruction"""
    # Heavily based on the Capstone unit tests (in lieu of decent documentation):
    # https://github.com/aquynh/capstone/blob/next/bindings/python/test_x86.py#L206
    if operand.type == capstone.x86.X86_OP_REG and operand.reg == capstone.x86.X86_REG_RIP:
        return instruction.address + instruction.size
    if operand.type == capstone.x86.X86_OP_IMM:
        if capstone.x86.X86_GRP_JUMP in instruction.groups or capstone.x86.X86_GRP_CALL in instruction.groups:
            return operand.imm
    if operand.type == capstone.x86.X86_OP_MEM:
        if operand.mem.segment == 0 and operand.mem.base == capstone.x86.X86_REG_RIP and operand.mem.index == 0:
            return instruction.address + instruction.size + operand.mem.disp
    return None


class Function:
    """Internal representation of a function"""
    def __init__(self, symbol):
        self.name  = symbol.name
        self.addr  = symbol.addr
        self.range = None


class MiniMap:
    """A helper class to serve as a multi-key map"""
    def __init__(self):
        self.data = []
        self.map  = {}

    def __contains__(self, item):
        return item in self.map

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, key):
        return self.map[key]

    def add(self, value, *keys):
        for key in keys:
            self.map[key] = value
        self.data.append(value)

    def get(self, key, default=None):
        return self.map.get(key, default)


class Scanner:
    def __init__(self, binary):
        self.elf = binary.elf
        self.cap = binary.cap

        self.sections = MiniMap()
        self.scan_sections()

        self.symbols = MiniMap()
        self.plt = IntervalTree()
        self.scan_symbols()

        self.functions = MiniMap()
        self.scan_functions()

    def scan_functions(self):
        """Collect all local function symbols"""
        functions = []
        text = self.sections['.text']

        for symbol in self.symbols:
            if symbol['st_info']['type'] == 'STT_FUNC':
                if symbol.addr in text.range:
                    f = Function(symbol)
                    self.functions.add(f, f.name, f.addr)
                    functions.append(f)

        functions.sort(key=lambda f: f.addr)
        for i in range(1, len(functions)):
            # Assume that all functions are contiguous...
            functions[i-1].range = range(functions[i-1].addr, functions[i].addr)
        # And assume that the last function ends the .text section...
        functions[-1].range = range(functions[-1].addr, text.range.stop)

    def scan_plt(self):
        """Get symbols for any functions called through the .plt"""
        section = self.sections.get('.plt')
        if not section: return

        prev = section.addr
        for instruction in self.cap.disasm(section.data(), section.addr):
            if capstone.x86.X86_GRP_JUMP in instruction.groups:
                addr = address(instruction, instruction.operands[0])
                if addr != section.addr:
                    symbol = self.symbols.get(addr)
                    if symbol and symbol.name:
                        addr = instruction.address + instruction.size
                        self.plt[prev:addr] = symbol.name + '@plt'
                    prev = instruction.address + instruction.size

    def scan_plt_sec(self):
        """Get symbols for any functions called through the .plt.sec"""
        section = self.sections.get('.plt.sec')
        if not section: return

        prev = section.addr
        for instruction in self.cap.disasm(section.data(), section.addr):
            if capstone.x86.X86_GRP_JUMP in instruction.groups:
                addr   = address(instruction, instruction.operands[0])
                symbol = self.symbols.get(addr)
                if symbol and symbol.name:
                    addr = instruction.address + instruction.size
                    self.plt[prev:addr] = symbol.name + '@plt.sec'
                prev = instruction.address + instruction.size

    def scan_sections(self):
        """Index all available sections and their addresses"""
        for section in self.elf.iter_sections():
            section.addr  = section['sh_addr']
            section.range = range(section.addr, section.addr + section.data_size)
            self.sections.add(section, section.name, section.addr)

    def scan_symbols(self):
        """Find and index all the symbols that we can"""
        self.scan_symtab()
        self.scan_relocations()

        self.scan_plt()
        self.scan_plt_sec()

    def scan_symtab(self):
        """Read symbols stored in the .symtab section"""
        for symbol in self.sections['.symtab'].iter_symbols():
            if symbol.name:
                symbol.addr = symbol.__dict__['entry']['st_value']
                self.symbols.add(symbol, symbol.name, symbol.addr)

    def scan_relocations(self):
        """Read symbols from any relocation sections"""
        for section in self.sections:
            if isinstance(section, RelocationSection):
                symtab = self.elf.get_section(section['sh_link'])
                for relocation in section.iter_relocations():
                    symbol = symtab.get_symbol(relocation['r_info_sym'])
                    if symbol.name:
                        symbol.addr = relocation['r_offset']
                        self.symbols.add(symbol, symbol.name, symbol.addr)
