# *stretchable* by Example

The following is a tour of the various features of **stretchable** and how to use them.

For a detailed reference, see {doc}`api`.

## Building Node Trees

You can chain {py:class}`stretchable.Node.add()` and create a node tree like this:

```python
from stretchable import Node
from stretchable.style import PCT, AUTO

root = Node(
    margin=20,
    size=(500, 300),
).add(
    Node(border=5, size=(50*PCT, AUTO)),
    Node(padding=10*PCT, size=50*PCT)
)
```

You can also create each node separately and then add child nodes:

```python
from stretchable import Node
from stretchable.style import PCT, AUTO

root = Node(
    margin=20,
    size=(500, 300),
)
child_1 = Node(border=5, size=(50*PCT, AUTO))
root.append(child_1)
child_2 = Node(padding=10*PCT, size=50*PCT)
root.append(child_2)
```

## Configuring Styles

Styles can be specified in different ways, as illustrated here:

```python
from stretchable import Node, Style
from strechable.style import SizePointsPercentAuto

# Using style keyword arguments on the Node constructor:
node = Node(key="content", min_size=SizePointsPercentAuto(width=300))

# Creating a Style instance explicitly:
node = Node(key="content", style=Style(min_size=SizePointsPercentAuto(width=300))
```

Similarly, style arguments that specify a geometry can be specified in different ways, as illustrated here:

```python
from stretchable import Node, Style
from strechable.style import PCT, PT, AUTO

# The following all produce the same result:
# (floats/ints are automatically interpreted as points, PT)
node = Node(key="content", min_size=(300, AUTO))
node = Node(key="content", min_size=SizePointsPercentAuto(width=300))
node = Node(key="content", min_size=SizePointsPercentAuto(width=300*PT))

# Using percentages, both of these produce the same result:
node = Node(key="content", min_size=(AUTO, 50*PCT))
node = Node(key="content", min_size=SizePointsPercentAuto(height=50*PCT))
```

## Locating Nodes

Suppose you have a tree of nodes that looks like this (with the {py:class}`stretchable.Node.key` of each node as shown):

```{eval-rst}
.. mermaid::

    flowchart LR
        A['canvas'] --> B1['header']
        A --> B2['main']
        A --> B3['footer']
        B2 --> C1['left-sidebar'] 
        B2 --> C2['content'] 
        B2 --> C3['right-sidebar'] 
```

You can use {py:class}`stretchable.Node.find()` to locate the nodes as illustrated here:

```python
# Assume you've created a node tree and have a reference to the root node:
canvas_node = ...

# Get the header node
header_node = canvas_node.find("header")

# Get the content node using absolute location:
# (you could use any node in the tree, not just node_header())
content_node = header_node.find("/main/content")

# Get the footer node using relative location:
footer_node = content_node.find("../../header")

# Get the right sidebar node using relative location and indices:
right_sidebar_note = footer_node.find("../1/2")
```

You can get the address of each node from the {py:class}`stretchable.Node.address` property.

## Retrieve Layout

Use {py:class}`stretchable.Node.compute_layout()` on the root node to compute (or recompute) the layout. The layout of the node and all child nodes will be computed. If only part of the node tree has changed, you can invoke layout computation on part of the node tree.

After the layout has been computed, you can get the position and size of each of the nodes using {py:class}`stretchable.Node.get_box()`:

```python
from stretchable import Edge

root = ...  # Build node tree
root.compute_layout()

node = root.find("/main/content")

# Get the position and size of the border box of a node relative to the parent node, 
# with 'y' measured from the top of the container (increasing downwards).
border_box = node.border_box

# The same box can be gotten using get_box() without any arguments (or the defaults).
border_box = node.get_box()

# Get the content box relative to the parent node, 'y' measured from the top.
content_box = node.get_box(Edge.CONTENT)

# Get the content box relative to the root, 'y' measured from the bottom 
# (increasing upwards)
content_box = node.get_box(Edge.CONTENT, relative=False, flip_y=True)
```

## Using *measure* Functions

```{eval-rst}
.. todo:: Add examples of using *measure* functions.
```
