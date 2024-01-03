#! /usr/bin/env python3

import fnmatch
import re
import sys

from binary import Binary

def print_text(disasm, stream=sys.stdout):
    for name, info in disasm.items():
        stream.write(info['asm'])
        stream.write('\n')

def print_yaml(disasm, stream=sys.stdout):
    from yaml import Dumper
    dumper = Dumper(stream)

    # Force a Git-friendly output format:
    # https://stackoverflow.com/a/8641732
    def strdump(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    dumper.add_representer(str, strdump)

    dumper.open()
    dumper.represent(disasm)
    dumper.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--language', help='the original source language', required=True)
    parser.add_argument('-s', '--srcmap',   help='include line numbers from the debug info', action='store_true')
    parser.add_argument('-y', '--yaml',     help='produce YAML output instead of plaintext', action='store_true')
    parser.add_argument('binary',           help='path to an ELF binary to disassemble')
    parser.add_argument('patterns',         help='function names (glob patterns)', nargs='+')

    args   = parser.parse_args()
    binary = Binary(args.binary, args.language)
    disasm = binary.disassemble(args.patterns, args.srcmap)

    if args.yaml:
        print_yaml(disasm)
    else:
        print_text(disasm)
