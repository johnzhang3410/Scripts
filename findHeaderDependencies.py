import os
import re
import sys
from collections import deque

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py target_header.h")
        sys.exit(1)
    target_header = sys.argv[1].replace('\\', '/')

    # Regular expression to match #include statements
    include_re = re.compile(r'^\s*#include\s*["<]([^">]+)[">]')

    root_dir = os.getcwd()

    # Directories to exclude
    exclude_dirs = {'build_caches', 'coverage-reports'}

    # Build a mapping from files to the files they include
    file_includes = {}

    # Collect all .h and .cpp files and their includes
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Modify dirnames in-place to remove excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for filename in filenames:
            if filename.endswith('.h') or filename.endswith('.cpp'):
                file_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(file_path, root_dir).replace('\\', '/')
                includes = set()
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            m = include_re.match(line)
                            if m:
                                # Extract the included file path
                                included = m.group(1).replace('\\', '/')
                                included_normalized = os.path.normpath(included).replace('\\', '/')
                                includes.add(included_normalized)
                    # Store the set of included files for this file
                    file_includes[rel_path] = includes
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

    # Build a reverse mapping from included files to the files that include them
    included_by = {}
    for file, includes in file_includes.items():
        # Exclude files ending with _test.cpp or _test.h
        if file.endswith('_test.cpp') or file.endswith('_test.h'):
            continue  # Skip test files
        for included in includes:
            included_by.setdefault(included, set()).add(file)

    # Use a queue for BFS traversal and build the dependency tree
    queue = deque()
    dependencies = {}
    processed_files = set()

    target_header_normalized = os.path.normpath(target_header).replace('\\', '/')
    queue.append((target_header_normalized, None))  # (current_file, parent_file)

    while queue:
        current_file, parent_file = queue.popleft()
        if current_file in processed_files:
            continue
        processed_files.add(current_file)

        # Add to dependencies with parent information
        dependencies[current_file] = parent_file

        # Find all files that include the current file
        including_files = set()
        for included_path, files in included_by.items():
            if included_path.endswith(current_file):
                including_files.update(files)

        for including_file in including_files:
            if including_file not in dependencies:
                # Exclude files ending with _test.cpp or _test.h
                if including_file.endswith('_test.cpp') or including_file.endswith('_test.h'):
                    continue  # Skip test files
                # Add to the queue for processing
                queue.append((including_file, current_file))

    # Calculate the common prefix among all file paths
    all_files = list(dependencies.keys())
    common_prefix = os.path.commonprefix(all_files)
    # Ensure the common prefix ends at a directory separator
    common_prefix = os.path.dirname(common_prefix) + '/'

    # Function to recursively print the dependency tree with visual representation
    def print_dependency_tree(file, prefix='', is_last=True, visited=set()):
        if file in visited:
            display_name = file[len(common_prefix):].lstrip('/')
            print(f"{prefix}{'└── ' if is_last else '├── '}{display_name} (already visited)")
            return
        visited.add(file)
        display_name = file[len(common_prefix):].lstrip('/')
        connector = '└── ' if is_last else '├── '
        print(f"{prefix}{connector}{display_name}")
        children = [f for f, parent in dependencies.items() if parent == file]
        # Sort children for consistent output
        children.sort()
        for i, child in enumerate(children):
            is_child_last = (i == len(children) - 1)
            new_prefix = prefix + ('    ' if is_last else '│   ')
            print_dependency_tree(child, new_prefix, is_child_last, visited)

    # Start printing the dependency tree from the target header
    print("Dependency Tree:")
    print_dependency_tree(target_header_normalized)

if __name__ == '__main__':
    main()
