#!/usr/bin/env python3
"""
Simple script to randomize kernel module metadata for obfuscation.
This helps hide the original module name, author, and description.
"""

import re
import sys
import random
import string

def generate_random_name():
    """Generate a random module name that looks plausible"""
    prefixes = ['kmod', 'kern', 'sys', 'drv', 'mod', 'hw', 'dev', 'net', 'usb', 'pci']
    suffixes = ['core', 'utils', 'helper', 'driver', 'support', 'handler', 'mgmt', 'ctrl']
    
    prefix = random.choice(prefixes)
    suffix = random.choice(suffixes)
    number = random.randint(10, 99)
    
    return f"{prefix}_{suffix}_{number}"

def generate_random_author():
    """Generate a random but plausible author name"""
    first_names = ['Alex', 'Chris', 'Jordan', 'Sam', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery', 'Blake']
    last_names = ['Smith', 'Johnson', 'Brown', 'Wilson', 'Davis', 'Miller', 'Garcia', 'Anderson', 'Thomas', 'Jackson']
    
    first = random.choice(first_names)
    last = random.choice(last_names)
    
    return f"{first} {last}"

def generate_random_description():
    """Generate a random but plausible module description"""
    components = ['Device', 'System', 'Hardware', 'Network', 'Memory', 'Process', 'Driver', 'Interface']
    actions = ['Management', 'Control', 'Support', 'Handler', 'Monitor', 'Utility', 'Helper', 'Service']
    purposes = ['for enhanced performance', 'with advanced features', 'providing core functionality', 
               'with optimized handling', 'for system stability', 'with improved efficiency']
    
    component = random.choice(components)
    action = random.choice(actions)
    purpose = random.choice(purposes)
    
    return f"{component} {action} {purpose}"

def randomize_header_metadata(header_file, output_file):
    """Randomize MODULE_NAME, MODULE_AUTHOR_NAME, and MODULE_DESC in header file"""
    
    with open(header_file, 'r') as f:
        content = f.read()
    
    # Generate random values
    random_name = generate_random_name()
    random_author = generate_random_author()
    random_desc = generate_random_description()
    
    # Replace the defines
    content = re.sub(r'#define\s+MODULE_NAME\s+"[^"]*"', 
                     f'#define MODULE_NAME "{random_name}"', content)
    
    content = re.sub(r'#define\s+MODULE_AUTHOR_NAME\s+"[^"]*"', 
                     f'#define MODULE_AUTHOR_NAME "{random_author}"', content)
    
    content = re.sub(r'#define\s+MODULE_DESC\s+"[^"]*"', 
                     f'#define MODULE_DESC "{random_desc}"', content)
    
    # Write to output file
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"Randomized metadata:")
    print(f"  Name: {random_name}")
    print(f"  Author: {random_author}")
    print(f"  Description: {random_desc}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 randomize_metadata.py <input_header.h> <output_header.h>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    randomize_header_metadata(input_file, output_file)
    print(f"Updated {output_file} with randomized metadata")

if __name__ == '__main__':
    main()
