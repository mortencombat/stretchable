API Reference
=============

.. module:: stretchable

What follows is an API reference. If you'd like a more hands-on tutorial, have a look at :doc:`examples`.

Node
----

.. autoclass:: Node
    :members: address, parent, is_dirty, key, is_root, root, style, find, compute_layout, mark_dirty, get_box

.. autoclass:: Box
   
.. autoenum:: Edge()

Style
-----

.. class:: Style(**kwargs)

    All :py:obj:`Style` properties listed below can also be passed as keyword arguments when creating a new instance.

    .. note::
       The `Style` class is immutable. To change the style of a node, assign a new Style instance. 

    .. property:: display
        :type: Display

        Used to control node visibility and layout strategy.

    .. property:: overflow
        :type: Overflow

        Controls the desired behavior when content does not fit inside the parent node.

    .. property:: position
        :type: Position

        The positioning strategy for this node.

    .. property:: align_items
        :type: AlignItems

        Used to control how child nodes are aligned.

    .. property:: justify_items
        :type: JustifyItems

        Used to control how child nodes are aligned.

    .. property:: align_self
        :type: AlignSelf

        Used to control how the node is aligned.

    .. property:: justify_self
        :type: JustifySelf

        Used to control how the node is aligned.

    .. property:: align_content
        :type: AlignContent

        Sets the distribution of space between and around content items.

    .. property:: justify_content
        :type: JustifyContent

        Sets the distribution of space between and around content items.

-------
Options
-------

.. autoenum:: stretchable.style.Display()

.. autoenum:: stretchable.style.Overflow()

.. autoenum:: stretchable.style.Position()

=========
Alignment
=========

.. autoenum:: stretchable.style.AlignItems()

.. autoenum:: stretchable.style.JustifyItems()

.. autoenum:: stretchable.style.AlignSelf()

.. autoenum:: stretchable.style.JustifySelf()

.. autoenum:: stretchable.style.AlignContent()

.. autoenum:: stretchable.style.JustifyContent()

=======
Flexbox
=======

.. autoenum:: stretchable.style.FlexWrap()

.. autoenum:: stretchable.style.FlexDirection()

====
Grid
====

.. autoenum:: stretchable.style.GridAutoFlow()

.. autoenum:: stretchable.style.GridIndexType()

.. class:: GridTrackSize


--------
Geometry
--------

The :mod:`stretchable.style.geometry` module contains three basic structures: Length, Size and Rect.


======
Length
======



====
Size
====


====
Rect
====

.. todo:: Include the signature and arguments of Rect, then list the other variants and describe what type of parameters they can take, referring to the Length section.

.. autoclass:: stretchable.style.geometry.rect.Rect

.. autoclass:: stretchable.style.geometry.size.SizePoints

.. autoclass:: stretchable.style.geometry.size.SizeAvailableSpace


Exceptions
----------

.. autoexception:: stretchable.exceptions.TaffyUnavailableError
.. autoexception:: stretchable.exceptions.NodeLocatorError
.. autoexception:: stretchable.exceptions.NodeNotFound
.. autoexception:: stretchable.exceptions.LayoutNotComputedError
    
    
