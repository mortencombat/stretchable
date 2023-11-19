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
.. todo:: Add examples of identifying and locating nodes in a tree. Move example tree/addresses from `stretchable.Node` API reference to here.
```

Example node tree and corresponding addresses:

.. code-block:: python

    root
    +- header
    +- body
    |  +- left
    |  +- center
    |  |  +- title      /body/center/title   /1/1/0
    |  |  +- content    /body/1/1
    |  +- right
    +- footer           /footer              /2

Examples of relative address when using ``find()`` on the ``body`` node:

.. code-block:: python

    center/title        ->  title
    ./center/title      ->  title
    1/1                 ->  content
    ../footer           -> footer
