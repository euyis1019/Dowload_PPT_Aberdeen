# folder_tree

A Python package for printing folder directory trees.

## Features

- Supports ignoring hidden files and folders.
- Supports wildcard pattern exclusion of files or folders.
- Supports different output formats: string, JSON, XML.
- Optionally display file sizes.
- Customizable maximum recursion depth.

## Installation

```bash
git clone https://github.com/euyis1019/folder_treeForLLM.git
cd folder_tree
pip install .
```
## How to use
### Base

```python
import folder_tree

# basic usage
output = folder_tree.print_tree(path='..', max_depth=2)
print(output)

# parameters
output = folder_tree.print_tree(
    path='..',
    max_depth=3,
    exclude=['.git'],
    exclude_patterns=['*.pyc', '__pycache__'],
    show_hidden=False,
    include_file_sizes=True,
    output_format='string',
)
print(output)
```
### Json, XML format
```python
exclude = ['node_modules']
exclude_patterns = ['*.pyc', '__pycache__']

# String
output_str = folder_tree.print_tree(
    path='.',
    max_depth=2,
    exclude=exclude,
    exclude_patterns=exclude_patterns,
    show_hidden=False,
    include_file_sizes=True,
    output_format='string'
)
print(output_str)

# JSON
output_json = folder_tree.print_tree(
    path='',
    max_depth=1,
    exclude=exclude,
    exclude_patterns=exclude_patterns,
    show_hidden=False,
    include_file_sizes=True,
    output_format='json'
)
print(json.dumps(output_json, indent=4, ensure_ascii=False))

# XML
output_xml = folder_tree.print_tree(
    path='',
    max_depth=1,
    exclude=exclude,
    exclude_patterns=exclude_patterns,
    show_hidden=False,
    include_file_sizes=True,
    output_format='xml'
)
root = ET.Element('root')
for elem in output_xml:
    root.append(elem)
tree = ET.ElementTree(root)
tree.write('output.xml', encoding='utf-8', xml_declaration=True)
```
