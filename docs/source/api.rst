API Reference
=============

.. module:: stretchable

What follows is an API reference. If you'd like a more hands-on tutorial, have a look at :doc:`examples`.

Nodes
-----

.. autoclass:: Node
    :members: address, parent, is_dirty, add, key, is_root, root, style, find, compute_layout, mark_dirty, get_box

.. autoclass:: Box
   
.. autoenum:: Edge()

Styles
------

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

    .. property:: gap
        :type: SizePointsPercent

        Sets the gaps (gutters) between rows and columns in a grid layout
        (default: ``0.0``).

    .. property:: padding
        :type: RectPointsPercent

        Sets the padding area between the :term:`content edge <Content edge>` and the :term:`padding edge <Padding edge>`
        (default: ``0.0``).

    .. property:: border
        :type: RectPointsPercent

        Sets the border area between the :term:`padding edge <Padding edge>` and the :term:`border edge <Border edge>`
        (default: ``0.0``).

    .. property:: margin
        :type: RectPointsPercentAuto

        Sets the margin area between the :term:`border edge <Border edge>` and the :term:`margin edge <Margin edge>`
        (default: ``0.0``).

    .. property:: size
        :type: SizePointsPercentAuto

        Sets the desired width and height of the :term:`border box <box>`
        (default: ``AUTO``).
    
    .. property:: min_size
        :type: SizePointsPercentAuto

        Sets the minimum width and height of the :term:`border box <box>`
        (default: ``AUTO``).

    .. property:: max_size
        :type: SizePointsPercentAuto

        Sets the maximum width and height of the :term:`border box <box>`
        (default: ``AUTO``).

    .. property:: aspect_ratio
        :type: float

        Sets the desired width-to-height of the :term:`border box <box>`
        (default: :py:obj:`None`).

    .. property:: flex_wrap
        :type: FlexWrap

        Sets whether flex items are forced onto one line or can wrap onto multiple lines. If wrapping is allowed, it sets the direction that lines are stacked
        (default: ``NO_WRAP``).

    .. property:: flex_direction
        :type: FlexDirection

        Sets how flex items are placed in the flex container defining the main axis and the direction (normal or reversed)
        (default: ``ROW``).

    .. property:: flex_grow
        :type: float

        Sets the flex grow factor, which specifies how much of the flex container's remaining space should be assigned to the flex item's main size.
        (default: ``0.0``).

    .. property:: flex_shrink
        :type: float

        Sets the flex shrink factor of a flex item. If the size of all flex items is larger than the flex container, items shrink to fit according to flex-shrink
        (default: ``1.0``).

    .. property:: flex_basis
        :type: LengthPointsPercentAuto

        Sets the initial main size of the :term:`border box <box>` of a flex item
        (default: ``AUTO``)

    .. property:: grid_auto_flow
        :type: GridAutoFlow

        Controls how the auto-placement algorithm works, specifying exactly how auto-placed items get flowed into the grid.

    .. property:: grid_template_rows
        :type: list[GridTrackSizing]

        Defines the track sizing functions of the grid rows
        (default: :py:obj:`None`).

    .. property:: grid_template_columns
        :type: list[GridTrackSizing]

        Defines the track sizing functions of the grid columns
        (default: :py:obj:`None`).

    .. property:: grid_auto_rows
        :type: list[GridTrackSize]

        Specifies the size of an implicitly-created grid row track or pattern of tracks.
        (default: :py:obj:`None`).
    
    .. property:: grid_auto_columns
        :type: list[GridTrackSize]

        Specifies the size of an implicitly-created grid column track or pattern of tracks.
        (default: :py:obj:`None`).

    .. property:: grid_row
        :type: GridPlacement

        Specifies a grid item's size and location within a grid row
        (default: ``AUTO``).

    .. property:: grid_column
        :type: GridPlacement

        Specifies a grid item's size and location within a grid column
        (default: ``AUTO``).

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

.. class:: stretchable.style.GridTrackSize

.. class:: stretchable.style.GridTrackSizing

.. class:: stretchable.style.GridPlacement

--------
Geometry
--------

The :mod:`stretchable.style.geometry` module describes :ref:`length <Length>`, :ref:`size <Size>` (2 lengths, typically width and height) and :ref:`rectangles <Rect>` (4 lengths). For each of these, different :ref:`scales <Scale>` (eg. points, percentages, etc.) are available.

All of the classes have different variants which limit the allowed scales for a specific context/setting on the :py:class:`Style` class.

=====
Scale
=====

.. autoenum:: stretchable.style.geometry.Scale()

.. autoenum:: stretchable.style.geometry.Points()

.. autoenum:: stretchable.style.geometry.PointsPercent()

.. autoenum:: stretchable.style.geometry.PointsPercentAuto()

.. autoenum:: stretchable.style.geometry.AvailableSpace()

.. autoenum:: stretchable.style.geometry.MinTrackSize()

.. autoenum:: stretchable.style.geometry.MaxTrackSize()

======
Length
======

.. class:: stretchable.style.geometry.Length(scale: Scale, value: float) -> Length

    Represents a length. For some values of `scale`, `value` is not applicable.

    It is recommended to use the static constructors on the different variants of `Length`, instead of using the constructor directly.

.. todo::
    Add documentation for Length constructors and variants.


====
Size
====


.. class:: stretchable.style.geometry.Size(*values: Length, width: Length = None, height: Length = None) -> Size

    Represents two :ref:`lengths <Length>` (typically the size of a rectangle eg. width and height).

.. todo::
    Add documentation for Size constructors and variants.


====
Rect
====

.. class:: stretchable.style.geometry.Rect(*values: Length, top: Length = None, right: Length = None, bottom: Length = None, left: Length = None) -> Rect

    Represents four :ref:`lengths <Length>`.

.. todo::
    Add documentation for Rect constructors and variants.


Exceptions
----------

.. autoexception:: stretchable.exceptions.TaffyUnavailableError
.. autoexception:: stretchable.exceptions.NodeLocatorError
.. autoexception:: stretchable.exceptions.NodeNotFound
.. autoexception:: stretchable.exceptions.LayoutNotComputedError

.. todo::
    Add documentation for exceptions.

    
