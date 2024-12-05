from folder_treeForLLM import folder_tree

# basic usage
output = folder_tree.print_tree(path='.', max_depth=2)
print(output)


# parameters
output = folder_tree.print_tree(
    path='..',
    max_depth=0,
    exclude=['.git'],
    exclude_patterns=['*.pyc', '__pycache__'],
    show_hidden=False,
    include_file_sizes=True,
    output_format='string',
)
print(output)