import re
import sys
import os

def xor_obfuscate(s, key):
    return [ord(c) ^ key for c in s] + [0]

def macro_name(s):
    # Create a valid C identifier from the string
    return 'OBF_' + re.sub(r'[^a-zA-Z0-9_]', '_', s.upper())

def process_file(c_file, key=0xAA):
    with open(c_file, 'r') as f:
        content = f.read()
    pattern = r'O_STRING\(("[^"]+")\)'
    matches = re.findall(pattern, content)
    entries = {}
    for m in matches:
        s = m.strip('"')
        name = macro_name(s)
        obf = xor_obfuscate(s, key)
        entries[m] = {
            'original': s,
            'macro': name,
            'obfuscated': obf
        }
    return content, entries

def write_header(entries, header_file, key=0xAA):
    with open(header_file, 'w') as f:
        f.write('// Auto-generated obfuscated pointers\n')
        f.write('#ifndef OBFUSCATED_STRINGS_H\n#define OBFUSCATED_STRINGS_H\n\n')
        for entry in entries.values():
            arr = ', '.join(f'0x{b:02X}' for b in entry['obfuscated'])
            f.write(f'static const unsigned char {entry['macro']}[] = {{{arr}}}; // "{entry['original']}"\n')
            f.write(f'#define {entry['macro']}_LEN {len(entry['obfuscated'])}\n')
            f.write(f'#define {entry['macro']}_KEY 0x{key:02X}\n')
        f.write('\n#endif // OBFUSCATED_STRINGS_H\n')

def replace_placeholders(content, entries, key=0xAA):
    for placeholder, entry in entries.items():
        # Place comment after the semicolon, not inside the function call
        replacement = f'deobfuscate({entry["macro"]}, {entry["macro"]}_LEN, {entry["macro"]}_KEY)'  # function call only
        # Replace and add comment after semicolon if present
        pattern = re.escape(f'O_STRING("{entry["original"]}")') + r'(\s*;)'
        content = re.sub(pattern, replacement + r'; /* "' + entry["original"] + '" */', content)
        # Fallback for cases without semicolon (e.g., macro usage in expressions)
        content = content.replace(f'O_STRING("{entry["original"]}")', replacement)
    return content

def ensure_header_included(content, header_name):
    include_line = f'#include "{header_name}"\n'
    # Insert after first #include or at the top if none found
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith('#include'):
            # Insert after the first #include
            lines.insert(i+1, include_line)
            break
    else:
        # No #include found, insert at top
        lines.insert(0, include_line)
    return ''.join(lines)

def main():
    if len(sys.argv) < 4:
        print('Usage: python obfuscate_and_replace.py <source.c> <output.c> <output.h> [key]')
        sys.exit(1)
    c_file = sys.argv[1]
    out_c_file = sys.argv[2]
    header_file = sys.argv[3]
    key = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0xAA
    content, entries = process_file(c_file, key)
    write_header(entries, header_file, key)
    new_content = replace_placeholders(content, entries, key)
    new_content = ensure_header_included(new_content, header_file)
    with open(out_c_file, 'w') as f:
        f.write(new_content)
    print(f'Updated {out_c_file} and generated {header_file}.')

if __name__ == '__main__':
    main()
