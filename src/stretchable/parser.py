from __future__ import annotations

import io
import logging
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Iterable, Optional, Protocol

import cssselect2
import tinycss2
from lxml import etree

from .node import Node
from .style import Style

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


class UnsupportedElementError(Exception):
    ...


class ElementType(Enum):
    # The element contains style rules
    STYLES = auto()
    # The element is the root node
    ROOT = auto()
    # The element is a child node
    CHILD = auto()
    # The element can be skipped silently
    SKIP = auto()
    # The element is unsupported
    UNSUPPORTED = auto()


class NodeFactory(Protocol):
    def get_type(self, element: etree.Element) -> ElementType:
        """Return the type of the element.

        If the type returned is STYLE or SKIP, any child elements will be
        ignored.
        """

    def process_element(
        self, element: etree.Element, fileprovider: FileProvider
    ) -> None:
        """Processes the element, optionally modifying or removing it from the tree."""

    def get_styles(
        self,
        element: etree.Element,
        fileprovider: FileProvider,
    ) -> Iterable[tinycss2.parser.AtRule | tinycss2.parser.QualifiedRule]:
        """Return the style rules from the element.

        If the element links to another file, `fileprovider` should be used to
        get the file.
        """

    def get_node(
        self, tag: str, style: Style, children: list[Node], content: str, **attributes
    ) -> Node:
        """Return a Node instance if possible, otherwise raise UnsupportedElementError."""
        ...


class FileType(Enum):
    XML = "xml"
    XHTML = "xhtml"
    HTML = "html"
    CSS = "css"


class FileProvider(Protocol):
    # TODO: fileprovider should be able to pass either just the filepath, or the contents.
    def read(filepath: Path) -> tuple[str | Path, FileType]:
        ...


class HTMLNodeFactory:
    """A basic implementation of NodeFactory that supports styles from
    <style> elements and <link ... />, and nodes from <body> and <div> elements
    with no content."""

    def process_element(
        self, element: etree.Element, fileprovider: FileProvider
    ) -> None:
        """Processes the element, optionally modifying or removing it from the tree."""
        ...

    def get_type(self, element: etree.Element) -> ElementType:
        # Supported style elements
        if element.tag == "style":
            return ElementType.STYLES
        if element.tag == "link" and "rel" in element.attrib:
            return ElementType.STYLES

        # Supported node elements
        parent = element.getparent()
        if element.tag == "body":
            if parent.tag != "html":
                return ElementType.UNSUPPORTED
            return ElementType.ROOT
        if element.tag == "div":
            if parent.tag not in ("body", "div"):
                return ElementType.UNSUPPORTED
            return ElementType.CHILD

        return ElementType.SKIP

    def get_styles(
        self,
        element: etree.Element,
        fileprovider: FileProvider,
    ) -> Iterable[tinycss2.parser.AtRule | tinycss2.parser.QualifiedRule]:
        """Return the style rules from the element."""

        raise NotImplementedError

    def get_node(
        self, tag: str, style: Style, children: list[Node], content: str, **attributes
    ) -> Node:
        if tag not in ("body", "div"):
            raise UnsupportedElementError(
                "Only <body> and <div> elements are supported"
            )
        if content:
            raise UnsupportedElementError("Elements containing text are not supported")
        for attr, value in attributes.items():
            logger.warn(
                "Attribute '%s' ('%s') is unsupported and will be ignored", attr, value
            )
        return Node(*children, style=style)


class StandardFileProvider:
    """Standard implementation of FileProvider with no preprocessing of files."""

    def read(filepath: Path) -> tuple[str | Path, FileType]:
        if not isinstance(filepath, Path):
            filepath = Path(filepath)


# def load(
#     filepath: Path,
#     *,
#     elementfactory: Optional[NodeFactory] = None,
#     fileprovider: Optional[FileProvider] = None,
# ) -> Node:
#     """Parse XML/HTML from file into a node tree."""

#     if not fileprovider:
#         fileprovider = StandardFileProvider()
#     with fileprovider.open(filepath) as f:
#         return loads(
#             f,
#             elementfactory=elementfactory,
#             fileprovider=fileprovider,
#         )


def loads(
    content: io.BytesIO | io.StringIO | str | bytes,
    *,
    nodefactory: Optional[NodeFactory] = None,
    fileprovider: Optional[FileProvider] = None,
) -> Node:
    """Parse a string, bytes array or stream of an HTML/XML document into a node tree."""

    def iterup(element: etree.Element, method: Callable[[etree.Element], None]):
        """Walks the tree and applies `method` to all elements starting with the
        deepest elements and walking up the tree."""
        for e in element:
            iterup(e, method)
        method(element)

    # TODO: Determine if content is XML/XHTML or HTML.
    is_HTML = True

    if not nodefactory:
        if not is_HTML:
            raise ValueError("`nodefactory` is required for parsing XML")
        nodefactory = HTMLNodeFactory()

    # Parse tree
    parser = etree.HTMLParser() if is_HTML else None
    tree = etree.parse(content, parser)
    root = tree.getroot()

    # Process elements using the nodefactory
    # TODO: should process_element be able to register styles?
    # TODO: How to handle elements that should be skipped but their children should not?
    #       Fx. <html> should not create a node but the contained <body> element should
    #       If there is no parent node, a skipped element will still parse child elements?
    iterup(root, lambda e: nodefactory.process_element(e, fileprovider))

    # Check for any ElementType.STYLE and assemble style rules
    rules = []

    # Build CSS matcher
    matcher = cssselect2.Matcher()
    for rule in rules:
        selectors = cssselect2.compile_selector_list(rule.prelude)
        payload = (rule.prelude, rule.content)
        for selector in selectors:
            matcher.add_selector(selector, payload)

    def element_to_node(element: etree.Element, has_root: bool) -> Node | None:
        print("tag", element.tag)

        # Check element type
        t = nodefactory.get_type(element)
        if t == ElementType.UNSUPPORTED:
            raise UnsupportedElementError
        if t == ElementType.STYLES:
            return None
        if t == ElementType.SKIP and has_root:
            return None
        if t == ElementType.ROOT and has_root:
            raise Exception("There can only be a single root node")
        if t == ElementType.CHILD and not has_root:
            raise Exception("Cannot add child nodes without a root node")

        # if t == ElementType.STYLES or t == ElementType.SKIP:
        #     return None
        # elif t == ElementType.UNSUPPORTED:
        #     raise UnsupportedElementError
        # elif t == ElementType.ROOT and has_root:
        #     raise Exception("There can only be a single root node")
        # elif t == ElementType.CHILD and not has_root:
        #     raise Exception("Cannot add child nodes without a root node")

        if t == ElementType.ROOT:
            has_root = True

        children = []
        for child in element:
            node = element_to_node(child, has_root)
            if node is None:
                continue
            children.append(node)

        # Create style
        style = None

        # Create node
        node = nodefactory.get_node(
            element.tag, style, children, element.text, **element.attrib
        )
        print("node", node)
        return node

    # has_root = False
    root_node = element_to_node(root, False)

    # Walk the tree to create the nodes.
    # get_wrapper = (
    #     cssselect2.ElementWrapper.from_html_root
    #     if is_HTML
    #     else cssselect2.ElementWrapper.from_xml_root
    # )
    # for element in get_wrapper(tree).iter_subtree():
    #     tag = element.etree_element.tag.split("}")[-1]
    #     print('Found tag "{}"'.format(tag))

    #     # Check element type (only include ElementType.NODE)
    #     match nodefactory.get_type(element):
    #         case ElementType.STYLES | ElementType.SKIP:
    #             continue
    #         case ElementType.UNSUPPORTED:
    #             raise UnsupportedElementError
    #         case ElementType.ROOT:
    #             # TODO: If root/parent node is already created, raise error, there cannot be multiple root nodes
    #             ...

    #     matches = matcher.match(element)
    #     if matches:
    #         for match in matches:
    #             specificity, order, pseudo, (prelude, content) = match
    #             print(
    #                 'Matching selector "{}" ({})'.format(
    #                     tinycss2.serialize(prelude), tinycss2.serialize(content)
    #                 )
    #             )
    #     else:
    #         print("No rule matching this tag")

    #     # Create style
    #     style = ...

    #     # Create node
    #     node = nodefactory.get_node(
    #         tag, style, [], element.etree_element.text, **element.etree_element.attrib
    #     )
    #     ...

    return root_node
