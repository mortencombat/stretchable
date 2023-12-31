from stretchable.parser import loads

filepath = "test.html"

root = loads(filepath)
print(root)
for e in root:
    print(e)

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
