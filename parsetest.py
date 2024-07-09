from stretchable.parser import StandardFileProvider, load

filepath = "test.html"


def print_nodes(node, level: int = 0):
    print(" " * level * 2, node)
    for e in node:
        print_nodes(e, level + 1)


root = load(filepath, fileprovider=StandardFileProvider(filepath))
print_nodes(root)
