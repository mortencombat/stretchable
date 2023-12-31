# Glossary

:::{glossary}
node
    A node is an element which can contain child nodes and/or other types of content. The position and size of the node on the canvas is determined by the style parameters of the node itself and the content of the node (child nodes or other types of content such as images and text). **stretchable** cannot intrinsically measure node contents (other than child nodes), but a custom measure function can be associated with each node to allow for layouts that include images, text, etc.

leaf node
    A node which does not contain any child nodes.

style
    The style of a node determines the size and position of the node relative to the canvas and other nodes. **stretchable** supports the *CSS Grid* and *Flexbox* styling algorithms.

box
    A box is a rectangle with a certain position (relative to the containing node or the root node) and size. The box can correspond to different edges as defined in the CSS box model. The position and size of the box is the result of a layout computation.

CSS
    Cascading Style Sheets (CSS) is a stylesheet language used to describe the presentation of a document written in HTML or XML. **stretchable** uses the layout elements and algorithms of CSS (as implemented in [Taffy](https://github.com/dioxuslabs/taffy)).

CSS box model
    In CSS, the term "box model" is used when talking about design and layout. The [CSS box model](https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/The_box_model) is essentially a box that wraps around every node/element. It consists of *content*, *padding*, *borders* and *margins*. The image below illustrates the box model:

    ![](_static/box-model.png)

content edge
    The content edge is the box surrounding the content, where text and images appear.

padding edge
    Padding clears an area around the content, between the content and the border. The padding edge is the box surrounding the padding, which also lines up with the inside of the border.

border edge
    The border goes around the padding and content. The border edge is the box surrounding the outside of the border. **stretchable** uses `box-sizing: border-box`, which means that the dimensions (width and height) that you assign to an element corresponds to the border box of the element.

margin edge
    Margin clears an area outside the border. The margin edge is the box surrounding the margin, eg. the outermost bounds of the element.
