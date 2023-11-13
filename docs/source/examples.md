# *stretchable* by Example

## Basics

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
root.compute_layout()

```

## Locating Nodes

```{eval-rst}
.. todo:: Add examples of identifying and locating nodes in a tree. Move example tree/addresses from `Node` API reference to here.
```
