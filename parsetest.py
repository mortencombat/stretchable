from stretchable.parser import StandardFileProvider, load

filepath = "test.html"


def print_nodes(node, level: int = 0):
    print(" " * level * 2, node)
    for e in node:
        print_nodes(e, level + 1)


root = load(filepath, fileprovider=StandardFileProvider(filepath))
print_nodes(root)

# from lxml import etree

# filepath = "test.html"

# parser = etree.HTMLParser()

# with open(filepath, "r") as f:
#     tree: etree.ElementTree = etree.parse(f, parser)

# root = tree.getroot()


# def modify_element(e: etree.Element) -> etree.Element:
#     e.tag = "blabla"
#     return e


# print("Tree is now:")
# print(root)

# print("Removing...")
# for e in root:
#     print(e)
#     root.remove(e)

# print("Tree is now:")
# print(root)
# for e in root:
#     print(e)
