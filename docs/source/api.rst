API Reference
=============

.. module:: stretchable

What follows is an API reference. If you'd like a more hands-on tutorial, have a look at :doc:`examples`.

Node
----

.. autoclass:: Node
    :members:

.. autoclass:: Frame
    :members: offset

.. autoenum:: Box()

Style
-----




Geometry
--------

The :mod:`stretchable.style.geometry` module contains three basic structures: Length, Size and Rect.


------
Length
------



----
Size
----


----
Rect
----

.. todo:: Include the signature and arguments of Rect, then list the other variants and describe what type of parameters they can take, referring to the Length section.

.. autoclass:: stretchable.style.geometry.rect.Rect

.. autoclass:: stretchable.style.geometry.size.SizePoints

.. autoclass:: stretchable.style.geometry.size.SizeAvailableSpace


.. class:: stretchable.style.geometry.size.SizeAvailableSpace

Exceptions
----------

.. autoexception:: stretchable.exceptions.TaffyUnavailableError
.. autoexception:: stretchable.exceptions.NodeLocatorError
.. autoexception:: stretchable.exceptions.NodeNotFound
.. autoexception:: stretchable.exceptions.LayoutNotComputedError
    
    
