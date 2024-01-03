import struct

# The Reader class handles reading constants
# (typically strings) out of the binary.

class Reader:
    def __init__(self, binary):
        self.binary = binary
        self.elf    = binary.elf

    def read_bytes(self, addr, size):
        """Read raw data from the binary"""
        stream  = self.elf.stream
        offsets = list(self.elf.address_offsets(addr))
        if len(offsets) != 1:
            return None
        stream.seek(offsets[0])
        return stream.read(size)

    def read_string(self, addr, size=32):
        """Try to intelligently load a string constant"""
        if self.binary.language == 'c':
            return self.read_string_data(addr, size)

        elif self.binary.language == 'cpp':
            return self.read_string_data(addr, size)

        elif self.binary.language == 'go':
            _, _, string  = self.read_string_struct(addr)
            if string and len(string) > 1:
                return string
            string = self.read_string_data(addr, size)
            if string and len(string) > 1:
                return string

        elif self.binary.language == 'rust':
            ptr, size, string = self.read_string_struct(addr)
            # The format {} is replaced by a space and the string after the format
            # is stored as a separate "struct str" at addr + 16.
            if self.read_bytes(ptr + size, 1) == b' ':
                _, _, suffix = self.read_string_struct(addr + 16)
                if string and suffix:
                    return string + '{}' + suffix
            return string or self.read_string_data(addr, size)

        elif self.binary.language == 'swift':
            string = self.read_string_data(addr, size)
            if string and len(string) > 1:
                return string

    def read_string_data(self, addr, size, cstring=True):
        """Read UTF-8 character data from the binary"""
        if not addr or not size:
            return None

        mem = self.read_bytes(addr, min(32, size))
        if not mem:
            return None
        if cstring:
            mem = mem.split(b'\x00')[0]

        try:
            mem = mem.decode('utf-8')
        except UnicodeDecodeError:
            return None

        if len(mem) > 29:
            mem = mem[:29] + '...'
        return mem

    def read_string_struct(self, addr):
        """Read a typical string struct (including data) from the binary"""
        ptr    = self.read_uint64(addr)
        size   = self.read_uint64(addr + 8)
        string = self.read_string_data(ptr, size)
        return ptr, size, string

    def read_uint64(self, addr):
        """Read a little-endian UInt64 from the binary"""
        mem = self.read_bytes(addr, 8)
        if not mem:
            return None
        return struct.unpack('<Q', mem)[0]
