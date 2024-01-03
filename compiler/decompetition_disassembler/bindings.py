import sys
import io
import yaml
from decompetition_disassembler.binary import Binary
from diff_match_patch import diff_match_patch
dmp = diff_match_patch()

def diff_all(disasm, target):
    """Diff two disassembly maps"""
    names = set()
    names.update(disasm.keys())
    names.update(target.keys())

    result = {}
    deltas = [0, 0, 0, 0]

    for name in names:
        if name not in disasm:
            t = target[name]['asm']
            n = nlines(t)
            hunks  = [[1, t, n]]
            delta  = [0, 0, n, n]
            srcmap = []
        elif name not in target:
            d = disasm[name]['asm']
            n = nlines(d)
            hunks  = [[-1, d, n]]
            delta  = [n, 0, 0, n]
            srcmap = disasm[name].get('map', [])
        else:
            t = target[name]['asm']
            d = disasm[name]['asm']
            hunks, delta = diff_one(d, t)
            srcmap = disasm[name].get('map', [])

        for i in range(4):
            deltas[i] += delta[i]

        result[name] = {
            'hunks':  hunks,
            'delta':  delta,
            'srcmap': srcmap
        }

    return result, deltas

def diff_one(disasm, target):
    """Diff two text blocks of disassembly"""
    d, t, map = dmp.diff_linesToChars(disasm, target)
    diffs = dmp.diff_main(d, t, False)
    dmp.diff_charsToLines(diffs, map)

    delta = [0, 0, 0, 0]
    hunks = []
    for diff in diffs:
        n = diff[1].count('\n')
        hunks.append([diff[0], diff[1], n])

        delta[diff[0] + 1] += n
        delta[3] += n

    return hunks, delta

def nlines(text):
    """Count the number of lines in a text block"""
    n = text.count('\n')
    if not text.endswith('\n'):
        n += 1
    return n


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

def get_disasm(binary_path, language, func_name):
    binary = Binary(binary_path, language)
    disasm = binary.disassemble([func_name], None)

    return disasm