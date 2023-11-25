# Overview

**stretchable** uses nodes to represent rectangular blocks or containers, each of which optionally can contain any number of child nodes.

For each node you can define styles according to {ref}`Flexbox` and/or {ref}`CSS Grid`. These define the requirements for the layout of the nodes.

You can assign custom *measure* functions to nodes. Such functions are used by **stretchable** during the computation of the node layout, to be able to determine the appropriate dimensions of the node.

Building a tree of nodes and calculating the layout is as simple as:

```{include} ../../README.md
:start-after: 'Building a tree of nodes and calculating the layout is as simple as:'
:end-before: For more information and details
```

There are several different ways of building the node tree, configuring styles, and locating nodes. See {doc}`examples` for a more in-depth tour of the features of **stretchable**.
