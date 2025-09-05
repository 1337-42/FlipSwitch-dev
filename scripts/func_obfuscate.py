import re
import sys
import random
import string

def random_name(length=8):
    """Generate a random obfuscated function name"""
    return 'f_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def find_functions_to_obfuscate(header_file):
    """Find function names and variable names marked for obfuscation in header file"""
    functions = set()
    variables = set()
    
    try:
        with open(header_file, 'r') as f:
            header_content = f.read()
        
        # Look for function prototypes followed by // obfuscate comment
        function_patterns = [
            # Pattern 1: return_type function_name(params); // obfuscate
            r'^\s*[\w\s]+\s+(\w+)\s*\([^)]*\)\s*;\s*//\s*obfuscate',
            # Pattern 2: return_type *function_name(params); // obfuscate (pointer return)
            r'^\s*[\w\s]+\s*\*\s*(\w+)\s*\([^)]*\)\s*;\s*//\s*obfuscate',
            # Pattern 3: static inline return_type function_name(params); // obfuscate
            r'^\s*static\s+inline\s+[\w\s]+\s+(\w+)\s*\([^)]*\)\s*;\s*//\s*obfuscate'
        ]
        
        for pattern in function_patterns:
            for match in re.finditer(pattern, header_content, re.MULTILINE | re.IGNORECASE):
                func_name = match.group(1)
                if func_name and len(func_name) > 2:
                    functions.add(func_name)
        
        # Look for variable declarations followed by // obfuscate comment
        # Yes this is a mess but its only a PoC.
        variable_patterns = [
            # Pattern 1: type variable_name = value; // obfuscate
            r'^\s*[\w\s]+\s+(\w+)\s*=\s*[^;]*;\s*//\s*obfuscate',
            # Pattern 2: type *variable_name = value; // obfuscate (pointer variables)
            r'^\s*[\w\s]+\s*\*\s*(\w+)\s*=\s*[^;]*;\s*//\s*obfuscate',
            # Pattern 3: static type variable_name = value; // obfuscate
            r'^\s*static\s+[\w\s]+\s+(\w+)\s*=\s*[^;]*;\s*//\s*obfuscate',
            # Pattern 4: static type *variable_name = value; // obfuscate
            r'^\s*static\s+[\w\s]+\s*\*\s*(\w+)\s*=\s*[^;]*;\s*//\s*obfuscate'
        ]
        
        for pattern in variable_patterns:
            for match in re.finditer(pattern, header_content, re.MULTILINE | re.IGNORECASE):
                var_name = match.group(1)
                if var_name and len(var_name) > 2:
                    variables.add(var_name)
        
        print(f"Found {len(functions)} functions marked for obfuscation: {sorted(functions)}")
        print(f"Found {len(variables)} variables marked for obfuscation: {sorted(variables)}")
        
        # Combine functions and variables
        all_symbols = functions.union(variables)
        
    except Exception as e:
        print(f"Error: Could not read header file {header_file}: {e}")
        return set()

    return all_symbols

def create_obfuscation_header(symbols, macro_file):
    """Create a simple header file with #define macros for function and variable obfuscation"""
    
    # Generate random names for each symbol
    name_map = {symbol: random_name() for symbol in symbols}
    
    # Write the macro header file
    with open(macro_file, 'w') as f:
        f.write('// Auto-generated function and variable obfuscation macros\n')
        f.write('#ifndef FUNC_OBF_MACROS_H\n')
        f.write('#define FUNC_OBF_MACROS_H\n\n')
        
        f.write('// Function and variable name obfuscation macros\n')
        for original, obfuscated in sorted(name_map.items()):
            f.write(f'#define {original} {obfuscated}\n')
        
        f.write('\n#endif // FUNC_OBF_MACROS_H\n')
    
    print(f'Generated {macro_file} with {len(name_map)} symbol renames.')
    return name_map

def create_obfuscated_source(source_file, out_file, macro_file, name_map, header_file=None):
    """Create obfuscated source file by including the macro header first and handling special cases"""
    
    with open(source_file, 'r') as f:
        content = f.read()
    
    # Handle special kernel module cases - replace function names in module_init/exit before macro substitution
    for original, obfuscated in name_map.items():
        # Handle module_init and module_exit calls
        content = re.sub(rf'\bmodule_init\s*\(\s*{re.escape(original)}\s*\)', f'module_init({obfuscated})', content)
        content = re.sub(rf'\bmodule_exit\s*\(\s*{re.escape(original)}\s*\)', f'module_exit({obfuscated})', content)
    
    # Add the macro header include at the very top, before any other includes
    include_line = f'#include "{macro_file}"\n'
    
    # If we have a custom header file (like randomized metadata), include it too
    if header_file:
        include_line += f'#include "{header_file}"\n'
    
    # Split content into lines
    lines = content.splitlines()
    
    # Insert the macro include as the very first line
    lines.insert(0, include_line)
    
    # Write to output file
    with open(out_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f'Created obfuscated source: {out_file} (macro header included first)')

def main():
    if len(sys.argv) < 4:
        print('Usage: python func_obfuscate.py <header.h> <source.c> <output.c> [custom_header.h]')
        sys.exit(1)
    
    header_file = sys.argv[1]
    source_file = sys.argv[2]
    out_file = sys.argv[3]
    custom_header = sys.argv[4] if len(sys.argv) > 4 else None
    macro_file = 'func_obf_macros.h'
    
    print(f"Simple symbol obfuscation: {header_file} + {source_file} -> {out_file}")
    
    # Find functions and variables marked for obfuscation in header
    symbols = find_functions_to_obfuscate(header_file)
    
    if not symbols:
        print("No symbols found marked for obfuscation!")
        print("Add '// obfuscate' comment after function prototypes and variable declarations in the header file.")
        return
    
    # Create obfuscation header with simple #define macros
    name_map = create_obfuscation_header(symbols, macro_file)
    
    # Create obfuscated source file
    create_obfuscated_source(source_file, out_file, macro_file, name_map, custom_header)
    
    print(f'Symbol obfuscation complete!')
    print(f'Obfuscated {len(name_map)} symbols (functions + variables) using simple #define macros')

if __name__ == '__main__':
    main()
