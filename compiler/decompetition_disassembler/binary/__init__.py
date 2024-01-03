import capstone
import fnmatch
import re

from elftools.elf.elffile import ELFFile

from .mapper   import Mapper
from .reader   import Reader
from .renderer import Renderer
from .scanner  import Scanner

# Regex for removing annoying Rust hashes:
DERUST = re.compile(r'17h[0-9a-f]{16}E\b')


class Binary:
    def __init__(self, path, language, arch=capstone.CS_ARCH_X86, mode=capstone.CS_MODE_64):
        self.file = open(path, 'rb')
        self.elf  = ELFFile(self.file)
        self.cap  = capstone.Cs(arch, mode)
        self.cap.detail = True

        self.language = language
        self.scanner  = Scanner(self)
        self.mapper   = Mapper(self)
        self.reader   = Reader(self)
        self.renderer = Renderer(self)

    def disassemble(self, patterns, srcmap=True):
        result = {}

        for function in self.functions:
            fname = function.name
            for pattern in patterns:
                if fnmatch.fnmatchcase(fname, pattern):
                    d, a = self.renderer.render_function(fname)
                    if self.language == 'rust':
                        d = [re.sub(DERUST, 'E', i) for i in d]
                        fname = re.sub(DERUST, 'E', fname)
                    if d and d[-1] != '':
                        d.append('')

                    output = {'asm': '\n'.join(d)}
                    if srcmap:
                        output['map'] = self.get_source_lines(a)
                    result[fname] = output

        return result

    @property
    def functions(self):
        return self.scanner.functions

    def get_source_lines(self, addrs):
        return self.mapper.get_source_lines(addrs)

    @property
    def plt(self):
        return self.scanner.plt

    def read_string(self, addr):
        return self.reader.read_string(addr)

    @property
    def sections(self):
        return self.scanner.sections

    @property
    def symbols(self):
        return self.scanner.symbols
