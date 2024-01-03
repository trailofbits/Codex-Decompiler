import functools
import intervaltree

# The Mapper class handles mapping instruction
# addresses to source code lines. It reads this
# information out of the debug info as needed.

class Mapper:
    def __init__(self, binary):
        self.binary = binary
        self.elf    = binary.elf

    def get_source_line(self, address):
        """Map a single instruction address to a line number"""
        if address is None:
            return None
        matches = self.source_map[address]
        if len(matches) == 1:
            return next(iter(matches)).data
        # sys.stderr.write('Multiple source map lines!?\n')

    def get_source_lines(self, addresses):
        """Map a list of instruction addresses to a list of line numbers"""
        return list(map(self.get_source_line, addresses))

    @functools.cached_property
    def source_map(self):
        index = intervaltree.IntervalTree()
        dinfo = self.elf.get_dwarf_info()

        def get_cu_die(cu):
            for die in cu.iter_DIEs():
                if die.tag == 'DW_TAG_compile_unit':
                    return die

        for cu in dinfo.iter_CUs():
            # Go includes a huge amount of extra debug info. It's slow. Skip it.
            if self.binary.language == 'go':
                die = get_cu_die(cu)
                if die.attributes['DW_AT_name'].value != b'main':
                    continue

            lineprog  = dinfo.line_program_for_CU(cu)
            prevstate = None
            if lineprog is None:
                continue
            for entry in lineprog.get_entries():
                if entry.state is None:
                    continue
                if entry.state.end_sequence:
                    prevstate = None
                    continue
                if prevstate:
                    a = prevstate.address
                    z = entry.state.address
                    if a == z:
                        z += 1
                    index[a:z] = prevstate.line
                prevstate = entry.state
        return index
