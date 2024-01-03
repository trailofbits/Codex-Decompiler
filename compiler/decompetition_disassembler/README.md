# Disassembler & Differ

This is a refactor of the disassembler and differ used in Decompetition 2020.


## The Disassembler

You can use the disassembler via the command line:

```sh
python3 disassembler.py -l language path/to/binary.out funcname ...
```

This will produce plain text output.  Add the `-y` option to get the YAML output
used by the differ.  This has the following format:

```yaml
functions:
  (funcname):
    asm: | # disassembly text for this function
      nop
      nop
      nop
    map: # source code line number for each instruction, if available
    - 42
    - null
    - 108
```

The source map will only be present in YAML mode, and even then only when passed
the `-s` option to enable the it.


## The Differ

You can also use the differ via the command line:

```sh
python3 differ.py path/to/candidate.yml path/to/target.yml
```

This will produce YAML output with the following format:

```yaml
functions:
  (funcname):
    delta:
    - 1 # number of lines appearing only in the candidate
    - 2 # number of lines appearing in both disassemblies
    - 3 # number of lines appearing only in the target
    - 6 # total number of lines in this function
    hunks:
    - - 1 # hunk type (-1 = candidate only; 0 = shared; 1 = target only)
      - | # disassembly text for this hunk
        nop
        nop
      - 2 # total number of lines in this hunk
    - ...
    srcmap: # source code line numbers from the candidate
    - null
    - 69
    - ...
```

## The Binary Class

Most of the work happens in the disassembler, which has been spread over several
files for readability.  If you're interested in specific functionality, here's
where to look:

- `binary/__init__.py` contains the `Binary` class, but not much happens here.
- `binary/mapper.py` has functions for mapping assembly instructions to source code lines.
- `binary/reader.py` has functions for reading string constants out of the binary.
- `binary/renderer.py` takes care of generating the disassembly text.
- `binary/scanner.py` finds symbols and names in the binary.
