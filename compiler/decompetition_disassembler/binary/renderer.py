import capstone
import json

# The Renderer class renders machine instructions
# as sanitized assembly code.

def hext(num, pos='', neg='-'):
    """Renders an integer as a hexidecimal text string"""
    result = pos if num >= 0 else neg
    if -10 < num < 10:
        result += str(abs(num))
    else:
        result += '0x%x' % abs(num)
    return result

def is_terminal(instruction):
    """Returns whether or not an instruction redirects execution"""
    if instruction.mnemonic == 'jmp':
        return True
    if instruction.mnemonic == 'ud2':
        return True
    if capstone.x86.X86_GRP_RET in instruction.groups:
        return True
    if capstone.x86.X86_GRP_INT in instruction.groups:
        return True
    return False


class Renderer:
    def __init__(self, binary):
        self.binary    = binary
        self.elf       = binary.elf
        self.cap       = binary.cap
        self.plt       = binary.plt
        self.functions = binary.functions
        self.sections  = binary.sections
        self.symbols   = binary.symbols

        self.memory = {}

    def render(self, name):
        """Disassemble a function or section"""
        if name in self.functions:
            return self.render_function(name)
        elif name in self.sections:
            return self.render_section(name)
        else:
            raise Exception('Could not find target: %s' % name)

    def render_address(self, addr, names={}):
        """Get the human-friendly name for an address if there is one"""
        if addr in self.symbols:
            return self.symbols[addr].name
        if self.plt[addr]:
            return next(iter(self.plt[addr])).data
        if addr in self.sections:
            return self.sections[addr].name
        if addr in self.memory:
            return self.memory[addr]
        if addr in names:
            return names[addr]
        # return '0x%x' % addr
        return None

    def render_disassembly(self, data, addr):
        """Disassemble a block of machine instructions"""
        disasm  = list(self.cap.disasm(data, addr))
        leaders = set([addr])
        blocks  = {}

        # Hack to force local scoping of global names:
        self.memory = {}

        for i in disasm:
            if capstone.x86.X86_GRP_JUMP in i.groups:
                leaders.add(i.operands[0].value.imm)
                leaders.add(i.address + i.size)

        leaders = sorted(leaders)
        for baddr in leaders:
            if baddr in self.sections or baddr in self.symbols:
                continue
            blocks[baddr] = 'block' + str(len(blocks) + 1)

        d = [] # Textual Disassembly
        a = [] # Instruction Addresses

        for i in disasm:
            if i.address in self.symbols:
                d.append(self.symbols[i.address].name + ':')
                a.append(i.address)
            elif i.address in self.sections:
                d.append(self.sections[i.address].name + ':')
                a.append(i.address)
            elif i.address in blocks:
                d.append(blocks[i.address] + ':')
                a.append(i.address)

            if i.mnemonic == 'nop':
                continue

            ops = ', '.join([self.render_operand(i, o, blocks) for o in i.operands])
            d.append(('  %-7s %s' % (i.mnemonic, ops)).rstrip())
            a.append(i.address)

            if i.address >= leaders[-1] and is_terminal(i):
                break
        return d, a

    def render_function(self, name):
        """Disassemble a function by name or address"""
        func = self.functions[name]
        text = self.sections['.text']
        a    = func.range.start - text.addr
        z    = func.range.stop  - text.addr
        data = text.data()[a:z]
        return self.render_disassembly(data, func.addr)

    def render_operand(self, instruction, operand, names={}):
        """Generate a human-friendly representation for an assembly operand"""
        # Heavily based on the Capstone unit tests (in lieu of decent documentation):
        # https://github.com/aquynh/capstone/blob/next/bindings/python/test_x86.py#L206
        if operand.type == capstone.x86.X86_OP_REG:
            return instruction.reg_name(operand.reg)
        if operand.type == capstone.x86.X86_OP_IMM:
            if capstone.x86.X86_GRP_JUMP in instruction.groups or capstone.x86.X86_GRP_CALL in instruction.groups:
                name = self.render_address(operand.imm, names)
                if not name:
                    name = 'mem' + str(len(self.memory) + 1)
                    self.memory[operand.imm] = name
                return name
            return hext(operand.imm)
        if operand.type == capstone.x86.X86_OP_MEM:
            if operand.mem.segment == 0 and operand.mem.base == capstone.x86.X86_REG_RIP and operand.mem.index == 0:
                addr = instruction.address + instruction.size + operand.mem.disp
                name = self.render_address(addr, names)
                if not name:
                    name = 'mem' + str(len(self.memory) + 1)
                    self.memory[addr] = name
                string = self.binary.read_string(addr)
                if string:
                    return '[' + name + ']; ' + json.dumps(string)
                else:
                    return '[' + name + ']'
            result = '['
            if operand.mem.segment != 0:
                result  = instruction.reg_name(operand.mem.segment) + ':['
            if operand.mem.base != 0:
                result += instruction.reg_name(operand.mem.base)
            if operand.mem.index != 0:
                if not result.endswith('['):
                    result += '+'
                result += instruction.reg_name(operand.mem.index)
                if operand.mem.scale != 1:
                    result += ' * %d' % operand.mem.scale
            if operand.mem.disp != 0:
                if result.endswith('['):
                    result += hext(operand.mem.disp)
                else:
                    result += hext(operand.mem.disp, pos='+')
            return result + ']'

    def render_section(self, name):
        """Disassemble a section by name or address"""
        s = self.sections[name]
        return self.render_disassembly(s.data(), s.addr)
